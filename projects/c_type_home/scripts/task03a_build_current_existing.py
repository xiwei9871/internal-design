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
    'W-INT-DRY-STUB':   'kitchen dry-side stub — opened',
    'W-INT-Y4500-b-CLKSEG': 'cloakroom-south segment of Y4500-b — OPEN to secondary master (owner RC1.5: this is how it merged); DWG draws only 600mm stub x10800-11400 -> residual, TO_VERIFY',
}
# RC1.5/RC2 owner confirmation: cloakroom N/W/E walls are RETAINED —
# owner marked them green on the supplied image AND the measured DWG draws
# them (coverage 0.75-1.0). Two sources agree; they were NOT demolished.
CLK_RETAINED = {
    'W-INT-CLK-N': 'cloakroom N wall RETAINED (owner image markup + DWG drawn) — incl. existing door opening to corridor (leaf status TO_VERIFY)',
    'W-INT-CLK-E': 'cloakroom E wall RETAINED (owner image markup + DWG drawn) — shared with master-bath wet zone',
    'W-INT-CLK-W': 'cloakroom W wall RETAINED (owner image markup + DWG drawn) — bounds suite foyer',
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

# ================================================================ RC2.2 window register
# Authority: P1 owner-confirmed current status > P2 dev-plan graphic > P3 measured DWG.
# Every dev-plan window/bay/glazing on the perimeter gets a record; ambiguous ones
# stay TO_VERIFY — never silently reverted to solid wall.
WINDOWS = [
    {'window_id': 'W-KIT-S', 'room_or_zone': 'kitchen', 'orientation_plan_relative': 'south',
     'window_type': 'STANDARD_WINDOW', 'host_wall': 'W-EXT-S',
     'opening_rect_mm': [6100, -200, 7100, 0], 'span_mm': 1000,
     'source_plan_evidence': 'thin-line window symbol inside south wall band under kitchen',
     'measured_dwg_evidence': '4-line glazing symbol x6100-7100 inside S-S.WALL band y0-200',
     'current_status': 'EXISTING_WINDOW', 'proposed_status': 'EXISTING_KEEP',
     'sill_or_bay_note': 'in-wall window, no projection',
     'confidence': 'HIGH', 'verification_status': 'CONFIRMED',
     'notes': 'kitchen south window; both sources agree'},
    {'window_id': 'W-KIT-SW', 'room_or_zone': 'kitchen/life-balcony corner', 'orientation_plan_relative': 'south',
     'window_type': 'STANDARD_WINDOW', 'host_wall': None,
     'opening_rect_mm': [5000, -200, 5380, 0], 'span_mm': 380,
     'source_plan_evidence': 'break in south wall band beside AC box — could be small window or door to life balcony',
     'measured_dwg_evidence': 'gap x5000-5380 between south wall segments (W-EXT-S-W1/-W2)',
     'current_status': 'OPENING_TO_VERIFY', 'proposed_status': 'EXISTING_KEEP',
     'sill_or_bay_note': 'narrow 380mm gap',
     'confidence': 'LOW', 'verification_status': 'TO_VERIFY',
     'notes': 'ambiguous narrow opening — verify on site whether window or balcony door'},
    {'window_id': 'W-SMB-S', 'room_or_zone': 'secondary master bedroom', 'orientation_plan_relative': 'south',
     'window_type': 'BAY_WINDOW', 'host_wall': 'W-EXT-S',
     'opening_rect_mm': [8500, -200, 10900, 0], 'span_mm': 2400,
     'source_plan_evidence': 'protruding box outline on south edge at secondary bedroom',
     'measured_dwg_evidence': 'outer-face gap x8500-10900; bay box x8400-11000 projecting to y-700; jamb+front triple lines',
     'current_status': 'EXISTING_WINDOW', 'proposed_status': 'EXISTING_KEEP',
     'sill_or_bay_note': 'bay projects 700 south; glazed front x8400-11000 y-700/-650/-600',
     'confidence': 'HIGH', 'verification_status': 'CONFIRMED',
     'bay': {'jambs': [[8400, -700, 8500, 0], [10900, -700, 11000, 0]],
             'front': [8400, -700, 11000, -600]},
     'notes': 'south bay window'},
    {'window_id': 'W-MB-S', 'room_or_zone': 'master bedroom', 'orientation_plan_relative': 'south',
     'window_type': 'BAY_WINDOW', 'host_wall': 'W-EXT-S',
     'opening_rect_mm': [12100, -200, 14800, 0], 'span_mm': 2700,
     'source_plan_evidence': 'protruding box outline on south edge at master bedroom',
     'measured_dwg_evidence': 'outer-face gap x12100-14800; bay box x12000-14900 projecting to y-700; jamb+front triple lines',
     'current_status': 'EXISTING_WINDOW', 'proposed_status': 'EXISTING_KEEP',
     'sill_or_bay_note': 'bay projects 700 south; glazed front x12000-14900 y-700/-650/-600',
     'confidence': 'HIGH', 'verification_status': 'CONFIRMED',
     'bay': {'jambs': [[12000, -700, 12100, 0], [14800, -700, 14900, 0]],
             'front': [12000, -700, 14900, -600]},
     'notes': 'south bay window'},
    {'window_id': 'W-LIV-N', 'room_or_zone': 'living', 'orientation_plan_relative': 'north',
     'window_type': 'BAY_WINDOW', 'host_wall': 'W-EXT-N-LV',
     'opening_rect_mm': [3800, 12750, 6900, 12950], 'span_mm': 3100,
     'source_plan_evidence': 'hollow bay band + protruding outline on north edge at living room',
     'measured_dwg_evidence': 'wall-face gap x3800-6900 (faces y13000/13200); glazed front triple-line y13800/13850/13900 x3600-7100',
     'current_status': 'EXISTING_WINDOW', 'proposed_status': 'EXISTING_KEEP',
     'sill_or_bay_note': 'bay projects ~900 north of wall face; glazed front x3600-7100 y13800-13900',
     'confidence': 'HIGH', 'verification_status': 'CONFIRMED',
     'bay': {'jambs': [[3650, 12950, 3800, 13800], [6900, 12950, 7050, 13800]],
             'front': [3600, 13800, 7100, 13900]},
     'notes': 'living-room north bay — the old W-BAY-F rect sat mid-air at y13400-13600 (floating segment); corrected to measured front y13800-13900'},
    {'window_id': 'W-STUDY-NE', 'room_or_zone': 'study', 'orientation_plan_relative': 'north (NE corner)',
     'window_type': 'BAY_WINDOW', 'host_wall': None,
     'opening_rect_mm': [13600, 10900, 15700, 11100], 'span_mm': 2100,
     'source_plan_evidence': 'stepped/protruding outline at NE corner of study on dev plan',
     'measured_dwg_evidence': 'wall face y11100 with gap x13600-15700; bay jambs x13500-13600 & x15700-15800 spanning y11100-11800; glazed front triple-line y11700/11750/11800',
     'current_status': 'EXISTING_WINDOW', 'proposed_status': 'EXISTING_KEEP',
     'sill_or_bay_note': 'full-width bay projects to y11800; glazed front x13500-15800 y11700-11800',
     'confidence': 'HIGH', 'verification_status': 'CONFIRMED',
     'bay': {'jambs': [[13500, 11100, 13600, 11800], [15700, 11100, 15800, 11800]],
             'front': [13500, 11700, 15800, 11800]},
     'notes': 'study lit by this NE bay — east wall is solid in BOTH sources (no east window); old W-EXT-NE band y11350-11550 sat inside bay projection = floating red segment, corrected'},
    {'window_id': 'W-GBATH-N', 'room_or_zone': 'guest bath', 'orientation_plan_relative': 'north',
     'window_type': 'STANDARD_WINDOW', 'host_wall': 'W-INT-Y10800',
     'opening_rect_mm': [8900, 10700, 9700, 10900], 'span_mm': 800,
     'source_plan_evidence': 'dev-plan read ambiguous at this band — bath onto open balcony',
     'measured_dwg_evidence': 'triple-line glazing symbol x8900-9700 within wall band y10900-11040',
     'current_status': 'EXISTING_WINDOW', 'proposed_status': 'EXISTING_KEEP',
     'sill_or_bay_note': 'in-wall window facing open north balcony',
     'confidence': 'MED', 'verification_status': 'TO_VERIFY',
     'notes': 'DWG draws glazing lines but dev-plan unclear — verify on site'},
    {'window_id': 'G-GB-BALC', 'room_or_zone': 'guest bedroom', 'orientation_plan_relative': 'north',
     'window_type': 'GLASS_DOOR', 'host_wall': 'W-INT-Y10800',
     'opening_rect_mm': [10400, 10700, 12400, 10900], 'span_mm': 2000,
     'source_plan_evidence': 'glass door zone to balcony marked on dev plan',
     'measured_dwg_evidence': 'triple-line glazing x10400-12400 in wall band; door insert present',
     'current_status': 'EXISTING_GLASS_DOOR', 'proposed_status': 'EXISTING_KEEP',
     'sill_or_bay_note': 'double glass door; interior door — NOT the exterior balcony enclosure',
     'confidence': 'HIGH', 'verification_status': 'CONFIRMED',
     'notes': 'existing double glass door guest bedroom -> north balcony; keep-clear zone wider than leaf span'},
    {'window_id': 'D-BALC-W', 'room_or_zone': 'north balcony west', 'orientation_plan_relative': 'west end of north balcony',
     'window_type': 'GLASS_DOOR', 'host_wall': 'W-EXT-N-LV',
     'opening_rect_mm': [7800, 12750, 8400, 12950], 'span_mm': 600,
     'source_plan_evidence': 'door mark at balcony west end',
     'measured_dwg_evidence': 'door block insert rot270 at balcony west edge; north wall face ends x7800 (measured)',
     'current_status': 'EXISTING_DOOR', 'proposed_status': 'EXISTING_KEEP',
     'sill_or_bay_note': 'access door into north balcony from living side',
     'confidence': 'MED', 'verification_status': 'MEASURED',
     'notes': 'leaf type (solid vs glazed) TO_VERIFY on site'},
    {'window_id': 'G-DIN-LIV', 'room_or_zone': 'kitchen/dining <-> living', 'orientation_plan_relative': 'interior',
     'window_type': 'GLASS_DOOR', 'host_wall': None,
     'opening_rect_mm': [2950, 4530, 5650, 4715], 'span_mm': 2700,
     'source_plan_evidence': 'owner blue-line markup — new sliding glass partition',
     'measured_dwg_evidence': 'owner statement; existing opening in measured plan',
     'current_status': 'EXISTING_GLASS_DOOR', 'proposed_status': 'EXISTING_KEEP',
     'sill_or_bay_note': '3-track sliding glass door ~2700mm, interior partition',
     'confidence': 'HIGH', 'verification_status': 'CONFIRMED',
     'notes': 'owner-installed sliding glass partition kitchen/dining <-> living'},
    {'window_id': 'N-BALC-ENCL', 'room_or_zone': 'north balcony outer edge', 'orientation_plan_relative': 'north',
     'window_type': 'PROPOSED_BALCONY_ENCLOSURE', 'host_wall': None,
     'opening_rect_mm': [7900, 13400, 13000, 13600], 'span_mm': 5100,
     'source_plan_evidence': 'dev plan shows open balcony parapet',
     'measured_dwg_evidence': 'parapet outline x7880-13020 y11100-13820 — railing only, NO glazing',
     'current_status': 'OPEN_NOT_ENCLOSED', 'proposed_status': 'PROPOSED_LEGAL_TO_ENCLOSE',
     'sill_or_bay_note': 'proposed glazing sits on existing parapet line',
     'confidence': 'HIGH', 'verification_status': 'PROPOSED',
     'notes': 'TIME-STATE: current = OPEN_NOT_ENCLOSED; future enclosure = PROPOSED only — must not be drawn as existing window'},
]

# RC2.2 rect corrections — only where a wall rect contradicts measured window/bay
# geometry (display-level correction; no furniture/layout change).
RECT_OVERRIDE = {
    'W-BAY-JW':  [3650, 12950, 3800, 13800],   # living bay west jamb -> measured extent
    'W-BAY-JE':  [6900, 12950, 7050, 13800],   # living bay east jamb
    'W-EXT-NE':  [13000, 10900, 13600, 11100], # study north wall WEST segment (was floating band inside bay)
    'W-EXT-NE2': [15700, 10900, 16400, 11100], # study north wall EAST segment to east wall
}
# W-BAY-F is not a wall — it is the glazed front of W-LIV-N (kept as bay component)
DROP_WALLS = {'W-BAY-F'}
# entry door opening in west exterior wall (measured leaf gap y5440-6540)
DOOR_SPLITS = {
    'W-EXT-W': [[2700, 2300, 2900, 5440], [2700, 6540, 2900, 13600]],
}
VISUAL.update({'W-EXT-NE-WSEG': ('WHITE_FILL', 'HIGH', 'study N wall west of bay opening'),
               'W-EXT-NE-ESEG': ('WHITE_FILL', 'HIGH', 'study N wall east of bay opening')})

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
    if wid in DROP_WALLS:
        continue                                    # glazed bay front, not a wall
    base_rect = RECT_OVERRIDE.get(wid, w['rect_mm'])
    if wid in DOOR_SPLITS:
        pieces = [(f'{wid}-S{i}', r) for i, r in enumerate(DOOR_SPLITS[wid])]
    else:
        pieces = SPLIT_WALLS.get(wid, [(wid, base_rect)])
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
                      'note': DEMOLISHED.get(pid) or PARTIAL.get(pid) or CLK_RETAINED.get(pid) or ''})

