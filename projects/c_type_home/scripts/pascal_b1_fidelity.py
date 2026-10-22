#!/usr/bin/env python3
"""PASCAL_B1 fidelity gate: Pascal full scene vs MASTER_V2 extraction (b1_model.json)."""
import json, math, collections

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
M = json.load(open(f'{BASE}/design/b1_blockout/b1_model.json'))
G = json.load(open(f'{BASE}/design/pascal_b1/pascal_full_scene.json'))
IDM = json.load(open(f'{BASE}/design/pascal_b1/pascal_full_id_map.json'))['map']
N = G['nodes']
MM = 1000.0

by_canon = collections.defaultdict(list)
for e in IDM:
    if e.get('canonical_id'):
        for cid in str(e['canonical_id']).split('+'):
            by_canon[cid].append(e)
by_fcstd = {e['fcstd']: e for e in IDM if e.get('fcstd')}

rep = {'furniture': [], 'openings': [], 'windows': [], 'walls_uncovered': [],
       'zones': [], 'missing': []}

# ---------- furniture ----------
for f in M['furniture'] + M['kitchen_cabinets']:
    src = f.get('obj') or f.get('id')
    e = by_fcstd.get(src) or (by_canon.get(src) or by_canon.get(f['label'] or '') or [None])[0]
    r = f['rect']
    scx, scz = (r[0]+r[2])/2, (r[1]+r[3])/2
    sw, sd = r[2]-r[0], r[3]-r[1]
    if not e:
        rep['missing'].append(('furniture', src)); continue
    n = N[e['pascal_id']]
    pcx, pcz = n['position'][0]*MM, n['position'][2]*MM
    drift = math.hypot(pcx-scx, pcz-scz)
    ams = n['metadata'].get('actual_project_size_m', [None, None])
    dw = abs((ams[0] or 0)*MM - sw); dd = abs((ams[1] or 0)*MM - sd)
    rep['furniture'].append({'src': src, 'label': f.get('label'), 'drift_mm': round(drift, 2),
        'dw_mm': round(dw, 2), 'dd_mm': round(dd, 2), 'zone_src': f.get('zone'),
        'zone_pascal': n['metadata'].get('room_zone'),
        'status': n['metadata'].get('review_status')})

def gcenter(n):
    """opening node -> (along_axis_center_mm, cross_axis_center_mm, horiz_wall)."""
    w = N[n['wallId']]
    dx, dz = w['end'][0]-w['start'][0], w['end'][1]-w['start'][1]
    L = math.hypot(dx, dz)
    t = n['position'][0] / L
    gx = (w['start'][0] + dx*t) * MM
    gz = (w['start'][1] + dz*t) * MM
    horiz = abs(dz) < abs(dx)
    return (gx, gz, horiz) if horiz else (gz, gx, horiz)

# ---------- openings (doors) ----------
for o in M['openings']:
    es = [e for e in by_canon.get(o['id'], [])
          if N[e['pascal_id']]['type'] == 'door']
    if not es:
        rep['missing'].append(('door', o['id'])); continue
    n = N[es[0]['pascal_id']]
    ga, gc, horiz = gcenter(n)
    r = o['rect']
    sa = (r[0]+r[2])/2 if horiz else (r[1]+r[3])/2   # src along-axis center
    sc = (r[1]+r[3])/2 if horiz else (r[0]+r[2])/2   # src cross-axis center
    span = (r[2]-r[0]) if horiz else (r[3]-r[1])     # along-wall extent
    rep['openings'].append({'id': o['id'], 'along_drift_mm': round(abs(ga-sa), 2),
        'cross_offset_mm': round(abs(gc-sc), 2),
        'dw_mm': round(abs(n['width']*MM - span), 2),
        'kind': n['metadata'].get('opening_class'), 'host': n['wallId']})

