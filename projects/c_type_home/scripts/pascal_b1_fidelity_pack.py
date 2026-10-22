#!/usr/bin/env python3
"""Visual fidelity pack: canonical MASTER_V2 model vs exported Pascal graphs.

All drawing in canonical mm frame (x east, y north-up).
Pascal coords (x,z) in metres -> canonical (x*1000, -z*1000) after the
north-direction fix (canonical +y north == Pascal -z).

Outputs (design/pascal_b1/):
  MASTER_V2_2D_REFERENCE.png
  PASCAL_ARCH_2D.png
  PASCAL_VS_MASTER_ARCH_OVERLAY.png
  MASTER_V2_FURNITURE_PLAN.png
  PASCAL_FURNITURE_PLAN.png
  PASCAL_VS_MASTER_FURNITURE_OVERLAY.png
  PASCAL_BLOCKOUT_CLEAN_PLAN.png
  PASCAL_BLOCKOUT_CLEAN_AXON.png
  FIDELITY_NUMERIC.json   (residuals + 8-object metadata/collision/bbox table)
"""
import json, math, struct, os
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family'] = ['PingFang SC', 'DejaVu Sans']
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = '/Users/xiwei/interior_design/projects/c_type_home'
OUT = f'{ROOT}/design/pascal_b1'
ITEMS_DIR = os.path.expanduser('~/.pascal/runtime/1.0.3/apps/editor/public/items')
MM = 1000.0

M = json.load(open(f'{ROOT}/design/b1_blockout/b1_model.json'))

def load_scene(name):
    s = json.load(open(f'{OUT}/export_{name}.json'))
    n = s['nodes']
    return list(n.values()) if isinstance(n, dict) else n

ARCH_NODES = load_scene('pascal_b1_arch_only_v1')
BLK_NODES = load_scene('pascal_b1_blocks_v1')
FULL_NODES = load_scene('pascal_b1_full_v2')

def p2c(x, z):  # pascal m -> canonical mm
    return x * MM, -z * MM

def rect_of(r):
    return (r[0], r[1], r[2] - r[0], r[3] - r[1])

def pwall_poly(n):
    sx, sz = n['start']; ex, ez = n['end']
    dx, dz = ex - sx, ez - sz
    L = math.hypot(dx, dz) or 1
    nx, nz = -dz / L, dx / L
    t = n['thickness'] / 2
    return [p2c(sx + nx * t, sz + nz * t), p2c(ex + nx * t, ez + nz * t),
            p2c(ex - nx * t, ez - nz * t), p2c(sx - nx * t, sz - nz * t)]

def wall_index(nodes):
    return {n['id']: n for n in nodes if n['type'] == 'wall'}

def popening_seg(n, widx):
    w = widx.get(n.get('wallId'))
    sx, sz = w['start']; ex, ez = w['end']
    dx, dz = ex - sx, ez - sz
    L = math.hypot(dx, dz) or 1
    ux, uz = dx / L, dz / L
    local = n['position'][0]; half = n['width'] / 2
    cx, cz = sx + ux * local, sz + uz * local
    return (*p2c(cx - ux * half, cz - uz * half), *p2c(cx + ux * half, cz + uz * half))

def pitem_rect(n):
    a = n['metadata'].get('actual_project_size_m') or [abs(n['scale'][0]), abs(n['scale'][2])]
    cx, cy = p2c(n['position'][0], n['position'][2])
    w, d = a[0] * MM, a[1] * MM
    return (cx - w / 2, cy - d / 2, w, d)

def glb_bbox(path):
    """POSITION accessor min/max across all primitives in a GLB."""
    try:
        data = open(path, 'rb').read()
    except OSError:
        return None
    if data[:4] != b'glTF':
        return None
    jlen = struct.unpack('<I', data[12:16])[0]
    gltf = json.loads(data[20:20 + jlen])
    mins, maxs = [1e9] * 3, [-1e9] * 3
    for mesh in gltf.get('meshes', []):
        for prim in mesh.get('primitives', []):
            acc = gltf['accessors'][prim['attributes']['POSITION']]
            if 'min' in acc:
                mins = [min(a, b) for a, b in zip(mins, acc['min'])]
                maxs = [max(a, b) for a, b in zip(maxs, acc['max'])]
    return mins, maxs if mins[0] < 1e8 else None

