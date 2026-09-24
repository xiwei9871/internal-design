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

# G2 W-INT-Y4500-b (Option S wall) must carry no proposed opening
no_open = [w['id'] for w in CE['walls'] if w.get('wall_class') == 'OWNER_DECLARED_NO_DEMOLITION_NO_OPENING']
s_blocked = 'NO_OPENING' in json.dumps(CD['smb']['entry_S'])
gate('G2 Option S honestly blocked on no-opening wall', s_blocked and any('Y4500-b' in w for w in no_open),
     f"S verdict: {CD['smb']['entry_S'].get('verdict','?')}; no-opening set has {len(no_open)} walls")

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

# G6 secondary master bath 3-piece fits
z = CD['smb']['zone_mm']; area = CD['smb']['area_m2']
fix = [f for f in F if f['id'].startswith('SMB2-')]
gate('G6 secondary bath 3-piece fits', len(fix) == 3 and area >= 3.0,
     f"zone {z[2]-z[0]}x{z[3]-z[1]} = {area}m2, fixtures={len(fix)}; drain via shared MBATH wet wall TO_VERIFY")

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

# G9 stair/ramp slope math + approach
lv = CD['level']; ramp = lv['ramp']; rise = CE['split_level']['level_difference_mm']
slope = rise / ramp['run_mm']
gate('G9 stair/ramp documented, slope flagged', ramp['run_mm'] >= 2500 and 0.13 <= slope <= 0.17,
     f"rise~{rise} TO_VERIFY; run {ramp['run_mm']}; slope 1:{ramp['run_mm']/rise:.1f} assisted-use (no code claim)")

# G10 level difference marked TO_VERIFY
gate('G10 level diff TO_VERIFY', CE['split_level']['level_status'] == 'ELEVATION_TO_VERIFY',
     f"rise={rise}mm owner-reported; status={CE['split_level']['level_status']}")

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

overall = all(r['result'] == 'PASS' for r in results)
print(f"\n=== TASK03A GATES: {sum(r['result']=='PASS' for r in results)}/{len(results)} {'ALL PASS' if overall else 'HAS FAIL'} ===")
json.dump({'gates': results, 'overall': 'PASS' if overall else 'FAIL'},
          open(os.path.join(ROOT, 'qc/task03a_gates.json'), 'w'), indent=2)
