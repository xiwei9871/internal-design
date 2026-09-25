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

CE = json.load(open(ROOT / 'current_existing/current_existing_v1.json'))
CANONICAL = json.load(open(ROOT / 'current_existing/canonical_plan_v1.json'))

AX, AY = 1298172.0, -296458.0          # task01 origin in abs coords

PRESENTATION_HIDE_LAYERS = {
    'A-WALL-DEMO', 'A-SURVEY-SUPERSEDED', 'A-SURVEY-HATCH',
    'A-QC-ZONE', 'A-ELEM-TAG', 'F-TEXT', 'F-FURN', 'RC-GRILL',
}
PRESENTATION_HIDE_TYPES = {'HATCH', 'DIMENSION'}
REVIEW_HIDE_LAYERS = set()
REVIEW_HIDE_TYPES = set()

# presentation layer restyle (in-memory only — DXF on disk untouched)
PRESENTATION_LAYER_STYLE = {
    'A-GLAZ-EXST': dict(color=153),        # glazing lighter: wall dominates
    'A-OPEN-EXST': dict(color=8),          # opening extents toned down
}
PRESENTATION_LAYER_LINWEIGHT = {'A-GLAZ-EXST': 9, 'A-OPEN-EXST': 9}

WALL_FACE = {  # render-only wall poche, by canonical type
    'exterior':        dict(fc='#8f8f8f', ec='#262626', lw=1.8, z=1),
    'interior':        dict(fc='#c4c4c4', ec='#4d4d4d', lw=1.0, z=1),
    'shaft':           dict(fc='#c4c4c4', ec='#4d4d4d', lw=1.0, z=1),
    'railing_parapet': dict(fc='#eeeeee', ec='#a0a0a0', lw=0.6, z=1),
}
REVIEW_WALL_FACE_ALPHA = 0.45            # review gets a lighter poche underlay
CANONICAL_WALL_TYPES = {'exterior', 'interior', 'shaft', 'railing_parapet'}


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


def _wall_report(wall, hostless_windows=None):
    """Build one wall's render-only fragment and clipped-cut report."""
    wr = [int(v) for v in wall['rect_mm']]
    if not (wr[2] > wr[0] and wr[3] > wr[1]):
        raise ValueError(f"invalid wall rectangle {wall.get('id')}: {wr!r}")
    cuts, clipped_cuts = [], []
    # Ordinary openings are explicit canonical cuts.
    for opening in CANONICAL['openings']:
        clipped = _clip(wr, opening['rect_mm'])
        if clipped:
            item = {'id': opening['id'], 'source_type': 'opening', 'rect_mm': clipped}
            cuts.append(item); clipped_cuts.append(item)
    # Window cuts require a registered host wall; hostless fenestration is
    # retained as metadata only because a gap already present in CAD must not
    # be invented from JSON alone.
    for window in CANONICAL['windows']:
        wid = window.get('window_id') or window.get('name')
        clipped = _clip(wr, window['opening_rect_mm'])
        if not clipped:
            continue
        if window.get('host_wall_id') == wall['id']:
            association = 'parapet_cut' if wall.get('type') == 'railing_parapet' else 'wall_cut'
            item = {'id': wid, 'source_type': 'window', 'association_type': association, 'rect_mm': clipped}
            cuts.append(item); clipped_cuts.append(item)
    # Hostless windows become cuts only when active glazing covers their gap and overlaps this wall.
    if hostless_windows:
        for hw in hostless_windows:
            if hw.get('verified') and (clipped := _clip(wr, hw['rect_mm'])):
                association = 'parapet_cut' if wall.get('type') == 'railing_parapet' else 'wall_cut'
                item={'id':hw['id'],'source_type':'window','association_type':association,'rect_mm':clipped}
                cuts.append(item); clipped_cuts.append(item)
    # De-duplicate identical cuts while retaining all IDs for audit metadata.
    unique_rects = []
    for item in cuts:
        if item['rect_mm'] not in unique_rects:
            unique_rects.append(item['rect_mm'])
    fragments = _fragment_rectangles(wr, unique_rects)
    wall_area = _rect_area(wr)
    cut_union = _cut_union_area(wr, [item['rect_mm'] for item in clipped_cuts])
    report = {
        'wall_id': wall['id'], 'wall_type': wall.get('type', 'interior'),
        'wall_area_mm2': wall_area, 'cut_union_area_mm2': cut_union,
        'fragment_area_mm2': sum(_rect_area(r) for r in fragments),
        'area_error_mm2': wall_area - cut_union - sum(_rect_area(r) for r in fragments),
        'fragment_rects': fragments,
        'cut_ids': [item['id'] for item in clipped_cuts],
        'clipped_cuts': clipped_cuts,
        'hostless_cuts': [],
    }
    if report['area_error_mm2'] != 0:
        raise RuntimeError(f"fragment area mismatch for {wall['id']}: {report}")
    return report


