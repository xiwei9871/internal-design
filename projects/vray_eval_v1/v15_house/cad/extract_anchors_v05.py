#!/usr/bin/env python3
"""geometry_v05: P1.3.2 — D02修正映射 + 跨状态禁自动合并 + 冲突候选分离"""
import os
import json, hashlib, subprocess, sys
from pathlib import Path
import ezdxf
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiPoint, box
from shapely.ops import unary_union, polygonize
from shapely import concave_hull

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
MANIFEST = CAD / 'CONSTRUCTION_INPUT_MANIFEST.json'
FCMD = '/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd'
BLENDER = '/opt/homebrew/bin/blender'
DER = CAD / 'derived'; DER.mkdir(exist_ok=True)

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_manifest(): return {i['id']: i for i in json.loads(MANIFEST.read_text())['inputs']}
def src_status(items):
    st = {}
    for iid, it in items.items():
        p = ROOT / it['path']
        cur = sha256(p) if p.exists() else 'MISSING'
        st[iid] = {'path': it['path'], 'recorded': it['sha256'], 'current': cur,
                   'state': 'FRESH' if cur == it['sha256'] else 'STALE_OR_MISSING'}
    return st

def dump_fc(fc_path, out_json):
    out_json.unlink(missing_ok=True)
    code = f'''
import FreeCAD as App, json
doc = App.openDocument({str(fc_path)!r})
out = []
for o in doc.Objects:
    if hasattr(o, 'Shape') and o.Shape.Vertexes:
        bb = o.Shape.BoundBox
        out.append({{'name': o.Name, 'label': o.Label,
                    'bbox': [round(bb.XMin,2),round(bb.YMin,2),round(bb.XMax,2),round(bb.YMax,2)],
                    'z': [round(bb.ZMin,2),round(bb.ZMax,2)],
                    'verts': [[round(v.Point.x,2),round(v.Point.y,2)] for v in o.Shape.Vertexes]}})
json.dump(out, open({str(out_json)!r}, 'w'), ensure_ascii=False)
'''
    r = subprocess.run([FCMD, '-c', code], capture_output=True, text=True, timeout=300)
    if not out_json.exists():
        print(r.stdout[-1500:], r.stderr[-800:]); sys.exit('fc dump failed')

def dump_blender(blend_path, out_json):
    r = subprocess.run([BLENDER, '-b', str(blend_path), '-P', str(CAD/'blender_dump_geom.py'),
                        '--', str(out_json)], capture_output=True, text=True, timeout=600)
    if not out_json.exists():
        print(r.stdout[-1500:], r.stderr[-800:]); sys.exit('blender dump failed')

def polys_from_segs(segs):
    if not segs: return []
    rings = list(polygonize([LineString(s) for s in segs]))
    polys = [r for r in rings if r.area > 100]
    if polys: return polys
    u = unary_union([LineString(s) for s in segs])
    return []

def union_polys(tris):
    polys = []
    for t in tris:
        p = Polygon(t)
        if p.is_valid and p.area > 1: polys.append(p)
    if not polys: return []
    u = unary_union(polys)
    parts = [u] if isinstance(u, Polygon) else list(u.geoms) if isinstance(u, MultiPolygon) else []
    return [p for p in parts if p.area > 100]

def poly_pts(p): return [[round(x,1),round(y,1)] for x,y in p.exterior.coords[:-1]]
def part_dict(p):
    return {'exterior': poly_pts(p),
            'holes': [[[round(x,1),round(y,1)] for x,y in r.coords[:-1]] for r in p.interiors]}
def is_sliver(p):
    x0,y0,x1,y1=p.bounds
    return min(x1-x0,y1-y0)<60 and p.area<60000
SLIVERS=[]
def poly_bb(p): b=p.bounds; return [round(b[0],1),round(b[1],1),round(b[2],1),round(b[3],1)]
def in_plan(b): return 0<=b[0]<=17000 and -800<=b[1]<=16000 and 0<=b[2]<=17000 and -800<=b[3]<=16000

