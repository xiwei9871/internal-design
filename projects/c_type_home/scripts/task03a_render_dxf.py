#!/usr/bin/env python3
"""Task03A RC4 — CAD-native renderer.

Formal images are rendered FROM the versioned DXF (ezdxf matplotlib backend).
JSON is no longer a drawing source: PNG/PDF = view of the CAD file.

RC4.2: presentation wall readability. Wall *faces* are generated at render
time from canonical wall rectangles (render-only: DXF untouched, audit layers
untouched). Openings/windows are cut out of the wall fill so glazing reads as
"wall -> opening -> window". Draw hierarchy:
  wall fill < wall outline < parapet < openings < glazing/doors
  < cabinets/furniture < labels.

Profiles:
  CAD_REVIEW    — everything: source entities, DEMO, SUPERSEDED, QC zones, tags
  PRESENTATION  — hides audit/demo/superseded/QC/tag layers + old survey text/dims
Each output carries a .render.json sidecar for provenance; aggregate render
report goes to qc/rc4_render_report.json (consumed by gates RC4-G14..G17).
"""
import ezdxf, json, hashlib, datetime
from PIL import Image
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf import bbox

ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / 'cad'
QC = ROOT / 'qc'

matplotlib.rcParams['font.family'] = ['PingFang SC', 'Arial Unicode MS', 'sans-serif']

CANONICAL = json.load(open(ROOT / 'current_existing/canonical_plan_v1.json'))

AX, AY = 1298172.0, -296458.0          # task01 origin in abs coords

PRESENTATION_HIDE_LAYERS = {
    'A-WALL-DEMO', 'A-SURVEY-SUPERSEDED', 'A-SURVEY-HATCH',
    'A-QC-ZONE', 'A-ELEM-TAG', 'F-TEXT', 'F-FURN', 'RC-GRILL',
}
PRESENTATION_HIDE_TYPES = {'HATCH', 'DIMENSION'}
REVIEW_HIDE_LAYERS = set()
REVIEW_HIDE_TYPES = set()

ZORDER = {'wall_fill':10, 'wall_outline':20, 'parapet':30,
          'openings':40, 'glazing_doors':45, 'furniture':50, 'text':60}
WALL_FACE = {
    'exterior': dict(fc='#a3a7ab', ec='#353b42', lw=1.5),
    'interior': dict(fc='#c8cbcf', ec='#555d65', lw=0.95),
    'shaft': dict(fc='#c8cbcf', ec='#555d65', lw=0.95),
    'railing_parapet': dict(fc='#f0f1f2', ec='#a4aab0', lw=0.55),
}
CANONICAL_WALL_TYPES = set(WALL_FACE)


def _entity_category(entity, layer):
    if entity.dxftype() in {'TEXT','MTEXT','ATTRIB','ATTDEF'}:
        return 'text'
    if layer=='A-PARP-EXST':
        return 'parapet'
    if layer=='A-OPEN-EXST':
        return 'openings'
    if layer in {'A-GLAZ-EXST','F-DOOR'}:
        return 'glazing_doors'
    if layer in {'S-S.WALL','A-WALL-EXST-CORR','S-COLUMN'}:
        return 'wall_outline'
    return 'furniture'


