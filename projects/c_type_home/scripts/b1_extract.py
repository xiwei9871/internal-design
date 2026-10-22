"""B1 extraction: canonical architecture + FCStd furniture -> b1_model.json
All output in canonical task01 mm coords (x east, y north, z up).
FCStd -> canonical: x = x_fc - 1298172, y = y_fc + 296458 (pure translation,
verified by 30+ furniture label pairs, dominant offset exact match).
"""
import json, re, os

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
CANON = json.load(open(f'{BASE}/current_existing/canonical_plan_v1.json'))
GEO = json.load(open(f'{BASE}/data/geometry.json'))
FC = json.load(open(f'{BASE}/design/b1_blockout/b1_fcstd_objects.json'))
OUT = f'{BASE}/design/b1_blockout/b1_model.json'

DX, DY = -1298172.0, 296458.0  # fc -> canonical

# ---------------- architecture ----------------
walls, parapets, removed = [], [], []
for w in CANON['walls']:
    rec = {'id': w['id'], 'rect': w['rect_mm'], 'cls': w['type'], 'disp': w['disposition']}
    if w['disposition'] == 'EXISTING':
        (parapets if w['type'] == 'railing_parapet' else walls).append(rec)
    else:
        removed.append(rec)

# --- door semantic resolution (2026-09-29, owner directive) ---
# D-CLK: pierces W-INT-CLK-N; S=R-CLOAK(owner ensuite) / N=R-LEISURE hall -> real door
# D-MASTER?: pierces W-INT-X11500; W=R-BED-S(owner) / E=R-MASTER(mother) -> real connecting door
# D-LIV-STUDY?: all flanks R-LEISURE, rect overlaps real D-SM -> FALSE SEED, remove
DOOR_RENAME = {'D-CLK': 'D-ENS-OWNER', 'D-MASTER?': 'D-CONN-MB-SMB'}
DOOR_FALSE_SEED = {'D-LIV-STUDY?': 'overlaps real door D-SM region; all flanking samples = R-LEISURE'}
openings, removed_openings = [], []
for o in CANON['openings']:
    oid = o['id']
    if oid in DOOR_FALSE_SEED:
        removed_openings.append({'id': oid, 'rect': o['rect_mm'], 'reason': DOOR_FALSE_SEED[oid],
                                 'resolution': 'REMOVE_FALSE_SEED'})
        continue
    rec = {'id': DOOR_RENAME.get(oid, oid), 'kind': o['kind'], 'rect': o['rect_mm'],
           'status': 'EXISTING' if oid in DOOR_RENAME else o['status'],
           'source_id': oid}
    openings.append(rec)
windows = [{'id': w['window_id'], 'type': w['type'], 'rect': w['opening_rect_mm'],
            'orientation': w['orientation'], 'span': w['span_mm'],
            'bay': w.get('bay')} for w in CANON['windows']]
kcabs = [{'id': c['id'], 'rect': c['rect_mm']} for c in CANON['kitchen_cabinets']]

# balcony slabs (derived from parapet + exterior wall envelope)
balconies = [
    {'id': 'north_balcony', 'poly': [[7900, 10900], [13020, 10900], [13020, 13600], [7900, 13600]],
     'open': True},
    {'id': 'life_balcony', 'poly': [[1300, 450], [5800, 450], [5800, 2560], [1300, 2560]],
     'open': False},  # W-LBALC-S glazing sits on S parapet; W-BALC-N demolished -> interior merges dining
]

def clip_x(poly, x, keep):
    out = []
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        in1 = (x1 < x) == (keep == 'lt'); in2 = (x2 < x) == (keep == 'lt')
        if in1: out.append([x1, y1])
        if in1 != in2:
            t = (x - x1) / (x2 - x1)
            out.append([x, y1 + t * (y2 - y1)])
    return out

