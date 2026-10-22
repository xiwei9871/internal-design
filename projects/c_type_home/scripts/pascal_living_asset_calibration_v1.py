#!/usr/bin/env python3
"""PASCAL ASSET CALIBRATION — LIVING ROOM V1.

Reads:
  design/b1_blockout/furniture_3d_dimension_register_v01.json   (target dims)
  design/b1_blockout/furniture_orientation_register_v01.json    (rect + facing)
  design/pascal_b1/pascal_master_direct_furnished_v1.json       (arch scene template)

Writes:
  design/pascal_b1/FURNITURE_ASSET_CALIBRATION_V01.json
  design/pascal_b1/pascal_living_calib_v1.json  (arch + 6 calibrated items)
"""
import json, math, copy, sys

ROOT = '/Users/xiwei/interior_design/projects/c_type_home'
DIM_REG = f'{ROOT}/design/b1_blockout/furniture_3d_dimension_register_v01.json'
ORI_REG = f'{ROOT}/design/b1_blockout/furniture_orientation_register_v01.json'
SCENE   = f'{ROOT}/design/pascal_b1/pascal_master_direct_furnished_v1.json'
OUT_JSON= f'{ROOT}/design/pascal_b1/FURNITURE_ASSET_CALIBRATION_V01.json'
OUT_SCENE=f'{ROOT}/design/pascal_b1/pascal_living_calib_v1.json'

# ---- measured GLB natives (scripts/glb_inspect.py, node transforms applied) ----
# dims = native bbox size [x,y,z] metres; pivot min/max per axis; front axis from structure.
ASSETS = {
 'sofa':          dict(dims=[2.050,0.731,1.009], min=[-1.023,-0.009,-0.551], max=[1.027,0.722,0.459],
                       front='+Z', evidence='frame extends z-0.551 (backrest side) vs front z+0.459; seat cushion reaches z+0.447'),
 'lounge-chair':  dict(dims=[0.671,1.028,1.252], min=[-0.336,-0.003,-0.715], max=[0.336,1.025,0.537],
                       front='+Z', evidence='backrest block z[-0.55,0] high y; seat/leg rest extends +Z'),
 'coffee-table':  dict(dims=[1.718,0.295,1.034], min=[-0.859,0,-0.526], max=[0.859,0.295,0.508],
                       front='N/A', evidence='symmetric table, no semantic front'),
 'bedside-table': dict(dims=[0.444,0.480,0.455], min=[-0.222,0,-0.221], max=[0.221,0.480,0.234],
                       front='+Z', evidence='drawer pull prim at z+0.22'),
 'tv-stand':      dict(dims=[1.852,0.346,0.318], min=[-0.926,-0.207,-0.159], max=[0.926,0.139,0.159],
                       front='+Z', evidence='open console face assumed +Z (catalog convention; verify in render)'),
}
ASSET_URL = '/items/{}/model.glb'

def cad_facing_to_pascal_yaw(theta_deg):
    """CAD cardinal facing (0=E,+X ; 90=N,+Y ; CCW) -> Pascal rotation.y radians
    for an asset whose native front is +Z (glTF/three: R_y positive sends +Z->+X)."""
    if theta_deg is None: return 0.0
    return math.radians((90.0 + theta_deg) % 360.0)

def rot_y(v, yaw):
    c,s = math.cos(yaw), math.sin(yaw)
    return [v[0]*c + v[2]*s, v[1], -v[0]*s + v[2]*c]

def entries(reg):
    return reg if isinstance(reg, list) else reg.get('entries', reg.get('items', reg))