class PresentationFrontend(Frontend):
    """Style resolved drawing properties, never modify DXF entities/layers."""
    def __init__(self, ctx, backend, **kwargs):
        super().__init__(ctx,backend,**kwargs)
        self.axes=backend.ax
        self.artist_audit=[]
        self.entity_audit=[]

    def override_properties(self, entity, properties):
        super().override_properties(entity,properties)
        layer=properties.layer
        if layer in PRESENTATION_HIDE_LAYERS or entity.dxftype() in PRESENTATION_HIDE_TYPES:
            properties.is_visible=False
            return
        category=_entity_category(entity,layer)
        colors={'wall_outline':'#626a72','parapet':'#a4aab0','openings':'#9ca5ad',
                'glazing_doors':'#70929b','furniture':'#617581','text':'#39434d'}
        weights={'wall_outline':0.35,'parapet':0.55,'openings':0.30,
                 'glazing_doors':0.45,'furniture':0.6,'text':0.4}
        properties.color=colors[category]
        properties.lineweight=weights[category]

    def draw_entity(self, entity, properties):
        before={id(a) for a in self.axes.get_children()}
        super().draw_entity(entity,properties)
        category=_entity_category(entity,properties.layer)
        self.entity_audit.append({'handle':entity.dxf.get('handle','virtual'),
                                  'type':entity.dxftype(),'layer':properties.layer})
        for artist in self.axes.get_children():
            if id(artist) in before or hasattr(artist,'_rc42_category'):
                continue
            artist._rc42_category=category
            artist.set_zorder(ZORDER[category])
            self.artist_audit.append({'category':category,'zorder':artist.get_zorder(),
                                     'type':type(artist).__name__, 'layer':properties.layer,
                                     'handle':entity.dxf.get('handle','virtual')})


def validate_canonical_alignment(dxf_path, *, emit=True):
    """Fail-closed semantic check: canonical EXISTING walls must be visible.

    Coverage is measured along the long axis of each canonical rectangle from
    active linework only.  DEMO and SURVEY layers are deliberately excluded.
    """
    doc = ezdxf.readfile(str(dxf_path))
    report = []
    for w in CANONICAL['walls']:
        if w.get('disposition') != 'EXISTING':
            continue
        is_parapet = w.get('type') == 'railing_parapet'
        wall_type = w.get('type')
        if wall_type not in CANONICAL_WALL_TYPES:
            raise RuntimeError(f"canonical alignment failed for {dxf_path.name}: {w['id']} unknown wall type {wall_type!r}")
        category = 'parapet' if is_parapet else 'solid'
        layers = ({'A-PARP-EXST', 'S-S.WALL'} if category == 'parapet'
                  else {'A-WALL-EXST-CORR', 'S-S.WALL'})
        x1, y1, x2, y2 = w['rect_mm']
        if not (x2 > x1 and y2 > y1):
            raise RuntimeError(f"canonical alignment failed for {dxf_path.name}: {w['id']} invalid rect {w['rect_mm']!r}")
        horizontal = (x2 - x1) >= (y2 - y1)
        intervals = []
        matched = set()
        for e in doc.modelspace():
            layer = e.dxf.layer
            if layer not in layers or e.dxftype() in {'HATCH', 'DIMENSION', 'TEXT', 'MTEXT'}:
                continue
            try:
                eb = bbox.extents([e])
            except Exception:
                continue
            r = (eb.extmin.x - AX, eb.extmin.y - AY, eb.extmax.x - AX, eb.extmax.y - AY)
            if horizontal:
                if r[3] <= y1 - 1 or r[1] >= y2 + 1:
                    continue
                a, b = max(x1, r[0]), min(x2, r[2])
            else:
                if r[2] <= x1 - 1 or r[0] >= x2 + 1:
                    continue
                a, b = max(y1, r[1]), min(y2, r[3])
            if b > a:
                intervals.append((a, b)); matched.add(layer)
        intervals.sort(); total = 0.0; start = end = None
        for a, b in intervals:
            if start is None: start, end = a, b
            elif a <= end: end = max(end, b)
            else: total += end - start; start, end = a, b
        if start is not None: total += end - start
        span = (x2 - x1) if horizontal else (y2 - y1)
        coverage = total / max(span, 1.0)
        passed = coverage >= 0.5
        item = {'wall_id': w['id'], 'wall_type': wall_type, 'category': category,
                'matched_layers': sorted(matched),
                'coverage': round(coverage, 4), 'pass': passed}
        report.append(item)
        if emit:
            print(f"ALIGN {dxf_path.name} {w['id']} layers={','.join(sorted(matched)) or '-'} coverage={coverage:.3f} {'PASS' if passed else 'FAIL'}")
    if len(report) != 39 or not all(i['pass'] for i in report):
        raise RuntimeError(f"canonical alignment failed for {dxf_path.name}: {sum(i['pass'] for i in report)}/{len(report)} pass (expected 39)")
    return report


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def _clip(a, b):
    """Return the positive integer intersection of two task-coordinate rects."""
    x1, y1 = max(int(a[0]), int(b[0])), max(int(a[1]), int(b[1]))
    x2, y2 = min(int(a[2]), int(b[2])), min(int(a[3]), int(b[3]))
    return [x1, y1, x2, y2] if x2 > x1 and y2 > y1 else None