canon_walls = [w['rect'] for w in M['walls'] + M['parapets']]

def draw_canon_arch(ax, fill=True):
    for r in canon_walls:
        ax.add_patch(mp.Rectangle(rect_of(r)[:2], *rect_of(r)[2:],
                     fc='#666' if fill else 'none', ec='#666', zorder=2))
    for o in M['openings']:
        ax.add_patch(mp.Rectangle(rect_of(o['rect'])[:2], *rect_of(o['rect'])[2:],
                     fc='#2e7d32', alpha=.85, zorder=4))
    for w in M['windows']:
        ax.add_patch(mp.Rectangle(rect_of(w['rect'])[:2], *rect_of(w['rect'])[2:],
                     fc='#1565c0', alpha=.85, zorder=4))
        if w.get('bay'):
            ax.add_patch(mp.Rectangle(rect_of(w['bay']['front'])[:2],
                         *rect_of(w['bay']['front'])[2:],
                         fc='none', ec='#1565c0', lw=1.2, zorder=4))

def draw_pascal_arch(ax, nodes):
    widx = wall_index(nodes)
    for n in nodes:
        if n['type'] == 'wall':
            ax.add_patch(mp.Polygon(pwall_poly(n), closed=True, fc='none',
                         ec='red', lw=1.2, zorder=3))
        elif n['type'] == 'door':
            x0, y0, x1, y1 = popening_seg(n, widx)
            ax.plot([x0, x1], [y0, y1], color='#ff2d78', lw=2.4, zorder=6)
        elif n['type'] == 'window':
            x0, y0, x1, y1 = popening_seg(n, widx)
            ax.plot([x0, x1], [y0, y1], color='#ff8f00', lw=2.4, zorder=6)

def frame(ax, title):
    ax.set_aspect('equal'); ax.set_title(title)
    ax.set_xlim(-500, 17500); ax.set_ylim(-500, 15000)
    ax.grid(alpha=.15)
    ax.annotate('N', xy=(500, 14200), fontsize=16, weight='bold')
    ax.annotate('', xy=(500, 14000), xytext=(500, 13200),
                arrowprops=dict(arrowstyle='->', lw=2))

def zone_labels(ax):
    for s in M['spaces']:
        poly = s.get('polygon')
        if not poly:
            continue
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        ax.text(sum(xs) / len(xs), sum(ys) / len(ys), s['id'].replace('R-', ''),
                ha='center', va='center', fontsize=7, color='#0d47a1', zorder=7)

# ---------- 1. MASTER_V2 2D reference ----------
fig, ax = plt.subplots(figsize=(14, 12))
frame(ax, 'MASTER_V2 / canonical b1_model (mm, north up)')
draw_canon_arch(ax)
zone_labels(ax)
plt.tight_layout(); plt.savefig(f'{OUT}/MASTER_V2_2D_REFERENCE.png', dpi=130); plt.close()
print('MASTER_V2_2D_REFERENCE ok')

# ---------- 2. PASCAL arch 2D ----------
fig, ax = plt.subplots(figsize=(14, 12))
frame(ax, 'PASCAL arch-only (exported, mapped to canonical mm)')
for n in ARCH_NODES:
    if n['type'] == 'wall':
        ax.add_patch(mp.Polygon(pwall_poly(n), closed=True, fc='#999', ec='#333', zorder=2))
widx = wall_index(ARCH_NODES)
for n in ARCH_NODES:
    if n['type'] == 'door':
        x0, y0, x1, y1 = popening_seg(n, widx)
        ax.plot([x0, x1], [y0, y1], color='#2e7d32', lw=3, zorder=4)
    elif n['type'] == 'window':
        x0, y0, x1, y1 = popening_seg(n, widx)
        ax.plot([x0, x1], [y0, y1], color='#1565c0', lw=3, zorder=4)
    elif n['type'] == 'zone':
        pts = [p2c(*p) for p in (n.get('polygon') or {}).get('points', [])] \
              if isinstance(n.get('polygon'), dict) else [p2c(*p) for p in (n.get('polygon') or [])]
        if pts:
            ax.add_patch(mp.Polygon(pts, closed=True, fc='none', ec='#90caf9',
                         lw=.8, ls=':', zorder=1))
            ax.text(sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts),
                    n.get('name', n['id']), ha='center', va='center', fontsize=7,
                    color='#0d47a1', zorder=7)
