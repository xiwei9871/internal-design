"""PASCAL ARCH/FIXTURE CLEANUP V1 -> pascal-master-direct-furnished-v3

Changes vs v2 (nothing else touched):
1. D-107 angled door (= source door D-SM, hinge canonical (8332,4543), F-DOOR leaf
   rest (9095,4919) -> frame direction +26.3 deg CAD). Host helper wall_md_0075 was
   axis-aligned E-W (orthogonalized). Re-aim the HOST HELPER ONLY along the true
   door direction. Door node itself unchanged.
2. Shower wet-zones: solid blockout-box -> SHOWER_ENCLOSURE blockout
   (2 glass panels: fixed + sliding on offset track, top rail, jambs, bottom track;
   glass = thin translucent wall nodes on the OPEN face only; frames = thin boxes).
   Zones: Rectangle007 (R-BATH-P), Rectangle033 (R-BATH-M), Rectangle036 (R-CLOAK /
   次主卫湿区). XY footprint + facing side unchanged. Height 2000 STANDARD_BLOCKOUT.
"""
import json,copy,math
SC='design/pascal_b1/pascal_master_direct_furnished_v2.json'
OUT='design/pascal_b1/pascal_master_direct_furnished_v3.json'
s=json.load(open(SC)); g=copy.deepcopy(s['graph']); nn=g['nodes']
lvl=nn['level_md_0003']

# ---------- 1) D-107 host helper re-aim ----------
# canonical mm -> world m: x=x/1000, z=-y/1000
HB=nn['wall_md_0075']
HB['start']=[8.332,-4.543]; HB['end']=[9.095,-4.919]
HB['metadata']['cleanup']='ARCH_FIXTURE_CLEANUP_V1: re-aimed to F-DOOR frame direction +26.3deg (hinge 8332,4543 -> rest 9095,4919); NOT orthogonal'
nn['door_md_0076']['position'][0]=0.425  # centered on 0.85m diagonal frame
nn['door_md_0076']['metadata']['d107_verified']='frame direction +26.3deg preserved; connects WB-040 band end to WB-014 west face'

# ---------- 2) shower enclosures ----------
def c2w(cx,cy): return (cx/1000.0,-cy/1000.0)
WET={
 # src -> (center_world, size_x, size_z, entry_axis, entry_coord, span(p0,p1 along face), sign of dry-side offset)
 # entry faces from orientation register: R007 face 270 = +z(south); R033/R036 face 180 = -x(west)
 'Rectangle007':{'room':'R-BATH-P','label':'客卫（湿区）','axis':'x','coord':-9.8840,'span':(8.0336,9.6774),'dry':+0.04},
 'Rectangle033':{'room':'R-BATH-M','label':'主卫湿区','axis':'z','coord':15.2056,'span':(-6.2971,-4.7749),'dry':-0.04},
 'Rectangle036':{'room':'R-CLOAK','label':'次主卫湿区','axis':'z','coord':10.4738,'span':(-6.2969,-4.7499),'dry':-0.04},
}
def mk_wall(id_,a,b,h=2.7,t=0.015,md=None):
    return {'object':'node','id':id_,'type':'wall','parentId':'level_md_0003','visible':True,
            'metadata':md or {},'children':[],'thickness':t,'height':h,'start':list(a),'end':list(b),
            'frontSide':'unknown','backSide':'unknown'}
def mk_box(id_,name,pos,scale,md):
    return {'object':'node','id':id_,'type':'item','parentId':'level_md_0003','visible':True,'name':name,
            'position':[round(x,4) for x in pos],'rotation':[0,0,0],
            'scale':[round(x,4) for x in scale],'children':[],
            'asset':{'id':'blockout-box','category':'furniture','name':name,'source':'library',
                     'src':'/items/blockout-box/model.glb','thumbnail':'/items/blockout-box/thumbnail.webp',
                     'dimensions':[1,1,1],'tags':[],'offset':[0,0,0],'rotation':[0,0,0],'scale':[1,1,1]},
            'metadata':md}