# room floor plates; level = 'upper' (+TEMP 350) for east bedroom wing x>7800
UPPER = {'R-BED-S', 'R-MASTER', 'R-CLOAK', 'R-BATH-M', 'R-BED-N', 'R-STUDY', 'R-BATH-P'}
spaces = []
for s in GEO['spaces']:
    poly = s['polygon_mm']
    if s['id'] == 'R-LEISURE':  # L-hall spans the split line -> clip at x=7800
        spaces.append({'id': 'R-LEISURE-W', 'name': s['name_zh'], 'poly': clip_x(poly, 7800, 'lt'), 'level': 'lower'})
        spaces.append({'id': 'R-LEISURE-E', 'name': s['name_zh'], 'poly': clip_x(poly, 7800, 'gt'), 'level': 'upper'})
        continue
    spaces.append({'id': s['id'], 'name': s['name_zh'], 'poly': poly,
                   'level': 'upper' if s['id'] in UPPER else 'lower'})

split = CANON['split_level']
stairs = {'zone': split['zone_mm'], 'risers': split['risers'],
          'tread': split['tread_mm'], 'delta_mm': 350,  # BLOCKOUT_TEMP_VALUE
          'steps': [[7200, 6600, 7500, 7800, 175], [7500, 6600, 7800, 7800, 350]]}

# ---------------- furniture from FCStd ----------------
GENERIC = re.compile(r'^(Line|Arc|Circle|Rectangle|Polyline|Bspline|Text|MTEXT|Dimension|Wire|Ellipse)\d*$')
EXTRA = {'Rectangle050': ('餐桌', 'dining_table'), 'Circle012': ('餐椅', 'dining_chair'),
         'Rectangle051': ('床背板', 'headboard'), 'Rectangle052': ('窄书桌', 'desk_strip')}
# 'Rectangle' (847x3163, living-room west, unlabeled) = stale working outline overlapping
# 三人位 sofa footprint; confirmed real object in FCStd but excluded from B1 build —
# documented here instead of modeling it.
EXCLUDED = {'Rectangle': 'unlabeled working outline overlapping 三人位 sofa zone; not a design element'}

def fc_rect(b):  # fc bbox -> canonical rect
    return [b[0] + DX, b[1] + DY, b[3] + DX, b[4] + DY]

furniture, ramp = [], None
for name, r in FC['objects'].items():
    lb, b = r.get('label', ''), r.get('bbox')
    sem = None
    if lb and not GENERIC.match(lb):
        sem = lb
    elif name in EXTRA:
        sem = EXTRA[name][0]
    if not sem or not b or abs(b[0]) > 1e15:
        continue
    rect = fc_rect(b)
    if name in EXCLUDED:
        continue
    if sem == '斜坡给未来轮椅使用预留':
        ramp = {'id': 'RAMP-FUTURE', 'rect': rect, 'label': sem}
        continue
        ramp = {'id': 'RAMP-FUTURE', 'rect': rect, 'label': sem}
        continue
    shape = 'cyl' if r['type'] == 'Part::Feature' and 'Circle' in name else 'box'
    furniture.append({'obj': name, 'label': sem, 'rect': rect, 'shape': shape,
                      'w': round(rect[2]-rect[0]), 'd': round(rect[3]-rect[1])})

def zone_of(rect):
    cx, cy = (rect[0]+rect[2])/2, (rect[1]+rect[3])/2
    for s in spaces + [{'id': 'north_balcony', 'poly': balconies[0]['poly']},
                       {'id': 'life_balcony', 'poly': balconies[1]['poly']}]:
        if inside(cx, cy, s['poly']): return s['id']
    return 'UNZONED'

def inside(x, y, poly):
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % n]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1:
            c = not c
    return c

for f in furniture:
    f['zone'] = zone_of(f['rect'])

