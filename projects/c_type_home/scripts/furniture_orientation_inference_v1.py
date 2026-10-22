#!/usr/bin/env python3
"""
FURNITURE_ORIENTATION_INFERENCE_V1

Infer furniture facing from spatial semantics — no manual FreeCAD tagging.

INPUTS (read-only):
  design/b1_blockout/b1_model.json                       furniture rects (CAD mm, x east / y north)
  design/b1_blockout/furniture_3d_dimension_register_v01.json   semantic types + dims
  design/pascal_b1/KITCHEN_CABINET_3D_REGISTER_V01.json         PDF-authoritative kitchen cabinets
  design/pascal_b1/master_direct_arch_v1_walls.json             extracted wall bands (CAD mm)

CONVENTION:
  geometry_axis_deg   = long-axis angle, degrees CCW from +X, range [0,180)
  semantic_facing_deg = direction the FRONT faces, degrees CCW from +X (east),
                        0=E 90=N 180=W 270=S; None when NOT_APPLICABLE
"""

import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'design', 'b1_blockout')
P = os.path.join(ROOT, 'design', 'pascal_b1')

MODEL = json.load(open(os.path.join(D, 'b1_model.json')))
REG = json.load(open(os.path.join(D, 'furniture_3d_dimension_register_v01.json')))
KCAB = json.load(open(os.path.join(P, 'KITCHEN_CABINET_3D_REGISTER_V01.json')))
WALLS = json.load(open(os.path.join(P, 'master_direct_arch_v1_walls.json')))

WALL_RECTS = [w['rect'] for w in WALLS['walls']]
# openings also act as backing boundary? no — only physical wall bands.
SPACES = {s['id']: s for s in MODEL['spaces']}
REG_BY_OBJ = {i['source_name']: i for i in REG['items']}
FURN = MODEL['furniture']

# ---------- geometry helpers ----------
def ctr(r): return ((r[0]+r[2])/2, (r[1]+r[3])/2)
FACING_SIDE = {0.0:'E',90.0:'N',180.0:'W',270.0:'S'}
def walled_sides(item, tol=400):
    """side->min signed gap to a wall on that side (negative = wall overlaps the edge).
    An edge embedded in / flush against a wall counts as walled."""
    ix1,iy1,ix2,iy2=item; sides={}
    for wx1,wy1,wx2,wy2 in WALL_RECTS:
        ov_y=min(iy2,wy2)-max(iy1,wy1); ov_x=min(ix2,wx2)-max(ix1,wx1)
        if ov_y>0.2*(iy2-iy1):
            for side,g in (('E',wx1-ix2),('W',ix1-wx2)):
                if -tol<g<tol and (side not in sides or g<sides[side]): sides[side]=g
        if ov_x>0.2*(ix2-ix1):
            for side,g in (('N',wy1-iy2),('S',iy1-wy2)):
                if -tol<g<tol and (side not in sides or g<sides[side]): sides[side]=g
    return sides

def interior_facing(item, zone, tol=400):
    """front = free side (no wall within tol) closest to room-center direction."""
    ws=walled_sides(item,tol)
    c=room_center(zone); ix,iy=ctr(item)
    pref=snap4((c[0]-ix,c[1]-iy)) if c else None
    FREE_FACE = {'E':0.0,'N':90.0,'W':180.0,'S':270.0}
    free=[FREE_FACE[s] for s in ('E','N','W','S') if s not in ws]
    if not free: return None,len(ws),'all sides walled'
    if pref is not None and pref in free:
        return pref,len(ws),'free side matches room-center'
    if pref is None:
        return free[0],len(ws),'no room center'
    dang=lambda a,b:min((a-b)%360,(b-a)%360)
    best=min(free,key=lambda f:dang(f,pref))
    return best,len(ws),f'nearest free side to room-center (pref={pref})'
