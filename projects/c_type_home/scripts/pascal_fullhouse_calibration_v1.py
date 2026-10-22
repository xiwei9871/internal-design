#!/usr/bin/env python3
"""PASCAL FULL-HOUSE FURNITURE CALIBRATION V1 -> scene pascal-master-direct-furnished-v2.

Sources (all read-only):
  furniture_3d_dimension_register_v01.json  (target dims)
  furniture_orientation_register_v01.json   (rect + design facing)
  pascal_master_direct_furnished_v1.json    (arch + kitchen blockouts + floor heights)

Rules:
  cad_facing_to_pascal_yaw(theta) = (90+theta)%360 deg, for native_front=+Z assets.
  Anchor = FOOTPRINT_CENTER_ON_FLOOR.
  Facing vs long-axis conflicts => OVERRIDE toward room side, flagged.
  Kitchen stays blockout primitives (PDF register), reused verbatim from v1.
Outputs:
  FURNITURE_ASSET_CALIBRATION_V02.json
  pascal_master_direct_furnished_v2.json
"""
import json, math, copy

ROOT = '/Users/xiwei/interior_design/projects/c_type_home'
DIM_REG = f'{ROOT}/design/b1_blockout/furniture_3d_dimension_register_v01.json'
ORI_REG = f'{ROOT}/design/b1_blockout/furniture_orientation_register_v01.json'
SCENE_V1= f'{ROOT}/design/pascal_b1/pascal_master_direct_furnished_v1.json'
OUT_JSON= f'{ROOT}/design/pascal_b1/FURNITURE_ASSET_CALIBRATION_V02.json'
OUT_SCENE=f'{ROOT}/design/pascal_b1/pascal_master_direct_furnished_v2.json'

# ---- measured GLB natives (glb_inspect, node transforms applied) ----
A = {
 'sofa':           dict(d=[2.050,0.731,1.009], mn=[-1.023,-0.009,-0.551], mx=[ 1.027,0.722,0.459], f='+Z'),
 'lounge-chair':   dict(d=[0.671,1.028,1.252], mn=[-0.336,-0.003,-0.715], mx=[ 0.336,1.025,0.537], f='+Z'),
 'coffee-table':   dict(d=[1.718,0.295,1.034], mn=[-0.859, 0.000,-0.526], mx=[ 0.859,0.295,0.508], f='N/A'),
 'bedside-table':  dict(d=[0.444,0.480,0.455], mn=[-0.222, 0.000,-0.221], mx=[ 0.221,0.480,0.234], f='+Z'),
 'tv-stand':       dict(d=[1.852,0.346,0.318], mn=[-0.926,-0.207,-0.159], mx=[ 0.926,0.139,0.159], f='+Z?'),
 'double-bed':     dict(d=[1.515,0.701,1.994], mn=[-0.760, 0.000,-0.970], mx=[ 0.750,0.700,1.020], f='+Z(feet)/-Z(head)'),
 'single-bed':     dict(d=[1.080,0.593,2.134], mn=[-0.540, 0.000,-1.050], mx=[ 0.540,0.593,1.080], f='+Z(feet)/-Z(head): pillow prim at z<-0.65'),
 'closet':         dict(d=[1.946,2.257,0.599], mn=[-0.973, 0.000,-0.290], mx=[ 0.973,2.257,0.310], f='+Z'),
 'dresser':        dict(d=[1.225,0.729,0.602], mn=[-0.612, 0.000,-0.295], mx=[ 0.612,0.729,0.308], f='+Z'),
 'bookshelf':      dict(d=[0.921,1.986,0.321], mn=[-0.461, 0.000,-0.161], mx=[ 0.461,1.986,0.160], f='+Z(open shelves assumed)'),
 'dining-table':   dict(d=[2.153,0.698,0.942], mn=[-1.080, 0.000,-0.455], mx=[ 1.080,0.698,0.480], f='N/A'),
 'dining-chair':   dict(d=[0.464,0.864,0.494], mn=[-0.230, 0.000,-0.250], mx=[ 0.230,0.864,0.250], f='+Z(backrest at -z)'),
 'office-chair':   dict(d=[0.655,1.158,0.689], mn=[-0.330,-0.002,-0.380], mx=[ 0.330,1.158,0.310], f='+Z'),
 'toilet':         dict(d=[0.417,0.814,0.711], mn=[-0.210, 0.000,-0.120], mx=[ 0.210,0.814,0.590], f='+Z(bowl opens +z, tank -z)'),
 'sink-cabinet':   dict(d=[0.971,1.263,0.636], mn=[-0.486,-0.553,-0.330], mx=[ 0.486,0.710,0.270], f='+Z(pulls at +z)'),
 'washing-machine':dict(d=[0.599,0.857,0.529], mn=[-0.300, 0.000,-0.250], mx=[ 0.300,0.857,0.280], f='+Z(drum door +z)'),
 'blockout-box':   dict(d=[1.000,1.000,1.000], mn=[-0.500, 0.000,-0.500], mx=[ 0.500,1.000,0.500], f='N/A'),
}
URL='/items/{}/model.glb'

