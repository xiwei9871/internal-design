#!/usr/bin/env python3
"""MASTER DIRECT ARCH — FINAL 2D CLOSURE review images + machine gate.

Inputs: MASTER_ARCH_OBJECT_INVENTORY (linework), master_direct_arch_v1.json +
pascal_master_direct_scene.json (derived model), FINAL_WINDOW_REGISTER.
Outputs: MASTER_V2_GROUND_TRUTH_2D.png / PASCAL_MASTER_DIRECT_2D.png /
MASTER_VS_PASCAL_2D_OVERLAY_FINAL.png / FINAL_2D_GATE.json
"""
import json, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MplPolygon

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
OUTD = f'{BASE}/design/pascal_b1'
DX, DY = -1298172.0, 296458.0
XLIM, YLIM = (300, 17000), (-1500, 14700)   # same origin/north/scale/crop

inv = json.load(open(f'{OUTD}/wall_audit/MASTER_ARCH_OBJECT_INVENTORY.json'))['objects']
M = json.load(open(f'{OUTD}/master_direct_arch_v1.json'))
G = json.load(open(f'{OUTD}/pascal_master_direct_scene.json'))
WREG = json.load(open(f'{BASE}/design/s2_current_design_v1/FINAL_WINDOW_REGISTER_95ab90e.json'))['windows']
WDOC = json.load(open(f'{OUTD}/master_direct_arch_v1_walls.json'))

# ---------------- linework -------------------------------------------------
ARCH_LAYERS = {'S-S.WALL', 'F-DOOR', 'S-楼梯'}
def wall_segs():
    """every architectural linework object: (obj, layers, raw_pts)"""
    out = []
    for n, v in inv.items():
        if not set(v['dwg_layers'] or []) & ARCH_LAYERS or not v.get('edges'): continue
        for e in v['edges']:
            P = [(p[0]+DX, p[1]+DY) for p in e['pts']]
            out.append((n, v['dwg_layers'], P))
    return out
LINework = wall_segs()

def seg_atoms(P):
    """split polyline into atomic segments"""
    res = []
    for i in range(len(P)-1):
        (x0,y0),(x1,y1) = P[i],P[i+1]
        res.append((x0,y0,x1,y1))
    return res

# ---------------- pascal plan rects ----------------------------------------
def wrect(n):
    (x0,z0),(x1,z1) = n['start'], n['end']; t = n['thickness']*1000
    X0,X1 = sorted([x0*1000, x1*1000]); Y0,Y1 = sorted([-z0*1000,-z1*1000])
    if Y1-Y0 < 1: Y0 -= t/2; Y1 += t/2
    else: X0 -= t/2; X1 += t/2
    return [X0,Y0,X1,Y1]

truth_walls, helpers, screens, pier_nodes, slabs, doors, wins = [], [], [], [], [], [], []
for n in G['nodes'].values():
    md = n['metadata'] or {}
    if n['type'] == 'wall':
        if md.get('representation_mode') == 'GLAZED_SCREEN': screens.append(wrect(n))
        elif md.get('role') == 'PASCAL_OPENING_HOST_HELPER': helpers.append((wrect(n), md.get('canonical_id')))
        elif md.get('wall_class') == 'PIER': pier_nodes.append(wrect(n))
        else: truth_walls.append((wrect(n), md.get('canonical_id')))
    elif n['type'] == 'slab': slabs.append(n)
    elif n['type'] == 'door': doors.append(n)
    elif n['type'] == 'window': wins.append(n)

def in_rects(x, y, rects, pad=45):
    return any(r[0]-pad <= x <= r[2]+pad and r[1]-pad <= y <= r[3]+pad for r in rects)

ALL_COVER = [r for r,_ in truth_walls] + [r for r,_ in helpers] + \
            [r for r in pier_nodes] + screens

# classified detail (explained non-wall) lookup by (obj, orient, coord, span)
detail_keys = set()
for rc in WDOC.get('residual_classified', []):
    detail_keys.add((rc['obj'], rc['orient'], round(rc['coord']), round(rc['span'][0]), round(rc['span'][1])))
explained_objs = {r[0] for r in WDOC['residual'] if r[1] in ('NON_WALL_DETAIL','DIAGONAL_OR_DETAIL')}

def seg_state(x0,y0,x1,y1,obj,layers):
    """-> 'covered' | 'explained' | 'missing'"""
    if 'F-DOOR' in (layers or []):
        return 'explained'   # door swing/leaf symbols -> represented by door nodes
    # sample along segment
    n = max(2, int(math.hypot(x1-x0,y1-y0)/60))
    pts = [(x0+(x1-x0)*k/(n-1), y0+(y1-y0)*k/(n-1)) for k in range(n)]
    hit = sum(1 for x,y in pts if in_rects(x,y,ALL_COVER))/n
    if hit >= 0.6: return 'covered'
    # explained detail: short detail linework / classified / inside opening
    if obj in explained_objs or math.hypot(x1-x0,y1-y0) <= 300: return 'explained'
    o = 'H' if abs(y1-y0)<3 else ('V' if abs(x1-x0)<3 else 'D')
    c = round((y0+y1)/2) if o=='H' else round((x0+x1)/2)
    lo,hi = (round(min(x0,x1)),round(max(x0,x1))) if o=='H' else (round(min(y0,y1)),round(max(y0,y1)))
    if (obj,o,c,lo,hi) in detail_keys: return 'explained'
    mx,my = (x0+x1)/2,(y0+y1)/2
    for w in WREG:
        r = w['opening_rect_mm']
        if r[0]-260<=mx<=r[2]+260 and r[1]-260<=my<=r[3]+260: return 'explained'
    return 'missing'

