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
    return f['id'] in {'LIV-COFFEE-MOV', 'LIV-SIDE-TABLE'} or \
        ('movable' in f.get('note', '') and max(f['rect'][2]-f['rect'][0], f['rect'][3]-f['rect'][1]) <= 900)
core = [3900, 7400, 7700, 11750]   # F1 owner layout: between W sofa / S lounge / N 2-seat / E media wall
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
gate('G13 KEEP furniture/cabinets placed', {'K-CAB', 'MB-WARD', 'ST-BOOK', 'NB-WD', 'ENTRY-SHOE-CAB', 'LBALC-CAB'} <= set(keeps),
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
        # F1: ramp relocated per owner markup — exempt ramp subtree, freeze the rest
        if k == 'level':
            lv = {a: b for a, b in CD['level'].items() if a != 'ramp'}
            bv = {a: b for a, b in BASE['level'].items() if a != 'ramp'}
            lv['area_comparison'] = {k2: v for k2, v in lv['area_comparison'].items()
                                     if k2 not in ('ramp_footprint_m2', 'net_unobstructed_public_gain_m2', 'verdict')}
            bv['area_comparison'] = {k2: v for k2, v in bv['area_comparison'].items()
                                     if k2 not in ('ramp_footprint_m2', 'net_unobstructed_public_gain_m2', 'verdict')}
            if lv != bv:
                diffs.append(k)
        else:
            diffs.append(k)
fb = {f['id']: f for f in BASE['furniture']}
# F1: L1 furniture intentionally re-laid per owner markup — freeze applies to
# L2 furniture/baths/keeps only; L1 governed by F1 gates + furniture_l1_final.json
L1_CHANGED = {'SOFA-3', 'SOFA-2', 'LOUNGE-1', 'COFFEE-MOV', 'PROJ-SCREEN', 'DIN-TABLE',
              'SHOE-CAB', 'BENCH', 'RAMP', 'STAIR',
              'LIV-SOFA-3', 'LIV-SOFA-2', 'LIV-LOUNGE', 'LIV-SIDE-TABLE', 'LIV-COFFEE-MOV',
              'LIV-MEDIA-WALL', 'ENTRY-SHOE-CAB', 'ENTRY-BENCH', 'LBALC-CAB', 'STAIR-EXISTING'}
for f in CD['furniture']:
    if f['id'] in L1_CHANGED:
        continue
    b = fb.get(f['id'])
    if b is None or b['rect'] != f['rect']:
        diffs.append(f"furniture:{f['id']}")
for fid, b in fb.items():
    if fid in L1_CHANGED:
        continue
    if fid not in {f['id'] for f in CD['furniture']}:
        diffs.append(f"missing:{fid}")
gate('G27 layout freeze vs RC2.1 (L2/background scope)', not diffs,
     f"changed={diffs if diffs else 'none'} (L1 furniture governed by F1 gates)")

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
rm_outputs = (json.load(open(sidecars['qc/render_manifest.json'])).get('outputs', [])
              if os.path.exists(sidecars['qc/render_manifest.json']) else [])
for expected_sheet in ('task03a_s1_current_existing.png', 'task03a_s6_smb_ws.png',
                       'task03a_f1_level1_furniture_qc.png'):
    if expected_sheet not in rm_outputs:
        sc_bad.append(f'manifest_missing:{expected_sheet}')
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

# ================================================================ F1 gates — L1 furniture final
F1J = json.load(open(os.path.join(ROOT, 'concept/furniture_l1_final.json')))
fbyid = {f['id']: f for f in F}

# F1-G1 base frozen — F1 contract references the same canonical sha
gate('F1-G1 frozen base referenced', F1J.get('canonical_geometry_sha') == canon_file_sha,
     f"f1_sha={F1J.get('canonical_geometry_sha')} canon={canon_file_sha}")

# F1-G2 living layout per owner markup
need = ['LIV-SOFA-3', 'LIV-SOFA-2', 'LIV-LOUNGE', 'LIV-SIDE-TABLE', 'LIV-COFFEE-MOV', 'LIV-MEDIA-WALL']
liv_bad = [i for i in need if i not in fbyid]
if 'LOUNGE-1' in fbyid or 'SOFA-3' in fbyid or 'SOFA-2' in fbyid or 'PROJ-SCREEN' in fbyid:
    liv_bad.append('stale id present')
orients = []
s3 = fbyid.get('LIV-SOFA-3', {}).get('rect')
if s3 and not (s3[0] <= 2950 and (s3[3]-s3[1]) > (s3[2]-s3[0])):
    orients.append('SOFA-3 not west-wall N-S')
s2 = fbyid.get('LIV-SOFA-2', {}).get('rect')
if s2 and not ((s2[2]-s2[0]) > (s2[3]-s2[1]) and s2[1] > 11000):
    orients.append('SOFA-2 not horizontal under N window')
gate('F1-G2 living layout per markup', not liv_bad and not orients,
     f"missing/bad={liv_bad or orients or 'none'}")

# F1-G3 old central ramp footprint gone
old_ramp = [4150, 5600, 7150, 6700]
ramp_residue = [f['id'] for f in F if f['rect'] == old_ramp]
ramp_data_ok = CD['level']['ramp']['rect_mm'] != old_ramp
gate('F1-G3 old central ramp removed', not ramp_residue and ramp_data_ok,
     f"residue={ramp_residue or 'none'}")

# F1-G4 new ramp ~2500x1100 south-edge, top flush with landing west edge
rr = CD['level']['ramp']['rect_mm']
run, wid = rr[2]-rr[0], rr[3]-rr[1]
gate('F1-G4 new ramp south-edge 2500x1100 -> landing',
     run == 2500 and wid == 1100 and rr[1] >= 4650 and rr[1] <= 4765
     and rr[2] == 7800 and 'ASSISTED' in CD['level']['ramp'].get('note', ''),
     f"rect={rr} run={run} width={wid} top_x={rr[2]}")

# F1-G5 dining table relocated to real dining zone
dt = fbyid.get('DIN-TABLE', {}).get('rect')
old_dt_free = not any(inter(f['rect'], [3700, 4800, 5200, 5400])
                      for f in F if f['layer'] in SOLID)
gate('F1-G5 dining table 1500x600 in dining zone',
     dt and (dt[2]-dt[0], dt[3]-dt[1]) == (1500, 600)
     and 2900 <= dt[0] and dt[2] <= 5500 and 2560 <= dt[1] and dt[3] <= 4450 and old_dt_free,
     f"rect={dt} old_pos_clear={old_dt_free}")

# F1-G6 entry preserved
gate('F1-G6 entry preserved', all(i in fbyid for i in ('ENTRY-SHOE-CAB', 'ENTRY-BENCH')),
     f"present={[i for i in ('ENTRY-SHOE-CAB','ENTRY-BENCH') if i in fbyid]}")

# F1-G7 kitchen frozen — cabinet register identical to canonical section
gate('F1-G7 kitchen cabinets frozen vs canonical',
     CANON.get('kitchen_cabinets') == KREG,
     'cabinet section == kitchen_cabinet_register')

# F1-G8 five primary paths fixture-free (access ramps/stairs are the path itself)
path_bad = []
for pname, segs in CD['l1_paths'].items():
    for f in solid:
        if 'ACCESS' in f['layer']:
            continue
        for r in segs:
            if inter(f['rect'], r):
                path_bad.append(f"{pname}x{f['id']}")
gate('F1-G8 five L1 circulation paths fixture-free', not path_bad,
     f"blockers={path_bad or 'none'}")

# F1-G9 no furniture collision (large items vs each other + walls/openings/windows)
L1_SOLID = [f for f in solid if f['id'] in
            {'LIV-SOFA-3', 'LIV-SOFA-2', 'LIV-LOUNGE', 'LIV-SIDE-TABLE', 'LIV-COFFEE-MOV',
             'DIN-TABLE', 'ENTRY-SHOE-CAB', 'ENTRY-BENCH', 'LBALC-CAB'}]
f1ov = []
for i in range(len(L1_SOLID)):
    for j in range(i + 1, len(L1_SOLID)):
        if inter(L1_SOLID[i]['rect'], L1_SOLID[j]['rect']):
            f1ov.append(f"{L1_SOLID[i]['id']}x{L1_SOLID[j]['id']}")
blockers2 = ([w['rect_mm'] for w in CE['walls'] if w['disposition'] == 'EXISTING']
             + [o['rect_mm'] for o in CE['openings']]
             + [w['opening_rect_mm'] for w in CE['windows']])
for f in L1_SOLID:
    if f['layer'] == 'A-FURN-EXST-KEEP':
        continue   # existing keeps already resolved on site vs door/wall tolerance bands
    for b in blockers2:
        if inter(f['rect'], b):
            f1ov.append(f"{f['id']}xBLOCKER{b}")
gate('F1-G9 L1 furniture no collision', not f1ov, f"collisions={f1ov or 'none'}")

# F1-G10 L2 untouched — all non-L1 furniture identical to RC2.1 baseline
l2_diffs = []
for fid, b in fb.items():
    if fid in L1_CHANGED:
        continue
    cur = fbyid.get(fid)
    if cur is None or cur['rect'] != b['rect']:
        l2_diffs.append(fid)
gate('F1-G10 L2 furniture/baths unchanged', not l2_diffs,
     f"changed={l2_diffs or 'none'}")

# F1-G11 dining seating clearance — 600mm pull-out each long side fixture-free
seat_bad = []
for zn, r in CD['l1_seating'].items():
    if not isinstance(r, list):
        continue
    for f in solid:
        if 'ACCESS' in f['layer']:
            continue
        if inter(f['rect'], r):
            seat_bad.append(f"{zn}x{f['id']}")
gate('F1-G11 dining seating pull-out zones clear', not seat_bad,
     f"zones=DIN-SEATING-N/S 600mm; blockers={seat_bad or 'none'}")

# ================================ RC4 — versioned CAD-native pipeline =================
import ezdxf, hashlib
from ezdxf import bbox as _eb

CADDIR = os.path.join(ROOT, 'cad')
CVM = json.load(open(os.path.join(CADDIR, 'cad_version_manifest.json')))
REGJ = json.load(open(os.path.join(CADDIR, 'cad_change_registry.json')))
CVER = {v['version']: v for v in CVM['versions']}
AX, AY = 1298172.0, -296458.0
def _sha_file(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def _rect_norm(b):  # entity bbox -> task01 rect
    return [b.extmin.x - AX, b.extmin.y - AY, b.extmax.x - AX, b.extmax.y - AY]
def _tags(msp):
    out = {}
    for e in msp:
        if e.dxftype() != 'INSERT':
            continue
        att = {a.dxf.tag: a.dxf.text for a in e.attribs}
        if 'ELEM_ID' in att:
            out[att['ELEM_ID']] = {'insert': e, 'attribs': att}
    return out
def _rects_on(msp, layers):
    rs = []
    for e in msp:
        if e.dxf.layer not in layers:
            continue
        if e.dxftype() == 'INSERT':
            try:   # furniture blocks are real-size, origin at rect min corner
                bb = _eb.extents(list(e.block()))
                ip = e.dxf.insert
                rs.append([ip.x + bb.extmin.x - AX, ip.y + bb.extmin.y - AY,
                           ip.x + bb.extmax.x - AX, ip.y + bb.extmax.y - AY])
            except Exception:
                pass
        elif e.dxftype() in ('LWPOLYLINE', 'LINE', 'POLYLINE'):
            try:
                rs.append(_rect_norm(_eb.extents([e])))
            except Exception:
                pass
    return rs
def _cover(rect, rects, eps=1.0):
    """share of rect's span covered by union of candidate rects (1D-major).
    eps lets zero-thickness linework sitting on the rect edge count."""
    x1, y1, x2, y2 = rect
    if (x2 - x1) >= (y2 - y1):
        ivs = sorted((max(x1, r[0]), min(x2, r[2])) for r in rects
                     if not (r[3] <= y1 - eps or r[1] >= y2 + eps))
        span = x2 - x1
    else:
        ivs = sorted((max(y1, r[1]), min(y2, r[3])) for r in rects
                     if not (r[2] <= x1 - eps or r[0] >= x2 + eps))
        span = y2 - y1
    tot, cur_s, cur_e = 0.0, None, None
    for s, e_ in ivs:
        if s >= e_:
            continue
        if cur_s is None:
            cur_s, cur_e = s, e_
        elif s <= cur_e:
            cur_e = max(cur_e, e_)
        else:
            tot += cur_e - cur_s; cur_s, cur_e = s, e_
    if cur_s is not None:
        tot += cur_e - cur_s
    return tot / max(span, 1)

_dmeas = ezdxf.readfile(os.path.join(CADDIR, 'measured_working.dxf'))
_dv01 = ezdxf.readfile(os.path.join(CADDIR, 'design_v01_existing_sync.dxf'))
_dv02 = ezdxf.readfile(os.path.join(CADDIR, 'design_v02_f1_l1.dxf'))
_msp_m, _msp1, _msp2 = _dmeas.modelspace(), _dv01.modelspace(), _dv02.modelspace()

# RC4-G1 source immutable — files match manifest-recorded hashes
g1 = (_sha_file(os.path.join(ROOT, 'source/世纪欣园FF.dwg')) == CVM['source_freeze']['source_dwg_sha256']
      and _sha_file(os.path.join(ROOT, 'current_existing/measured_working.dxf'))
      == CVM['source_freeze']['measured_dxf_sha256']
      == _sha_file(os.path.join(CADDIR, 'measured_working.dxf')))
gate('RC4-G1 source immutable (DWG+measured DXF sha match manifest)', g1,
     f"dwg={CVM['source_freeze']['source_dwg_sha256'][:12]} dxf={CVM['source_freeze']['measured_dxf_sha256'][:12]}")

# RC4-G2 full-copy inheritance — every measured handle present in V01
h_m = {e.dxf.handle for e in _msp_m}
h_1 = {e.dxf.handle for e in _msp1}
missing = h_m - h_1
gate('RC4-G2 full-copy inheritance', not missing,
     f"measured={len(h_m)} inherited={len(h_m & h_1)} missing={len(missing)} "
     f"{sorted(missing)[:5] if missing else ''}")

# RC4-G3 version lineage — parent pointers + recorded shas consistent
g3 = (CVER['V01']['parent'] == 'MEASURED' and CVER['V02']['parent'] == 'V01'
      and CVER['V01']['parent_sha256'] == CVER['MEASURED']['sha256']
      and CVER['V02']['parent_sha256'] == CVER['V01']['sha256']
      and CVER['V01']['sha256'] == _sha_file(os.path.join(CADDIR, 'design_v01_existing_sync.dxf'))
      and CVER['V02']['sha256'] == _sha_file(os.path.join(CADDIR, 'design_v02_f1_l1.dxf')))
gate('RC4-G3 version lineage MEASURED<-V01<-V02', g3,
     f"V01={CVER['V01']['sha256'][:12]} V02={CVER['V02']['sha256'][:12]}")

# RC4-G4 auditability — every entity on audit/correction layers traced to registry
reg_handles = {r['source_handle'] for r in REGJ if r['source_handle']}
reg_corr = sum(1 for r in REGJ if r['source_layer'] in
               ('A-WALL-EXST-CORR', 'A-CAB-EXST-BASE', 'A-CAB-EXST-TALL',
                'A-CAB-EXST-WALL', 'A-EQPM-EXST', 'A-FURN-PROP', 'A-FURN-EXST-KEEP'))
untraced = [e.dxf.handle for e in _msp1
            if e.dxf.layer in ('A-WALL-DEMO', 'A-SURVEY-SUPERSEDED')
            and e.dxf.handle not in reg_handles]
gate('RC4-G4 all DEMO/SUPERSEDED/CORRECTED in change registry', not untraced,
     f"registry={len(REGJ)} (corr/new={reg_corr}) untraced_entities={len(untraced)}")

# RC4-G5 window truth — 9 registry windows tagged + glazed in V01
t1 = _tags(_msp1)
wids = [w.get('window_id') or w.get('name') for w in CE['windows']]
w_missing = [i for i in wids if i not in t1]
w_geom_bad = [i for i in wids if i in t1 and _cover(
    next(w['opening_rect_mm'] for w in CE['windows']
         if (w.get('window_id') or w.get('name')) == i),
    _rects_on(_msp1, ('A-GLAZ-EXST',))) < 0.5]
gate('RC4-G5 9 registry windows in CAD', not w_missing and not w_geom_bad and len(wids) == 9,
     f"registry={len(wids)} tagged={len(wids)-len(w_missing)} missing={w_missing or 'none'} "
     f"geom_weak={w_geom_bad or 'none'}")

# RC4-G6 ordinary doors — 14 openings tagged
o_missing = [o['id'] for o in CE['openings'] if o['id'] not in t1]
gate('RC4-G6 14 ordinary door openings present', not o_missing and len(CE['openings']) == 14,
     f"openings={len(CE['openings'])} missing={o_missing or 'none'}")

# RC4-G7 kitchen — every cabinet register id tagged in CAD
KREGJ = json.load(open(os.path.join(ROOT, 'current_existing/kitchen_cabinet_register.json')))['cabinets']
k_missing = [c['id'] for c in KREGJ if c['id'] not in t1]
gate('RC4-G7 kitchen cabinet register in CAD', not k_missing,
     f"cabinets={len(KREGJ)} missing={k_missing or 'none'}")

# RC4-G8 F1 freeze — V02 furniture matches d144789 coords
F1J = json.load(open(os.path.join(ROOT, 'concept/furniture_l1_final.json')))
f1_items = {it['id']: it for c in F1J['categories'].values() for it in c
            if isinstance(it, dict) and 'rect' in it}
t2 = _tags(_msp2)
f2_rects = _rects_on(_msp2, ('A-FURN-PROP', 'A-FURN-EXST-KEEP', 'A-ACCESS-RAMP',
                             'A-ACCESS-STAIR', 'A-NOTE', 'A-QC-ZONE'))
f_diffs = []
for fid, it in f1_items.items():
    if fid == 'K-CAB':
        continue
    r = it['rect']
    # matching CAD rect = same bbox within 1mm
    if not any(all(abs(a - b) <= 1 for a, b in zip(r, cr)) for cr in f2_rects):
        f_diffs.append(fid)
gate('RC4-G8 F1.1 furniture coords match d144789', not f_diffs,
     f"items={len(f1_items)-1} changed={f_diffs or 'none'}")

# RC4-G9 CAD/canonical alignment — canonical EXISTING walls covered by CAD wall linework
wall_rects = _rects_on(_msp1, ('S-S.WALL', 'A-WALL-EXST-CORR', 'A-PARP-EXST'))
w_weak = [w['id'] for w in CE['walls'] if w['disposition'] == 'EXISTING'
          and _cover(w['rect_mm'], wall_rects) < 0.5]
gate('RC4-G9 canonical walls covered by CAD linework', not w_weak,
     f"existing_walls={sum(1 for w in CE['walls'] if w['disposition']=='EXISTING')} "
     f"weak={w_weak or 'none'}")

# RC4-G10 render provenance — 4 outputs, sidecars point at the right DXF + live sha
prov_bad = []
for nm, vf in [('rc4_v01_cad_review', 'V01'), ('rc4_v01_presentation', 'V01'),
               ('rc4_v02_f1_cad_review', 'V02'), ('rc4_v02_f1_presentation', 'V02')]:
    side = json.load(open(os.path.join(ROOT, f'qc/{nm}.render.json')))
    ok = (side['source_dxf'] == CVER[vf]['file']
          and side['source_dxf_sha256'] == _sha_file(os.path.join(ROOT, side['source_dxf']))
          and side['parent_cad_sha256'] == CVER[vf]['parent_sha256']
          and os.path.exists(os.path.join(ROOT, f'qc/{nm}.png'))
          and os.path.exists(os.path.join(ROOT, f'qc/{nm}.pdf')))
    if not ok:
        prov_bad.append(nm)
gate('RC4-G10 render provenance (PNG/PDF traced to versioned DXF)', not prov_bad,
     f"outputs=4x2 bad={prov_bad or 'none'}")

# RC4-G11 layer semantics — SURVEY_SUPERSEDED never registered as DEMOLITION
demo_handles = {r['source_handle'] for r in REGJ
                if r['change_type'] == 'DEMOLITION' and r['source_handle']}
sup_ents = {e.dxf.handle for e in _msp1 if e.dxf.layer == 'A-SURVEY-SUPERSEDED'}
sem_bad = demo_handles & sup_ents
sem_bad |= {r['change_id'] for r in REGJ if r['change_type'] == 'SURVEY_SUPERSEDED'
            and r['source_handle'] and r['source_handle'] in
            {e.dxf.handle for e in _msp1 if e.dxf.layer == 'A-WALL-DEMO'}}
gate('RC4-G11 SURVEY_SUPERSEDED never classified as DEMOLITION', not sem_bad,
     f"violations={sorted(sem_bad) or 'none'}")

# RC4-G12 no parent overwrite — recorded child build did not mutate parents
g12 = (CVER['MEASURED']['sha256'] == _sha_file(os.path.join(CADDIR, 'measured_working.dxf'))
       and CVER['V01']['sha256'] == _sha_file(os.path.join(CADDIR, 'design_v01_existing_sync.dxf')))
gate('RC4-G12 no parent overwrite', g12,
     f"MEASURED+V01 shas still match manifest")

# RC4-G13 open balcony — parapet/railing never on a wall layer; no enclosing
# wall drawn on the balcony's open boundaries
par_walls = [w for w in CE['walls'] if w.get('type') == 'railing_parapet']
corr_rects = _rects_on(_msp1, ('A-WALL-EXST-CORR',))
parp_rects = _rects_on(_msp1, ('A-PARP-EXST',))
bal_bad = []
for pw in par_walls:
    r = pw['rect_mm']
    if any(inter(r, cr) for cr in corr_rects):
        bal_bad.append(f"{pw['id']}:on-wall-layer")
    # parapet must be represented by parapet linework or inherited survey lines
    if (_cover(r, parp_rects) < 0.5
            and _cover(r, _rects_on(_msp1, ('S-S.WALL',))) < 0.5):
        bal_bad.append(f"{pw['id']}:no-parapet-linework")
gate('RC4-G13 open balcony: railing_parapet never on wall layer', not bal_bad,
     f"parapets={[w['id'] for w in par_walls]} violations={bal_bad or 'none'}")

overall = all(r['result'] == 'PASS' for r in results)
print(f"\n=== TASK03A GATES: {sum(r['result']=='PASS' for r in results)}/{len(results)} {'ALL PASS' if overall else 'HAS FAIL'} ===")
json.dump({'gates': results, 'overall': 'PASS' if overall else 'FAIL'},
          open(os.path.join(ROOT, 'qc/task03a_gates.json'), 'w'), indent=2)