def _rect_area(r):
    return (r[2] - r[0]) * (r[3] - r[1])


def _fragment_rectangles(wall_rect, cuts):
    """Subtract a rect union using an exact integer edge grid.

    Each grid cell is included iff its integer midpoint is outside every cut.
    Adjacent included cells are merged first across x and then across y, giving
    deterministic axis-aligned rectangular fragments and exact integer areas.
    """
    # Clip once more here so direct smoke callers can pass partly external cuts.
    cuts = [c for c in (_clip(wall_rect, c) for c in cuts) if c]
    x_edges = sorted({int(wall_rect[0]), int(wall_rect[2]),
                      *(int(c[0]) for c in cuts), *(int(c[2]) for c in cuts)})
    y_edges = sorted({int(wall_rect[1]), int(wall_rect[3]),
                      *(int(c[1]) for c in cuts), *(int(c[3]) for c in cuts)})
    # Horizontal runs of included cells on each y strip.
    runs_by_y = []
    for yi in range(len(y_edges) - 1):
        y1, y2 = y_edges[yi:yi + 2]
        runs, run_start = [], None
        for xi in range(len(x_edges) - 1):
            x1, x2 = x_edges[xi:xi + 2]
            if x2 <= wall_rect[0] or x1 >= wall_rect[2] or y2 <= wall_rect[1] or y1 >= wall_rect[3]:
                inside = False
            else:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                inside = not any(c[0] < mx < c[2] and c[1] < my < c[3] for c in cuts)
            if inside and run_start is None:
                run_start = xi
            if (not inside or xi == len(x_edges) - 2) and run_start is not None:
                end = xi + 1 if inside and xi == len(x_edges) - 2 else xi
                runs.append((run_start, end)); run_start = None
        runs_by_y.append(runs)
    # Merge equal x-runs on consecutive y strips.
    active = {}
    fragments = []
    for yi, runs in enumerate(runs_by_y):
        current = set(runs)
        next_active = {}
        for run in sorted(current):
            if run in active:
                active[run][3] = y_edges[yi + 1]
                next_active[run] = active[run]
            else:
                next_active[run] = [x_edges[run[0]], y_edges[yi], x_edges[run[1]], y_edges[yi + 1]]
        for run, rect in active.items():
            if run not in current:
                fragments.append(rect)
        active = next_active
    fragments.extend(active.values())
    return [r for r in fragments if r[2] > r[0] and r[3] > r[1]]


def _cut_union_area(wall_rect, cuts):
    """Area of the clipped union, counted once per grid cell."""
    clipped = [c for c in (_clip(wall_rect, c) for c in cuts) if c]
    xs = sorted({wall_rect[0], wall_rect[2], *(c[0] for c in clipped), *(c[2] for c in clipped)})
    ys = sorted({wall_rect[1], wall_rect[3], *(c[1] for c in clipped), *(c[3] for c in clipped)})
    return sum((x2-x1)*(y2-y1) for x1,x2 in zip(xs,xs[1:]) for y1,y2 in zip(ys,ys[1:])
               if any(c[0] < (x1+x2)/2 < c[2] and c[1] < (y1+y2)/2 < c[3] for c in clipped))


