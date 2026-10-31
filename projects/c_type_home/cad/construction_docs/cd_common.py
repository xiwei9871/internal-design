"""C-Type construction docs CD_V01 — shared base for A202 / A201.

Source hierarchy (highest first):
  1. A103 V7 plan (survey-based walls/openings + approved changes)  -> walls, windows, doors, dims
  2. Owner decisions (levels, ceiling step x=8000 / y=10900, 150 drop) -> OWNER below
  3. Design model WHOLE_HOUSE_CORRECTED_SUPPORTED_V2.blend (read-only)  -> room zones, materials, fixtures
Model geometry is read from inputs/plan_extract.json (extract_plan_geometry.py). Never from renders.
"""
import hashlib, json, math
from pathlib import Path

import ezdxf
from ezdxf.addons import Importer
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
INP = HERE / 'inputs'
A103 = INP / 'A103_CONSTRUCTION_POC_V7.dxf'
EXTRACT = INP / 'plan_extract.json'
INVENTORY = INP / 'model_inventory.json'
WORK, ISSUE, DATA = HERE / 'work', HERE / 'issue', HERE / 'data'

OWNER = {
    'floor_low': 0, 'floor_high': 450,
    'soffit_low': 2800, 'soffit_high': 3250,
    'drop': 150,                                   # finished ceiling = soffit - drop
    'step_path': [(8000, 4700), (8000, 10900), (13100, 10900)],   # P0.3.2 transition path
    'source': 'owner decision 2026-10-31 + P03_CEILING_SCHEME_A.md (P0.3.2, merged 2026-10-20)',
}
WALL_LAYERS = ('A-WALL', 'A-DESIGN', 'A-REVIEW', 'A-CONFLICT')
UNDERLAY = WALL_LAYERS + ('A-WINDOW', 'A-DOOR', 'A-STAIR')
H_TXT, H_SMALL, H_TINY, H_TITLE = 175, 125, 100, 300
NAMES = {
    'mother_bedroom': '主卧(母亲)', 'couple_bedroom': '次主卧(业主)', 'study': '书房',
    'guest_bedroom': '客卧', 'master_bath': '主卫', 'secondary_bath': '次主卫',
    'guest_bath': '客卫', 'hallway': '走廊', 'kitchen': '厨房', 'north_sunroom': '阳光房',
    'service_balcony': '生活阳台', 'living': '客厅/餐厅/玄关', 'stair': '三级台阶',
    'vestibule': '主卧/主卫前过道',
}
WET = {'master_bath', 'secondary_bath', 'guest_bath', 'kitchen', 'service_balcony'}
BATHS = {'master_bath', 'secondary_bath', 'guest_bath'}