def _active_glazing_rects(dxf_path):
    doc = ezdxf.readfile(str(dxf_path)); out=[]
    for e in doc.modelspace():
        if e.dxf.layer != 'A-GLAZ-EXST': continue
        try:
            b=bbox.extents([e]); r=[int(round(b.extmin.x-AX)),int(round(b.extmin.y-AY)),int(round(b.extmax.x-AX)),int(round(b.extmax.y-AY))]
            if r[2]>r[0] and r[3]>r[1]: out.append(r)
        except Exception: pass
    return out


def _hostless_records(dxf_path):
    glaz=_active_glazing_rects(dxf_path); records=[]
    for w in CANONICAL['windows']:
        if w.get('host_wall_id'): continue
        wr=[int(v) for v in w['opening_rect_mm']]; overlap=any(_clip(wr,g) for g in glaz)
        records.append({'id':w.get('window_id') or w.get('name'),'source_type':'window','rect_mm':wr,
                        'association_type':'active_gap' if overlap else 'unresolved_hostless','verified':bool(overlap)})
    return records


def wall_faces_report(dxf_path=None):
    dxf_path = dxf_path or (CAD / 'design_v02_f1_l1.dxf')
    glaz=_active_glazing_rects(dxf_path); unresolved=[]; walls=[]
    for w in CANONICAL['walls']:
        if w['disposition'] != 'EXISTING': continue
        # Hostless cuts are permitted only with active glazing coverage in the candidate.
        for win in CANONICAL['windows']:
            if win.get('host_wall_id') or not _clip(w['rect_mm'], win['opening_rect_mm']): continue
            if any(_clip(win['opening_rect_mm'], g) for g in glaz):
                win['_active_overlap']=True
        walls.append(_wall_report(w, _hostless_records(dxf_path)))
    return {'walls':walls, 'hostless_fenestration':_hostless_records(dxf_path)}


def draw_wall_faces(ax, profile, dxf_path):
    alignment = validate_canonical_alignment(dxf_path, emit=False)
    report = {'wall_face_ids': [], 'parapet_ids': [], 'cuts': [], 'wall_reports': [], 'alignment': alignment}
    wall_data = wall_faces_report(dxf_path)
    report['hostless_fenestration'] = wall_data['hostless_fenestration']
    for item in wall_data['walls']:
        wid, wtype = item['wall_id'], item['wall_type']
        if wtype == 'railing_parapet':
            report['parapet_ids'].append(wid)
        else:
            report['wall_face_ids'].append(wid)
        report['cuts'] += [{'wall': wid, 'opening': oid} for oid in item['cut_ids']]
        report['wall_reports'].append(item)
        style = WALL_FACE.get(wtype, WALL_FACE['interior'])
        alpha = REVIEW_WALL_FACE_ALPHA if profile == 'CAD_REVIEW' else 1.0
        for r in item['fragment_rects']:
            ax.add_patch(Rectangle((r[0] + AX, r[1] + AY), r[2] - r[0], r[3] - r[1],
                                   facecolor=style['fc'], edgecolor=style['ec'],
                                   lw=style['lw'], zorder=style['z'], alpha=alpha,
                                   joinstyle='miter'))
    return report