plt.tight_layout(); plt.savefig(f'{OUT}/PASCAL_ARCH_2D.png', dpi=130); plt.close()
print('PASCAL_ARCH_2D ok')

# ---------- 3. arch overlay ----------
fig, axes = plt.subplots(1, 3, figsize=(32, 11))
for ax, t in zip(axes, ['CANONICAL walls/openings', 'PASCAL exported arch-only',
                        'OVERLAY: canon fill + pascal red outline']):
    frame(ax, t)
draw_canon_arch(axes[0]); draw_pascal_arch(axes[1], ARCH_NODES)
draw_canon_arch(axes[2]); draw_pascal_arch(axes[2], ARCH_NODES)
plt.tight_layout(); plt.savefig(f'{OUT}/PASCAL_VS_MASTER_ARCH_OVERLAY.png', dpi=130); plt.close()
print('PASCAL_VS_MASTER_ARCH_OVERLAY ok')

# ---------- 4. MASTER furniture plan ----------
fig, ax = plt.subplots(figsize=(14, 12))
frame(ax, 'MASTER_V2 furniture (canonical rects)')
for r in canon_walls:
    ax.add_patch(mp.Rectangle(rect_of(r)[:2], *rect_of(r)[2:], fc='none', ec='#bbb', lw=.5, zorder=1))
for f in M['furniture']:
    x, y, w, d = rect_of(f['rect'])
    ax.add_patch(mp.Rectangle((x, y), w, d, fc='#90a4ae', alpha=.7, ec='#37474f', lw=.5, zorder=3))
    ax.text(x + w / 2, y + d / 2, f['label'], ha='center', va='center', fontsize=5, rotation=30, zorder=4)
plt.tight_layout(); plt.savefig(f'{OUT}/MASTER_V2_FURNITURE_PLAN.png', dpi=130); plt.close()
print('MASTER_V2_FURNITURE_PLAN ok')

# ---------- 5. PASCAL furniture plan (blockout scene) ----------
fig, ax = plt.subplots(figsize=(14, 12))
frame(ax, 'PASCAL furniture blockout (exported, actual sizes)')
for r in canon_walls:
    ax.add_patch(mp.Rectangle(rect_of(r)[:2], *rect_of(r)[2:], fc='none', ec='#bbb', lw=.5, zorder=1))
items = [n for n in BLK_NODES if n['type'] == 'item']
for n in items:
    x, y, w, d = pitem_rect(n)
    ax.add_patch(mp.Rectangle((x, y), w, d, fc='#ffe0a3', alpha=.8, ec='#8d6e00', lw=.6, zorder=3))
    lab = n['metadata'].get('label') or n['metadata'].get('canonical_id') or n.get('asset', {}).get('name', n['id'])
    ax.text(x + w / 2, y + d / 2, lab, ha='center', va='center', fontsize=5, rotation=30, zorder=4)
plt.tight_layout(); plt.savefig(f'{OUT}/PASCAL_FURNITURE_PLAN.png', dpi=130); plt.close()
print('PASCAL_FURNITURE_PLAN ok')

# ---------- 6. furniture overlay ----------
fig, axes = plt.subplots(1, 3, figsize=(32, 11))
for ax, t in zip(axes, ['CANONICAL furniture rects', 'PASCAL blockout items',
                        'OVERLAY: canon fill + pascal red dashed']):
    frame(ax, t)
    for r in canon_walls:
        ax.add_patch(mp.Rectangle(rect_of(r)[:2], *rect_of(r)[2:], fc='none', ec='#bbb', lw=.5, zorder=1))
for ax in (axes[0], axes[2]):
    for f in M['furniture']:
        x, y, w, d = rect_of(f['rect'])
        ax.add_patch(mp.Rectangle((x, y), w, d, fc='#90a4ae', alpha=.7, ec='#37474f', lw=.5, zorder=3))