def cad_facing_to_pascal_yaw(theta):
    return None if theta is None else (90.0+theta)%360.0

def entries(reg):
    return reg if isinstance(reg,list) else reg.get('entries',reg.get('items',reg))

# ---- full-house plan -----------------------------------------------------
# src -> dict(asset|PRIMITIVE, yaw_deg|None(use facing), repeat, floor_from_v1, note)
# yaw overridden where facing is axis-parallel or asset-freeform.
P = {
 'Rectangle004': dict(asset='tv-stand'),                                    # MEDIA_CABINET
 'Rectangle046': dict(asset='sofa'), 'Rectangle047': dict(asset='sofa'),
 'Rectangle048': dict(asset='lounge-chair', yaw_deg=90.0,
    note='chaise: recline axis E-W, back west, entry side north (design facing N)'),
 'Rectangle049': dict(asset='coffee-table', yaw_deg=90.0),                  # long axis N-S
 'Circle':       dict(asset='bedside-table', yaw_deg=0.0),
 'Rectangle011': dict(asset='PRIMITIVE'), 'Rectangle014': dict(asset='PRIMITIVE'),
 'Rectangle051': dict(asset='PRIMITIVE'),                                   # HEADBOARDs
 'Rectangle012': dict(asset='double-bed'), 'Rectangle013': dict(asset='double-bed'),
 'Rectangle017': dict(asset='single-bed'),
 'Rectangle015': dict(asset='closet'), 'Rectangle021': dict(asset='closet'),
 'Rectangle045': dict(asset='closet'),
 'Rectangle022': dict(asset='tv-stand'), 'Rectangle023': dict(asset='tv-stand'),
 'Rectangle024': dict(asset='bookshelf', repeat=4,
    note='4.2m run -> 4 bookshelf modules side by side'),
 'Rectangle025': dict(asset='bookshelf', repeat=2,
    note='1.6m run -> 2 bookshelf modules'),
 'Rectangle026': dict(asset='dining-table',
    note='tea-table/study workstation -> dining-table asset (flat top, near-uniform scale)'),
 'Circle007':    dict(asset='PRIMITIVE', note='STUDY_ARMCHAIR facing LOW conf -> human review'),
 'Rectangle027': dict(asset='PRIMITIVE'),                                   # BENCH
 'Circle008': dict(asset='PRIMITIVE'), 'Circle009': dict(asset='PRIMITIVE'),  # stools
 'Circle010': dict(asset='dining-chair'), 'Circle011': dict(asset='dining-chair'),
 'Circle012': dict(asset='dining-chair'), 'Circle013': dict(asset='dining-chair'),
 'Rectangle050': dict(asset='dining-table', yaw_deg=0.0),                   # axis0
 'Rectangle029': dict(asset='dresser'),
 'Rectangle031': dict(asset='PRIMITIVE'),                                   # shoe cabinet, no fit asset
 'Rectangle032': dict(asset='dresser', yaw_deg=180.0,
    note='OVERRIDE: register facing 180(W) is axis-parallel; cabinet hugs south balcony wall -> open north'),
 'Rectangle030': dict(asset='sink-cabinet', yaw_deg=90.0,
    note='OVERRIDE: register facing 90(N) is axis-parallel; long run N-S on west side -> open east'),
 'Rectangle035': dict(asset='sink-cabinet', yaw_deg=0.0,
    note='OVERRIDE: register facing 0(E) is axis-parallel; vanity on north side of bath -> open south'),
 'Rectangle037': dict(asset='sink-cabinet'),                                # face90 consistent
 'Rectangle007': dict(asset='PRIMITIVE', note='shower zone footprint 1.64x0.81 -> asset distortion, keep zone block'),
 'Rectangle033': dict(asset='PRIMITIVE', note='shower zone -> primitive'),
 'Rectangle036': dict(asset='PRIMITIVE', note='shower zone -> primitive'),
 'Rectangle008': dict(asset='toilet'),
 'Rectangle034': dict(asset='toilet'), 'Rectangle038': dict(asset='toilet'),
 'Rectangle039': dict(asset='PRIMITIVE', note='freezer asset 0.43m too small vs 1.2m chest -> distortion'),
 'Rectangle040': dict(asset='PRIMITIVE', note='stacked W+D: single washer asset stretch 1.98x vertical -> primitive'),
 'Rectangle041': dict(asset='washing-machine',
    note='3kg mini washer: scaled ~0.75; base_z TO_VERIFY'),
 'Rectangle043': dict(asset='PRIMITIVE'), 'Rectangle044': dict(asset='PRIMITIVE'),
 'Rectangle052': dict(asset='PRIMITIVE', note='350mm deep console-desk: desk asset crush -> primitive'),
}