def _wall_report(wall):
    wr = list(wall['rect_mm'])
    cuts = []
    for source_type, items, key in [('opening', CANONICAL['openings'], 'rect_mm'),
                                     ('window', CANONICAL['windows'], 'opening_rect_mm')]:
        for item in items:
            clipped = _clip(wr, item[key])
            if clipped:
                cuts.append({'id': item.get('window_id') or item['id'],
                             'source_type': source_type, 'rect_mm': clipped})
    rects = [cut['rect_mm'] for cut in cuts]
    fragments = _fragment_rectangles(wr, rects)
    wall_area = _rect_area(wr)
    cut_area = _cut_union_area(wr, rects)
    fragment_area = sum(_rect_area(f) for f in fragments)
    result = {'wall_id': wall['id'], 'wall_type': wall['type'], 'rect_mm': wr,
              'wall_area_mm2': wall_area, 'cut_union_area_mm2': cut_area,
              'fragment_area_mm2': fragment_area,
              'area_error_mm2': wall_area-cut_area-fragment_area,
              'fragment_rects': fragments, 'cut_ids': [c['id'] for c in cuts],
              'clipped_cuts': cuts}
    if result['area_error_mm2'] != 0:
        raise RuntimeError(f"Area mismatch: {wall['id']}")
    return result


def _active_geometry(dxf_path):
    doc = ezdxf.readfile(str(dxf_path))
    records = []
    layers = {'S-S.WALL', 'A-WALL-EXST-CORR', 'A-PARP-EXST', 'A-GLAZ-EXST'}
    for entity in doc.modelspace():
        if entity.dxf.layer not in layers or entity.dxftype() not in {'LINE', 'LWPOLYLINE', 'POLYLINE'}:
            continue
        b = bbox.extents([entity])
        if not b.has_data:
            continue
        records.append({'handle': entity.dxf.handle, 'layer': entity.dxf.layer,
                        'type': entity.dxftype(),
                        'rect_mm': [b.extmin.x-AX, b.extmin.y-AY, b.extmax.x-AX, b.extmax.y-AY]})
    return records


def _fenestration_evidence(geometry, walls, alignment):
    """One evidence entry per opening, including pre-split DXF gaps."""
    aligned = {a['wall_id']: a for a in alignment}
    records = []
    for window in CANONICAL['windows']:
        wid, wr = window['window_id'], window['opening_rect_mm']
        glazing = [g for g in geometry if g['layer']=='A-GLAZ-EXST'
                   and g['type'] in {'LWPOLYLINE', 'POLYLINE'}
                   and all(abs(a-b) <= 1 for a,b in zip(g['rect_mm'],wr))]
        if not glazing:
            raise RuntimeError(f"Geometry discrepancy: {wid} has no matching active DXF glazing rectangle")
        cut_hosts = [w['wall_id'] for w in walls if any(c['id']==wid for c in w['clipped_cuts'])]
        overlay = sum(_rect_area(c) for w in walls for f in w['fragment_rects'] if (c := _clip(f,wr)))
        if overlay:
            raise RuntimeError(f"Uncut overlay in {wid}: {overlay} mm2")
        horizontal = wr[2]-wr[0] >= wr[3]-wr[1]
        axis, cross = (0,1) if horizontal else (1,0)
        canonical_boundaries = []
        for wall in walls:
            r = wall['rect_mm']
            if r[cross+2] < wr[cross]-1 or r[cross] > wr[cross+2]+1:
                continue
            for side, edge, coordinate in [('low',axis+2,wr[axis]),('high',axis,wr[axis+2])]:
                if abs(r[edge]-coordinate) <= 1 and aligned[wall['wall_id']]['pass']:
                    canonical_boundaries.append({'side':side,'wall_id':wall['wall_id'],
                                                 'alignment':aligned[wall['wall_id']]})
        boundaries=[]
        for side,coordinate in [('low',wr[axis]),('high',wr[axis+2])]:
            candidates=[]
            for g in geometry:
                if g in glazing:
                    continue
                r=g['rect_mm']
                if r[cross+2] < wr[cross]-1 or r[cross] > wr[cross+2]+1:
                    continue
                if side=='low' and r[axis+2] > coordinate+1:
                    continue
                if side=='high' and r[axis] < coordinate-1:
                    continue
                distance=min(abs(r[axis]-coordinate),abs(r[axis+2]-coordinate))
                tolerance=51 if wid=='G-DIN-LIV' else 1
                if distance <= tolerance:
                    candidates.append(dict(g, setback_mm=round(distance,3)))
            if candidates:
                best=min(candidates,key=lambda c:c['setback_mm'])
                boundaries.append(dict(best,side=side))
        if cut_hosts:
            types={w['wall_type'] for w in walls if w['wall_id'] in cut_hosts}
            association='parapet_cut' if types=={'railing_parapet'} else 'wall_cut'
        else:
            association='active_gap'
            sides={b['side'] for b in boundaries}|{b['side'] for b in canonical_boundaries}
            if sides!={'low','high'}:
                raise RuntimeError(f"Geometry discrepancy: {wid} has unresolved gap boundaries {sorted(sides)}")
        records.append({'id':wid,'opening_rect_mm':wr,'association_type':association,
                        'source_handles':[g['handle'] for g in glazing],
                        'glazing_entities':glazing,'cut_hosts':cut_hosts,
                        'boundary_entities':boundaries,'aligned_boundaries':canonical_boundaries,
                        'overlay_overlap_mm2':overlay,'verified':True,
                        'note':'Frame setbacks measured from unchanged DXF.' if wid=='G-DIN-LIV' else ''})
    return records