# ---------------- labels ---------------------------------------------------
ROOMS = [('LIVING', 5000, 10200), ('KITCHEN', 3500, 1300), ('DINING', 4200, 3400),
         ('GUEST BEDROOM', 11200, 8600), ('OWNER BEDROOM', 14400, 2200),
         ('MOTHER BEDROOM', 10200, 2400), ('STUDY', 14600, 9000),
         ('NORTH BALCONY', 11400, 11500), ('BATH', 8900, 9300), ('BATH', 10300, 5500),
         ('ENSUITE', 14300, 5400), ('ENTRY', 2700, 7000)]
def label_rooms(ax):
    for t,x,y in ROOMS:
        ax.text(x, y, t, fontsize=8, color='#555', ha='center', va='center')
def label_openings(ax):
    for w in WREG:
        r = w['opening_rect_mm']
        ax.annotate(w['window_id'], ((r[0]+r[2])/2, (r[1]+r[3])/2),
                    fontsize=6.5, color='#8e24aa', ha='center',
                    xytext=(0, 7), textcoords='offset points')

def style(ax, title):
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM); ax.set_aspect('equal')
    ax.set_title(title); ax.grid(True, lw=.2, alpha=.4)

# ---------------- A: master ground truth 2D --------------------------------
fig, ax = plt.subplots(figsize=(14,14))
for n, layers, P in LINework:
    for x0,y0,x1,y1 in seg_atoms(P):
        ax.plot([x0,x1],[y0,y1],'k-',lw=.9)
label_rooms(ax); label_openings(ax)
style(ax,'MASTER_V2_GROUND_TRUTH_2D — S-S.WALL + F-DOOR + stairs linework')
plt.savefig(f'{OUTD}/MASTER_V2_GROUND_TRUTH_2D.png', dpi=140, bbox_inches='tight'); plt.close()

# ---------------- B: pascal 2D ---------------------------------------------
fig, ax = plt.subplots(figsize=(14,14))
for r,_ in truth_walls:
    ax.add_patch(Rectangle((r[0],r[1]),r[2]-r[0],r[3]-r[1],color='#455a64'))
for r,_ in helpers:
    ax.add_patch(Rectangle((r[0],r[1]),r[2]-r[0],r[3]-r[1],color='#ef6c00',alpha=.75))
for r in pier_nodes:
    ax.add_patch(Rectangle((r[0],r[1]),r[2]-r[0],r[3]-r[1],color='#455a64'))
for r in screens:
    ax.add_patch(Rectangle((r[0],r[1]),r[2]-r[0],r[3]-r[1],color='#26c6da'))
for s in slabs:
    ax.add_patch(MplPolygon([[p[0]*1000,-p[1]*1000] for p in s['polygon']],
                          closed=True,color='#b0bec5',alpha=.6))
for d in doors:
    w = G['nodes'][d['wallId']]
    (x0,z0),(x1,z1)=w['start'],w['end']
    L=math.hypot(x1-x0,z1-z0) or 1
    px,py = x0*1000+(x1-x0)/L*d['position'][0]*1000, -(z0*1000+(z1-z0)/L*d['position'][0]*1000)
    half = d['width']*500
    ux,uy = (x1-x0)/L*1000, (z1-z0)/L*1000
    ax.plot([px-ux*half/1000*1000, px+ux*half/1000*1000],[py-uy*half/1000*1000, py+uy*half/1000*1000],
            color='#ffffff', lw=3, solid_capstyle='butt')
    ax.plot([px-ux*half/1000*1000, px+ux*half/1000*1000],[py-uy*half/1000*1000, py+uy*half/1000*1000],
            color='#ffa726', lw=1.4)
for wn in wins:
    w = G['nodes'][wn['wallId']]
    (x0,z0),(x1,z1)=w['start'],w['end']
    L=math.hypot(x1-x0,z1-z0) or 1
    px,py = x0*1000+(x1-x0)/L*wn['position'][0]*1000, -(z0*1000+(z1-z0)/L*wn['position'][0]*1000)
    half = wn['width']*500
    ux,uy = (x1-x0)/L*1000, (z1-z0)/L*1000
    ax.plot([px-ux*half/1000*1000, px+ux*half/1000*1000],[py-uy*half/1000*1000, py+uy*half/1000*1000],
            color='#00acc1', lw=2.4)
label_rooms(ax); label_openings(ax)
style(ax,'PASCAL_MASTER_DIRECT_2D — walls | doors | windows | bays | helpers')
plt.savefig(f'{OUTD}/PASCAL_MASTER_DIRECT_2D.png', dpi=140, bbox_inches='tight'); plt.close()