# ------------------------------------------------- RC2.2 wall splits at window openings
# For every registered window/glass-door whose opening cuts a host wall, split the
# wall record into wall | opening | wall so no solid wall crosses a glazed span.
def _strict_overlap(a, b):
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])

def _cut(rect, op):
    """remove op span from rect along rect's long axis -> remaining pieces"""
    x1, y1, x2, y2 = rect
    ox1, oy1, ox2, oy2 = op
    out = []
    if (x2 - x1) >= (y2 - y1):
        if ox1 - x1 > 10: out.append([x1, y1, ox1, y2])
        if x2 - ox2 > 10: out.append([ox2, y1, x2, y2])
    else:
        if oy1 - y1 > 10: out.append([x1, y1, x2, oy1])
        if y2 - oy2 > 10: out.append([x1, oy2, x2, y2])
    return out

for win in WINDOWS:
    host = win.get('host_wall')
    if not host:
        continue
    op = win['opening_rect_mm']
    nxt = []
    for w in walls:
        r = w['rect_mm']
        if (w['id'] == host or w['id'].startswith(host + '#')) and _strict_overlap(r, op):
            for i, p in enumerate(_cut(r, op)):
                seg = dict(w)
                seg['id'] = f"{host}#{win['window_id']}.{i}"
                seg['rect_mm'] = p
                seg['note'] = (seg.get('note', '') +
                               f" [segment of {host} cut at {win['window_id']}]").strip()
                nxt.append(seg)
            win['split_applied'] = True
        else:
            nxt.append(w)
    walls = nxt

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
    {'id': 'D-CLK', 'kind': 'door', 'meas_zone': [[8500, 7636], [9200, 7836]],
     'status': 'EXISTING_TO_VERIFY', 'note': 'cloakroom north door opening (dev plan arc on CLK-N); leaf status TO_VERIFY — reusable as bath N entry candidate'},
    {'id': 'D-MASTER?', 'kind': 'door', 'meas_zone': [[10100, 4400], [10900, 4700]],
     'status': 'TO_VERIFY', 'note': 'master bedroom entry on north wall Y4500-bc per dev plan; not a block insert in measured DWG — position to verify'},
    {'id': 'G-GB-BALC', 'kind': 'glazing_door_double', 'meas_zone': [[9100, 12036], [11100, 12236]],
     'status': 'EXISTING_KEEP', 'note': 'existing interior double glass door guest bedroom -> north balcony, glazing x10400-12400 per DWG triple-line (replaced demolished black wall). NOT the exterior enclosure.'},
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
    'windows': WINDOWS,
    'split_level': stairs,
    'balconies': balconies,
    'keep_items': keep,
    'measured_dims': {'north_chain': [5100, 1900, 3200, 3300],
                      'south_chain': [1400, 3000, 2100, 3600, 3900, 900],
                      'west_chain': [500, 1800, 2200, 8500],
                      'east_chain': [4500, 1900, 4500, 2800]},
}
OUT_JSON.write_text(json.dumps(model, ensure_ascii=False, indent=1))