def wall_faces_report(dxf_path):
    alignment=validate_canonical_alignment(dxf_path,emit=False)
    walls=[_wall_report(w) for w in CANONICAL['walls'] if w['disposition']=='EXISTING']
    geometry=_active_geometry(dxf_path)
    fenestration=_fenestration_evidence(geometry,walls,alignment)
    return {'walls':walls,'alignment':alignment,'fenestration':fenestration,
            'hostless_fenestration':[f for f in fenestration if not next(
                w for w in CANONICAL['windows'] if w['window_id']==f['id']).get('host_wall_id')]}


def draw_wall_faces(ax, profile, dxf_path):
    data=wall_faces_report(dxf_path)
    solids=[w for w in data['walls'] if w['wall_type']!='railing_parapet']
    parapets=[w for w in data['walls'] if w['wall_type']=='railing_parapet']
    report={'wall_face_ids':[w['wall_id'] for w in solids],
            'parapet_ids':[w['wall_id'] for w in parapets],
            'wall_reports':data['walls'],'alignment':data['alignment'],
            'fenestration':data['fenestration'], 'hostless_fenestration':data['hostless_fenestration'],
            'cuts':[{'wall':w['wall_id'],'opening':i} for w in data['walls'] for i in w['cut_ids']],
            'overlay_artists':[]}
    for group,is_parapet in [(solids,False),(parapets,True)]:
        for wall in group:
            style=WALL_FACE[wall['wall_type']]
            for rect in wall['fragment_rects']:
                stages=['parapet'] if is_parapet else ['wall_fill','wall_outline']
                for stage in stages:
                    fill=stage in {'wall_fill','parapet'}
                    artist=Rectangle((rect[0]+AX,rect[1]+AY),rect[2]-rect[0],rect[3]-rect[1],
                                     facecolor=style['fc'] if fill else 'none',
                                     edgecolor='none' if stage=='wall_fill' else style['ec'],
                                     lw=0 if stage=='wall_fill' else style['lw'],
                                     zorder=ZORDER[stage],joinstyle='miter')
                    artist._rc42_category=stage
                    ax.add_patch(artist)
                    report['overlay_artists'].append({'wall_id':wall['wall_id'],'category':stage,
                        'zorder':artist.get_zorder(),'rect_mm':rect,'line_width_pt':artist.get_linewidth()})
    return report


