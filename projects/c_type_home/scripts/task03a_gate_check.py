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

# ================================================================ RC2.3 gates
WREG = json.load(open(os.path.join(ROOT, 'current_existing/window_register.json')))['windows']
REG_FIELDS = {'window_id', 'room_or_zone', 'type', 'orientation', 'current_status',
              'span_mm', 'projection_mm', 'source', 'confidence',
              'measurement_status', 'host_wall_id', 'opening_rect_mm', 'notes'}

# G21 exact registry truth — owner-confirmed fenestration set, not a subset
TRUTH = {'W-LIV-N', 'G-LIV-NBALC', 'G-GB-BALC', 'W-STUDY-NE', 'G-DIN-LIV',
         'W-LBALC-S', 'W-KIT-S', 'W-SMB-S', 'W-MB-S'}
ids = {w['window_id'] for w in WREG}
missing = TRUTH - ids; unexpected = ids - TRUTH
bad_fields = [w['window_id'] for w in WREG if not REG_FIELDS <= set(w)]
gate('G21 registry IDs == owner truth set (exact, not subset)',
     not missing and not unexpected and len(WREG) == 9 and not bad_fields,
     f"total={len(WREG)}; missing={missing}; unexpected={unexpected}; malformed={bad_fields}")

# G22 type correctness + no solid wall through any of the 9 openings
TYPE_TRUTH = {'W-LIV-N': 'BAY_WINDOW', 'W-STUDY-NE': 'BAY_WINDOW',
              'W-SMB-S': 'BAY_WINDOW', 'W-MB-S': 'BAY_WINDOW',
              'W-KIT-S': 'STANDARD_WINDOW', 'W-LBALC-S': 'BALCONY_WINDOW',
              'G-DIN-LIV': 'GLASS_SLIDING_DOOR', 'G-GB-BALC': 'GLASS_DOOR',
              'G-LIV-NBALC': 'GLASS_DOOR'}
type_bad = {w['window_id']: (w['type'], TYPE_TRUTH[w['window_id']])
            for w in WREG if w['window_id'] in TYPE_TRUTH
            and w['type'] != TYPE_TRUTH[w['window_id']]}
conf = []
for win in WREG:
    if win['type'] == 'BALCONY_WINDOW':
        continue                     # glazing sits ON parapet by design
    op = list(win['opening_rect_mm'])
    # full clear-opening check — frame/corner returns must be modeled as wall
    # or frame geometry OUTSIDE the opening, not excused by shrinking the test
    hit = [w['id'] for w in CE['walls'] if w['disposition'] == 'EXISTING'
           and not (w['rect_mm'][2] <= op[0] or w['rect_mm'][0] >= op[2] or
                    w['rect_mm'][3] <= op[1] or w['rect_mm'][1] >= op[3])]
    if hit:
        conf.append(f"{win['window_id']}<-{hit}")
gate('G22 type correctness + no solid wall through opening',
     not type_bad and not conf,
     f"type_mismatches={type_bad}; wall_conflicts={conf}")

# G23 north balcony CURRENT = open (no enclosure anywhere in existing model)
nb = CE['balconies']['north_balcony']
encl_ids = [w['window_id'] for w in WREG
            if 'N-BALC-ENCL' in w['window_id'] or 'ENCLOSURE' in w['type']]
gate('G23 north balcony current state = OPEN (no enclosure records)',
     nb.get('existing_north_enclosure') is False
     and nb.get('existing_east_enclosure') is False
     and not encl_ids,
     f"existing_north_enclosure={nb.get('existing_north_enclosure')}; "
     f"existing_east_enclosure={nb.get('existing_east_enclosure')}; "
     f"enclosure_records={encl_ids}; future={nb.get('future_enclosure')}")

# G24 TV-wall balcony door G-LIV-NBALC: on the vertical TV wall, ~850mm,
# northern section, host wall actually split, and no phantom D-BALC-W
gl = next((w for w in WREG if w['window_id'] == 'G-LIV-NBALC'), None)
tv_pieces = [w['rect_mm'] for w in CE['walls']
             if w['id'] == 'W-INT-X7900-U-TV' or w['id'].startswith('W-INT-X7900-U-TV#')]