# RC2.2: formal window register — JSON + CSV (evidence-led)
REG_JSON = ROOT / 'current_existing' / 'window_register.json'
REG_CSV = ROOT / 'current_existing' / 'window_register.csv'
REG_FIELDS = ['window_id', 'room_or_zone', 'orientation_plan_relative', 'window_type',
              'source_plan_evidence', 'measured_dwg_evidence', 'current_status',
              'proposed_status', 'span_mm', 'sill_or_bay_note', 'confidence',
              'verification_status', 'notes']
REG_JSON.write_text(json.dumps({'meta': {'task': 'TASK03A RC2.2 window register',
                    'authority': 'P1 owner-confirmed status > P2 dev-plan graphic > P3 measured DWG',
                    'north_balcony_time_state': 'current OPEN_NOT_ENCLOSED / enclosure PROPOSED / G-GB-BALC interior door EXISTING_KEEP'},
                                'windows': WINDOWS}, ensure_ascii=False, indent=1))
import csv
with open(REG_CSV, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=REG_FIELDS)
    w.writeheader()
    for win in WINDOWS:
        w.writerow({k: win.get(k, '') for k in REG_FIELDS})
print('model written:', OUT_JSON)
print('window register:', len(WINDOWS), 'records ->', REG_JSON.name, '+', REG_CSV.name)
print('walls kept:', sum(1 for w in walls if w['disposition'] == 'EXISTING'),
      'demolished:', sum(1 for w in walls if 'DEMOL' in w['disposition'] or 'PARTIAL' in w['disposition']))