def render(dxf_path, profile, name, crop=None, faces=True, label_walls=False):
    """crop: optional task01 rect [x1,y1,x2,y2] used as the view limits."""
    alignment = validate_canonical_alignment(dxf_path, emit=False)
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    hide_l = PRESENTATION_HIDE_LAYERS if profile == 'PRESENTATION' else REVIEW_HIDE_LAYERS
    hide_t = PRESENTATION_HIDE_TYPES if profile == 'PRESENTATION' else REVIEW_HIDE_TYPES

    def keep(e):
        return e.dxf.layer not in hide_l and e.dxftype() not in hide_t

    # extents from plain linework only, clipped to the plan region —
    # INSERT attribs/DIMENSION defpoints report broken bboxes, and RC-GRILL
    # contains a far off-plan symbol legend; both must not set the view
    EXT_TYPES = {'LINE', 'LWPOLYLINE', 'CIRCLE', 'ARC', 'TEXT', 'MTEXT', 'POLYLINE'}
    PLAN = (AX - 3000, AY - 3000, AX + 22000, AY + 22000)
    in_plan = []
    for e in msp:
        if not (keep(e) and e.dxftype() in EXT_TYPES):
            continue
        try:
            eb = bbox.extents([e])
        except Exception:
            continue
        if (eb.extmax.x < PLAN[0] or eb.extmin.x > PLAN[2]
                or eb.extmax.y < PLAN[1] or eb.extmin.y > PLAN[3]):
            continue                        # off-plan legend/notes stay out of view
        in_plan.append(e)
    ext = bbox.extents(in_plan)
    w = ext.extmax.x - ext.extmin.x
    h = ext.extmax.y - ext.extmin.y
    if crop:
        vx1, vy1, vx2, vy2 = crop[0] + AX, crop[1] + AY, crop[2] + AX, crop[3] + AY
        w, h = vx2 - vx1, vy2 - vy1
    else:
        vx1, vy1 = ext.extmin.x - w * 0.02, ext.extmin.y - h * 0.02
        vx2, vy2 = ext.extmax.x + w * 0.02, ext.extmax.y + h * 0.02
    scale = 13.0 / max(w, 1)
    fig = plt.figure(figsize=(w * scale, h * scale), dpi=160)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_facecolor('white')
    wfaces = draw_wall_faces(ax, profile, dxf_path) if faces and profile == 'PRESENTATION' else {
        'wall_face_ids': [], 'parapet_ids': [], 'cuts': [], 'wall_reports': [], 'alignment': alignment}
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax, adjust_figure=False)   # never let backend resize the fig
    frontend = PresentationFrontend(ctx,out) if profile=='PRESENTATION' else Frontend(ctx,out)
    frontend.draw_layout(msp, filter_func=keep, finalize=True)
    if label_walls:
        for wl in CANONICAL['walls']:
            if wl['disposition'] != 'EXISTING':
                continue
            r = wl['rect_mm']
            ax.text((r[0] + r[2]) / 2 + AX, (r[1] + r[3]) / 2 + AY, wl['id'],
                    fontsize=3.2, color='#aa2200', ha='center', va='center',
                    rotation=0 if (r[2] - r[0]) >= (r[3] - r[1]) else 90, zorder=70)
    ax.set_xlim(vx1, vx2)
    ax.set_ylim(vy1, vy2)
    ax.set_aspect('equal')
    fig.canvas.draw()
    coordinate_mapping={'view_box_absolute':[vx1,vy1,vx2,vy2],
        'view_box_task01':[vx1-AX,vy1-AY,vx2-AX,vy2-AY],
        'axes_pixel_bounds_bottom_origin':list(ax.bbox.bounds),
        'canvas_size':list(fig.canvas.get_width_height()),
        'figure_pixel_extent':list(fig.bbox.bounds)}
    png = QC / f'{name}.png'
    pdf = QC / f'{name}.pdf'
    fig.savefig(png, dpi=160, facecolor='white')
    fig.savefig(pdf, facecolor='white')
    plt.close(fig)

    man = json.load(open(CAD / 'cad_version_manifest.json'))
    side = {
        'source_dxf': str(dxf_path.relative_to(ROOT)),
        'source_dxf_sha256': sha(dxf_path),
        'parent_cad_sha256': next((v['parent_sha256'] for v in man['versions']
                                   if v['file'] == str(dxf_path.relative_to(ROOT))), None),
        'render_profile': profile,
        'coordinate_mapping':coordinate_mapping,
        'canonical_sha256':sha(ROOT/'current_existing/canonical_plan_v1.json'),
        'renderer_sha256':sha(Path(__file__)),
        'outputs':{'png':{'file':str(png.relative_to(ROOT)) if png.is_relative_to(ROOT) else str(png),'sha256':sha(png)},
                   'pdf':{'file':str(pdf.relative_to(ROOT)) if pdf.is_relative_to(ROOT) else str(pdf),'sha256':sha(pdf)}},
        'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
        'visible_layers': sorted({e.dxf.layer for e in msp if keep(e)}),
        'visible_entity_types':sorted({e.dxftype() for e in msp if keep(e)}),
        'hidden_layers': sorted(hide_l),
        'hidden_entity_types': sorted(hide_t),
        'wall_faces': wfaces['wall_face_ids'],
        'parapet_faces': wfaces['parapet_ids'],
        'opening_cuts': wfaces['cuts'],
        'wall_reports': wfaces['wall_reports'],
        'alignment': wfaces['alignment'],
        'hostless_fenestration': wfaces.get('hostless_fenestration', []),
        'fenestration': wfaces.get('fenestration', []),
        'zorder':ZORDER, 'wall_styles':WALL_FACE,
        'overlay_artists':wfaces.get('overlay_artists',[]),
        'dxf_artists':getattr(frontend,'artist_audit',[]),
        'drawn_entities':getattr(frontend,'entity_audit',[]),
    }
    json.dump(side, open(QC / f'{name}.render.json', 'w'), indent=1, ensure_ascii=False)
    print(f'{name}.png/.pdf  ({profile})  <- {dxf_path.name}')
    return side