tv_segs = [w for w in CE['walls'] if w['id'].startswith('W-INT-X7900-U-TV#G-LIV-NBALC')]
phantom = [o['id'] for o in CE['openings'] if o['id'] == 'D-BALC-W']
phantom += [w['window_id'] for w in WREG if w['window_id'] == 'D-BALC-W']
g24_ok = bool(gl and tv_pieces and tv_segs)
g24_note = 'missing records'
if gl and tv_pieces:
    oy1, oy2 = gl['opening_rect_mm'][1], gl['opening_rect_mm'][3]
    north_half_mid = (min(r[1] for r in tv_pieces) + max(r[3] for r in tv_pieces)) / 2
    in_north = (oy1 + oy2) / 2 > north_half_mid
    g24_ok = (gl['host_wall_id'] == 'W-INT-X7900-U-TV'
              and 700 <= gl['span_mm'] <= 950 and in_north
              and len(tv_segs) == 2 and not phantom)
    g24_note = (f"host={gl['host_wall_id']}; span={gl['span_mm']}; "
                f"opening_y={oy1}-{oy2} (wall_mid={north_half_mid:.0f}, north={in_north}); "
                f"wall_segments={len(tv_segs)}; phantom_D-BALC-W={phantom}")
gate('G24 TV-wall glass door G-LIV-NBALC placed + wall split + no phantom door',
     g24_ok, g24_note)

# G25 bay geometry: four bays have opening + outward projection geometry
BAYS = ['W-LIV-N', 'W-STUDY-NE', 'W-SMB-S', 'W-MB-S']
bay_bad = []
for bid in BAYS:
    w = next((w for w in WREG if w['window_id'] == bid), None)
    b = (w or {}).get('bay', {})
    if not w or not w.get('bay_geometry_confirmed') or not b.get('jambs') or not b.get('front') \
            or (w.get('projection_mm') or 0) <= 0 or not w.get('split_applied', True):
        bay_bad.append(bid)
gate('G25 bay windows have wall opening + outward projection geometry',
     not bay_bad, f"bays_checked={BAYS}; bad={bay_bad}")

# G26 ordinary door topology preserved — every measured door opening still in model
EXPECTED_DOORS = {'ENT-1', 'D-LIV-STUDY?', 'D-SM', 'D-MB', 'D-BATHM', 'D-STUDY',
                  'D-GBATH', 'D-GBED', 'D-CLK', 'D-MASTER?', 'G-GB-BALC',
                  'G-DIN-LIV', 'G-LIV-NBALC', 'OPEN-COR-LIV'}
model_doors = {o['id'] for o in CE['openings']}
missing_doors = EXPECTED_DOORS - model_doors
gate('G26 ordinary door openings preserved in model',
     not missing_doors,
     f"measured_door_count={len(EXPECTED_DOORS)}; model_door_count={len(model_doors)}; "
     f"missing_door_ids={missing_doors}")

# G27 layout freeze vs RC2.1 baseline 246ff12
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
gate('G27 layout freeze vs RC2.1', not diffs,
     f"changed={diffs if diffs else 'none'} (windows/wall-split/render changes exempt)")

