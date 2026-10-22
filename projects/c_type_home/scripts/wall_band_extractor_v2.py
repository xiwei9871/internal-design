#!/usr/bin/env python3
"""MASTER LINEWORK -> WALL BAND EXTRACTOR V2.

Authority: PRE_BLENDER_MASTER_V2 S-S.WALL linework decides where walls are.
Old wall register = semantic/provenance only.

Algorithm: collect every S-S.WALL edge as a segment (canonical mm),
pair parallel face lines (same orientation, overlapping projection,
separation 60..400mm) -> wall band = strip between faces.
Leftover linework must classify as DUPLICATE_FACE / NON_WALL_DETAIL /
UNPAIRED — nothing unexplained.
"""
import json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
DX, DY = -1298172.0, 296458.0
OUT = f'{BASE}/design/pascal_b1'
MIN_T, MAX_T = 55.0, 400.0
SNAP = 25.0

inv = json.load(open(f'{BASE}/design/pascal_b1/wall_audit/MASTER_ARCH_OBJECT_INVENTORY.json'))['objects']

segs = []   # (orient, coord, lo, hi, obj)
for n, v in inv.items():
    if 'S-S.WALL' not in (v['dwg_layers'] or []) or not v.get('edges'):
        continue
    for e in v['edges']:
        pts = e['pts']
        for i in range(len(pts)-1):
            x0, y0 = pts[i][0]+DX, pts[i][1]+DY
            x1, y1 = pts[i+1][0]+DX, pts[i+1][1]+DY
            if abs(y1-y0) < 3 and abs(x1-x0) >= 20:
                segs.append(['H', (y0+y1)/2, min(x0,x1), max(x0,x1), n])
            elif abs(x1-x0) < 3 and abs(y1-y0) >= 20:
                segs.append(['V', (x0+x1)/2, min(y0,y1), max(y0,y1), n])
            else:
                segs.append(['D', 0, 0, 0, n])   # diagonal/detail

# snap collinear duplicates: cluster segment coordinates
def snap_cluster(items, idx):
    items = sorted(items, key=lambda s: s[idx])
    groups = []
    for s in items:
        if groups and abs(s[idx]-groups[-1][0][idx]) <= SNAP:
            groups[-1].append(s)
        else:
            groups.append([s])
    return groups

def pair_orient(orient):
    lines = [s for s in segs if s[0] == orient]
    coords = snap_cluster(lines, 1)
    faces = []          # (coord, [ (lo,hi,obj) ])
    for g in coords:
        c = sum(s[1] for s in g)/len(g)
        faces.append({'c': c, 'runs': [(s[2], s[3], s[4]) for s in g], 'used': 0})
    bands = []
    for i, fa in enumerate(faces):
        for j, fb in enumerate(faces):
            if j <= i: continue
            d = fb['c']-fa['c']
            if not (MIN_T <= d <= MAX_T): continue
            # overlap of intervals between face runs (merge runs <40mm apart first)
            def merged(runs):
                ivs = sorted((l, h) for l, h, _ in runs)
                out = []
                for l, h in ivs:
                    if out and l - out[-1][1] < 60: out[-1][1] = max(out[-1][1], h)
                    else: out.append([l, h])
                return out
            A, B = merged(fa['runs']), merged(fb['runs'])
            for a in A:
                for b in B:
                    lo, hi = max(a[0], b[0]), min(a[1], b[1])
                    if hi-lo >= 250:
                        bands.append({'axis': 'y' if orient == 'H' else 'x',
                                      'lo_face': fa['c'], 'hi_face': fb['c'],
                                      'u0': lo, 'u1': hi})
                        fa['used'] += hi-lo; fb['used'] += hi-lo
    # merge collinear adjacent bands
    merged_bands = []
    for b in sorted(bands, key=lambda b: (round(b['lo_face']), round(b['hi_face']), b['u0'])):
        if merged_bands and abs(b['lo_face']-merged_bands[-1]['lo_face']) < 1 \
           and abs(b['hi_face']-merged_bands[-1]['hi_face']) < 1 \
           and b['u0']-merged_bands[-1]['u1'] < 80:
            merged_bands[-1]['u1'] = max(merged_bands[-1]['u1'], b['u1'])
        else:
            merged_bands.append(dict(b))
    return merged_bands, faces

hb, hfaces = pair_orient('H')
vb, vfaces = pair_orient('V')