for ax in (axes[1], axes[2]):
    for n in items:
        x, y, w, d = pitem_rect(n)
        ax.add_patch(mp.Rectangle((x, y), w, d, fc='none', ec='red', lw=1.0, ls='--', zorder=4))
plt.tight_layout(); plt.savefig(f'{OUT}/PASCAL_VS_MASTER_FURNITURE_OVERLAY.png', dpi=130); plt.close()
print('PASCAL_VS_MASTER_FURNITURE_OVERLAY ok')

# ---------- 7. clean blockout plan ----------
fig, ax = plt.subplots(figsize=(14, 12))
frame(ax, 'PASCAL B1 clean blockout plan — walls + furniture boxes (north up)')
for n in BLK_NODES:
    if n['type'] == 'wall':
        ax.add_patch(mp.Polygon(pwall_poly(n), closed=True, fc='#555', ec='#222', zorder=2))
widx = wall_index(BLK_NODES)
for n in BLK_NODES:
    if n['type'] == 'door':
        x0, y0, x1, y1 = popening_seg(n, widx)
        ax.plot([x0, x1], [y0, y1], color='#2e7d32', lw=3, zorder=4)
    elif n['type'] == 'window':
        x0, y0, x1, y1 = popening_seg(n, widx)
        ax.plot([x0, x1], [y0, y1], color='#1565c0', lw=3, zorder=4)
for n in items:
    x, y, w, d = pitem_rect(n)
    ax.add_patch(mp.Rectangle((x, y), w, d, fc='#ffe0a3', alpha=.85, ec='#8d6e00', lw=.6, zorder=3))
zone_labels(ax)
plt.tight_layout(); plt.savefig(f'{OUT}/PASCAL_BLOCKOUT_CLEAN_PLAN.png', dpi=130); plt.close()
print('PASCAL_BLOCKOUT_CLEAN_PLAN ok')

# ---------- 8. clean blockout axon ----------
fig = plt.figure(figsize=(16, 13))
ax = fig.add_subplot(111, projection='3d')
WH = 2600  # wall height mm display
verts = []
for n in BLK_NODES:
    if n['type'] != 'wall':
        continue
    p = pwall_poly(n)
    for i in range(4):
        x0, y0 = p[i]; x1, y1 = p[(i + 1) % 4]
        verts.append([(x0, y0, 0), (x1, y1, 0), (x1, y1, WH), (x0, y0, WH)])
for n in items:
    x, y, w, d = pitem_rect(n)
    h = abs(n['scale'][1]) * MM
    verts.append([(x, y, 0), (x + w, y, 0), (x + w, y, h), (x, y, h)])
    verts.append([(x + w, y + d, 0), (x, y + d, 0), (x, y + d, h), (x + w, y + d, h)])
    verts.append([(x, y + d, 0), (x, y, 0), (x, y, h), (x, y + d, h)])
    verts.append([(x + w, y, 0), (x + w, y + d, 0), (x + w, y + d, h), (x + w, y, h)])
    verts.append([(x, y, h), (x + w, y, h), (x + w, y + d, h), (x, y + d, h)])
pc = Poly3DCollection(verts, alpha=.9)
cols = []
i = 0
nw = sum(1 for n in BLK_NODES if n['type'] == 'wall')
for n in BLK_NODES:
    if n['type'] == 'wall':
        cols += ['#888'] * 4
for n in items:
    cols += ['#d9b36a'] * 5
pc.set_facecolor(cols[:len(verts)])
pc.set_edgecolor('#333'); pc.set_linewidth(.2)
ax.add_collection3d(pc)
ax.set_xlim(0, 17000); ax.set_ylim(0, 15000); ax.set_zlim(0, 3000)
ax.set_box_aspect((17, 15, 3))
ax.view_init(elev=38, azim=-62)
ax.set_title('PASCAL B1 clean blockout axon — walls + furniture boxes')
ax.set_axis_off()
plt.tight_layout(); plt.savefig(f'{OUT}/PASCAL_BLOCKOUT_CLEAN_AXON.png', dpi=130); plt.close()
print('PASCAL_BLOCKOUT_CLEAN_AXON ok')