# ---------- windows ----------
for w in M['windows']:
    # G-* glass doors are represented by door nodes (opening kind wins)
    es = [e for e in by_canon.get(w['id'], [])
          if N[e['pascal_id']]['type'] in ('window', 'door')]
    if not es:
        rep['missing'].append(('window', w['id'])); continue
    n = N[es[0]['pascal_id']]
    ga, gc, horiz = gcenter(n)
    r = w['rect']
    sa = (r[0]+r[2])/2 if horiz else (r[1]+r[3])/2
    sc = (r[1]+r[3])/2 if horiz else (r[0]+r[2])/2
    span = (r[2]-r[0]) if horiz else (r[3]-r[1])
    rep['windows'].append({'id': w['id'], 'along_drift_mm': round(abs(ga-sa), 2),
        'cross_offset_mm': round(abs(gc-sc), 2),
        'dw_mm': round(abs(n['width']*MM - span), 2), 'host': n['wallId'],
        'status': es[0]['status']})

# ---------- walls: every source rect must be covered by a Pascal wall span ----------
pwalls = [n for n in N.values() if n['type'] == 'wall' and 'SYNTHESIZED' not in json.dumps(n['metadata'])]
for w in M['walls'] + M['parapets']:
    r = w['rect']
    horiz = (r[3]-r[1]) <= (r[2]-r[0])
    c = (r[1]+r[3])/2 if horiz else (r[0]+r[2])/2
    covered = False
    for p in pwalls:
        phoriz = abs(p['end'][1]-p['start'][1]) < abs(p['end'][0]-p['start'][0])
        if phoriz != horiz:
            continue
        pc = (p['start'][1]+p['end'][1])/2*MM if phoriz else (p['start'][0]+p['end'][0])/2*MM
        if abs(pc-c) > p['thickness']*MM/2 + 150:
            continue
        a, b = (p['start'][0], p['end'][0]) if phoriz else (p['start'][1], p['end'][1])
        a, b = min(a, b)*MM, max(a, b)*MM
        lo, hi = (r[0], r[2]) if horiz else (r[1], r[3])
        if a <= lo+1 and b >= hi-1:
            covered = True; break
    if not covered:
        rep['walls_uncovered'].append({'id': w['id'], 'rect': r})

# ---------- zones ----------
for s in M['spaces']:
    es = by_canon.get(s['id'])
    if not es:
        rep['missing'].append(('zone', s['id'])); continue
    n = N[es[0]['pascal_id']]
    sp = s['poly']; pp = [[x*MM, y*MM] for x, y in n['polygon']]
    ok = len(sp) == len(pp) and all(math.hypot(a[0]-b[0], a[1]-b[1]) < 1 for a, b in zip(sp, pp))
    rep['zones'].append({'id': s['id'], 'poly_match': ok,
                         'name': n.get('name')})

# ---------- summary ----------
def mx(rows): return max((x.get('along_drift_mm', x.get('drift_mm', 0)) for x in rows), default=0)
print('=== FIDELITY ===')
print('furniture:', len(rep['furniture']), 'max_center_drift_mm:', mx(rep['furniture']),
      'max_dw:', max((x['dw_mm'] for x in rep['furniture']), default=0),
      'max_dd:', max((x['dd_mm'] for x in rep['furniture']), default=0))
print('  zone reassignment:', sum(1 for x in rep['furniture']
      if x['zone_src'] and x['zone_pascal'] and x['zone_src'] != x['zone_pascal']))
print('openings:', len(rep['openings']), 'max_along_drift:', mx(rep['openings']),
      'max_cross_offset:', max((x['cross_offset_mm'] for x in rep['openings']), default=0),
      'max_dw:', max((x['dw_mm'] for x in rep['openings']), default=0))
print('windows:', len(rep['windows']), 'max_along_drift:', mx(rep['windows']),
      'max_cross_offset:', max((x['cross_offset_mm'] for x in rep['windows']), default=0),
      'max_dw:', max((x['dw_mm'] for x in rep['windows']), default=0))
print('walls uncovered:', len(rep['walls_uncovered']))
print('zones poly_match:', sum(1 for z in rep['zones'] if z['poly_match']), '/', len(rep['zones']))
print('missing:', rep['missing'])
json.dump(rep, open(f'{BASE}/design/pascal_b1/fidelity_raw.json', 'w'), ensure_ascii=False, indent=1)