SCOPE = ['Rectangle046','Rectangle047','Rectangle048','Rectangle049','Circle','Rectangle004']
# target source -> (asset, extra yaw added to cad_facing_to_pascal_yaw, footprint map, note)
# footprint map: which LOCAL axes map to target rect width(x) / depth(y) BEFORE yaw.
MAP = {
 'Rectangle046': dict(asset='sofa',
     # target world footprint: x-extent=rect_w(0.9), z-extent=rect_d(2.3); yaw=90 sends localZ->x, localX->z
     local_to_world={'x':'z','z':'x'}, note='SOFA_3S seat cushions face east toward media cabinet'),
 'Rectangle047': dict(asset='sofa',
     local_to_world={'x':'x','z':'z'}, note='SOFA_2S on north edge faces south into room'),
 'Rectangle048': dict(asset='lounge-chair',
     local_to_world={'x':'z','z':'x'},
     extra_yaw_deg=0.0,  # see note
     note='CHAISE: register facing=90N is seat-open side, recline axis=E-W (rect 1.7x0.9). '
          'yaw chosen so recline axis lies E-W (back west, feet east); entry side faces north. REVIEW'),
 'Rectangle049': dict(asset='coffee-table',
     local_to_world={'x':'z','z':'x'}, note='COFFEE_TABLE long axis N-S; facing N/A'),
 'Circle':       dict(asset='bedside-table',
     local_to_world={'x':'x','z':'z'}, note='SIDE_TABLE square footprint; facing N/A'),
 'Rectangle004': dict(asset='tv-stand',
     local_to_world={'x':'z','z':'x'}, note='MEDIA_CABINET on east wall, open face west'),
}
# yaw per source (deg, final Pascal rotation.y)
YAW = {'Rectangle046':90.0,'Rectangle047':0.0,'Rectangle048':90.0,
       'Rectangle049':90.0,'Circle':0.0,'Rectangle004':270.0}

