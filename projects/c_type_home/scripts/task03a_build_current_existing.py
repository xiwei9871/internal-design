#!/usr/bin/env python3
"""Task03A: build current-existing model from measured DWG (P1) + owner statements (P2)
+ Task01 reconstruction (P3 reference).

Coordinate systems:
  measured-normalized: origin at SW dim corner of 世纪欣园FF.dwg (1299472,-297794 abs)
  task01:              original reconstruction coords
  mapping:             task01_x = meas_x + 1300 ; task01_y = meas_y - 1336
Output model coords  : task01 coords (continuity with semantics layer IDs).
"""
import ezdxf, json, hashlib, math, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DXF_IN = ROOT / 'current_existing' / 'measured_working.dxf'
GEO = json.load(open(ROOT / 'data' / 'geometry.json'))
OUT_JSON = ROOT / 'current_existing' / 'current_existing_v1.json'
OUT_DXF = ROOT / 'current_existing' / 'current_existing_v1.dxf'

OX_ABS, OY_ABS = 1299472.0, -297794.0
DX, DY = -1300.0, 1336.0  # task01 -> measured-normalized

# ---------------------------------------------------------------- measured read
doc = ezdxf.readfile(str(DXF_IN))
msp = doc.modelspace()
def mn(p): return (p[0] - OX_ABS, p[1] - OY_ABS)

wall_lines, san_lines, door_polys, stair_ents, hatch_polys, glazing = [], [], [], [], [], []
inserts = []
for e in msp:
    t, d = e.dxftype(), e.dxf
    if t == 'LINE':
        s, q = mn(d.start), mn(d.end)
        if not (-2000 < s[0] < 16000 and -2000 < s[1] < 16000):
            continue
        rec = (round(s[0], 1), round(s[1], 1), round(q[0], 1), round(q[1], 1))
        if d.layer == 'S-S.WALL': wall_lines.append(rec)
        elif d.layer == 'F-SAN FIT': san_lines.append(rec)
        elif d.layer == 'S-楼梯': stair_ents.append(('LINE', rec))
        elif d.layer == 'F-DOOR': door_polys.append(rec)
    elif t == 'LWPOLYLINE':
        pts = [mn(p) for p in e.get_points('xy')]
        if d.layer == 'S-S.WALL': glazing.append(pts)   # balcony glazing multilines
        elif d.layer == 'F-DOOR': door_polys.append(pts)
    elif t == 'ARC' and d.layer == 'S-楼梯':
        stair_ents.append(('ARC', mn(d.center), d.radius, d.start_angle, d.end_angle))
    elif t == 'HATCH' and d.layer == 'S-S.WALL':
        for p in e.paths.paths:
            if hasattr(p, 'vertices'):
                hatch_polys.append([(round(v[0]-OX_ABS, 1), round(v[1]-OY_ABS, 1)) for v in p.vertices])
    elif t == 'INSERT' and d.name.startswith('*U4'):
        inserts.append({'ins': mn(d.insert), 'rot': d.rotation, 'sx': d.xscale,
                        'blk': d.name, 'size': { '*U431':350, '*U432':750, '*U433':850,
                                                 '*U434':850, '*U435':750, '*U436':750 }[d.name]})

def t01(mx, my): return (mx - DX, my - DY)   # measured -> task01