# ---------------- C: overlay ------------------------------------------------
fig, ax = plt.subplots(figsize=(14,14))
for r,_ in truth_walls:
    ax.add_patch(Rectangle((r[0],r[1]),r[2]-r[0],r[3]-r[1],color='#66bb6a',alpha=.5))
for r,_ in helpers:
    ax.add_patch(Rectangle((r[0],r[1]),r[2]-r[0],r[3]-r[1],color='#ef6c00',alpha=.65))
for r in pier_nodes:
    ax.add_patch(Rectangle((r[0],r[1]),r[2]-r[0],r[3]-r[1],color='#66bb6a',alpha=.5))
for r in screens:
    ax.add_patch(Rectangle((r[0],r[1]),r[2]-r[0],r[3]-r[1],color='#26c6da',alpha=.7))
missing = []
for n, layers, P in LINework:
    for x0,y0,x1,y1 in seg_atoms(P):
        st = seg_state(x0,y0,x1,y1,n,layers)
        if st == 'missing': missing.append((x0,y0,x1,y1,n))
        ax.plot([x0,x1],[y0,y1], color={'covered':'#111111','explained':'#111111',
                                       'missing':'#d32f2f'}[st],
                lw=2.2 if st=='missing' else .9)
# purple: pascal ground-truth wall area with no linework nearby
purple = []
for r, cid in truth_walls:
    cx,cy = (r[0]+r[2])/2,(r[1]+r[3])/2
    ux,uy = (1,0) if r[2]-r[0]>=r[3]-r[1] else (0,1)
    L = max(r[2]-r[0],r[3]-r[1]); found=False
    for k in range(max(2,int(L/150))):
        px,py = cx+ux*(k*150-(max(2,int(L/150))-1)*75), cy+uy*(k*150-(max(2,int(L/150))-1)*75)
        for n,_l,P in LINework:
            for x0,y0,x1,y1 in seg_atoms(P):
                # point-to-seg dist
                dx,dy=x1-x0,y1-y0; L2=dx*dx+dy*dy
                if L2==0: continue
                t=max(0,min(1,((px-x0)*dx+(py-y0)*dy)/L2))
                if math.hypot(px-(x0+t*dx),py-(y0+t*dy))<160: found=True; break
            if found: break
        if found: break
    if not found:
        purple.append((r,cid))
        ax.add_patch(Rectangle((r[0],r[1]),r[2]-r[0],r[3]-r[1],
                               facecolor='#8e24aa',alpha=.5,edgecolor='none'))
label_rooms(ax); label_openings(ax)
style(ax,'MASTER_VS_PASCAL_2D_OVERLAY_FINAL — BLACK master / GREEN pascal / '
        'RED missing / PURPLE pascal-only / ORANGE host-helper / CYAN glazed screen')
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([],[],color='#111111',label='MASTER Ground Truth'),
                   Line2D([],[],color='#66bb6a',lw=6,label='Pascal wall'),
                   Line2D([],[],color='#d32f2f',label='MASTER missing in Pascal'),
                   Line2D([],[],color='#8e24aa',lw=6,label='Pascal-only wall'),
                   Line2D([],[],color='#ef6c00',lw=6,label='OPENING_HOST_HELPER'),
                   Line2D([],[],color='#26c6da',lw=6,label='glazed screen')],
          loc='lower right', fontsize=8)
plt.savefig(f'{OUTD}/MASTER_VS_PASCAL_2D_OVERLAY_FINAL.png', dpi=140, bbox_inches='tight'); plt.close()

# ---------------- gate ------------------------------------------------------
doors_out = 0
for d in doors:
    w = G['nodes'][d['wallId']]
    L=math.hypot(w['end'][0]-w['start'][0],w['end'][1]-w['start'][1]) or 1
    off=d['position'][0]*1000
    if off<0 or off>L*1000: doors_out+=1
ids={(n['metadata'] or {}).get('canonical_id') for n in G['nodes'].values()}
open9=['W-LIV-N','G-LIV-NBALC','G-GB-BALC','W-STUDY-NE','G-DIN-LIV','W-LBALC-S','W-KIT-S','W-SMB-S','W-MB-S']
gate = {
 'missing_ground_truth_wall': len(missing),
 'missing_detail': [f'{m[4]} ({m[0]:.0f},{m[1]:.0f})-({m[2]:.0f},{m[3]:.0f})' for m in missing],
 'unexplained_unpaired': sum(1 for r in WDOC.get('residual_classified',[]) if r['category']=='HUMAN_REVIEW_REQUIRED'),
 'verified_openings_present': sum(1 for x in open9 if x in ids),
 'doors_out_of_host': doors_out,
 'host_helper_count': len(helpers),
 'pascal_only_walls': [c for _,c in purple],
 'coordinate_frame': 'PASS (see COORDINATE_FRAME_SANITY.md)',
}
json.dump(gate, open(f'{OUTD}/FINAL_2D_GATE.json','w'), indent=1, ensure_ascii=False)
print(json.dumps(gate, indent=1, ensure_ascii=False))