# D02 权威拆改映射 (源: make_a102.py DEMO_FULL/DEMO_PART, 业主确认5处)
DEMO = {   # 部分拆除: 对象 -> 拆除矩形
    'W_INT_X5800':  [box(5700, 1800, 5900, 3800)],   # D02-1 厨房西墙中段(开放式厨房)
    'W_INT_X7900_U':[box(7800, 5000, 7900, 7800)],   # D02-2 走廊西墙中段(楼梯敞开)
    'W_BALC_N':     [box(3300, 2400, 5800, 2560)],   # D02-3 生活阳台北墙东段
}
DEMO_FULL_OBJS = {'W_EXT_N_LV','W_EXT_N_BAL'}        # D02-4 客厅北墙旧带 / D02-5 阳光房北带 整拆
PENDING_OBJS = {'W_INT_CLK_N','W_INT_CLK_E','W_INT_CLK_W'}   # 衣帽间隔墙→次卫: 非D02项, 待设计裁决
UNVERIFIED_OBJS = {'W_INT_COR_N_STUB'}
APPROVALS_FILE = CAD / 'adjudication_approvals.json'
def load_approvals():
    if APPROVALS_FILE.exists():
        return {tuple(sorted(x)) for x in json.loads(APPROVALS_FILE.read_text()).get('approved_merges',[])}
    return set()