def render(dxf_path, profile, name, crop=None, faces=True, label_walls=False):
    """crop: optional task01 rect [x1,y1,x2,y2] used as the view limits."""
    alignment = validate_canonical_alignment(dxf_path, emit=False)
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    if profile == 'PRESENTATION':            # in-memory restyle only
        for ln, st in PRESENTATION_LAYER_STYLE.items():
            if ln in doc.layers:
                doc.layers.get(ln).dxf.color = st['color']
        for ln, lw in PRESENTATION_LAYER_LINWEIGHT.items():
            if ln in doc.layers:
                doc.layers.get(ln).dxf.lineweight = lw
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
    wfaces = draw_wall_faces(ax, profile, dxf_path) if faces else {
        'wall_face_ids': [], 'parapet_ids': [], 'cuts': [], 'wall_reports': [], 'alignment': alignment}
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax, adjust_figure=False)   # never let backend resize the fig
    Frontend(ctx, out).draw_layout(msp, filter_func=keep, finalize=True)
    if label_walls:
        for wl in CE['walls']:
            if wl['disposition'] != 'EXISTING':
                continue
            r = wl['rect_mm']
            ax.text((r[0] + r[2]) / 2 + AX, (r[1] + r[3]) / 2 + AY, wl['id'],
                    fontsize=3.2, color='#aa2200', ha='center', va='center',
                    rotation=0 if (r[2] - r[0]) >= (r[3] - r[1]) else 90, zorder=9)
    ax.set_xlim(vx1, vx2)
    ax.set_ylim(vy1, vy2)
    ax.set_aspect('equal')
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
        'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
        'visible_layers': sorted({e.dxf.layer for e in msp if keep(e)}),
        'hidden_layers': sorted(hide_l),
        'hidden_entity_types': sorted(hide_t),
        'wall_faces': wfaces['wall_face_ids'],
        'parapet_faces': wfaces['parapet_ids'],
        'opening_cuts': wfaces['cuts'],
        'wall_reports': wfaces['wall_reports'],
        'alignment': wfaces['alignment'],
        'hostless_fenestration': wfaces.get('hostless_fenestration', []),
    }
    json.dump(side, open(QC / f'{name}.render.json', 'w'), indent=1, ensure_ascii=False)
    print(f'{name}.png/.pdf  ({profile})  <- {dxf_path.name}')
    return wfaces


def before_after(dxf_path, name, zones):
    """2xN composite: top row = legacy look (no faces), bottom = wall faces."""
    alignment = validate_canonical_alignment(dxf_path, emit=False)
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    keep = lambda e: (e.dxf.layer not in PRESENTATION_HIDE_LAYERS
                      and e.dxftype() not in PRESENTATION_HIDE_TYPES)
    fig, axs = plt.subplots(2, len(zones), figsize=(4.6 * len(zones), 9.5), dpi=150)
    fig.subplots_adjust(wspace=0.06, hspace=0.04)
    for row in range(2):
        for col, (zl, zr) in enumerate(zones.items()):
            ax = axs[row][col]
            ax.set_axis_off()
            if row == 1:
                draw_wall_faces(ax, 'PRESENTATION', dxf_path)
            out = MatplotlibBackend(ax, adjust_figure=False)
            Frontend(RenderContext(doc), out).draw_layout(
                msp, filter_func=keep, finalize=True)
            ax.set_xlim(zr[0] + AX, zr[2] + AX)
            ax.set_ylim(zr[1] + AY, zr[3] + AY)
            ax.set_aspect('equal')
            if row == 0:
                ax.set_title(f'BEFORE — {zl}', fontsize=8)
            else:
                ax.set_title(f'AFTER — {zl}', fontsize=8)
    png = QC / f'{name}.png'
    fig.savefig(png, dpi=150, facecolor='white')
    plt.close(fig)
    print(f'{name}.png  (before/after zones)')


def main():
    validate_canonical_alignment(CAD / 'design_v01_existing_sync.dxf', emit=False)
    validate_canonical_alignment(CAD / 'design_v02_f1_l1.dxf', emit=False)
    render(CAD / 'design_v01_existing_sync.dxf', 'CAD_REVIEW', 'rc4_v01_cad_review')
    render(CAD / 'design_v01_existing_sync.dxf', 'PRESENTATION', 'rc4_v01_presentation')
    render(CAD / 'design_v02_f1_l1.dxf', 'CAD_REVIEW', 'rc4_v02_f1_cad_review')
    render(CAD / 'design_v02_f1_l1.dxf', 'PRESENTATION', 'rc4_v02_f1_presentation')
    # RC4.1 visual check: north balcony must read as open parapet/railing, not wall
    render(CAD / 'design_v01_existing_sync.dxf', 'CAD_REVIEW', 'rc4_v01_open_balcony_check',
           crop=[7200, 10400, 13600, 14000])
    # RC4.2 readability outputs
    ZONES = {
        'living-N-window': [2500, 11000, 7500, 14000],
        'Nbalc-guestbath-guestbed-study': [7400, 9000, 14000, 14000],
        'dining-lifebalc-kitchen': [800, -800, 8300, 5200],
        'smbath-mbath-mbed-smbed': [7400, -800, 16800, 9200],
    }
    before_after(CAD / 'design_v02_f1_l1.dxf', 'rc4_2_wall_display_before_after', ZONES)
    render(CAD / 'design_v02_f1_l1.dxf', 'PRESENTATION', 'rc4_2_wall_readability_check',
           label_walls=True)


if __name__ == '__main__':
    main()