# ---------- numeric checks ----------
report = {}

def seg_dist_to_rect(sx, sy, ex, ey, r):
    cx = (r[0] + r[2]) / 2; cy = (r[1] + r[3]) / 2
    dx, dy = ex - sx, ey - sy
    L2 = dx * dx + dy * dy or 1
    t = max(0, min(1, ((cx - sx) * dx + (cy - sy) * dy) / L2))
    return math.hypot(cx - (sx + dx * t), cy - (sy + dy * t))

pw = [n for n in ARCH_NODES if n['type'] == 'wall']
worst = []
for r in canon_walls:
    d = min(seg_dist_to_rect(*p2c(n['start'][0], n['start'][1]), *p2c(n['end'][0], n['end'][1]), r) for n in pw)
    worst.append(round(d, 1))
report['arch_wall_center_residual_mm_max'] = max(worst)

# furniture centre residual: match by canonical_id
by_cid = {}
for n in items:
    cid = n['metadata'].get('label') or n['metadata'].get('canonical_id')
    by_cid.setdefault(cid, []).append(n)
fres = []
for f in M['furniture']:
    cand = by_cid.get(f['label'])
    if not cand:
        fres.append((f['label'], None))
        continue
    x0, y0, x1, y1 = f['rect']
    cxc, cyc = (x0 + x1) / 2, (y0 + y1) / 2
    d = min(math.hypot(p2c(n['position'][0], n['position'][2])[0] - cxc,
                       p2c(n['position'][0], n['position'][2])[1] - cyc) for n in cand)
    fres.append((f['label'], round(d, 1)))
report['furniture_center_residual_mm'] = {k: v for k, v in fres}
report['furniture_center_residual_mm_max'] = max(v for _, v in fres if v is not None)

# 8-object comparison: canonical footprint vs metadata vs rendered bbox
TARGETS = {
    'SOFA_3S': '三人位', 'SOFA_2S': '双人位', 'CHAISE': '贵妃椅',
    'DINING_TABLE': '餐桌', 'GUEST_BED': '次卧小床1.2', 'OWNER_BED': '主卧床',
    'MOTHER_BED': '次主卧床', 'STUDY_WORKSTATION': '窄书桌',
}
full_items = {}
for n in FULL_NODES:
    if n['type'] == 'item':
        full_items.setdefault(n['metadata'].get('label') or n['metadata'].get('canonical_id'), n)
blk_items = {}
for n in items:
    blk_items.setdefault(n['metadata'].get('label') or n['metadata'].get('canonical_id'), n)

rows = []
for eng, lab in TARGETS.items():
    f = next((f for f in M['furniture'] if f['label'] == lab), None)
    if not f:
        continue
    cw = f['rect'][2] - f['rect'][0]; cd = f['rect'][3] - f['rect'][1]
    row = {'id': eng, 'label': lab,
           'canonical_footprint_mm': [round(cw), round(cd)]}
    bn = blk_items.get(lab)
    if bn:
        a = bn['metadata'].get('actual_project_size_m')
        row['metadata_mm'] = [round(a[0] * MM), round(a[1] * MM)] if a else None
        row['rendered_bbox_mm_blockout'] = [round(abs(bn['scale'][0]) * MM),
                                            round(abs(bn['scale'][2]) * MM)]
    fn = full_items.get(lab)
    if fn and fn.get('asset'):
        bb = glb_bbox(f"{ITEMS_DIR}/{fn['asset']['id']}/model.glb")
        if bb:
            mins, maxs = bb
            sx, _, sz = fn['scale']
            row['rendered_bbox_mm_catalog'] = [
                round((maxs[0] - mins[0]) * abs(sx) * MM),
                round((maxs[2] - mins[2]) * abs(sz) * MM)]
            row['catalog_asset'] = fn['asset']['id']
    rows.append(row)
report['eight_object_bbox'] = rows

json.dump(report, open(f'{OUT}/FIDELITY_NUMERIC.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(report, ensure_ascii=False, indent=1))
