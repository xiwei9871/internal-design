#!/usr/bin/env python3
"""Visual fidelity overlays: canonical b1_model vs exported Pascal graph.
All in canonical mm frame (x east, y north-up). Pascal (x,z) m -> (x*1000, z*1000).
"""
import json, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mp

ROOT = '/Users/xiwei/interior_design/projects/c_type_home'
M = json.load(open(f'{ROOT}/design/b1_blockout/b1_model.json'))
S = json.load(open(f'{ROOT}/design/pascal_b1/pascal_full_scene_exported.json'))
nodes = list(S['nodes'].values()) if isinstance(S['nodes'], dict) else S['nodes']
MM = 1000.0

def rect_of(r): return (r[0], r[1], r[2]-r[0], r[3]-r[1])

def pwall_poly(n):
    sx, sz = n['start']; ex, ez = n['end']
    dx, dz = ex-sx, ez-sz; L = math.hypot(dx, dz) or 1
    nx, nz = -dz/L, dx/L; t = n['thickness']/2
    return [( (sx+nx*t)*MM, (sz+nz*t)*MM ), ((ex+nx*t)*MM, (ez+nz*t)*MM),
            ((ex-nx*t)*MM, (ez-nz*t)*MM), ((sx-nx*t)*MM, (sz-nz*t)*MM)]

wbid = {n['id']: n for n in nodes if n['type'] == 'wall'}

def popening_seg(n):
    w = wbid.get(n.get('wallId'))
    sx, sz = w['start']; ex, ez = w['end']
    dx, dz = ex-sx, ez-sz; L = math.hypot(dx, dz) or 1
    ux, uz = dx/L, dz/L
    local = n['position'][0]; half = n['width']/2
    cx, cz = sx+ux*local, sz+uz*local
    return ((cx-ux*half)*MM, (cz-uz*half)*MM, (cx+ux*half)*MM, (cz+uz*half)*MM)

def pitem_rect(n):
    a = n['metadata'].get('actual_project_size_m') or [0.4,0.4]
    return (n['position'][0]*MM - a[0]*MM/2, n['position'][2]*MM - a[1]*MM/2,
            a[0]*MM, a[1]*MM)

canon_walls = [w['rect'] for w in M['walls']+M['parapets']]
pw = [n for n in nodes if n['type']=='wall']
pdo = [n for n in nodes if n['type']=='door']
pwi = [n for n in nodes if n['type']=='window']
pit = [n for n in nodes if n['type']=='item']

def draw_canon_arch(ax, lw=0):
    for r in canon_walls:
        ax.add_patch(mp.Rectangle(rect_of(r)[:2], *rect_of(r)[2:], fc='#666', ec='#666', zorder=2))
    for o in M['openings']:
        ax.add_patch(mp.Rectangle(rect_of(o['rect'])[:2], *rect_of(o['rect'])[2:], fc='#2e7d32', alpha=.85, zorder=4))
    for w in M['windows']:
        ax.add_patch(mp.Rectangle(rect_of(w['rect'])[:2], *rect_of(w['rect'])[2:], fc='#1565c0', alpha=.85, zorder=4))
        if w.get('bay'):
            ax.add_patch(mp.Rectangle(rect_of(w['bay']['front'])[:2], *rect_of(w['bay']['front'])[2:], fc='none', ec='#1565c0', lw=1.2, zorder=4))

def draw_pascal_arch(ax):
    for n in pw:
        ax.add_patch(mp.Polygon(pwall_poly(n), closed=True, fc='none', ec='red', lw=1.2, zorder=3))
    for n in pdo:
        x0,y0,x1,y1 = popening_seg(n)
        ax.plot([x0,x1],[y0,y1], color='#ff2d78', lw=2.4, zorder=6)
    for n in pwi:
        x0,y0,x1,y1 = popening_seg(n)
        ax.plot([x0,x1],[y0,y1], color='#ff8f00', lw=2.4, zorder=6)

fig, axes = plt.subplots(1, 3, figsize=(30, 10))
for ax, t in zip(axes, ['CANONICAL walls/openings (mm, y-north up)',
                        'PASCAL exported walls/openings (x,z→mm)',
                        'OVERLAY: canon fill + pascal red outline']):
    ax.set_aspect('equal'); ax.set_title(t); ax.set_xlim(0,17000); ax.set_ylim(0,15000)
    ax.grid(alpha=.15)
draw_canon_arch(axes[0]); draw_pascal_arch(axes[1])
draw_canon_arch(axes[2]); draw_pascal_arch(axes[2])
plt.tight_layout(); plt.savefig(f'{ROOT}/design/pascal_b1/PASCAL_VS_MASTER_ARCH_OVERLAY.png', dpi=130)
print('arch overlay ok')

fig, axes = plt.subplots(1, 3, figsize=(30, 10))
for ax, t in zip(axes, ['CANONICAL furniture rects', 'PASCAL items (actual_project_size)',
                        'OVERLAY: canon fill + pascal red dashed']):
    ax.set_aspect('equal'); ax.set_title(t); ax.set_xlim(0,17000); ax.set_ylim(0,15000)
    ax.grid(alpha=.15)
    for r in canon_walls:
        ax.add_patch(mp.Rectangle(rect_of(r)[:2], *rect_of(r)[2:], fc='none', ec='#bbb', lw=.5, zorder=1))
for ax in (axes[0], axes[2]):
    for f in M['furniture']:
        ax.add_patch(mp.Rectangle(rect_of(f['rect'])[:2], *rect_of(f['rect'])[2:], fc='#90a4ae', alpha=.7, ec='#37474f', lw=.5, zorder=3))
for ax in (axes[1], axes[2]):
    for n in pit:
        ax.add_patch(mp.Rectangle(pitem_rect(n)[:2], *pitem_rect(n)[2:], fc='none', ec='red', lw=1.0, ls='--', zorder=4))
plt.tight_layout(); plt.savefig(f'{ROOT}/design/pascal_b1/PASCAL_VS_MASTER_FURNITURE_OVERLAY.png', dpi=130)
print('furniture overlay ok')

# numeric residual: each canonical wall rect centre covered by some pascal wall poly?
def seg_dist_to_rect(sx,sz,ex,ez,r):
    cx=(r[0]+r[2])/2; cy=(r[1]+r[3])/2
    dx,dz=ex-sx,ez-sz; L2=dx*dx+dz*dz or 1
    t=max(0,min(1,((cx-sx)*dx+(cy-sz)*dz)/L2))
    px,pz=sx+dx*t,sz+dz*t
    return math.hypot(cx-px,cy-pz)
worst=[]
for r in canon_walls:
    d=min(seg_dist_to_rect(*pwall_poly_seg(n) if False else (n['start'][0]*MM,n['start'][1]*MM,n['end'][0]*MM,n['end'][1]*MM), r) for n in pw)
    worst.append((round(d,1), r))
worst.sort(reverse=True)
print('worst wall centerline residual (mm):', worst[:8])