# ================================================================ RC3 gates
# G28 canonical base consistency — every artefact renders from one geometry
import hashlib
CANON = json.load(open(os.path.join(ROOT, 'current_existing/canonical_plan_v1.json')))
KREG = json.load(open(os.path.join(ROOT, 'current_existing/kitchen_cabinet_register.json')))['cabinets']
def _sha(o):
    return hashlib.sha256(json.dumps(o, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
hash_bad = []
sections = {'walls': CE['walls'], 'openings': CE['openings'], 'windows': CE['windows'],
            'kitchen_cabinets': KREG, 'keep_items': CE['keep_items'],
            'balconies': CE['balconies'], 'split_level': CE['split_level']}
for k, obj in sections.items():
    if _sha(obj) != CANON['hashes'].get(k):
        hash_bad.append(k)
    if CANON.get(k) != (KREG if k == 'kitchen_cabinets' else CE.get(k)):
        hash_bad.append(f'{k}:content')
# RC3.1: every rendered sheet / DXF must carry a sidecar declaring the same canonical sha
canon_file_sha = hashlib.sha256(
    open(os.path.join(ROOT, 'current_existing/canonical_plan_v1.json'), 'rb').read()
).hexdigest()[:16]
sidecars = {'qc/render_manifest.json': os.path.join(ROOT, 'qc/render_manifest.json'),
            'current_existing_v1.dxf': os.path.join(ROOT, 'current_existing/current_existing_v1.base.json'),
            'concept_dxfs': os.path.join(ROOT, 'concept/concept_dxf_base.json')}
sc_bad = []
for tag, sp in sidecars.items():
    if not os.path.exists(sp):
        sc_bad.append(f'{tag}:missing')
        continue
    if json.load(open(sp)).get('canonical_sha') != canon_file_sha:
        sc_bad.append(f'{tag}:sha_mismatch')
gate('G28 canonical base hash + output sidecars consistent',
     not hash_bad and not sc_bad,
     f"sections={list(sections)}; mismatched={hash_bad}; sidecars={sc_bad or 'all match'}")

# G29 kitchen cabinets never overlap walls / windows / door openings
cab_conf = []
blockers = ([w['rect_mm'] for w in CE['walls'] if w['disposition'] == 'EXISTING']
            + [w['opening_rect_mm'] for w in CE['windows']]
            + [o['rect_mm'] for o in CE['openings']])
for c in KREG:
    r = c['rect_mm']
    hit = [b for b in blockers
           if not (b[2] <= r[0] or b[0] >= r[2] or b[3] <= r[1] or b[1] >= r[3])]
    if hit:
        cab_conf.append(c['id'])
gate('G29 kitchen cabinets clear of walls/windows/doors',
     not cab_conf, f"cabinet_conflicts={cab_conf}")

# G30 independent floor-standing cabinets never overlap in area.
# Exemptions: parent/child containment, wall_cabinet_above, declared corner_join zones.
floor_kinds = {'base_cabinet_run', 'tall_cabinet', 'base_cabinet_sink_leg'}
floor_cabs = {c['id']: c for c in KREG if c['kind'] in floor_kinds and not c.get('parent')}
def _overlap(a, b):
    dx = min(a[2], b[2]) - max(a[0], b[0]); dy = min(a[3], b[3]) - max(a[1], b[1])
    return (dx, dy) if dx > 0 and dy > 0 else None
def _zone_contains(zone, rect):
    return (zone and zone[0] <= rect[0] and zone[1] <= rect[1]
            and zone[2] >= rect[2] and zone[3] >= rect[3])
cab_collisions, cab_exempted = [], []
ids = sorted(floor_cabs)
for i, a in enumerate(ids):
    for b in ids[i + 1:]:
        ov = _overlap(floor_cabs[a]['rect_mm'], floor_cabs[b]['rect_mm'])
        if not ov:
            continue
        dx, dy = ov
        orect = [max(floor_cabs[a]['rect_mm'][0], floor_cabs[b]['rect_mm'][0]),
                 max(floor_cabs[a]['rect_mm'][1], floor_cabs[b]['rect_mm'][1]),
                 min(floor_cabs[a]['rect_mm'][2], floor_cabs[b]['rect_mm'][2]),
                 min(floor_cabs[a]['rect_mm'][3], floor_cabs[b]['rect_mm'][3])]
        join = next((c[j] for c in (floor_cabs[a], floor_cabs[b])
                     for j in ['corner_join'] if c.get(j) and c[j].get('with') in (a, b)), None)
        if join and _zone_contains(join.get('zone'), orect):
            cab_exempted.append(f"{a}x{b} corner_join {dx}x{dy}mm (declared)")
        else:
            cab_collisions.append(f"{a}x{b} overlap {dx}x{dy}mm = {dx*dy/1e6:.3f}m2")
gate('G30 no unexplained floor-cabinet overlap',
     not cab_collisions,
     f"collisions={cab_collisions or 'none'}; exempted={cab_exempted or 'none'}")

overall = all(r['result'] == 'PASS' for r in results)
print(f"\n=== TASK03A GATES: {sum(r['result']=='PASS' for r in results)}/{len(results)} {'ALL PASS' if overall else 'HAS FAIL'} ===")
json.dump({'gates': results, 'overall': 'PASS' if overall else 'FAIL'},
          open(os.path.join(ROOT, 'qc/task03a_gates.json'), 'w'), indent=2)
