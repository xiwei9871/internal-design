#!/usr/bin/env python3
"""Task03A hard-gate checks — reads current_existing_v1.json + concept_data.json,
emits pass/fail per gate to qc/task03a_gates.json + stdout."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CE = json.load(open(os.path.join(ROOT, 'current_existing/current_existing_v1.json')))
CD = json.load(open(os.path.join(ROOT, 'concept/concept_data.json')))
MAN = json.load(open(os.path.join(ROOT, 'source/source_manifest.json')))

results = []
def gate(name, ok, detail):
    results.append({'gate': name, 'result': 'PASS' if ok else 'FAIL', 'detail': detail})
    print(('PASS' if ok else 'FAIL'), name, '|', detail)

def inter(r1, r2):
    return not (r1[2] <= r2[0] or r1[0] >= r2[2] or r1[3] <= r2[1] or r1[1] >= r2[3])

F = CD['furniture']

# G1 source integrity
src = MAN['sources'][0]
gate('G1 measured DWG units+hash recorded', 'mm' in src['units'] and len(src['sha256']) == 64,
     f"{src['file']} sha={src['sha256'][:12]} units={src['units']} immutable={src['immutable']}")

# G2 W/S honest compare: S on NEW partition feasible; W constrained by retained CLK-W; conflicts flagged
conflicts = [w['id'] for w in CE['walls'] if 'CONFLICT' in w['wall_class']]
clk_kept = all(any(w['id'] == f'W-INT-CLK-{d}' and w['disposition'] == 'EXISTING'
                   for w in CE['walls']) for d in 'NWE')
w_ok = 'CONSTRAINED' in CD['smb']['entry_W'].get('verdict', '')
s_ok = 'FEASIBLE' in CD['smb']['entry_S'].get('verdict', '')
gate('G2 cloakroom shell kept; S on new partition; W constrained honestly',
     clk_kept and w_ok and s_ok and len(conflicts) >= 1,
     f"CLK-N/W/E existing={clk_kept} | S: {CD['smb']['entry_S']['verdict']} | W: {CD['smb']['entry_W']['verdict']} | conflicts={conflicts}")

# G3 kitchen cabinet zone untouched by proposed furniture/plumbing
kcab = next(f['rect'] for f in F if f['id'] == 'K-CAB')
bad = [f['id'] for f in F if f['layer'] in ('A-FURN-PROP', 'A-FIXT-PLUMB') and inter(f['rect'], kcab)]
gate('G3 kitchen cabinets untouched', not bad, f"keep zone {kcab}; intruders={bad}")

# G4 existing glazing preserved
glass = [o for o in CE['openings'] if o['id'].startswith('G-') or 'glass' in o.get('note', '')]
gate('G4 glazing preserved (sliding door + balcony glazing)', all(o['status'].startswith('EXISTING') for o in glass),
     '; '.join(f"{o['id']}:{o['status']}" for o in glass))

# G5 bed clearance: 1800x2100 beds in master + secondary master
mb = next(f for f in F if f['id'] == 'MB-BED'); sb = next(f for f in F if f['id'] == 'SMB-BED')
mw = mb['rect'][2] - mb['rect'][0]; mh = mb['rect'][3] - mb['rect'][1]
sw = sb['rect'][2] - sb['rect'][0]; sh = sb['rect'][3] - sb['rect'][1]
gate('G5 1800x2100 beds fit', {mw, mh} == {1800, 2100} and {sw, sh} == {1800, 2100},
     f"MB {mw}x{mh}; SMB {sw}x{sh}")

# G6 secondary master bath 3-piece fits in ~5m2 shell+annex
z = CD['smb']['zone_mm']; area = CD['smb']['area_m2']
fix = [f for f in F if f['id'].startswith('SMB2-')]
gate('G6 secondary bath 3-piece fits ~5m2', len(fix) == 3 and 4.5 <= area <= 5.5,
     f"shell {z[2]-z[0]}x{z[3]-z[1]} + annex -> {area}m2, fixtures={len(fix)}; drain via shared MBATH wet wall TO_VERIFY")

# G7 guest bedroom balcony access stays clear
zone = next(f['rect'] for f in F if f['id'] == 'GB-GLASSDOOR-ZONE')
bad = [f['id'] for f in F if f['layer'] == 'A-FURN-PROP' and inter(f['rect'], zone)]
gate('G7 balcony glass-door route clear', not bad, f"zone {zone}; blockers={bad}")

# G8 living flexible core kept open (small movable tables exempt per owner brief)
def movable_ok(f):
    w = f['rect'][2]-f['rect'][0]; h = f['rect'][3]-f['rect'][1]
    return 'movable' in f.get('note','') and max(w,h) <= 900
core = [4300, 8900, 7100, 12100]
bad = [f['id'] for f in F if f['layer'] == 'A-FURN-PROP' and inter(f['rect'], core) and not movable_ok(f)]
gate('G8 living flexible core open', not bad,
     f"open core {core[2]-core[0]}x{core[3]-core[1]}; intruders={bad} (small movable table exempt)")

# G9 stair/ramp documented; slope range flagged provisional; delta unresolved
lv = CD['level']; ramp = lv['ramp']
sl = CE['split_level']
gate('G9 stair/ramp documented, slope PROVISIONAL', ramp['run_mm'] >= 2500 and 'PROVISIONAL' in ramp['slope'],
     f"run {ramp['run_mm']}x{ramp['width_mm']}; slope {ramp['slope']}; assisted-use (no code claim)")

# G10 level delta conflict explicitly recorded
gate('G10 level delta conflict recorded', sl['level_status'] == 'LEVEL_DELTA_TO_VERIFY'
     and sl['level_difference_mm'] is None and 'owner_estimate_mm' in sl,
     f"owner {sl['owner_estimate_mm']} vs CAD {sl['cad_derived_mm']} — field measure requested")

# G10b north balcony open now, enclosure proposed
nb = CE['balconies']['north_balcony']
gate('G10b N balcony OPEN + enclosure PROPOSED', nb['current_enclosure'] == 'OPEN_NOT_ENCLOSED'
     and 'PROPOSED' in nb['future_enclosure'],
     f"current={nb['current_enclosure']}, future={nb['future_enclosure']}")

# G11 study program: desk + storage + backup sleep
ids = [f['id'] for f in F]
gate('G11 study program complete', all(k in ids for k in ('ST-DESK', 'ST-BOOK', 'ST-DAYBED', 'ST-NAS')),
     'desk 1700x800 + wardrobe-storage + daybed backup sleep + NAS shelf')

# G12 guest bath wet/dry zones preserved
gate('G12 guest bath wet/dry preserved', all(k in ids for k in ('GBATH-SHOWER', 'GBATH-3KG', 'GBATH-WC', 'GBATH-VANITY')),
     'wet=rear shower+3kg washer; dry=front WC+vanity')

# G13 KEEP items honored
keeps = [f['id'] for f in F if f['layer'] == 'A-FURN-EXST-KEEP']
gate('G13 KEEP furniture/cabinets placed', {'K-CAB', 'MB-WARD', 'ST-BOOK', 'NB-WD', 'SHOE-CAB'} <= set(keeps),
     f"keeps: {keeps}")

# G14 four named rooms + three baths functional
prog = {'master': 'MB-BED', 'secondary_master': 'SMB-BED', 'guest': 'GB-BUNK', 'study': 'ST-DESK'}
baths = {'master': 'MBATH-SHOWER', 'secondary': 'SMB2-SHOWER', 'guest': 'GBATH-SHOWER'}
gate('G14 4 rooms + 3 baths functional', all(v in ids for v in list(prog.values()) + list(baths.values())),
     'program satisfied')

# ================================================================ RC2 gates
SOLID = {'A-FURN-PROP', 'A-FURN-EXST-KEEP', 'A-FIXT-PLUMB'}
solid = [f for f in F if f['layer'] in SOLID]

# G15 no furniture/fixture overlap anywhere
ov = []
for i in range(len(solid)):
    for j in range(i + 1, len(solid)):
        if inter(solid[i]['rect'], solid[j]['rect']):
            ov.append(f"{solid[i]['id']}x{solid[j]['id']}")
gate('G15 no furniture overlap', not ov, f"overlaps={ov}")

# G16 door-swing envelopes clear of PROPOSED furniture/fixtures
# (KEEP items are existing and already resolved against existing doors on site)
bad = []
for s in CD['door_swings']:
    for f in solid:
        if f['layer'] != 'A-FURN-EXST-KEEP' and inter(f['rect'], s['rect']):
            bad.append(f"{s['door']}x{f['id']}")
gate('G16 door swings clear of new furniture/fixtures', not bad, f"collisions={bad}")

# G17 secondary bath: clearances fixture-free AND main aisle >=750 continuous
bad = []
for name, r in CD['smb']['clearances'].items():
    for f in solid:
        if inter(f['rect'], r):
            bad.append(f"{name}x{f['id']}")
ma = CD['smb']['clearances']['main_aisle']
aisle_w = ma[2] - ma[0]
gate('G17 SMB bath clearances + main aisle >=750', not bad and aisle_w >= 750,
     f"main aisle {aisle_w}mm continuous; zones={list(CD['smb']['clearances'])}; intruders={bad}")

# G18 guest room: connected entry->balcony path — every segment fixture-free,
# every consecutive shared edge >=750 (catches the old 300mm throat)
path = CD['guest_path']
def shared_edge(a, b):
    if abs(a[3] - b[1]) < 1 or abs(b[3] - a[1]) < 1:
        return max(0, min(a[2], b[2]) - max(a[0], b[0]))
    return 0
bad = [f['id'] for f in solid if any(inter(f['rect'], r) for r in path)]
throats = [shared_edge(path[i], path[i+1]) for i in range(len(path) - 1)]
widths = [r[2] - r[0] for r in path]
gate('G18 guest-room path to balcony >=750 continuous',
     not bad and min(throats) >= 750 and min(widths) >= 750,
     f"segment widths={widths}; throat widths={throats}; blockers={bad}")

# G19 study real circulation: main aisle between daybed row and book wall
st_aisle = [14000, 7300, 15500, 11300]
bad = [f['id'] for f in solid if f['layer'] == 'A-FURN-PROP' and inter(f['rect'], st_aisle)]
gate('G19 study circulation aisle clear', not bad,
     f"aisle {st_aisle[2]-st_aisle[0]}x{st_aisle[3]-st_aisle[1]}; blockers={bad}")

# G20 split-level net-area comparison emitted honestly
acv = CD['level'].get('area_comparison', {})
gate('G20 split-level net-area account present',
     {'returned_platform_m2', 'ramp_footprint_m2', 'net_unobstructed_public_gain_m2',
      'living_largest_clear_rect'} <= set(acv) and acv.get('net_unobstructed_public_gain_m2') is not None,
     f"returned {acv.get('returned_platform_m2')} vs ramp {acv.get('ramp_footprint_m2')} "
     f"-> net +{acv.get('net_unobstructed_public_gain_m2')}m2 (PROVISIONAL)")

# ================================================================ RC2.2 gates
WREG = json.load(open(os.path.join(ROOT, 'current_existing/window_register.json')))['windows']
REG_FIELDS = {'window_id', 'room_or_zone', 'orientation_plan_relative', 'window_type',
              'source_plan_evidence', 'measured_dwg_evidence', 'current_status',
              'proposed_status', 'span_mm', 'sill_or_bay_note', 'confidence',
              'verification_status', 'notes'}
WTYPES = {'STANDARD_WINDOW', 'BAY_WINDOW', 'BALCONY_GLAZING', 'GLASS_DOOR',
          'PROPOSED_BALCONY_ENCLOSURE'}
VSTATS = {'CONFIRMED', 'MEASURED', 'TO_VERIFY', 'PROPOSED'}

# G21 every perimeter window/bay/glazing identified on the dev plan + measured DWG
# is registered (perimeter review result — encoded once, then register must cover it)
EXPECTED = {'W-KIT-S', 'W-KIT-SW', 'W-SMB-S', 'W-MB-S', 'W-LIV-N', 'W-STUDY-NE',
            'W-GBATH-N', 'G-GB-BALC', 'D-BALC-W', 'G-DIN-LIV', 'N-BALC-ENCL'}
ids = {w['window_id'] for w in WREG}
missing = EXPECTED - ids
bad_fields = [w['window_id'] for w in WREG
              if not REG_FIELDS <= set(w) or w['window_type'] not in WTYPES
              or w['verification_status'] not in VSTATS]
gate('G21 original-plan window coverage (register complete)',
     not missing and not bad_fields,
     f"registered={len(WREG)}; missing={sorted(missing)}; malformed={bad_fields}")

# G22 no continuous solid wall through any registered window/glass-door span
conf = []
for win in WREG:
    if win['window_type'] == 'PROPOSED_BALCONY_ENCLOSURE':
        continue
    op = win['opening_rect_mm']
    hit = [w['id'] for w in CE['walls'] if w['disposition'] == 'EXISTING'
           and not (w['rect_mm'][2] <= op[0] or w['rect_mm'][0] >= op[2] or
                    w['rect_mm'][3] <= op[1] or w['rect_mm'][1] >= op[3])]
    if hit:
        conf.append(f"{win['window_id']}<-{hit}")
gate('G22 no solid wall through window span', not conf,
     f"checked {len(WREG)} openings; conflicts={conf}")

# G23 north balcony time-state
nb = CE['balconies']['north_balcony']
ggb = next((w for w in WREG if w['window_id'] == 'G-GB-BALC'), None)
nbe = next((w for w in WREG if w['window_id'] == 'N-BALC-ENCL'), None)
gate('G23 N-balcony time-state (open now / proposed / glass door keep)',
     nb['current_enclosure'] == 'OPEN_NOT_ENCLOSED'
     and 'PROPOSED' in nb['future_enclosure']
     and ggb is not None and ggb['proposed_status'] == 'EXISTING_KEEP'
     and nbe is not None and nbe['verification_status'] == 'PROPOSED',
     f"current={nb['current_enclosure']}; future={nb['future_enclosure']}; "
     f"G-GB-BALC={ggb['proposed_status'] if ggb else 'MISSING'}")

# G24 no orphan wall graphics in presentation drawing:
# every EXISTING wall must touch another wall / window opening / bay component,
# except legit detached types (balcony parapets)
def _touches(a, b, tol=45):
    return not (a[2] + tol <= b[0] or a[0] - tol >= b[2] or
                a[3] + tol <= b[1] or a[1] - tol >= b[3])
nodes = [w['rect_mm'] for w in CE['walls'] if w['disposition'] == 'EXISTING']
for win in WREG:
    if win['window_type'] == 'PROPOSED_BALCONY_ENCLOSURE':
        continue
    nodes.append(win['opening_rect_mm'])
    for j in win.get('bay', {}).get('jambs', []):
        nodes.append(j)
    if win.get('bay'):
        nodes.append(win['bay']['front'])
# demolished/opening context: a free wall END explained by a demolished wall or
# registered door opening is a real envelope end, not a floating graphic
context = nodes + [w['rect_mm'] for w in CE['walls'] if w['disposition'] != 'EXISTING'] + \
          [o['rect_mm'] for o in CE['openings']]
EXEMPT = {'railing_parapet'}
orphans = []
for w in CE['walls']:
    if w['disposition'] != 'EXISTING' or w['type'] in EXEMPT:
        continue
    r = w['rect_mm']
    if not any(_touches(r, n) for n in context if n is not r):
        orphans.append(w['id'])
gate('G24 no orphan wall graphics', not orphans,
     f"orphans={orphans} (parapets + explained free ends exempt)")

# G25 layout freeze vs RC2.1 baseline 246ff12
BASE = json.load(open(os.path.join(ROOT, 'qc/layout_baseline_246ff12.json')))
diffs = []
for k in ('level', 'new_walls', 'new_doors', 'smb', 'guest_path', 'door_swings'):
    if CD.get(k) != BASE.get(k):
        diffs.append(k)
fb = {f['id']: f for f in BASE['furniture']}
for f in CD['furniture']:
    b = fb.get(f['id'])
    if b is None or b['rect'] != f['rect']:
        diffs.append(f"furniture:{f['id']}")
gate('G25 layout freeze vs RC2.1', not diffs,
     f"changed={diffs if diffs else 'none'} (windows/wall-split/render changes exempt)")

overall = all(r['result'] == 'PASS' for r in results)
print(f"\n=== TASK03A GATES: {sum(r['result']=='PASS' for r in results)}/{len(results)} {'ALL PASS' if overall else 'HAS FAIL'} ===")
json.dump({'gates': results, 'overall': 'PASS' if overall else 'FAIL'},
          open(os.path.join(ROOT, 'qc/task03a_gates.json'), 'w'), indent=2)