# consolidate: same-axis bands whose 2D areas overlap -> union rect
def consolidate(bs):
    out = []
    for b in sorted(bs, key=lambda b: (b['axis'], b['lo_face'], b['u0'])):
        merged = False
        for o in out:
            if o['axis'] != b['axis']: continue
            lo = max(o['lo_face'], b['lo_face']); hi = min(o['hi_face'], b['hi_face'])
            u0 = max(o['u0'], b['u0']); u1 = min(o['u1'], b['u1'])
            if hi-lo > 20 and u1-u0 > 100:          # real 2D overlap
                o['lo_face'] = min(o['lo_face'], b['lo_face'])
                o['hi_face'] = max(o['hi_face'], b['hi_face'])
                o['u0'] = min(o['u0'], b['u0']); o['u1'] = max(o['u1'], b['u1'])
                merged = True; break
        if not merged: out.append(dict(b))
    return out
# iterate to fixpoint
bands = hb + vb
for _ in range(4):
    nb = consolidate(bands)
    if len(nb) == len(bands): break
    bands = nb

# coverage of face lines by bands (for residual classification)
def line_covered(orient, coord, lo, hi):
    n = max(2, int((hi-lo)/40))
    hit = 0
    for k in range(n):
        u = lo+(hi-lo)*k/(n-1)
        ok = False
        for b in bands:
            if (orient == 'H') == (b['axis'] == 'y'):
                if b['lo_face']-SNAP <= coord <= b['hi_face']+SNAP and b['u0']-60 <= u <= b['u1']+60:
                    ok = True; break
        hit += ok
    return hit/n

residual = []
for s in segs:
    if s[0] == 'D':
        residual.append((s[4], 'DIAGONAL_OR_DETAIL', 0)); continue
    f = line_covered(s[0], s[1], s[2], s[3])
    if f < 0.6:
        residual.append((s[4], 'UNPAIRED' if (s[3]-s[2]) > 300 else 'NON_WALL_DETAIL', round(f, 2)))

# ---- classify every UNPAIRED segment; nothing may remain unexplained --------
WREG = json.load(open(f'{BASE}/design/s2_current_design_v1/FINAL_WINDOW_REGISTER_95ab90e.json'))['windows']
def classify_unpaired(s):
    name, o, c, l0, l1 = s[4], s[0], s[1], s[2], s[3]
    mid = ((l0+l1)/2, c) if o == 'H' else (c, (l0+l1)/2)
    # pass 1: end-cap exactly on a band's u-end
    for b in bands:
        if (o == 'V') == (b['axis'] == 'y'):
            d_end = min(abs(c-b['u0']), abs(c-b['u1']))
            if d_end <= 150 and l0 >= b['lo_face']-60 and l1 <= b['hi_face']+60:
                return 'WALL_RETURN'
    # pass 2: pier/jamb cluster just beyond a band end
    for b in bands:
        if (o == 'V') == (b['axis'] == 'y'):
            d_end = min(abs(c-b['u0']), abs(c-b['u1']))
            if d_end <= 400 and l0 >= b['lo_face']-350 and l1 <= b['hi_face']+350:
                return 'PIER_JAMB_DETAIL'
    # pass 3: edge line of a verified opening (bay facade line, sill edge)
    for w in WREG:
        r = w['opening_rect_mm']
        if r[0]-260 <= mid[0] <= r[2]+260 and r[1]-260 <= mid[1] <= r[3]+260:
            return 'BAY_DETAIL' if w['type'] == 'BAY_WINDOW' else 'OPENING_EDGE_DETAIL'
    return 'HUMAN_REVIEW_REQUIRED'

residual_classified = []
for s in segs:
    if s[0] == 'D': continue
    f = line_covered(s[0], s[1], s[2], s[3])
    if f < 0.6 and (s[3]-s[2]) > 300:
        cat = classify_unpaired(s)
        residual_classified.append({'obj': s[4], 'orient': s[0], 'coord': round(s[1], 1),
                                    'span': [round(s[2], 1), round(s[3], 1)],
                                    'category': cat, 'coverage': round(f, 2)})