# ---------------------------------------------------------------- wall coverage
def coverage(x1, y1, x2, y2, tol=200):
    """coverage of a task01 wall (rect edges) by measured lines, in measured coords."""
    mx1, my1, mx2, my2 = x1 + DX, y1 + DY, x2 + DX, y2 + DY
    horiz = abs(mx2 - mx1) >= abs(my2 - my1)
    best = 0.0
    for face in ((mx1, my1, mx2, my1), (mx1, my2, mx2, my2)) if horiz else \
                ((mx1, my1, mx1, my2), (mx2, my1, mx2, my2)):
        L = abs(face[3] - face[1]) if horiz is False else abs(face[2] - face[0])
        n = max(2, int(L // 150)); hit = 0
        for i in range(n):
            tt = (i + .5) / n
            px, py = face[0] + (face[2] - face[0]) * tt, face[1] + (face[3] - face[1]) * tt
            for sa, sb, sc, sd in wall_lines:
                if horiz:
                    if abs(sb - sd) < 2 and abs(sb - py) < tol and min(sa, sc) - 80 < px < max(sa, sc) + 80:
                        hit += 1; break
                else:
                    if abs(sa - sc) < 2 and abs(sa - px) < tol and min(sb, sd) - 80 < py < max(sb, sd) + 80:
                        hit += 1; break
        best = max(best, hit / n)
    return best

def struct_overlap_mm2(rect):
    mx1, my1, mx2, my2 = rect[0]+DX, rect[1]+DY, rect[2]+DX, rect[3]+DY
    tot = 0
    for poly in hatch_polys:
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        ox = max(0, min(mx2, max(xs)) - max(mx1, min(xs)))
        oy = max(0, min(my2, max(ys)) - max(my1, min(ys)))
        tot += ox * oy
    return tot

# ---------------------------------------------------------------- dispositions
# RC1 RULE: measured DWG decides DIMENSIONS; owner-confirmed current condition
# decides EXISTENCE. DWG lines that contradict confirmed reality -> dwg_stale.
# Wall demolishability class comes ONLY from dev-plan VISUAL white/black
# reading + owner declaration (manual table below) — never from thickness/hatch.
#
# Manual visual read of source_plan_original.jpg (RC1, per-wall crops):
#   WHITE_FILL  = hollow band with dark double outline (dev-plan "white wall")
#   BLACK_FILL  = solid filled band/block (dev-plan "black wall")
#   THIN_LINE   = single/thin line partition
#   AMBIGUOUS   = mixed or unreadable -> owner review
VISUAL = {  # wall_id: (original_color_class, confidence, evidence)
    'W-EXT-W':        ('BLACK_FILL', 'HIGH',   'solid filled band'),
    'W-EXT-S':        ('BLACK_FILL', 'MED',    'solid filled band'),
    'W-EXT-S-W1':     ('BLACK_FILL', 'MED',    'solid filled band'),
    'W-EXT-S-W2':     ('BLACK_FILL', 'MED',    'solid filled band'),
    'W-EXT-E1':       ('BLACK_FILL', 'HIGH',   'solid filled band'),
    'W-EXT-E2':       ('BLACK_FILL', 'HIGH',   'solid filled band'),
    'W-EXT-NE':       ('WHITE_FILL', 'HIGH',   'hollow band at AC bay'),
    'W-EXT-NE2':      ('WHITE_FILL', 'HIGH',   'hollow band at AC bay'),
    'W-EXT-N-LV':     ('BLACK_FILL', 'HIGH',   'solid filled band N of living'),
    'W-EXT-N-BAL':    ('WHITE_FILL', 'MED',    'thin hollow band = balcony parapet/rail edge'),
    'W-BAY-F':        ('WHITE_FILL', 'HIGH',   'hollow band at bay window'),
    'W-BAY-JW':       ('WHITE_FILL', 'MED',    'hollow band'),
    'W-BAY-JE':       ('WHITE_FILL', 'MED',    'hollow band'),
    'W-BALC-W':       ('BLACK_FILL', 'MED',    'solid band'),
    'W-BALC-S':       ('BLACK_FILL', 'MED',    'solid band'),
    'W-BALC-N':       ('BLACK_FILL', 'MED',    'solid band'),
    'W-INT-X5800':    ('BLACK_FILL', 'HIGH',   'solid band kitchen/dining'),
    'W-INT-X5800-STUB':('BLACK_FILL','MED',    'solid stub'),
    'W-INT-X7900-L':  ('BLACK_FILL', 'MED',    'solid band kitchen east'),
    'W-INT-X7900-U':  ('AMBIGUOUS',  'LOW',    'column block at top + mixed band — review'),
    'W-INT-X9800':    ('BLACK_FILL', 'MED',    'thin dark line gbath/study divider'),
    'W-INT-X11500':   ('BLACK_FILL', 'HIGH',   'solid band bed/master divider'),
    'W-INT-X13000':   ('WHITE_FILL', 'MED',    'hollow thin band study/master-bath divider'),
    'W-INT-Y4500-a':  ('BLACK_FILL', 'HIGH',   'solid band kitchen north'),
    'W-INT-Y4500-b':  ('WHITE_FILL', 'MED',    'hollow band under cloakroom; W end dark at foyer junction'),
    'W-INT-Y4500-bc': ('AMBIGUOUS',  'LOW',    'black at X11500 junction, hollow band w/ door at master bath — review'),
    'W-INT-CLK-N':    ('WHITE_FILL', 'HIGH',   'hollow band + door arc'),
    'W-INT-CLK-W':    ('WHITE_FILL', 'HIGH',   'hollow band'),
    'W-INT-CLK-E':    ('WHITE_FILL', 'MED',    'hollow band upper, dark junction lower'),
    'W-INT-COR-N-STUB':('BLACK_FILL','LOW',    'small dark block'),
    'W-INT-BEDN-S':   ('WHITE_FILL', 'HIGH',   'hollow band + door arc'),
    'W-INT-WC-S':     ('BLACK_FILL', 'HIGH',   'solid band guest-bath south'),
    'W-INT-STD-S':    ('WHITE_FILL', 'HIGH',   'hollow band + study door arc'),
    'W-INT-Y10800':   ('BLACK_FILL', 'HIGH',   'solid band under north balcony'),
    'W-INT-Y10800-EXT':('BLACK_FILL','HIGH',   'solid band'),
    'W-SHAFT-K':      ('BLACK_FILL', 'LOW',    'dark stub kitchen shaft'),
    'W-INT-DRY-STUB': ('BLACK_FILL', 'LOW',    'small dark stub'),
    'W-INT-NICHE':    ('THIN_LINE',  'LOW',    'thin partition niche'),
    # RC1 splits
    'W-INT-Y4500-b-FOYER': ('BLACK_FILL','LOW','foyer-side segment w/ D-SM door jamb; not on S-S.WALL in DWG'),
    'W-INT-Y4500-b-CLKSEG':('WHITE_FILL','MED','cloakroom-south segment; only 600mm stub x10800-11400 drawn in measured DWG'),
}
DEMOLISHED = {
    'W-INT-X5800':      'kitchen west wall to dining — owner: opened up; measured cov low',
    'W-INT-X5800-STUB': 'kitchen/dining stub — opened',
    'W-BALC-N':         'life-balcony/dining separation — opened (owner orange line)',
    'W-INT-CLK-N':      'cloakroom N wall — owner: demolished, merged into secondary master',
    'W-INT-CLK-E':      'cloakroom E wall — demolished',
    'W-INT-CLK-W':      'cloakroom W wall — demolished',
    'W-INT-DRY-STUB':   'kitchen dry-side stub — opened',
    'W-INT-Y4500-b-CLKSEG': 'cloakroom-south segment of Y4500-b — open/removed; secondary master is continuous space (owner); DWG draws only 600mm stub x10800-11400 -> stale',
}
PARTIAL = {
    'W-INT-X7900-U': 'lower part removed/open per measured; upper part = GUEST_BATH west wall kept',
    'W-INT-NICHE':   'niche wall absent in measured — treated as removed/open; resolves old D-10 as open passage',
    'W-SHAFT-K':     'kitchen shaft line absent in measured; keep as TO_VERIFY marker',
}
# RC1: split the old monolithic Y4500-b rect into foyer segment (kept, has D-SM)
# and cloakroom segment (open/absent per owner + DWG stale)
SPLIT_WALLS = {
    'W-INT-Y4500-b': [
        ('W-INT-Y4500-b-FOYER',  [8236, 4450, 9050, 4650]),
        ('W-INT-Y4500-b-CLKSEG', [9050, 4450, 11400, 4650]),
    ]
}

def policy_for(wid, visual_cls, disp, wall_type):
    """owner-declared rule mapping — NOT structural inference."""
    if disp != 'EXISTING':
        # demolished/partial walls: if they were drawn WHITE -> real conflict
        if visual_cls == 'WHITE_FILL':
            return 'CLASSIFICATION_CONFLICT_TO_REVIEW'
        return 'DEMOLISHED_OR_PARTIAL'
    if wall_type == 'exterior':
        return 'NO_OPEN_EXTERIOR_ENVELOPE'
    if visual_cls == 'WHITE_FILL':
        return 'OWNER_DECLARED_NO_DEMOLITION_NO_OPENING'
    if visual_cls == 'BLACK_FILL' or visual_cls == 'THIN_LINE':
        return 'MODIFIABLE_DECLARED'
    return 'CLASSIFICATION_TO_REVIEW'

walls = []
for w in GEO['walls']:
    wid = w['id']
    pieces = SPLIT_WALLS.get(wid, [(wid, w['rect_mm'])])
    for pid, rect in pieces:
        x1, y1, x2, y2 = rect
        cov = coverage(x1, y1, x2, y2)
        so = struct_overlap_mm2(rect)
        if pid in DEMOLISHED:
            disp, lay = 'DEMOLISHED_OWNER_CONFIRMED', 'A-WALL-EXST-REMOVE'
        elif pid in PARTIAL:
            disp, lay = 'PARTIAL_REMOVED_TO_VERIFY', 'A-WALL-EXST-REMOVE'
        else:
            disp, lay = 'EXISTING', 'A-WALL-EXST-KEEP'
        vcls, conf, ev = VISUAL.get(pid, VISUAL.get(wid, ('AMBIGUOUS', 'LOW', 'no manual read')))
        pol = policy_for(pid, vcls, disp, w.get('type'))
        stale = bool(disp != 'EXISTING' and cov > 0.5)
        walls.append({'id': pid, 'rect_mm': rect, 'type': w.get('type'),
                      'measured_coverage': round(cov, 2), 'struct_overlap_mm2': round(so),
                      'disposition': disp, 'layer': lay,
                      'original_color_class': vcls,
                      'owner_rule_applied': pol,
                      'wall_class': pol,
                      'dwg_stale_geometry': stale,
                      'confidence': conf, 'evidence': ev,
                      'note': DEMOLISHED.get(pid) or PARTIAL.get(pid) or ''})

# ---------------------------------------------------------------- openings (current state, measured)
def T(p): return [round(p[0] - DX), round(p[1] - DY)]
openings = [
    {'id': 'ENT-1', 'kind': 'entry_double_leaf', 'meas_zone': [[1400, 6400], [1600, 8100]],
     'status': 'EXISTING', 'note': 'main entry on west wall, two door-block inserts; width TO_VERIFY'},
    {'id': 'D-LIV-STUDY?', 'kind': 'door', 'meas_zone': [[6600, 5900], [7000, 7000]],
     'status': 'EXISTING_TO_VERIFY', 'note': 'arc r1000 at meas(5400,6936) on S-楼梯 layer — guest-bath/vestibule door, position TO_VERIFY'},
    {'id': 'D-SM', 'kind': 'door', 'meas_zone': [[6700, 5700], [7400, 6100]],
     'status': 'EXISTING', 'note': 'secondary master door opening to upper landing (insert rot206)'},
    {'id': 'D-MB', 'kind': 'door', 'meas_zone': [[11600, 5900], [12000, 6400]],
     'status': 'EXISTING', 'note': 'master bedroom door on X13000 wall'},
    {'id': 'D-BATHM', 'kind': 'door', 'meas_zone': [[11200, 7500], [11800, 7900]],
     'status': 'EXISTING', 'note': 'master bath door opening to corridor'},
    {'id': 'D-STUDY', 'kind': 'door', 'meas_zone': [[11500, 7900], [12100, 8300]],
     'status': 'EXISTING', 'note': 'study (NE bedroom) door on X13000 wall'},
    {'id': 'D-GBATH', 'kind': 'door', 'meas_zone': [[9200, 9136], [10000, 9536]],
     'status': 'EXISTING', 'note': 'guest bath south door (insert @meas x8300/y9336, on WC-S wall segment)'},
    {'id': 'D-GBED', 'kind': 'door', 'meas_zone': [[9600, 9136], [10400, 9536]],
     'status': 'EXISTING', 'note': 'guest bedroom south door (insert @meas x8700/y9336, on STD-S wall)'},
    {'id': 'D-MASTER?', 'kind': 'door', 'meas_zone': [[10100, 4400], [10900, 4700]],
     'status': 'TO_VERIFY', 'note': 'master bedroom entry on north wall Y4500-bc per dev plan; not a block insert in measured DWG — position to verify'},
    {'id': 'G-GB-BALC', 'kind': 'glazing_door_double', 'meas_zone': [[9200, 12036], [11700, 12436]],
     'status': 'EXISTING_KEEP', 'note': 'existing interior double glass door guest bedroom -> north balcony (replaced demolished black wall). NOT the exterior enclosure.'},
    {'id': 'G-DIN-LIV', 'kind': 'sliding_glass_3track', 'meas_zone': [[1650, 5866], [4350, 6051]],
     'status': 'EXISTING_KEEP', 'note': 'owner blue-line new sliding glass door kitchen-dining domain <-> living, ~2700mm 3-track'},
    {'id': 'D-BALC-W', 'kind': 'door', 'meas_zone': [[6500, 13900], [7100, 14500]],
     'status': 'EXISTING', 'note': 'west door into north balcony (insert rot270 at 6700,14236)'},
    {'id': 'OPEN-COR-LIV', 'kind': 'open_passage', 'meas_zone': [[5850, 6100], [6100, 7800]],
     'status': 'EXISTING_OPEN', 'note': 'former niche/D-10 zone absent in measured = open side of corridor onto living platform'},
]
for o in openings:
    o['rect_mm'] = [T(o['meas_zone'][0])[0], T(o['meas_zone'][0])[1],
                    T(o['meas_zone'][1])[0], T(o['meas_zone'][1])[1]]

# ---------------------------------------------------------------- stairs / level
# RC1: two estimates conflict and are BOTH recorded — nothing resolved silently.
stairs = {'zone_meas': [5900, 7936, 6500, 9136], 'risers': 2, 'tread_mm': 300,
          'run_direction': '+x (west=lower living/dining, east=upper bedroom wing)',
          'level_difference_mm': None,
          'level_status': 'LEVEL_DELTA_TO_VERIFY',
          'owner_estimate_mm': '<=350 (2 risers, 3rd step is the platform itself)',
          'cad_derived_mm': '~400 (inferred; not directly dimensioned in DWG)',
          'field_measure_request': 'L1 finished floor -> L2 finished floor vertical delta',
          'note': 'two 300mm treads drawn in S-楼梯; ramp slope + platform cut + living rectangle all PROVISIONAL until measured'}
stairs['zone_mm'] = [stairs['zone_meas'][0]-DX, stairs['zone_meas'][1]-DY,
                     stairs['zone_meas'][2]-DX, stairs['zone_meas'][3]-DY]

# ---------------------------------------------------------------- keep fixtures
keep = [
    {'id': 'K-CABINETS', 'kind': 'kitchen_cabinet_system', 'src': 'cabinet_plan.pdf',
     'meas_zone': [[4200, 1336], [6900, 6036]], 'note': 'L/U kitchen cabinetry KEEP; fridge slot 905x710; dishwasher 600; sink 990'},
    {'id': 'BALC-CAB-RED', 'kind': 'cabinet', 'meas_zone': [[100, 1400], [700, 3900]],
     'note': 'life balcony red cabinet KEEP'},
    {'id': 'WD-10KG', 'kind': 'washer_dryer', 'meas_zone': [[6600, 14400], [7300, 15100]],
     'note': '10kg washer+10kg dryer stacked, north balcony west end'},
    {'id': 'WB-MASTER', 'kind': 'wardrobe', 'meas_zone': [[10300, 5300], [14200, 5900]],
     'note': 'master bedroom custom wardrobe on north wall KEEP'},
    {'id': 'WB-STUDY', 'kind': 'wardrobe', 'meas_zone': [[11800, 9336], [14900, 9736]],
     'note': 'NE-bedroom (study) wardrobe on south wall KEEP, may convert to file/equipment'},
    {'id': 'WB-CLK', 'kind': 'wardrobe', 'meas_zone': [[7650, 5836], [8250, 7636]],
     'note': 'former cloakroom wardrobe on west side — conflicts with 5sqm bath carve-out, TO_VERIFY'},
    {'id': 'SHOE-CAB', 'kind': 'cabinet_low', 'meas_zone': [[200, 6600], [900, 7900]],
     'note': 'entry low shoe cabinet KEEP'},
    {'id': 'GB-DRY/WET', 'kind': 'bath_zones', 'meas_zone': [[6600, 9336], [8500, 12236]],
     'note': 'guest bath: front(green,S)=dry vanity+toilet; rear(red,N)=wet shower+3kg washer'},
]
for k in keep:
    k['rect_mm'] = [k['meas_zone'][0][0]-DX, k['meas_zone'][0][1]-DY,
                    k['meas_zone'][1][0]-DX, k['meas_zone'][1][1]-DY]

balconies = {
    'north_balcony': {
        'current_enclosure': 'OPEN_NOT_ENCLOSED',
        'future_enclosure': 'PROPOSED_LEGAL_TO_ENCLOSE',
        'evidence': 'owner statement RC1; DWG north-edge multilines = parapet/railing, NOT glazing',
        'interior_door': 'G-GB-BALC (guest bedroom <-> balcony, existing)'},
    'life_balcony': {'red_cabinet': 'KEEP'},
}

model = {
    'meta': {'task': 'TASK03A RC1 current-existing baseline',
             'rc1_changes': ['DWG governs dimensions; owner statements govern wall existence',
                             'white/black class from dev-plan visual read + owner declaration — no thickness inference',
                             'north balcony = OPEN, enclosure PROPOSED',
                             'level delta = LEVEL_DELTA_TO_VERIFY (owner <=350 vs CAD ~400)'],
             'coord_system': 'task01-compatible mm',
             'measured_origin': [OX_ABS, OY_ABS], 'offset_task01_to_measured': [DX, DY],
             'authority': 'measured DWG (dims) + owner statements (existence) > developer plan (policy/history) > task02 semantics'},
    'walls': walls,
    'structural_fills_measured': [[t01(*[min(p[0] for p in poly), min(p[1] for p in poly)])[0],
                                   t01(*[min(p[0] for p in poly), min(p[1] for p in poly)])[1],
                                   max(p[0] for p in poly)-DX, max(p[1] for p in poly)-DY]
                                  for poly in hatch_polys],
    'openings': openings,
    'split_level': stairs,
    'balconies': balconies,
    'keep_items': keep,
    'measured_dims': {'north_chain': [5100, 1900, 3200, 3300],
                      'south_chain': [1400, 3000, 2100, 3600, 3900, 900],
                      'west_chain': [500, 1800, 2200, 8500],
                      'east_chain': [4500, 1900, 4500, 2800]},
}
OUT_JSON.write_text(json.dumps(model, ensure_ascii=False, indent=1))
print('model written:', OUT_JSON)
print('walls kept:', sum(1 for w in walls if w['disposition'] == 'EXISTING'),
      'demolished:', sum(1 for w in walls if 'DEMOL' in w['disposition'] or 'PARTIAL' in w['disposition']))