def axis_deg(r):
    dx,dy = r[2]-r[0], r[3]-r[1]
    if abs(dx-dy)<1: return None  # square: axis undefined
    return 0.0 if dx>=dy else 90.0
def snap4(v):
    """direction of vector v snapped to nearest of E/N/W/S, returns deg"""
    deg=math.degrees(math.atan2(v[1],v[0]))%360
    return round(deg/90)*90%360
def dir_from_to(a,b):
    ax,ay=ctr(a); bx,by=ctr(b); return snap4((bx-ax,by-ay))

def room_center(zone_id):
    s=SPACES.get(zone_id)
    if not s: return None
    xs=[p[0] for p in s['poly']]; ys=[p[1] for p in s['poly']]
    return ((min(xs)+max(xs))/2,(min(ys)+max(ys))/2)

def in_zone(zone_id):
    return [f for f in FURN if f.get('zone')==zone_id]

def find_type(zone_id, types, exclude_obj=None):
    out=[]
    for f in in_zone(zone_id):
        r=REG_BY_OBJ.get(f['obj'])
        if r and r['semantic_type'] in types and f['obj']!=exclude_obj: out.append(f)
    return out

# ---------- rule engine ----------
WALL_BACKED = {'TV_CABINET','MEDIA_CABINET','WARDROBE','GUEST_WARDROBE','CABINET','SHOE_CABINET',
               'TALL_BOOKCASE','LOW_BOOKCASE','FREEZER','STACKED_WASHER_DRYER','3KG_WASHER',
               'PRINTER','NAS','VANITY','WC'}
NA = {'DINING_TABLE','COFFEE_TABLE','SIDE_TABLE','STOOL','BENCH'}

