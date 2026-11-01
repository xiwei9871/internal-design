"""A201 lighting review CD_V01 -> V2 candidate (FUNCTIONAL_DESIGN_REVIEW).
Context loading + automatic conflict checks shared by review_a201_lighting.py and the QA."""
import json, re
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union

from cd_common import HERE, DATA, INP, OWNER

FIN = {'low': OWNER['soffit_low'] - OWNER['drop'], 'high': OWNER['soffit_high'] - OWNER['drop']}
CCT_RANGE = (3000, 4000)


def load():
    pts = json.loads((DATA / 'lighting_points.json').read_text())['points']
    inv = json.loads((INP / 'model_inventory.json').read_text())['objects']
    zj = json.loads((DATA / 'a202_zones.json').read_text())
    zones = {}
    for z in zj['zones']:
        zones.setdefault(z['id'], []).append(Polygon(z['polygon'], z.get('holes') or []))
    zones = {k: unary_union(v) for k, v in zones.items()}
    cz = json.loads((DATA / 'a201_ceiling_zones.json').read_text())
    return pts, inv, zones, cz


def floor_level(x, y):
    return OWNER['floor_high'] if (x >= 8000 and y < 10900) or x >= 13100 else OWNER['floor_low']


def finished_ceiling(x, y):
    return FIN['high'] if (8000 <= x < 13100 and y < 10900) or x >= 13100 else FIN['low']


def full_height_storage(inv):
    """Furniture whose top is within 600 mm of the finished ceiling (owner scheme), footprint > 0.15 m2."""
    out = []
    for o in inv:
        b = o['b']
        if re.search(r'WALL(?!-E)|CEIL|DOOR|WIN|GLASS|FRAME|CURTAIN|Curtain|SOFFIT|_HEAD|INNER_HEAD|PANEL|VIEW_|FLOOR|TRACK|JAMB|'
                     r'PATCH|LOUVER|SHELF$|RAIL|enamel_dome|Pendant', o['n']):
            continue                      # architecture, glazing, and luminaires themselves are not storage
        if (b[2] - b[0]) * (b[3] - b[1]) < 0.15e6 or b[5] - b[4] < 15: continue
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        fc = finished_ceiling(cx, cy)
        if fc - 600 <= b[5] <= fc + 50 and b[5] - floor_level(cx, cy) > 1500:
            out.append({'name': o['n'], 'rect': box(*b[:4]), 'top': b[5]})
    return out


def beds(inv):
    """Lying positions: mattresses and the study daybed."""
    return [{'name': o['n'], 'rect': box(*o['b'][:4])} for o in inv
            if 'mattress' in o['n'] or o['n'] == 'STUDY_V1_DAYBED_TIMBER_TOP']


def showers(inv):
    """Shower footprints from real objects: tray, or glass enclosure bounding box."""
    out = []
    for o in inv:
        if o['n'] == 'R3_SHOWER_TRAY': out.append({'name': o['n'], 'room': 'secondary_bath', 'rect': box(*o['b'][:4])})
    g = [o['b'] for o in inv if o['n'].startswith('B11_Rectangle033_GLASS')]
    if g:   # master bath sliding glass at x≈15206; shower is east of it up to the wall x=16200
        out.append({'name': 'B11_Rectangle033 (glass, x≥15206)', 'room': 'master_bath',
                    'rect': box(min(b[0] for b in g), min(b[1] for b in g), 16200, max(b[3] for b in g))})
    return out


def nodrop_zones(zones):
    """Original-soffit zones (no ceiling void): stair, and +450 floor under the 2800 soffit (x<8000)."""
    out = [zones['stair']] if 'stair' in zones else []
    if 'hallway' in zones: out.append(zones['hallway'].intersection(box(-1e5, -1e5, 8000, 1e5)))
    return [g for g in out if not g.is_empty]


def wall_cabinets(inv):
    """Wall-hung cabinets (bottom > 1400) with a counter below: ceiling light above them misses the counter."""
    out = []
    for o in inv:
        if re.match(r'^B11_K-(WALL-E|TALL-L_UPPER)_TOP$', o['n']):
            b = o['b']; out.append({'name': o['n'], 'rect': box(*b[:4])})
    return out


def step_line():
    return LineString(OWNER['step_path'])


def checks(p, ctx):
    """Return list of (severity, code, detail) for one ceiling or wall point."""
    out = []
    q = Point(p['x'], p['y'])
    ceiling = p['mount'] in ('recessed', 'surface', 'pendant')
    zone = ctx['zones'].get(p['room'])
    if zone is not None and p['room'] != 'stair':
        tol = 60 if ceiling else 320
        if not zone.buffer(tol).contains(q): out.append(('FAIL', 'OUT_OF_ROOM', p['room']))
    if ceiling:
        for f in ctx['storage']:
            if f['rect'].buffer(50).contains(q): out.append(('FAIL', 'OVER_FULL_HEIGHT_STORAGE', f['name']))
        for b in ctx['beds']:
            if b['rect'].buffer(150).contains(q): out.append(('FAIL', 'OVER_BED', b['name']))
        if p['mount'] == 'recessed':
            if q.distance(ctx['step']) < 350: out.append(('FAIL', 'NEAR_STEP_LINE', round(q.distance(ctx['step']))))
            if any(z.contains(q) for z in ctx['nodrop']): out.append(('FAIL', 'RECESSED_IN_NO_DROP_ZONE', 'original soffit, no void'))
        for w in ctx['wallcab']:
            if p['layer'] == 'task' and w['rect'].buffer(30).contains(q):
                out.append(('FAIL', 'TASK_LIGHT_ABOVE_WALL_CABINET', w['name']))
    for s in ctx['showers']:
        if s['rect'].contains(q): out.append(('FLAG', 'IN_SHOWER_FOOTPRINT', s['name']))
    if p.get('cct_k') and not CCT_RANGE[0] <= p['cct_k'] <= CCT_RANGE[1]:
        out.append(('FAIL', 'CCT_OUT_OF_RANGE', p['cct_k']))
    return out


def context():
    pts, inv, zones, cz = load()
    return pts, {'inv': inv, 'zones': zones, 'cz': cz, 'storage': full_height_storage(inv), 'beds': beds(inv),
                 'showers': showers(inv), 'nodrop': nodrop_zones(zones), 'wallcab': wall_cabinets(inv),
                 'step': step_line()}