# ---------------- FORMALIZATION CLEANUP (V003 policy) ----------------
# Priority: HARD ARCHITECTURE > HUMAN-APPROVED OBJECT > ANALYSIS/REGION BOUNDARY
# - Furniture/fixtures: auto-translate ONLY if total shift <= 50mm (drafting noise);
#   larger conflicts are FLAGGED, not moved.
# - Revoked list: objects the owner confirmed are already at final human positions.
# - Wet zones are DESIGN REGIONS, not furniture: clip their rect to wall inner
#   faces instead of translating; region shrinkage is boundary cleanup.
HARD = ([w['rect'] for w in walls] + [p['rect'] for p in parapets]
        + [o['rect'] for o in openings] + [w['rect'] for w in windows])
GAP = 3
REVOKED = {'次卧小床1.2', '次卧衣柜', '3kg洗衣机', '床背板', '窄书桌'}   # owner: latest human positions verbatim
ACCEPTED = {'主卫马桶', '次主卫马桶', '主卧电视柜', '双人位'}   # HUMAN_ACCEPTED_AS_DRAWN: no move, no further collision fix
REGION_KIND = {'湿区'}                              # clip region boundary, never move content
AUTO_LIMIT = 50

def overlap(r, h):
    dx = min(r[2], h[2]) - max(r[0], h[0])
    dy = min(r[3], h[3]) - max(r[1], h[1])
    return (dx, dy) if dx > 0 and dy > 0 else None

def clip_to_hard(r, h):
    """Shrink rect r on the side(s) that intrude into hard rect h."""
    dx = min(r[2], h[2]) - max(r[0], h[0])
    dy = min(r[3], h[3]) - max(r[1], h[1])
    if dx <= 0 or dy <= 0: return
    cx, cy = (r[0]+r[2])/2, (r[1]+r[3])/2
    hx, hy = (h[0]+h[2])/2, (h[1]+h[3])/2
    if dx <= dy:
        if cx < hx: r[2] = h[0] - GAP
        else: r[0] = h[2] + GAP
    else:
        if cy < hy: r[3] = h[1] - GAP
        else: r[1] = h[3] + GAP

form_deltas = []
for f in furniture:
    src = list(f['rect'])
    if f['label'] in REVOKED:
        ovs = [h for h in HARD if overlap(f['rect'], h)]
        form_deltas.append({'label': f['label'], 'obj': f['obj'], 'zone': f['zone'],
                            'source_rect': src, 'formal_rect': src,
                            'resolution': 'USER_MANUAL_CORRECTION_KEPT',
                            'note': 'owner: human position is authoritative; residual overlap %d rect(s) accepted' % len(ovs)})
        continue
    if f['label'] in ACCEPTED:
        ovs = [h for h in HARD if overlap(f['rect'], h)]
        form_deltas.append({'label': f['label'], 'obj': f['obj'], 'zone': f['zone'],
                            'source_rect': src, 'formal_rect': src,
                            'resolution': 'HUMAN_ACCEPTED_AS_DRAWN',
                            'note': 'owner approved as-drawn; NO_MOVE / NO_AUTO_FORMALIZATION / NO_FURTHER_COLLISION_FIX; residual overlap %d rect(s)' % len(ovs)})
        continue
    is_region = any(k in f['label'] for k in REGION_KIND)
    if is_region:
        clipped = False
        for _ in range(3):
            for h in HARD:
                if overlap(f['rect'], h):
                    clip_to_hard(f['rect'], h); clipped = True
        if clipped:
            form_deltas.append({'label': f['label'], 'obj': f['obj'], 'zone': f['zone'],
                                'source_rect': src, 'formal_rect': list(f['rect']),
                                'resolution': 'REGION_BOUNDARY_CLEANUP',
                                'note': 'wet-zone boundary clipped to wall inner face; contents unmoved'})
        continue
    moved = []
    for _ in range(3):
        any_overlap = False
        for h in HARD:
            ov = overlap(f['rect'], h)
            if not ov:
                continue
            dx, dy = ov
            if dx <= dy:
                side = -1 if (f['rect'][0]+f['rect'][2])/2 < (h[0]+h[2])/2 else 1
                f['rect'][0] += side*(dx+GAP); f['rect'][2] += side*(dx+GAP)
                moved.append(('x', side*(dx+GAP)))
            else:
                side = -1 if (f['rect'][1]+f['rect'][3])/2 < (h[1]+h[3])/2 else 1
                f['rect'][1] += side*(dy+GAP); f['rect'][3] += side*(dy+GAP)
                moved.append(('y', side*(dy+GAP)))
            any_overlap = True
        if not any_overlap:
            break
    if moved:
        tdx = f['rect'][0]-src[0]; tdy = f['rect'][1]-src[1]
        rec = {'label': f['label'], 'obj': f['obj'], 'zone': f['zone'],
               'source_rect': src, 'formal_rect': list(f['rect']),
               'shift_mm': [tdx, tdy], 'dims_mm': [f['w'], f['d']]}
        if abs(tdx) <= AUTO_LIMIT and abs(tdy) <= AUTO_LIMIT:
            rec['resolution'] = 'AUTO_DRAFTING_CLEANUP'
        else:
            f['rect'] = src  # not a drafting slip -> keep human position, flag it
            rec['resolution'] = 'FLAGGED_KEPT_HUMAN_POSITION'
            f['to_verify'] = True
        form_deltas.append(rec)