def infer(f):
    r=REG_BY_OBJ.get(f['obj']); st=r['semantic_type']; zone=f.get('zone')
    rect=f['rect']; ax=axis_deg(rect)
    if st in NA:
        return dict(axis=ax,facing=None,src='RULE:not_applicable',conf='HIGH',
                    reason=f'{st}: facing semantically N/A (axis only)')
    if st in WALL_BACKED:
        deg,nw,detail=interior_facing(rect,zone)
        if deg is None:
            return dict(axis=ax,facing=None,src='NONE',conf='LOW',
                        reason=f'{st}: all sides walled — REVIEW')
        conf='HIGH' if nw==1 else 'MEDIUM'
        return dict(axis=ax,facing=deg,src=f'interior_facing({nw} walled sides)',conf=conf,
                    reason=f'{st}: back against wall, front toward room ({detail})')
    if st=='BED_BASE':
        hb=find_type(zone,{'HEADBOARD'},f['obj'])
        if hb:
            h=hb[0]; deg=dir_from_to(h['rect'],rect)
            return dict(axis=ax,facing=deg,src='headboard->bed',conf='HIGH',
                        reason='BED: facing = headboard→foot direction (headboard found in zone)')
        deg,nw,detail=interior_facing(rect,zone)
        if deg is not None:
            return dict(axis=ax,facing=deg,src='interior_facing(no headboard)',conf='MEDIUM',
                        reason='BED: no headboard object; fell back to wall adjacency — verify')
        return dict(axis=ax,facing=None,src='NONE',conf='LOW',reason='BED: no headboard, no wall — REVIEW')
    if st=='HEADBOARD':
        beds=find_type(zone,{'BED_BASE'},f['obj'])
        if beds:
            deg=dir_from_to(rect,beds[0]['rect'])
            return dict(axis=ax,facing=deg,src='headboard->bed',conf='HIGH',
                        reason='HEADBOARD panel: front faces the bed')
        deg,nw,detail=interior_facing(rect,zone)
        if deg is not None: return dict(axis=ax,facing=deg,src='interior_facing',conf='MEDIUM',reason='HEADBOARD: no bed link — faces off wall')
        return dict(axis=ax,facing=None,src='NONE',conf='LOW',reason='HEADBOARD: no bed, no wall — REVIEW')
    if st in ('SOFA_3S','SOFA_2S','CHAISE'):
        tgt=find_type(zone,{'COFFEE_TABLE'},f['obj']) or find_type(zone,{'MEDIA_CABINET','TV_CABINET'},f['obj'])
        c=room_center(zone)
        if tgt:
            deg=dir_from_to(rect,tgt[0]['rect'])
            # constrain to axis-perpendicular when sofa is elongated
            if ax is not None:
                perp=(ax+90)%180
                d_perp = perp if abs(((deg-(perp))%360))<90 else (perp+180)%360
                deg=d_perp
            return dict(axis=ax,facing=deg,src='sofa->coffee_table/tv',conf='HIGH',
                        reason='SOFA: faces coffee table / media wall')
        if c:
            deg=snap4((c[0]-ctr(rect)[0],c[1]-ctr(rect)[1]))
            return dict(axis=ax,facing=deg,src='sofa->room_center',conf='MEDIUM',reason='SOFA: no coffee table/TV — faces room center')
        return dict(axis=ax,facing=None,src='NONE',conf='LOW',reason='SOFA: no anchor — REVIEW')
    if st in ('NARROW_DESK','STUDY_WORKSTATION'):
        seat=find_type(zone,{'STUDY_ARMCHAIR','STOOL','BENCH'},f['obj'])
        if seat:
            deg=dir_from_to(rect,seat[0]['rect'])
            return dict(axis=ax,facing=deg,src='desk->seat',conf='MEDIUM',
                        reason='DESK: front faces the seat side (chair/stool found)')
        deg,nw,detail=interior_facing(rect,zone)
        if deg is not None: return dict(axis=ax,facing=deg,src='interior_facing',conf='MEDIUM',reason='DESK: no seat found; faces off wall — verify')
        return dict(axis=ax,facing=None,src='NONE',conf='LOW',reason='DESK: no seat, no wall — REVIEW')
    if st=='DINING_CHAIR':
        tbl=find_type(zone,{'DINING_TABLE'},f['obj'])
        if tbl:
            deg=dir_from_to(rect,tbl[0]['rect'])
            return dict(axis=ax,facing=deg,src='chair->table',conf='MEDIUM',
                        reason='DINING_CHAIR: faces table center')
        return dict(axis=ax,facing=None,src='NONE',conf='LOW',reason='CHAIR: no table — REVIEW')
    if st=='SHOWER_ZONE':
        c=room_center(zone)
        if c:
            deg=snap4((c[0]-ctr(rect)[0],c[1]-ctr(rect)[1]))
            return dict(axis=ax,facing=deg,src='shower->room',conf='MEDIUM',
                        reason='SHOWER_ZONE glass screen: opens toward bathroom interior')
        return dict(axis=ax,facing=None,src='NONE',conf='LOW',reason='SHOWER: no room center — REVIEW')
    return dict(axis=ax,facing=None,src='NONE',conf='LOW',reason=f'{st}: no rule — REVIEW')

# kitchen cabinets from PDF register — front = free side facing kitchen interior
def infer_cabinet(c):
    rect=c['rect']; ax=axis_deg(rect)
    deg,nw,detail=interior_facing(rect,'R-KITCHEN')
    if deg is None:
        return dict(axis=ax,facing=None,src='NONE',conf='LOW',reason='cabinet: all sides walled — REVIEW')
    conf='HIGH' if c['confidence']=='HIGH' and nw==1 else 'MEDIUM'
    return dict(axis=ax,facing=deg,src=f'interior_facing({nw} walled)+pdf',conf=conf,
                reason=f"{c['type']}: front toward kitchen interior ({detail}; PDF {c['cabinet_id']})")

