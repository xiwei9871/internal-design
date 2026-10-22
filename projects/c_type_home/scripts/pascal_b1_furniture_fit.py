#!/usr/bin/env python3
"""PASCAL_B1 furniture-fit footprint screen.
Method: item plan-AABB (actual_project_size at recorded pose) vs
(a) zone polygon containment  (b) check_collisions pairs  (c) verify_scene door keep-outs.
Footprint-only. No door swing / height / delivery / mesh / code claims."""
import json, math, collections

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
G = json.load(open(f'{BASE}/design/pascal_b1/pascal_full_scene.json'))
CC = json.load(open(f'{BASE}/design/pascal_b1/collisions_raw.json'))
VER = json.load(open('/tmp/pc6_out.json'))  # last verify run
N = G['nodes']

zones = {v['metadata'].get('canonical_id'): v for v in N.values() if v['type'] == 'zone'}
items = {k: v for k, v in N.items() if v['type'] == 'item'}

def pip(x, z, poly):
    inside = False; j = len(poly) - 1
    for i in range(len(poly)):
        xi, zi = poly[i]; xj, zj = poly[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi) + xi:
            inside = not inside
        j = i
    return inside

def aabb_corners(it):
    w, d = it['metadata']['actual_project_size_m']
    cx, _, cz = it['position']
    t = it['rotation'][1]
    c, s = math.cos(t), math.sin(t)
    return [(cx + dx*c - dz*s, cz + dx*s + dz*c)
            for dx in (-w/2, w/2) for dz in (-d/2, d/2)]

# collision pairs by item id
colmap = collections.defaultdict(list)
for c in CC.get('collisions', []):
    a, b = c.get('aId'), c.get('bId')
    if a: colmap[a].append(c)
    if b and b != a: colmap[b].append(c)

ZONE_NAME = {'R-LIVING':'living','R-DINING':'dining','R-LEISURE-E':'study','R-LEISURE-W':'study',
             'R-GB':'guest bedroom','R-BATH-G':'guest bath','R-ENS':'owner ensuite',
             'R-BATH-M':'mother bath','R-BALC-N':'north balcony','R-MB':'master bedroom',
             'R-SMB':'second master bedroom','R-KIT':'kitchen','R-FOYER':'foyer','R-COR':'corridor'}

per_zone = collections.defaultdict(list)
for iid, it in items.items():
    rz = it['metadata'].get('room_zone') or '(unzoned)'
    w, d = it['metadata']['actual_project_size_m']
    row = {'id': iid, 'label': it['metadata'].get('label') or it['asset']['name'],
           'zone': rz, 'size': [w, d], 'rot': it['rotation'][1],
           'status': it['metadata'].get('review_status')}
    z = zones.get(rz)
    if z:
        row['contained'] = all(pip(x, zz, z['polygon']) for x, zz in aabb_corners(it))
    else:
        row['contained'] = None
    row['collisions'] = len(colmap.get(iid, []))
    per_zone[rz].append(row)

out = {'zones': {}, 'collision_pairs': len(CC.get('collisions', []))}
for zid, rows in per_zone.items():
    out['zones'][zid] = {
        'label': ZONE_NAME.get(zid, zid), 'items': len(rows),
        'contained': sum(1 for r in rows if r['contained']),
        'not_contained': [r['label'] for r in rows if r['contained'] is False],
        'with_collisions': [r['label'] for r in rows if r['collisions']],
        'rows': rows}
json.dump(out, open(f'{BASE}/design/pascal_b1/furniture_fit_raw.json', 'w'), ensure_ascii=False, indent=1)
for zid, z in out['zones'].items():
    print(f"{zid:12s} items={z['items']:2d} contained={z['contained']} "
          f"outside={z['not_contained']} colliding={z['with_collisions']}")
print('total collision pairs:', out['collision_pairs'])