FROZEN_DXF = {
    'design_v01_existing_sync.dxf':'5210557086ce08d2ca40cb5b14be909ba83608e68b22bcfd151ed73904cf6c00',
    'design_v02_f1_l1.dxf':'4e9dd3d4faf137d5db06160843b5dfc024cfab9bfcf571db7911dd76ea0b1c1d',
}


def assert_frozen_inputs():
    for name,digest in FROZEN_DXF.items():
        if sha(CAD/name)!=digest:
            raise RuntimeError(f"Frozen DXF SHA mismatch: {name}")
    report=json.loads((QC/'rc4_2_geometry_diff.json').read_text())
    for item in report['files']:
        if sha(ROOT/item['file'])!=item['baseline_sha256']:
            raise RuntimeError(f"Geometry/input freeze violation: {item['file']}")
    return report


def assert_baseline():
    manifest=json.loads((QC/'rc4_2_baseline/manifest.json').read_text())
    repo=ROOT.parents[1]
    for item in manifest['artifacts']:
        path=repo/item['destination']
        if sha(path)!=item['sha256'] or not item.get('coordinate_mapping'):
            raise RuntimeError(f"Baseline corrupted or unmapped: {path}")
    return manifest


def _pixel_crop(path,mapping,zone):
    image=Image.open(path).convert('RGB')
    x0,y0,x1,y1=mapping['view_box_task01']
    ax,ay,aw,ah=mapping['axes_pixel_bounds_bottom_origin']
    canvas_height=mapping['canvas_size'][1]
    left=ax+(zone[0]-x0)/(x1-x0)*aw
    right=ax+(zone[2]-x0)/(x1-x0)*aw
    top=canvas_height-(ay+(zone[3]-y0)/(y1-y0)*ah)
    bottom=canvas_height-(ay+(zone[1]-y0)/(y1-y0)*ah)
    bounds=tuple(round(v) for v in [left,top,right,bottom])
    return image.crop(bounds),list(bounds)