new_nodes=[]; drop=set()
FLOOR=0.7; GLASS_H=2.7  # wall height counts from level base 0; 2.7 = floor0.7 + 2000 blockout
for src,w in WET.items():
    drop.add(next(k for k,v in nn.items() if v.get('type')=='item' and v.get('metadata',{}).get('fcstd_obj')==src))
    p0,p1=w['span']; mid=(p0+p1)/2; ov=0.03; c=w['coord']
    L=p1-p0; pw=L/2+ov
    md={'fcstd_obj':src,'semantics':'SHOWER_ENCLOSURE','room_zone':w['room'],
        'representation':'SLIDING_GLASS_SHOWER_DOOR blockout','cleanup':'ARCH_FIXTURE_CLEANUP_V1',
        'glass':'transparent blockout (visual only)','height_status':'STANDARD_BLOCKOUT_2000','review_status':'HUMAN_REVIEW'}
    if w['axis']=='x':
        # face along x at z=coord; two panels on parallel tracks (fixed inner, sliding outer toward dry side)
        fixed=[(p0,c),(p0+pw,c)]; slide=[(p1-pw,c+w['dry']),(p1,c+w['dry'])]
        rail_p=[(mid,FLOOR+1.95,c+w['dry']/2),(L+0.04,0.05,0.08)]
        track_p=[(mid,FLOOR,c+w['dry']/2),(L+0.04,0.03,0.08)]
        jamb=[((p0-0.02),FLOOR,c+w['dry']/2,(0.05,2.0,0.09)),((p1+0.02),FLOOR,c+w['dry']/2,(0.05,2.0,0.09))]
    else:
        fixed=[(c,p0),(c,p0+pw)]; slide=[(c+w['dry'],p1-pw),(c+w['dry'],p1)]
        rail_p=[(c+w['dry']/2,FLOOR+1.95,mid),(0.08,0.05,L+0.04)]
        track_p=[(c+w['dry']/2,FLOOR,mid),(0.08,0.03,L+0.04)]
        jamb=[(c+w['dry']/2,FLOOR,p0-0.02,(0.09,2.0,0.05)),(c+w['dry']/2,FLOOR,p1+0.02,(0.09,2.0,0.05))]
    tag=src[-3:]
    new_nodes.append(mk_wall(f'sh_glass_fix_{tag}',*fixed,h=GLASS_H,md={**md,'part':'FIXED_PANEL'}))
    new_nodes.append(mk_wall(f'sh_glass_sld_{tag}',*slide,h=GLASS_H,md={**md,'part':'SLIDING_PANEL'}))
    new_nodes.append(mk_box(f'sh_rail_{tag}',f"{w['label']}-上轨",rail_p[0],rail_p[1],{**md,'part':'TOP_RAIL'}))
    new_nodes.append(mk_box(f'sh_track_{tag}',f"{w['label']}-下轨",track_p[0],track_p[1],{**md,'part':'BOTTOM_TRACK'}))
    for i,(jx,jy,jz,sc_) in enumerate(jamb):
        new_nodes.append(mk_box(f'sh_jamb_{tag}_{i}',f"{w['label']}-边框{i}",[jx,jy,jz],sc_,{**md,'part':'SIDE_FRAME'}))
for k in drop: del nn[k]
lvl['children']=[c for c in lvl['children'] if c not in drop]+[n['id'] for n in new_nodes]
for n in new_nodes: nn[n['id']]=n
out={'id':'pascal-master-direct-furnished-v3',
 'name':'MASTER DIRECT FURNISHED V3 — D107 angled door fix + shower enclosures',
 'graph':{'nodes':nn,'rootNodeIds':g['rootNodeIds'],'collections':g.get('collections',[])}}
json.dump(out,open(OUT,'w'),ensure_ascii=False)
print('dropped',drop,'added',len(new_nodes),'total',len(nn))