# ---------- run ----------
out_items=[]
for f in FURN:
    r=REG_BY_OBJ.get(f['obj'])
    if not r: continue
    res=infer(f)
    out_items.append({
        'source_name':f['obj'],'label':f.get('label'),'semantic_type':r['semantic_type'],
        'room':r['room'],'zone':f.get('zone'),'rect':f['rect'],'level':r.get('level'),
        'geometry_axis_deg':res['axis'],'semantic_facing_deg':res['facing'],
        'inference_source':res['src'],'confidence':res['conf'],'reason':res['reason']})
for c in KCAB['cabinets']:
    res=infer_cabinet(c)
    out_items.append({
        'source_name':c['cabinet_id'],'label':c['type'],'semantic_type':c['type'],
        'room':'R-KITCHEN/厨房','zone':'R-KITCHEN','rect':c['rect'],'level':'lower',
        'geometry_axis_deg':res['axis'],'semantic_facing_deg':res['facing'],
        'inference_source':res['src'],'confidence':res['conf'],'reason':res['reason'],
        'authority':'KITCHEN_CABINET_3D_REGISTER_V01 (cabinet_plan.pdf)'})

reg={'register':'FURNITURE_ORIENTATION_REGISTER_V01','units':'deg CCW from +X (east), y=north',
     'convention':{'geometry_axis_deg':'[0,180) long axis','semantic_facing_deg':'[0,360) front direction; null=N/A'},
     'items':out_items}
json.dump(reg,open(os.path.join(D,'furniture_orientation_register_v01.json'),'w'),ensure_ascii=False,indent=1)

cnt={}
for i in out_items: cnt[i['confidence']]=cnt.get(i['confidence'],0)+1
low=[i for i in out_items if i['confidence']=='LOW']
med=[i for i in out_items if i['confidence']=='MEDIUM']
print('total',len(out_items),cnt)
for i in out_items: print(f"{i['confidence']:6s} {i['source_name']:18s} {i['semantic_type']:26s} axis={i['geometry_axis_deg']} face={i['semantic_facing_deg']} {i['inference_source']}")

# ---------- review plot ----------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow
fig,axp=plt.subplots(figsize=(16,14))
for w in WALL_RECTS:
    axp.add_patch(Rectangle((w[0],w[1]),w[2]-w[0],w[3]-w[1],fc='#d0d0d0',ec='#888888',lw=.4,zorder=1))
COL={'HIGH':'#2e9e4f','MEDIUM':'#e08a00','LOW':'#d22'}
for it in out_items:
    r=it['rect']; x,y=r[0],r[1];w_,h_=r[2]-r[0],r[3]-r[1]
    axp.add_patch(Rectangle((x,y),w_,h_,fc='#cfe3ff',ec='#5577cc',lw=.6,zorder=2,alpha=.7))
    cx,cy=ctr(r)
    axp.text(cx,cy,it['source_name'].replace('Rectangle','R').replace('Circle','C'),fontsize=5,ha='center',va='center',zorder=4)
    if it['semantic_facing_deg'] is not None:
        deg=math.radians(it['semantic_facing_deg']); L=min(max(w_,h_)*0.55,900)
        axp.add_patch(FancyArrow(cx,cy,math.cos(deg)*L,math.sin(deg)*L,width=20,
            head_width=140,head_length=160,length_includes_head=True,
            color=COL[it['confidence']],zorder=3))
axp.set_aspect('equal'); axp.invert_yaxis()
xs=[c for w in WALL_RECTS for c in (w[0],w[2])]; ys=[c for w in WALL_RECTS for c in (w[1],w[3])]
axp.set_xlim(min(xs)-800,max(xs)+800); axp.set_ylim(max(ys)+800,min(ys)-800)
axp.set_title('FURNITURE FACING REVIEW — arrows = semantic facing (green HIGH / orange MEDIUM / red LOW)')
fig.savefig(os.path.join(D,'FURNITURE_FACING_REVIEW.png'),dpi=140)
print('wrote FURNITURE_FACING_REVIEW.png + furniture_orientation_register_v01.json')