def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def polys(g):
    if g is None or g.is_empty: return []
    if g.geom_type == 'Polygon': return [g]
    return [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']


def union_tris(tris):
    return unary_union([Polygon(t[:3]) for t in tris if Polygon(t[:3]).area > 1]).buffer(0)


def high_region():
    """Owner ceiling scheme: high (3250) = x>=8000 south of y=10900 up to x=13100, and all x>=13100."""
    return unary_union([box(8000, -1e5, 13100, 10900), box(13100, -1e5, 1e5, 1e5)])


class Base:
    def __init__(self):
        self.src = ezdxf.readfile(A103)
        self.ext = json.loads(EXTRACT.read_text())
        self.inv = json.loads(INVENTORY.read_text())['objects']
        msp = self.src.modelspace()

        def lw(layers):
            out = []
            for e in msp.query('LWPOLYLINE'):
                pts = list(e.get_points('xy'))
                if e.dxf.layer in layers and len(pts) >= 3:
                    p = Polygon(pts).buffer(0)
                    if p.area > 100: out.append(p)
            return out
        self.walls = unary_union(lw(WALL_LAYERS)).buffer(0)
        self.windows = [box(*p.bounds) for p in lw(('A-WINDOW',))]
        self.doors = [box(*p.bounds) for p in lw(('A-DOOR',))]
        self._spaces()
        self._zones()

    # ---------- independent interior reference (survey CAD only, no buffer closing) ----------
    def _spaces(self):
        solid = unary_union([self.walls] + self.windows + self.doors).buffer(1).buffer(-1)
        win = unary_union(self.windows)
        self.spaces = []
        for p in polys(solid):
            for ring in p.interiors:
                h = Polygon(ring)
                if h.area < 0.1e6: continue
                share = h.boundary.intersection(win.buffer(5)).length / h.length
                if h.buffer(-100).is_empty: kind = 'NICHE_THIN'
                elif share >= 0.3 and h.area < 2e6: kind = 'BAY_NICHE'
                else: kind = 'ROOM'
                self.spaces.append({'geom': h, 'kind': kind, 'window_share': round(share, 2)})
        self.interior = unary_union([s['geom'] for s in self.spaces if s['kind'] == 'ROOM'])

    # ---------- floor zones from model meshes ----------
    def _zones(self):
        F, S = self.ext['floor'], self.ext['stair']
        lower = union_tris(F['FLOOR_LOWER']['tris'])
        upper = union_tris(F['R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD']['tris'])
        steps = {k: union_tris(v['tris']) for k, v in S.items()}
        self.step_levels = {k: sorted({t[3] for t in v['tris']})[-1] for k, v in S.items()}
        stair = unary_union(list(steps.values()))
        Z = {}
        for k, v in F.items():
            if not k.startswith('PRESENTATION_'): continue
            key = k.split('_', 2)[2]
            Z[key] = {'geom': union_tris(v['tris']), 'mat': 'TILE' if 'TILE' in v['mats'][0] else 'WOOD',
                      'level': OWNER['floor_high'] if v['tris'][0][3] > 200 else OWNER['floor_low'],
                      'source': f'model:{k} ({v["mats"][0]})', 'status': 'MODEL'}
        Z['stair'] = {'geom': stair, 'mat': 'WOOD', 'level': None,
                      'source': 'model:STEP_0/1/2', 'status': 'MODEL'}
        named = unary_union([z['geom'] for z in Z.values()])
        for z in Z.values(): z['geom'] = z['geom'].intersection(self.interior).buffer(0)
        self.records = []
        resid = unary_union([lower, upper]).intersection(self.interior).difference(named)
        living = []
        for p in polys(resid.buffer(-20).buffer(20)):
            lvl = OWNER['floor_low'] if p.intersection(lower).area > p.intersection(upper).area else OWNER['floor_high']
            if lvl == 0 and p.area >= 3e6: living.append(p)
            else: self._merge(Z, p, 'MODEL_RESIDUAL', lvl)
        Z['living'] = {'geom': unary_union(living), 'mat': 'WOOD', 'level': OWNER['floor_low'],
                       'source': 'model:FLOOR_LOWER minus named zones (AM2_WOOD_FLOOR_BOARDS)', 'status': 'MODEL'}
        self.zones = Z
        self._fill_gaps(lower, upper)
        self.model_spill = unary_union([lower, upper, stair]).difference(self.interior).difference(self.walls)

    def _neighbors(self, p, dist=300, level=None):
        out = []
        for k, z in self.zones.items():
            if level is not None and z['level'] not in (level, None): continue
            L = p.boundary.intersection(z['geom'].buffer(dist)).length
            if L > 50: out.append((L, k))
        return [k for _, k in sorted(out, reverse=True)]

    def _merge(self, Z, p, why, level=None):
        self.zones = Z
        nb = self._neighbors(p, 60, level) or self._neighbors(p, 300, level)
        if not nb:
            self.records.append({'type': why, 'action': 'HOLD_UNASSIGNED', 'area_m2': round(p.area / 1e6, 3),
                                 'at': [round(c) for c in p.representative_point().coords[0]]})
            return
        Z[nb[0]]['geom'] = unary_union([Z[nb[0]]['geom'], p]).buffer(0)
        if p.area > 0.05e6:
            self.records.append({'type': why, 'action': f'MERGED_INTO:{nb[0]}', 'area_m2': round(p.area / 1e6, 3),
                                 'at': [round(c) for c in p.representative_point().coords[0]]})

    def _fill_gaps(self, lower, upper):
        Z = self.zones
        gaps = self.interior.difference(unary_union([z['geom'] for z in Z.values()]))
        for p in sorted(polys(gaps), key=lambda q: -q.area):
            if p.area < 0.02e6: continue
            if p.area < 0.3e6 or p.buffer(-150).is_empty:
                self._merge(Z, p, 'SLIVER'); continue
            nb = self._neighbors(p, 300)
            levels = {Z[k]['level'] for k in nb if Z[k]['level'] is not None}
            dry = [Z[k]['mat'] for k in nb if k not in WET]
            key = 'vestibule' if {'master_bath', 'mother_bedroom'} <= set(nb) else f'fill_{len(self.records)}'
            Z[key] = {'geom': p, 'mat': max(set(dry), key=dry.count) if dry else 'WOOD',
                      'level': levels.pop() if len(levels) == 1 else None,
                      'source': f'survey-enclosed interior (A103 walls+openings); neighbours {nb}',
                      'status': 'FILLED_FROM_ENCLOSURE; material OWNER_REVIEW; level SITE_VERIFY_REQUIRED'}
            self.records.append({'type': 'INTERIOR_MISSING', 'action': f'FILLED:{key}',
                                 'area_m2': round(p.area / 1e6, 3), 'neighbours': nb,
                                 'level': Z[key]['level'], 'material': Z[key]['mat'],
                                 'at': [round(c) for c in p.representative_point().coords[0]]})

    def zone_at(self, x, y, tol=60):
        pt = Point(x, y)
        for k, z in self.zones.items():
            if z['geom'].buffer(tol).contains(pt): return k
        return None

    def model_doors(self):
        """Door leaves in the model that cross A103 walls (A103 shows no opening there)."""
        out = []
        for o in self.inv:
            b = o['b']
            dx, dy = b[2] - b[0], b[3] - b[1]
            if not (b[4] <= 500 and b[5] - b[4] > 1800 and min(dx, dy) <= 120 and max(dx, dy) >= 500): continue
            if not any(t in o['n'] for t in ('LEAF', 'SLIDING')): continue
            r = box(*b[:4])
            if r.intersection(self.walls).area / r.area > 0.2 and \
                    not any(r.intersection(d).area / r.area > 0.2 for d in self.doors):
                horiz = dx > dy
                band = box(b[0], b[1] - 110, b[2], b[3] + 110) if horiz else box(b[0] - 110, b[1], b[2] + 110, b[3])
                out.append({'name': o['n'], 'leaf': b, 'rect': band, 'horiz': horiz})
        return out

    def find_objects(self, pattern, region=None):
        import re
        rx = re.compile(pattern)
        out = []
        for o in self.inv:
            if not rx.search(o['n']): continue
            c = Point((o['b'][0] + o['b'][2]) / 2, (o['b'][1] + o['b'][3]) / 2)
            if region is None or region.contains(c): out.append(o)
        return out

    # ---------- sheet ----------
    def new_sheet(self):
        doc = ezdxf.new('R2010', setup=True)
        doc.header['$INSUNITS'] = 4
        st = doc.styles.get('Standard'); st.dxf.font = 'gbenor.shx'; st.dxf.bigfont = 'gbcbig.shx'
        msp = doc.modelspace()
        imp = Importer(self.src, doc)
        imp.import_entities([e for e in self.src.modelspace() if e.dxf.layer in UNDERLAY
                             and e.dxftype() not in ('TEXT', 'MTEXT', 'DIMENSION')])
        imp.finalize()
        for ln in UNDERLAY:
            if ln in doc.layers:
                doc.layers.get(ln).color = 8
                doc.layers.get(ln).dxf.lineweight = 25 if ln in WALL_LAYERS else 18
        layer(doc, 'A-WALL-FILL', 253)
        hatch(msp, self.walls, 'A-WALL-FILL')
        self._dims(doc)
        return doc

    def _dims(self, doc):
        layer(doc, 'A-DIMS', 3, 13)
        if 'CD50' not in doc.dimstyles:
            doc.dimstyles.new('CD50', dxfattribs={
                'dimtxt': 150, 'dimasz': 100, 'dimexo': 80, 'dimexe': 100, 'dimgap': 40,
                'dimdec': 0, 'dimtad': 1, 'dimtxsty': 'Standard', 'dimblk': 'ARCHTICK',
                'dimclrd': 3, 'dimclre': 3, 'dimclrt': 3})
        msp = doc.modelspace()
        self.dims = []
        for d in self.src.modelspace().query('DIMENSION'):
            if d.dxf.layer != 'A-DIMS' or d.dimtype not in (0, 1): continue
            p1, p2, base = d.dxf.defpoint2, d.dxf.defpoint3, d.dxf.defpoint
            xy = lambda v: (v.x, v.y)
            nd = msp.add_linear_dim(base=xy(base), p1=xy(p1), p2=xy(p2), angle=d.dxf.get('angle', 0),
                                    dimstyle='CD50', dxfattribs={'layer': 'A-DIMS'})
            nd.render()
            self.dims.append({'p1': [round(p1.x), round(p1.y)], 'p2': [round(p2.x), round(p2.y)],
                              'value': round(nd.dimension.get_measurement())})


def layer(doc, name, color, lw=25, linetype='Continuous'):
    if name not in doc.layers:
        if linetype not in doc.linetypes: linetype = 'Continuous'
        doc.layers.new(name, dxfattribs={'color': color, 'lineweight': lw, 'linetype': linetype})
    return name


def text(msp, x, y, s, h=H_TXT, lay='A-NOTE', align='MIDDLE_CENTER', rot=0):
    t = msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': lay, 'style': 'Standard'})
    t.set_placement((x, y), align=TextEntityAlignment[align])
    return t


def outline(msp, g, lay, closed=True):
    for p in polys(g):
        for ring in [p.exterior] + list(p.interiors):
            msp.add_lwpolyline([(round(x, 1), round(y, 1)) for x, y in ring.coords[:-1]], close=closed,
                               dxfattribs={'layer': lay})


def hatch(msp, g, lay, pattern='SOLID', scale=1.0, angle=0):
    for p in polys(g):
        h = msp.add_hatch(color=256, dxfattribs={'layer': lay})
        h.paths.add_polyline_path(list(p.exterior.coords)[:-1], is_closed=True)
        for r in p.interiors: h.paths.add_polyline_path(list(r.coords)[:-1], is_closed=True)
        if pattern == 'SOLID': h.set_solid_fill(color=256)
        else: h.set_pattern_fill(pattern, scale=scale, angle=angle, color=256)


def clip_lines(msp, g, horizontal, step, origin, lay):
    x0, y0, x1, y1 = g.bounds
    lo, hi = (y0, y1) if horizontal else (x0, x1)
    v = origin + math.floor((lo - origin) / step) * step
    n = 0
    while v <= hi:
        ln = LineString([(x0 - 10, v), (x1 + 10, v)] if horizontal else [(v, y0 - 10), (v, y1 + 10)])
        seg = g.intersection(ln)
        for s in ([seg] if seg.geom_type == 'LineString' else getattr(seg, 'geoms', [])):
            if s.geom_type == 'LineString' and s.length > 20:
                a, b = s.coords[0], s.coords[-1]
                msp.add_line((round(a[0], 1), round(a[1], 1)), (round(b[0], 1), round(b[1], 1)),
                             dxfattribs={'layer': lay}); n += 1
        v += step
    return n


def label_point(g):
    p = max(polys(g), key=lambda q: q.area)
    c = p.representative_point()
    return c.x, c.y


def notes(msp, x, y, title, lines, lay='A-NOTE'):
    text(msp, x, y, title, H_TXT * 1.2, lay, 'LEFT')
    yy = y - H_TXT * 2.2
    for ln in lines:
        text(msp, x, yy, ln, H_SMALL, lay, 'LEFT'); yy -= H_SMALL * 1.9
    return yy


def render_png(dxf_path, png_path, window, width_in, dpi=100):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy
    doc = ezdxf.readfile(dxf_path)
    (x0, y0), (x1, y1) = window
    fig = plt.figure(figsize=(width_in, width_in * (y1 - y0) / (x1 - x0)))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    Frontend(RenderContext(doc), MatplotlibBackend(ax),
             config=Configuration(background_policy=BackgroundPolicy.WHITE)
             ).draw_layout(doc.modelspace(), finalize=False)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
    fig.savefig(png_path, dpi=dpi, facecolor='white'); plt.close(fig)
