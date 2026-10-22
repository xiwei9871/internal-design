#!/usr/bin/env python3
"""PASCAL ARCH GROUND-TRUTH VISUAL VALIDATION — read-only.
MASTER_V2 arch linework (b1_fcstd_objects.json, GROUND_TRUTH_ARCH class)
vs stored Pascal graph (pascal-arch-truth-v1) in identical canonical coords.
Outputs PNG overlays + opening table. No writes to any model.
"""
import json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
DX, DY = -1298172.0, 296458.0
OUT = f'{BASE}/design/pascal_b1'

fp = json.load(open(f'{BASE}/design/pascal_b1/wall_audit/ARCH_GROUND_TRUTH_FINGERPRINT.json'))['objects']
arch = []   # master linework rects in canonical mm
for n, v in fp.items():
    if v['class'] != 'GROUND_TRUTH_ARCH' or not v.get('bbox') or len(v['bbox']) < 6:
        continue
    b = v['bbox']
    r = [b[0]+DX, b[1]+DY, b[3]+DX, b[4]+DY]
    if r[0] > 17500 or r[2] < -2000 or r[1] > 16500 or r[3] < -2500: continue
    arch.append((n, r))

G = json.load(open('/tmp/at.json'))['graph'] if False else None
import urllib.request
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
G = json.loads(op.open('http://pascal.localhost:57071/api/scenes/pascal-arch-truth-v1', timeout=15).read())['graph']

def wrect(n):
    (x0, z0), (x1, z1) = n['start'], n['end']; t = n['thickness']*1000
    X0, X1 = sorted([x0*1000, x1*1000]); Y0, Y1 = sorted([-z0*1000, -z1*1000])
    if Y1-Y0 < 1: Y0 -= t/2; Y1 += t/2
    else: X0 -= t/2; X1 += t/2
    return [X0, Y0, X1, Y1]

pwalls = [(wrect(n), n) for n in G['nodes'].values() if n['type'] == 'wall']
pslabs = [n for n in G['nodes'].values() if n['type'] == 'slab']
pdoors = [n for n in G['nodes'].values() if n['type'] == 'door']
pwins  = [n for n in G['nodes'].values() if n['type'] == 'window']

def slabrect(s):
    xs = [p[0]*1000 for p in s['polygon']]; ys = [-p[1]*1000 for p in s['polygon']]
    return [min(xs), min(ys), max(xs), max(ys)]

def draw_master(ax, col='#111111', lw=0.5):
    for n, r in arch:
        ax.add_patch(Rectangle((r[0], r[1]), max(r[2]-r[0],1), max(r[3]-r[1],1),
                     fill=False, edgecolor=col, lw=lw, alpha=.7))
def draw_pascal(ax, alpha=.55):
    for r, n in pwalls:
        md = n.get('metadata') or {}
        c = '#8e24aa' if md.get('bay_assembly') else ('#26c6da' if md.get('representation_mode')=='GLAZED_SCREEN' else ('#ef6c00' if md.get('representation_mode') else '#2e7d32'))
        ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], color=c, alpha=alpha))
    for s in pslabs:
        r = slabrect(s)
        ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], color='#ffd54f', alpha=.5))

EXT = [(500, -1200), (17000, -1200), (17000, 14500), (500, 14500)]
def frame(ax, crop=None, title=''):
    if crop: ax.set_xlim(crop[0], crop[2]); ax.set_ylim(crop[3], crop[1])
    else: ax.set_xlim(EXT[0][0], EXT[2][0]); ax.set_ylim(EXT[2][1], EXT[0][1])
    ax.set_aspect('equal'); ax.set_title(title, fontsize=10)

fig, ax = plt.subplots(figsize=(13, 13)); draw_master(ax); frame(ax, title='MASTER_V2_ARCH_REFERENCE (arch-only linework, canonical mm)')
plt.savefig(f'{OUT}/MASTER_V2_ARCH_REFERENCE.png', dpi=130, bbox_inches='tight'); plt.close()

fig, ax = plt.subplots(figsize=(13, 13)); draw_pascal(ax); frame(ax, title='PASCAL_ARCH_RENDERED_2D — pascal-arch-truth-v1 stored graph')
plt.savefig(f'{OUT}/PASCAL_ARCH_RENDERED_2D.png', dpi=130, bbox_inches='tight'); plt.close()

fig, ax = plt.subplots(figsize=(13, 13)); draw_master(ax); draw_pascal(ax, .5)
frame(ax, title='MASTER(black linework) vs PASCAL(green walls / purple bays / cyan screen / yellow slabs)')
plt.savefig(f'{OUT}/MASTER_V2_VS_PASCAL_OVERLAY.png', dpi=130, bbox_inches='tight'); plt.close()

# ---- 9-opening table -------------------------------------------------------
WREG = {w['window_id']: w for w in json.load(open(f'{BASE}/design/s2_current_design_v1/FINAL_WINDOW_REGISTER_95ab90e.json'))['windows']}
idmap = {m['canonical_id']: m for m in json.load(open(f'{OUT}/pascal_arch_truth_id_map.json'))['map']}
rows = []
for oid, w in WREG.items():
    hits = [m for m in idmap.values() if m['canonical_id'] == oid]
    rows.append({'id': oid, 'type': w['type'], 'register_rect': w['opening_rect_mm'],
                 'span_mm': w['span_mm'], 'projection_mm': w.get('projection_mm'),
                 'pascal_nodes': [{'id': m['pascal_id'], 'cat': m['category'],
                                   'width_m': m.get('extra', {}).get('width_m')} for m in hits],
                 'present': bool(hits)})
json.dump(rows, open(f'{OUT}/wall_audit/OPENING_9_VALIDATION.json', 'w'), indent=1, ensure_ascii=False)
for r in rows: print(r['id'], r['type'], '->', [(p['id'], p['cat']) for p in r['pascal_nodes']])

# ---- bay crops -------------------------------------------------------------
CROPS = {'BAY_LIV_N':   [3200, 12500, 7600, 14400],
         'BAY_STUDY_NE':[12900, 10500, 16600, 12200],
         'BAY_SMB_S':   [8000, -1400, 11400, 1200],
         'BAY_MB_S':    [11600, -1400, 15300, 1200]}
for name, c in CROPS.items():
    fig, ax = plt.subplots(figsize=(10, 7))
    draw_master(ax); draw_pascal(ax, .55)
    frame(ax, crop=c, title=f'{name} — master linework vs pascal')
    plt.savefig(f'{OUT}/ARCH_TRUTH_{name}.png', dpi=140, bbox_inches='tight'); plt.close()
print('done')