def extract(fcstd_override=None, blend_override=None, out_name='geometry_v05.json',
            fc_dump=None, bl_dump=None):
    items = load_manifest(); st = src_status(items)
    fc_path = Path(fcstd_override) if fcstd_override else ROOT/items['baseline_fcstd']['path']
    bl_path = Path(blend_override) if blend_override else \
        ROOT/items.get('v15_work_blend',{'path':'projects/vray_eval_v1/v15_house/V15_WORK.blend'})['path']
    fc_sha = sha256(fc_path); bl_sha = sha256(bl_path) if bl_path.exists() else 'MISSING'
    fc_raw = fc_dump or DER/'fc_objects_raw.json'
    bl_raw = bl_dump or DER/'blender_geom_raw.json'
    dump_fc(fc_path, fc_raw)
    if bl_dump is None or not Path(bl_raw).exists(): dump_blender(bl_path, bl_raw)
    objs = {o['name']: o for o in json.loads(Path(fc_raw).read_text())}
    blobs = json.loads(Path(bl_raw).read_text())
    derived_reg = {
        'fc_objects_raw': {'file': str(fc_raw), 'sha256': sha256(fc_raw), 'parent_sha256': fc_sha},
        'blender_geom_raw': {'file': str(bl_raw), 'sha256': sha256(bl_raw), 'parent_sha256': bl_sha}}
    AN=[]
    def A(aid,x,y,src,oid,sub,role,ds,vs,ev):
        AN.append({'id':aid,'x':round(x,2),'y':round(y,2),'source_file':src['path'],
                   'source_file_sha256':src['sha'],'source_revision':src['sha'][:12],
                   'source_object_id':oid,'subelement_reference':sub,'geometry_role':role,
                   'design_status':ds,'verification_status':vs,'evidence':ev})
    rev_fc={'path':str(fc_path),'sha':fc_sha}; rev_bl={'path':str(bl_path),'sha':bl_sha}
    def fc_ext(aid,name,axis,mm,role='wall_face'):
        vs=objs[name]['verts']; tgt=(min if mm=='min' else max)(v[axis] for v in vs)
        idx=next(i for i,v in enumerate(vs) if v[axis]==tgt)
        A(aid,vs[idx][0],vs[idx][1],rev_fc,name,f'Shape.Vertexes[{idx}]',role,
          'EXISTING','OBJECT_IDENTIFIED',f'fcstd:{name}.{chr(120+axis)}{mm}')
    for spec in [('S-SPAN-W','W_BALC_S',0,'min'),('S-SPAN-E','W_EXT_E1',0,'max'),
                 ('W-SPAN-S','W_BALC_S',1,'min'),('W-SPAN-N','W_EXT_N_BAL',1,'max'),
                 ('KIT-W-FACE','W_INT_X5800',0,'min'),('KIT-E-FACE','W_INT_X7900_L',0,'min'),
                 ('MBED-W-FACE','W_INT_X7900_L',0,'max'),('MBED-E-FACE','W_INT_X11500',0,'min'),
                 ('MOT-W-FACE','W_INT_X11500',0,'max'),('MOT-E-FACE','W_EXT_E1',0,'min'),
                 ('LWIN-W','W_BAY_F',0,'min'),('LWIN-E','W_BAY_F',0,'max'),
                 ('BALC-N-W','W_EXT_N_BAL',0,'min'),('BALC-N-E','W_EXT_N_BAL',0,'max'),
                 ('BATH2E-FACE','W_INT_X11500',0,'min')]:
        fc_ext(*spec)
    def bl_ext(aid,name,xs,ys,role,vs_='OBJECT_IDENTIFIED'):
        b=blobs[name]['bbox']
        A(aid, b[0] if xs=='W' else b[2], b[1] if ys=='S' else b[3], rev_bl, name,
          f'bbox.corner({xs}{ys})',role,'PROPOSED',vs_,f'blender:{name} bbox {xs}{ys}')
    steps={k:v for k,v in blobs.items() if k.startswith(('STEP_','WAVE_STEP')) and 'RAMP' not in k}
    env={}
    for n,d in steps.items():
        for t in d['tris_xy']:
            for x,y in t:
                for tag,val,cmp in (('W',x,-1),('E',x,1),('S',y,-1),('N',y,1)):
                    if tag not in env or cmp*val>cmp*env[tag][0]: env[tag]=(val,n,x,y)
    for tag in 'WESN':
        v,n,x,y=env[tag]
        A('STAIR-'+tag,x,y,rev_bl,n,f'mesh_extremum({tag})','step_extremum','PROPOSED','FIELD_VERIFY',f'blender:{n} {tag}')
    if 'VIEW_WALL_R3_WEST_PARTITION' in blobs:
        bl_ext('BATH2-NET-W','VIEW_WALL_R3_WEST_PARTITION','E','S','partition_inner_face')
    if 'VIEW_WALL_R3_SOUTH_POCKET_PARTITION' in blobs:
        bl_ext('BATH2-NET-S','VIEW_WALL_R3_SOUTH_POCKET_PARTITION','W','N','partition_inner_face')
    if 'R3_COMPLETE_PARTITION_WALLS' in blobs:
        for tag,xs,ys in (('W','W','S'),('E','E','S'),('S','W','S'),('N','W','N')):
            bl_ext('BATH2-'+tag,'R3_COMPLETE_PARTITION_WALLS',xs,ys,'partition_face')
    if 'KITCHEN_DIVIDER_PIER_SITE_REVIEW' in blobs:
        bl_ext('KOPEN-S','KITCHEN_DIVIDER_PIER_SITE_REVIEW','W','N','opening_edge','FIELD_VERIFY')
    if 'W_wall_md_0010' in blobs:
        bl_ext('KOPEN-N','W_wall_md_0010','W','S','opening_edge','FIELD_VERIFY')

    # 基准 DXF 门洞 (先提取, 供墙体差集使用)
    ddoc=ezdxf.readfile(ROOT/items['baseline_dxf']['path'])
    openings=[]
    for e in ddoc.modelspace():
        if e.dxf.layer=='A-DOOR' and e.dxftype()=='LWPOLYLINE':
            pts=[(p[0],p[1]) for p in e.get_points('xy')]
            xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
            w,h=max(xs)-min(xs),max(ys)-min(ys)
            openings.append({'handle':e.dxf.handle,'rect':[min(xs),min(ys),max(xs),max(ys)],
                'opening_len':round(max(w,h)),'wall_thk':round(min(w,h)),
                'orient':'H' if w>=h else 'V','design_status':'EXISTING','swing':'UNKNOWN_UNVERIFIED'})
    def ext_rect(op, m=250):
        x0,y0,x1,y1=op['rect']; w,h=x1-x0,y1-y0
        return box(x0-m,y0,x1+m,y1) if w<h else box(x0,y0-m,x1,y1+m)
    OPEN_RECTS=[ext_rect(op) for op in openings]

    # ---------- 管理实体: FC 剖切语义 + 拆除差集 + 门洞差集 ----------
    managed=[]
    for n,o in objs.items():
        if not n.startswith(('W_','COL_')) or not o.get('verts'): continue
        try:
            h=concave_hull(MultiPoint(o['verts']),ratio=0.0)
            if h.geom_type!='Polygon' or h.area<1: continue
        except Exception: continue
        if not in_plan(o['bbox']): continue
        status=('UNVERIFIED' if n in UNVERIFIED_OBJS else
                'EXISTING_DEMOLISHED' if n in DEMO_FULL_OBJS else
                'DESIGN_REVIEW_PENDING' if n in PENDING_OBJS else 'EXISTING_RETAINED')
        geoms=[h]
        demolished=[]; opening_cuts=[]
        for rect in DEMO.get(n,[]):
            new_geoms=[]
            for g0 in geoms:
                if g0.intersects(rect):
                    rem=g0.intersection(rect)
                    if rem.area>100: demolished.append(poly_pts(rem))
                    g0=g0.difference(rect)
                new_geoms += [p for p in ([g0] if isinstance(g0,Polygon) else list(g0.geoms)) if p.area>100]
            geoms=new_geoms
        for rect in [r for r in OPEN_RECTS if any(g0.intersects(r) for g0 in geoms)]:
            new_geoms=[]
            for g0 in geoms:
                if g0.intersects(rect):
                    rem=g0.intersection(rect)
                    if rem.area>100: opening_cuts.append(poly_pts(rem))
                    g0=g0.difference(rect)
                new_geoms += [p for p in ([g0] if isinstance(g0,Polygon) else list(g0.geoms)) if p.area>100]
            geoms=new_geoms
        if status=='EXISTING_DEMOLISHED':
            demolished += [poly_pts(p) for p in geoms]; geoms=[]
            managed.append({'object':n,'source_file':str(fc_path),'source_file_sha256':fc_sha,
                'source':'fcstd','design_status':status,'layer':'A-DEMO',
                'parts':[],'demolished_parts':demolished,'opening_cuts':opening_cuts,
                'bbox':o['bbox'],'outline_bbox':o['bbox']})
            continue
        geoms=[g0 for g0 in geoms if not is_sliver(g0)]
        if not geoms: continue
        managed.append({'object':n,'source_file':str(fc_path),'source_file_sha256':fc_sha,
            'source':'fcstd','design_status':status,
            'layer':('A-UNCERTAIN' if status in ('UNVERIFIED','DESIGN_REVIEW_PENDING')
                     else 'A-DEMO' if status=='EXISTING_DEMOLISHED' else 'A-WALL'),
            'parts':[part_dict(p) for p in geoms],'demolished_parts':demolished,
            'opening_cuts':opening_cuts,'cut_height':'FC_SHELL',
            'bbox':o['bbox'],'outline_bbox':poly_bb(unary_union(geoms))})
    # ---------- Blender: 剖切线段→parts, 按 zmin 选标高 ----------
    WALLISH=('WALL','PARTITION','PIER','POCKET','DIVIDER','HOST_WALL','RETURN_WALL')
    def level(d): return '1650' if d['z'][0]>=300 else '1150'
    for n,d in blobs.items():
        if n.startswith('VIEW_WALL_W_wall_md_'): continue
        wallish=n.startswith('W_wall') or any(k in n for k in WALLISH)
        stepish=n.startswith(('STEP_','WAVE_STEP'))
        if not (wallish or stepish) or 'RAMP' in n or 'ROLLED_BACK' in n or '_OLD' in n: continue
        if not in_plan(d['bbox']): continue
        h=level(d)
        parts=polys_from_segs(d['segs'].get(h,[]))
        cut=h if parts else None
        if not parts:
            zlo,zhi=d['z']
            if zlo>=2000: cut='OVERHEAD_NOT_PLAN_WALL'
            elif zhi<=1100: cut='BELOW_CUT'
            else: cut='FOOTPRINT_FALLBACK' if wallish else 'FOOTPRINT'
            parts=union_polys(d['tris_xy'])
        if not parts: continue
        if wallish:
            newp=[]
            for g0 in parts:
                for r in OPEN_RECTS:
                    if g0.intersects(r):
                        g0=g0.difference(r)
                newp += [p for p in ([g0] if isinstance(g0,Polygon) else list(g0.geoms)) if p.area>100]
            parts=[p for p in newp if not is_sliver(p)]
            if not parts: continue
        managed.append({'object':n,'source_file':str(bl_path),'source_file_sha256':bl_sha,
            'source':'blender','design_status':'PROPOSED_NEW',
            'layer':'A-DESIGN' if stepish or cut=='OVERHEAD_NOT_PLAN_WALL' else 'A-WALL',
            'parts':[part_dict(p) for p in parts],'cut_height':cut,
            'demolished_parts':[],'bbox':d['bbox'],
            'outline_bbox':poly_bb(unary_union(parts))})
    # ---------- 去重合并: outline IoU>0.7 → 单实体多源名 ----------
    def iou(a,b):
        ix=max(0,min(a[2],b[2])-max(a[0],b[0])); iy=max(0,min(a[3],b[3])-max(a[1],b[1]))
        i=ix*iy; u=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-i
        return i/u if u else 0
    merged=[]; used=set(); conflicts=[]
    APPROVALS=load_approvals()
    for i,m1 in enumerate(managed):
        if i in used: continue
        names=[m1['object']]; parts=m1['parts']; src=m1['source']
        ds=m1['design_status']; layer=m1['layer']; f=m1['source_file']; sh=m1['source_file_sha256']
        for j,m2 in enumerate(managed):
            if j<=i or j in used: continue
            if iou(m1['outline_bbox'],m2['outline_bbox'])>0.7:
                pair=tuple(sorted((m1['object'],m2['object'])))
                if m2['design_status']!=ds and pair not in APPROVALS:
                    # 跨状态未批准 → 不合并, 记冲突候选
                    conflicts.append({'a':m1['object'],'b':m2['object'],
                        'status_a':m1['design_status'],'status_b':m2['design_status'],
                        'iou':round(iou(m1['outline_bbox'],m2['outline_bbox']),3),
                        'disposition':'BOTH_KEPT_AS_CONFLICT_CANDIDATES'})
                    continue
                used.add(j); names.append(m2['object'])
                if m2['design_status']!=ds:
                    m1.setdefault('merge_review',[]).append(
                        {'with':m2['object'],'status':m2['design_status'],
                         'rule':'cross_status_merge_APPROVED','iou':round(iou(m1['outline_bbox'],m2['outline_bbox']),3)})
                if m2['source']=='fcstd' and m1['source']!='fcstd':   # FC 几何优先
                    parts=m2['parts']; f=m2['source_file']; sh=m2['source_file_sha256']
        used.add(i)
        merged.append({'objects':names,'source_file':f,'source_file_sha256':sh,'source':src,
            'design_status':ds,'layer':layer,'parts':parts,
            'demolished_parts':m1.get('demolished_parts',[]),
            'opening_cuts':m1.get('opening_cuts',[]),
            'merge_review':m1.get('merge_review',[]),
            'outline_bbox':m1['outline_bbox'],
            'cut_height':m1.get('cut_height'),'bbox':m1['bbox']})
    # part 级吸收: 某 spec 的 part >95% 被另一 spec 的 part 覆盖 → 移除并挂名
    anomalies=[]
    spec_polys={}
    for mi,m in enumerate(merged):
        for pi,part in enumerate(m['parts']):
            spec_polys[(mi,pi)]=(Polygon(part['exterior']),[Polygon(h) for h in part['holes']])
    drop=set(); alias={}
    keys=list(spec_polys)
    for i in range(len(keys)):
        for j in range(len(keys)):
            if i==j or keys[i] in drop or keys[j] in drop: continue
            pi_,_ = spec_polys[keys[i]]; pj_,_ = spec_polys[keys[j]]
            if pi_.area<1: continue
            ov=pi_.intersection(pj_).area/pi_.area
            si,sj=merged[keys[i][0]]['design_status'],merged[keys[j][0]]['design_status']
            pair=tuple(sorted((merged[keys[i][0]]['objects'][0],merged[keys[j][0]]['objects'][0])))
            if ov>0.95 and (si==sj or pair in APPROVALS):
                drop.add(keys[i])
                alias.setdefault(keys[j],[]).extend(merged[keys[i][0]]['objects'])
                anomalies.append({'rule':'subsumed','dropped':merged[keys[i][0]]['objects'],
                                  'into':merged[keys[j][0]]['objects'],'overlap':round(ov,3),
                                  'status_i':si,'status_j':sj,'review':'auto' if si==sj else 'APPROVED'})
            elif ov>0.95:
                merged[keys[i][0]].setdefault('conflict_parts',[]).append(keys[i][1])
                anomalies.append({'rule':'overlap_unresolved','kept_both':
                                  [merged[keys[i][0]]['objects'],merged[keys[j][0]]['objects']],
                                  'overlap':round(ov,3),'status_i':si,'status_j':sj,'review':'REQUIRED'})
    for mi,m in enumerate(merged):
        m['parts']=[p for pi,p in enumerate(m['parts']) if (mi,pi) not in drop]
        extra=[n for (mj,pj),ns in alias.items() if mj==mi for n in ns]
        m['objects']+= [n for n in extra if n not in m['objects']]
    merged=[m for m in merged if m['parts'] or m.get('demolished_parts')]

    out={'version':'v05','generated_by':'extract_anchors_v04.py','units':'mm',
         'sources':st,'derived_data':derived_reg,'anchors':AN,'door_openings':openings,'anomalies':anomalies,'conflicts':conflicts,
         'managed_entities':merged,
         'dims':{'south_total':{'a':'S-SPAN-W','b':'S-SPAN-E','axis':'x'},
                 'west_total':{'a':'W-SPAN-S','b':'W-SPAN-N','axis':'y'},
                 'kitchen_face':{'a':'KIT-W-FACE','b':'KIT-E-FACE','axis':'x'},
                 'master_clear':{'a':'MBED-W-FACE','b':'MBED-E-FACE','axis':'x'},
                 'mother_clear':{'a':'MOT-W-FACE','b':'MOT-E-FACE','axis':'x'},
                 'living_window':{'a':'LWIN-W','b':'LWIN-E','axis':'x'},
                 'balcony_north':{'a':'BALC-N-W','b':'BALC-N-E','axis':'x'},
                 'stair_width':{'a':'STAIR-W','b':'STAIR-E','axis':'x'},
                 'stair_depth':{'a':'STAIR-S','b':'STAIR-N','axis':'y'},
                 'bath2_envelope_w':{'a':'BATH2-W','b':'BATH2-E','axis':'x'},
                 'bath2_net_w':{'a':'BATH2-NET-W','b':'BATH2E-FACE','axis':'x'},
                 'kitchen_open':{'a':'KOPEN-S','b':'KOPEN-N','axis':'y'}}}
    (DER/out_name).write_text(json.dumps(out,ensure_ascii=False,indent=1))
    stale=[k for k,v in st.items() if v['state']!='FRESH']
    print(f'anchors={len(AN)} managed={len(merged)}(from {len(managed)}) openings={len(openings)} dims={len(out["dims"])} stale={stale}')
    return out

if __name__=='__main__': extract()