# ---------------- window fidelity cross-check ----------------
win_check = []
for w in windows:
    ref = FC['window_ref_unions'].get('WINDOW_REF_' + w['id'].replace('-', '_'))
    if not ref or not ref['union_bbox_xy']:
        win_check.append({'id': w['id'], 'status': 'NO_REF_UNION'})
        continue
    ub0 = ref['union_bbox_xy']
    ub = [ub0[0] + DX, ub0[1] + DY, ub0[2] + DX, ub0[3] + DY]
    asm = list(w['rect'])
    if w.get('bay'):
        for j in w['bay']['jambs']: asm = [min(asm[0],j[0]), min(asm[1],j[1]), max(asm[2],j[2]), max(asm[3],j[3])]
        asm = [min(asm[0],w['bay']['front'][0]), min(asm[1],w['bay']['front'][1]),
               max(asm[2],w['bay']['front'][2]), max(asm[3],w['bay']['front'][3])]
    cc = [(asm[0]+asm[2])/2, (asm[1]+asm[3])/2]
    uc = [(ub[0]+ub[2])/2, (ub[1]+ub[3])/2]
    win_check.append({'id': w['id'], 'canon_asm_bbox': asm, 'fc_union_bbox': ub,
                      'center_delta_mm': [round(uc[0]-cc[0],1), round(uc[1]-cc[1],1)],
                      'resolved': ref['resolved']})

model = {
    'coord_frame': 'canonical_task01_mm (x east, y north)',
    'walls': walls, 'parapets': parapets, 'removed_walls': removed,
    'openings': openings, 'windows': windows, 'kitchen_cabinets': kcabs,
    'spaces': spaces, 'balconies': balconies, 'stairs': stairs, 'ramp': ramp,
    'furniture': furniture, 'window_fidelity': win_check,
    'removed_openings': removed_openings, 'excluded_objects': EXCLUDED,
    'formalization_delta': form_deltas,
    'sources': {'arch': 'current_existing/canonical_plan_v1.json',
                'spaces': 'data/geometry.json',
                'furniture': 'PRE_BLENDER_MASTER_V2.FCStd via b1_fcstd_objects.json',
                'transform_fc_to_canon': [DX, DY]},
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(model, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('walls', len(walls), 'parapets', len(parapets), 'removed', len(removed),
      'openings', len(openings), 'windows', len(windows), 'spaces', len(spaces),
      'kcabs', len(kcabs), 'furniture', len(furniture), 'ramp', bool(ramp))
for f in furniture: print('  %-28s %-14s %5dx%-5d zone=%s' % (f['label'], f['obj'], f['w'], f['d'], f['zone']))
for c in win_check: print('  WIN', c['id'], c.get('center_delta_mm'), c.get('resolved'))
for f in form_deltas: print('  FORMDELTA', f['label'], f.get('shift_mm'), f['resolution'])