# junction piers: bbox of all short linework clustered at a band end that had
# PIER_JAMB_DETAIL linework (real masonry nib at T-junction)
piers = []
for rc in residual_classified:
    if rc['category'] != 'PIER_JAMB_DETAIL': continue
    o, c, (l0, l1) = rc['orient'], rc['coord'], rc['span']
    # pier rect = union bbox of this seg + every other UNCOVERED seg within 600mm
    if o == 'V': x0, y0, x1, y1 = c, l0, c, l1
    else:        x0, y0, x1, y1 = l0, c, l1, c
    for s2 in segs:
        o2, c2, a0, a1 = s2[0], s2[1], s2[2], s2[3]
        if o2 == 'D' or line_covered(o2, c2, a0, a1) >= 0.6: continue
        b0, c0, b1, c1 = (c2, a0, c2, a1) if o2 == 'V' else (a0, c2, a1, c2)
        if not (b1 < x0-600 or b0 > x1+600 or c1 < y0-600 or c0 > y1+600):
            x0, y0, x1, y1 = min(x0, b0), min(y0, c0), max(x1, b1), max(y1, c1)
    piers.append({'rect': [round(x0), round(y0), round(x1), round(y1)],
                  'evidence': rc['obj']})
# dedupe identical piers
seen = set(); piers = [p for p in piers if not (tuple(p['rect']) in seen or seen.add(tuple(p['rect'])))]

# wall band -> canonical rect + centerline
walls = []
for i, b in enumerate(bands):
    t = b['hi_face']-b['lo_face']; c = (b['lo_face']+b['hi_face'])/2
    if b['axis'] == 'y':
        rect = [b['u0'], b['lo_face'], b['u1'], b['hi_face']]
        cl = [[b['u0'], c], [b['u1'], c]]
    else:
        rect = [b['lo_face'], b['u0'], b['hi_face'], b['u1']]
        cl = [[c, b['u0']], [c, b['u1']]]
    walls.append({'id': f'WB-{i:03d}', 'axis': b['axis'], 'thickness': round(t),
                  'rect': [round(v, 1) for v in rect],
                  'centerline': [[round(x, 1), round(y, 1)] for x, y in cl]})

print('segments:', len(segs), 'diag:', sum(1 for s in segs if s[0] == 'D'))
print('bands:', len(walls), '(H', len(hb), 'V', len(vb), ')')
from collections import Counter
print('residual:', Counter(r[1] for r in residual))
print('residual_classified:', Counter(r['category'] for r in residual_classified))
for r in residual_classified:
    print('  ', r)
print('piers:', piers)
json.dump({'source': 'PRE_BLENDER_MASTER_V2 S-S.WALL linework (direct pairing)',
           'walls': walls, 'residual': residual,
           'residual_classified': residual_classified, 'piers': piers},
          open(f'{OUT}/master_direct_arch_v1_walls.json', 'w'), indent=1)

# ---- regression images -----------------------------------------------------
def draw_master(ax):
    for n, v in inv.items():
        if 'S-S.WALL' not in (v['dwg_layers'] or []) or not v.get('edges'): continue
        for e in v['edges']:
            xs = [p[0]+DX for p in e['pts']]; ys = [p[1]+DY for p in e['pts']]
            ax.plot(xs, ys, color='#111111', lw=1.0)

fig, ax = plt.subplots(figsize=(13, 13)); draw_master(ax)
ax.set_xlim(300, 17000); ax.set_ylim(14700, -1500); ax.set_aspect('equal')
ax.set_title('MASTER_RAW_WALLS — S-S.WALL linework only')
plt.savefig(f'{OUT}/MASTER_RAW_WALLS.png', dpi=140, bbox_inches='tight'); plt.close()

fig, ax = plt.subplots(figsize=(13, 13))
for w in walls:
    r = w['rect']
    ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], color='#388e3c', alpha=.6))
    ax.plot([w['centerline'][0][0], w['centerline'][1][0]],
            [w['centerline'][0][1], w['centerline'][1][1]], 'k-', lw=.5)
ax.set_xlim(300, 17000); ax.set_ylim(14700, -1500); ax.set_aspect('equal')
ax.set_title(f'EXTRACTED_WALL_BANDS — {len(walls)} bands from face pairing')
plt.savefig(f'{OUT}/EXTRACTED_WALL_BANDS.png', dpi=140, bbox_inches='tight'); plt.close()

fig, ax = plt.subplots(figsize=(13, 13))
for w in walls:
    r = w['rect']
    ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], color='#9ccc65', alpha=.5))
draw_master(ax)
ax.set_xlim(300, 17000); ax.set_ylim(14700, -1500); ax.set_aspect('equal')
ax.set_title('MASTER_VS_EXTRACTED_OVERLAY — black linework should sit inside green bands')
plt.savefig(f'{OUT}/MASTER_VS_EXTRACTED_OVERLAY.png', dpi=140, bbox_inches='tight'); plt.close()
print('images done')