def main():
    dims = {e['source_name']:e for e in entries(json.load(open(DIM_REG)))}
    ori  = {e['source_name']:e for e in entries(json.load(open(ORI_REG)))}
    scene= json.load(open(SCENE))

    calib=[]
    items=[]
    for i,src in enumerate(SCOPE):
        o=ori[src]; d=dims[src]; m=MAP[src]; a=ASSETS[m['asset']]
        x0,y0,x1,y1=o['rect']
        tw=(x1-x0)/1000.0; td=(y1-y0)/1000.0          # world extents: x-east, z-south(-y)
        cx=(x0+x1)/2/1000.0; cz=-(y0+y1)/2/1000.0
        th=d.get('height',0)/1000.0
        yaw=math.radians(YAW[src])
        # scale: local axis -> world extent it must cover
        l2w=m['local_to_world']
        sx = (td if l2w['x']=='z' else tw)/a['dims'][0]
        sy = (th/a['dims'][1]) if a['dims'][1] else 1.0
        sz = (tw if l2w['z']=='x' else td)/a['dims'][2]
        # anchor: footprint-center-on-floor
        bc=[(a['min'][0]+a['max'][0])/2,(a['min'][1]+a['max'][1])/2,(a['min'][2]+a['max'][2])/2]
        off=rot_y([bc[0]*sx,0,bc[2]*sz],yaw)         # scaled local bbox-center offset in world
        pos=[round(cx-off[0],4), round(-a['min'][1]*sy,4), round(cz-off[2],4)]
        # distortion metric
        plan_ratio=max(sx,sz)/min(sx,sz)
        cls='PASS'
        reason=[]
        if plan_ratio>1.6: cls='SIZE_DISTORTION'; reason.append(f'plan scale ratio {plan_ratio:.2f} > 1.6')
        elif plan_ratio>1.25: reason.append(f'moderate non-uniform plan scale ratio {plan_ratio:.2f}')
        if src=='Rectangle048': reason.append('facing semantics ambiguous for chaise: recline axis E-W, seat open side N')
        if m['asset']=='tv-stand' and a['front']=='+Z': reason.append('open-face side assumed +Z, verify in render')
        item={
          'id':f'item_cal_{i+1:04d}','type':'item','object':'node','name':d['label'],
          'parentId':'level_md_0003','visible':True,
          'position':pos,'rotation':[0,round(yaw,6),0],'scale':[round(sx,4),round(sy,4),round(sz,4)],
          'children':[],
          'asset':{'id':m['asset'],'category':'furniture','name':d['label'],'source':'library',
                   'src':ASSET_URL.format(m['asset']),
                   'thumbnail':f"/items/{m['asset']}/thumbnail.webp",
                   'dimensions':a['dims'],'tags':[],'offset':[0,0,0],
                   'rotation':[0,0,0],'scale':[1,1,1]},
          'metadata':{'fcstd_obj':src,'semantics':d['semantic_type'],'room_zone':o.get('zone','R-LIVING'),
                      'calibration':'FURNITURE_ASSET_CALIBRATION_V01','review_status':'HUMAN_REVIEW',
                      'design_facing_deg':o['semantic_facing_deg']}}
        items.append(item)
        calib.append({
          'source_name':src,'semantic_type':d['semantic_type'],'room':o.get('room'),
          'cad_rect_mm':o['rect'],'target_dims_m':{'x_extent':round(tw,3),'z_extent':round(td,3),'height':round(th,3)},
          'target_center_m':[round(cx,4),0,round(cz,4)],
          'design_axis_deg':o['geometry_axis_deg'],'design_facing_deg':o['semantic_facing_deg'],
          'candidate_asset':{'id':m['asset'],'src':ASSET_URL.format(m['asset']),
            'native_dims_m':a['dims'],'native_min':a['min'],'native_max':a['max'],
            'native_pivot':'xz-center of mesh; y as listed','native_front_axis':a['front'],
            'front_evidence':a['evidence']},
          'project_facing_yaw_deg':(90+o['semantic_facing_deg'])%360 if o['semantic_facing_deg'] is not None else None,
          'native_front_correction_deg':0,
          'final_yaw_deg':YAW[src],
          'anchor_offset_local_m':[round(bc[0],4),round(-a['min'][1],4),round(bc[2],4)],
          'scale_xyz':[round(sx,4),round(sy,4),round(sz,4)],
          'plan_scale_ratio':round(plan_ratio,3),
          'classification':cls,'confidence':'MEDIUM' if reason else 'HIGH',
          'notes':'; '.join([m['note']]+reason)})

    out={'version':'V01','status':'HUMAN_REVIEW','convention':{
          'world':'x=east(+CAD x), y=up, z=south(-CAD y); rotation=three.js Euler rad XYZ',
          'yaw_formula':'yaw_deg = (90 + cad_facing_deg) mod 360 for native_front=+Z',
          'anchor':'FOOTPRINT_CENTER_ON_FLOOR: position.xz = rect center - R(s*local_bbox_center_xz); position.y = -minY*sy'},
        'items':calib}
    json.dump(out,open(OUT_JSON,'w'),ensure_ascii=False,indent=2)

    # scene: arch nodes from furnished scene minus items, + 6 calibrated items
    g=scene['graph'];nodes=g['nodes']
    lvl=nodes['level_md_0003']
    nonitem=[c for c in lvl['children'] if nodes.get(c,{}).get('type')!='item']
    lvl['children']=nonitem+[it['id'] for it in items]
    for k in [k for k,n in nodes.items() if n.get('type')=='item']: del nodes[k]
    for it in items: nodes[it['id']]=it
    sc={'id':'pascal-living-calib-v1','name':'LIVING ASSET CALIB V1 — arch + 6 calibrated living-room items',
        'graph':{'nodes':nodes,'rootNodeIds':g['rootNodeIds'],'collections':g.get('collections',[])}}
    json.dump(sc,open(OUT_SCENE,'w'),ensure_ascii=False)
    for c in calib:
        print(f"{c['source_name']:14s} {c['semantic_type']:13s} {c['candidate_asset']['id']:14s} yaw={c['final_yaw_deg']:5.1f} scale={c['scale_xyz']} cls={c['classification']} {c['confidence']}")
    print('wrote',OUT_JSON,OUT_SCENE)

if __name__=='__main__': main()