def rot_y(v,yaw):
    c,s=math.cos(yaw),math.sin(yaw)
    return [v[0]*c+v[2]*s, v[1], -v[0]*s+v[2]*c]

def main():
    dims={e['source_name']:e for e in entries(json.load(open(DIM_REG)))}
    ori ={e['source_name']:e for e in entries(json.load(open(ORI_REG)))}
    sc1 =json.load(open(SCENE_V1))
    nodes1=sc1['graph']['nodes']
    floor_y={n['metadata']['fcstd_obj']:n['position'][1]
             for n in nodes1.values() if n.get('type')=='item' and n.get('metadata',{}).get('fcstd_obj')}
    kitchen_nodes={k:n for k,n in nodes1.items()
                   if n.get('type')=='item' and not n.get('metadata',{}).get('fcstd_obj')}

    calib=[]; items=[]; ii=0
    def mk_item(src,aid,pos,rot,scale,label,zone,sub=''):
        nonlocal ii; ii+=1
        a=A[aid]
        return {'id':f'item_v2_{ii:04d}','type':'item','object':'node','name':label,
          'parentId':'level_md_0003','visible':True,
          'position':[round(x,4) for x in pos],'rotation':[0,round(rot,6),0],
          'scale':[round(x,4) for x in scale],'children':[],
          'asset':{'id':aid,'category':'furniture','name':label,'source':'library',
                   'src':URL.format(aid),'thumbnail':f'/items/{aid}/thumbnail.webp',
                   'dimensions':a['d'],'tags':[],'offset':[0,0,0],'rotation':[0,0,0],'scale':[1,1,1]},
          'metadata':{'fcstd_obj':src,'semantics':dims[src]['semantic_type'],'room_zone':zone,
                      'calibration':'FURNITURE_ASSET_CALIBRATION_V02','review_status':'HUMAN_REVIEW',
                      'design_facing_deg':ori[src]['semantic_facing_deg'],'sub':sub}}

    for src,cfg in P.items():
        o=ori[src]; d=dims[src]; x0,y0,x1,y1=o['rect']
        tw=(x1-x0)/1000.0; td=(y1-y0)/1000.0
        cx=(x0+x1)/2/1000.0; cz=-(y0+y1)/2/1000.0
        th=(d.get('height') or 500)/1000.0
        fy=floor_y.get(src,0.0)
        face=o['semantic_facing_deg']
        yaw_d=cfg.get('yaw_deg')
        if yaw_d is None: yaw_d=cad_facing_to_pascal_yaw(face) or 0.0
        yaw=math.radians(yaw_d)
        aid=cfg['asset']
        if aid=='PRIMITIVE':
            a=A['blockout-box']
            pos=[cx,fy,cz]; scale=[tw,th,td]
            it=mk_item(src,'blockout-box',pos,0.0,scale,d['label'],o.get('zone'))
            items.append(it)
            calib.append({'source_name':src,'semantic_type':d['semantic_type'],'room':o.get('room'),
              'cad_rect_mm':o['rect'],'target_dims_m':{'x':round(tw,3),'z':round(td,3),'h':round(th,3)},
              'target_center_m':[round(cx,4),round(fy,4),round(cz,4)],
              'design_facing_deg':face,'candidate_asset':{'id':'PRIMITIVE(blockout-box)'},
              'final_yaw_deg':0,'scale_xyz':scale,'classification':'PRIMITIVE_FALLBACK',
              'confidence':'MEDIUM','notes':cfg.get('note','no suitable catalog asset')})
            continue
        a=A[aid]; n=cfg.get('repeat',1)
        # coverage: which world extent each LOCAL axis must cover (before considering repeat)
        swapped = (round(yaw_d)%180)!=0
        cover_x = td if swapped else tw    # world extent covered by local x
        cover_z = tw if swapped else td
        sx = cover_x/(a['d'][0]*n) if n>1 else cover_x/a['d'][0]
        sz = cover_z/a['d'][2]
        sy = th/a['d'][1]
        bc=[(a['mn'][0]+a['mx'][0])/2,(a['mn'][1]+a['mx'][1])/2,(a['mn'][2]+a['mx'][2])/2]
        pr=max(sx,sz)/min(sx,sz)
        cls='PASS';notes=[]
        if pr>1.6: cls='SIZE_DISTORTION';notes.append(f'plan ratio {pr:.2f}>1.6')
        elif pr>1.25: notes.append(f'moderate plan ratio {pr:.2f}')
        if 'OVERRIDE' in cfg.get('note',''): notes.append('facing overridden: register facing axis-parallel')
        for k in range(n):
            # modules spread along the world axis that local x maps to
            loc=[(k-(n-1)/2)*(cover_x/n),0,0] if n>1 else [0,0,0]
            woff=rot_y(loc,yaw)
            base_off=rot_y([bc[0]*sx,0,bc[2]*sz],yaw)
            pos=[round(cx-base_off[0]+woff[0],4), round(fy-a['mn'][1]*sy,4), round(cz-base_off[2]+woff[2],4)]
            it=mk_item(src,aid,pos,yaw,[sx,sy,sz],d['label'],o.get('zone'),sub=f'module {k+1}/{n}' if n>1 else '')
            items.append(it)
        calib.append({'source_name':src,'semantic_type':d['semantic_type'],'room':o.get('room'),
          'cad_rect_mm':o['rect'],'target_dims_m':{'x':round(tw,3),'z':round(td,3),'h':round(th,3)},
          'target_center_m':[round(cx,4),round(fy,4),round(cz,4)],
          'design_axis_deg':o['geometry_axis_deg'],'design_facing_deg':face,
          'candidate_asset':{'id':aid,'repeat':n,'native_dims_m':a['d'],'native_min':a['mn'],'native_max':a['mx'],
            'native_pivot':'xz-center of bbox; y as listed','native_front_axis':a['f']},
          'project_facing_yaw_deg':cad_facing_to_pascal_yaw(face),
          'native_front_correction_deg':0,'final_yaw_deg':yaw_d,
          'anchor_offset_local_m':[round(-bc[0],4),round(-a['mn'][1],4),round(-bc[2],4)],
          'scale_xyz':[round(sx,4),round(sy,4),round(sz,4)],'plan_scale_ratio':round(pr,3),
          'classification':cls,'confidence':'MEDIUM' if notes else 'HIGH',
          'notes':'; '.join(filter(None,[cfg.get('note','')]+notes))})

    # build scene: arch + kitchen blockouts (verbatim) + calibrated items
    g=copy.deepcopy(sc1['graph']); nn=g['nodes']
    lvl=nn['level_md_0003']
    keep=[c for c in lvl['children'] if nn.get(c,{}).get('type')!='item']
    kn=[k for k in kitchen_nodes]
    for k in [k for k,n in nn.items() if n.get('type')=='item']: del nn[k]
    for k in kn: nn[k]=kitchen_nodes[k]
    for it in items: nn[it['id']]=it
    lvl['children']=keep+kn+[it['id'] for it in items]
    sc={'id':'pascal-master-direct-furnished-v2',
        'name':'MASTER DIRECT FURNISHED V2 — full-house calibrated assets + kitchen blockouts',
        'graph':{'nodes':nn,'rootNodeIds':g['rootNodeIds'],'collections':g.get('collections',[])}}
    json.dump({'version':'V02','status':'HUMAN_REVIEW',
        'convention':{'world':'x=east, y=up, z=south(-CAD y)','yaw_formula':'(90+cad_facing)%360 for native_front +Z',
                      'anchor':'FOOTPRINT_CENTER_ON_FLOOR','note':'kitchen = PDF blockout primitives verbatim from v1'},
        'items':calib},open(OUT_JSON,'w'),ensure_ascii=False,indent=1)
    json.dump(sc,open(OUT_SCENE,'w'),ensure_ascii=False)
    import collections
    cc=collections.Counter(c['classification'] for c in calib)
    print(dict(cc),'items:',len(items))
    for c in calib: print(f"{c['source_name']:15s} {c['semantic_type']:20s} {str(c['candidate_asset']['id'])[:16]:16s} yaw={c['final_yaw_deg']:5.0f} {c['classification']}")

if __name__=='__main__': main()