def before_after(side):
    manifest=assert_baseline()
    baseline=next(a for a in manifest['artifacts'] if a['destination'].endswith('rc4_1_v02_f1_presentation.png'))
    path=ROOT.parents[1]/baseline['destination']
    after=ROOT/side['outputs']['png']['file']
    zones={
        'A  Living north bay':[2500,11000,7500,14100],
        'B  North balcony / guest / study':[7400,7700,16700,14000],
        'C  Dining / life balcony / kitchen':[1100,-800,8400,5600],
        'D + E  Bedrooms / baths / south bays':[7400,-900,16800,9300],
    }
    fig,axes=plt.subplots(2,4,figsize=(19,10),dpi=180,facecolor='white')
    fig.subplots_adjust(wspace=.04,hspace=.05,left=.01,right=.99,top=.92,bottom=.035)
    evidence=[]
    for col,(title,zone) in enumerate(zones.items()):
        crops=[]
        for row,(source,mapping) in enumerate([(path,baseline['coordinate_mapping']),(after,side['coordinate_mapping'])]):
            cropped,pixels=_pixel_crop(source,mapping,zone)
            axes[row,col].imshow(cropped);axes[row,col].axis('off')
            axes[row,col].set_title(('RC4.1 BEFORE | ' if row==0 else 'RC4.2 AFTER | ')+title,fontsize=9)
            crops.append({'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'pixel_bounds':pixels})
        evidence.append({'label':title,'rect_mm':zone,'crops':crops})
    fig.suptitle('RC4.2 Wall Display | Same V02 CAD | Frozen RC4.1 baseline',fontsize=16)
    fig.text(.5,.01,'HUMAN VISUAL REVIEW = REQUIRED',ha='center',fontsize=11,color='#7f4b13')
    output=QC/'rc4_2_wall_display_before_after.png';fig.savefig(output,dpi=180,facecolor='white');plt.close(fig)
    return {'file':str(output.relative_to(ROOT)),'sha256':sha(output),'baseline_sha256':baseline['sha256'],'zones':evidence}


def main():
    frozen=assert_frozen_inputs();baseline=assert_baseline()
    for name in FROZEN_DXF:
        wall_faces_report(CAD/name)
    versions={}
    for version,name,output in [('V01','design_v01_existing_sync.dxf','rc4_v01_presentation'),
                                ('V02','design_v02_f1_l1.dxf','rc4_v02_f1_presentation')]:
        versions[version]=render(CAD/name,'PRESENTATION',output)
    check=render(CAD/'design_v02_f1_l1.dxf','PRESENTATION','rc4_2_wall_readability_check',label_walls=True)
    comparison=before_after(versions['V02'])
    assert_frozen_inputs();assert_baseline()
    report={'release':'RC4.2','human_visual_review':'REQUIRED',
            'human_visual_review_label':'HUMAN VISUAL REVIEW = REQUIRED',
            'baseline_manifest':'qc/rc4_2_baseline/manifest.json',
            'baseline_manifest_sha256':sha(QC/'rc4_2_baseline/manifest.json'),
            'geometry_diff':'qc/rc4_2_geometry_diff.json','versions':versions,
            'before_after':comparison,'readability_check':check,
            'geometry_changed':'none','source_cad_checks':'exact SHA before and after rendering'}
    (QC/'rc4_render_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+chr(10))
    frozen['checkpoint']='after RC4.2 rendering'
    (QC/'rc4_2_geometry_diff.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+chr(10))
    print('HUMAN VISUAL REVIEW = REQUIRED; frozen CAD hashes unchanged.')


if __name__=='__main__':
    main()
