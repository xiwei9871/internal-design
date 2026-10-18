#!/usr/bin/env python3
"""三源对象映射: 开发商结构图(S-S.WALL) + 现状测绘(FC/DXF) + 设计目标(Blender)
输出: 统一墙体状态表 + 受保护墙冲突检查 + 差集QA"""
import json, hashlib
from pathlib import Path
import ezdxf
from shapely.geometry import Polygon, MultiPolygon, LineString, box
from shapely.ops import unary_union, polygonize

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
AX, AY = 1298172.0, -296458.0   # DWG->模型坐标偏移 (build_structure_only_cad.py 权威)
STRUCT = ROOT/'projects/c_type_home/cad/structure_only_source_sync.dxf'
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# ---------- 1) 结构墙多边形 ----------
doc = ezdxf.readfile(STRUCT)
segs, polys = [], []
for e in doc.modelspace():
    if e.dxf.layer != 'S-S.WALL': continue
    if e.dxftype() == 'LINE':
        s, t = e.dxf.start, e.dxf.end
        segs.append(LineString([(s.x-AX, s.y-AY), (t.x-AX, t.y-AY)]))
    elif e.dxftype() == 'LWPOLYLINE':
        pts = [(p[0]-AX, p[1]-AY) for p in e.get_points('xy')]
        if len(pts) >= 3: polys.append(Polygon(pts))
        else: segs.append(LineString(pts))
    elif e.dxftype() == 'HATCH':
        for b in e.paths:
            try:
                pts = [(v[0]-AX, v[1]-AY) for v in b.vertices]
                if len(pts) >= 3: polys.append(Polygon(pts))
            except Exception: pass
rings = [p for p in polygonize(segs) if p.area > 1000]
struct_polys = unary_union(rings + [p for p in polys if p.area > 1000])
struct_parts = list(struct_polys.geoms) if hasattr(struct_polys,'geoms') else [struct_polys]
print(f'structural: {len(rings)} rings + {len(polys)} polys -> {len(struct_parts)} union parts')

def protection_ratio(poly):
    if poly.area < 1: return 0
    return poly.intersection(struct_polys).area / poly.area

# ---------- 2) FC 现状墙 → 保护等级 ----------
walls = []
for m in GEO['managed_entities']:
    if m['source'] != 'fcstd': continue
    for o in m['objects']:
        if not o.startswith(('W_','COL_')): continue
        for p in m['parts']:
            sp = Polygon(p['exterior'])
            r = protection_ratio(sp)
            cls = 'PROTECTED' if r > 0.6 else 'PARTIAL' if r > 0.1 else 'MODIFIABLE'
            walls.append({'object':o,'status':m['design_status'],'protection':cls,
                          'prot_ratio':round(r,3),'area':round(sp.area),
                          'bbox':p['exterior'] and [round(v) for v in sp.bounds]})
        if not m['parts']:
            for p in m.get('demolished_parts',[]):
                sp = Polygon(p)
                r = protection_ratio(sp)
                walls.append({'object':o,'status':m['design_status'],'protection':'DEMOL_PART',
                              'prot_ratio':round(r,3),'area':round(sp.area),
                              'bbox':[round(v) for v in sp.bounds]})
        break   # 每 spec 只查 primary

# ---------- 3) 拆除段 vs 保护墙 → 冲突 ----------
conflicts, demo_rows = [], []
for m in GEO['managed_entities']:
    for p in m.get('demolished_parts',[]):
        sp = Polygon(p); r = protection_ratio(sp)
        row = {'object':m['objects'][0],'decision':'D02','demo_area':round(sp.area),
               'prot_ratio':round(r,3),'bbox':[round(v) for v in sp.bounds]}
        demo_rows.append(row)
        if r > 0.1:
            conflicts.append({'type':'PROTECTED_WALL_DEMOLITION','object':m['objects'][0],
                'prot_ratio':round(r,3),'area':round(sp.area),'bbox':row['bbox'],
                'evidence':'demolished_parts ∩ S-S.WALL structural polygons',
                'recommendation':'BLOCK pending structural engineer review'})
# 设计新增墙压占保护墙?
fc_polys={}
for m in GEO['managed_entities']:
    if m['source']=='fcstd':
        for p in m['parts']:
            fc_polys.setdefault(m['objects'][0],[]).append(Polygon(p['exterior']))
for m in GEO['managed_entities']:
    if m['design_status'] != 'PROPOSED_NEW': continue
    for p in m['parts']:
        sp = Polygon(p['exterior'])
        # 与现状FC对象重合>0.7 → 现状墙体的设计模型副本, 非新增
        eq = any(sp.intersection(fp).area/sp.area > 0.7
                 for fps in fc_polys.values() for fp in fps)
        r = protection_ratio(sp)
        if r > 0.5 and not eq:
            conflicts.append({'type':'NEW_WALL_ON_PROTECTED','object':m['objects'][0],
                'prot_ratio':round(r,3),'bbox':[round(v) for v in sp.bounds],
                'evidence':'genuinely-new wall covers >50% of a structural wall polygon',
                'recommendation':'verify: 是替换/饰面还是覆盖误差'})

# ---------- 4) Blender 设计墙 → 与现状关系 ----------
design_rows = []
for m in GEO['managed_entities']:
    if m['source'] != 'blender': continue
    for p in m['parts']:
        sp = Polygon(p['exterior'])
        best, hit = 0, None
        for w in walls:
            wb = box(*w['bbox'])
            i = sp.intersection(wb).area / sp.area
            if i > best: best, hit = i, w['object']
        rel = 'NEW_NO_OVERLAP' if best < 0.2 else 'REPLACES_DEMOLISHED' \
              if hit and next((w2['status'] for w2 in walls if w2['object']==hit),'' )=='EXISTING_DEMOLISHED' \
              else 'OVERLAPS_RETAINED' if best>0.7 else 'PARTIAL_OVERLAP'
        design_rows.append({'object':m['objects'][0],'relation':rel,'overlap':round(best,3),
                            'matched_existing':hit,'bbox':[round(v) for v in sp.bounds]})
        break

# ---------- 5) 输出 ----------
summary = {
 'sources': {
   'developer_plan_dxf': {'file': str(ROOT/'projects/c_type_home/cad/C型_原始户型数字化基准图.dxf'),
     'sha256': sha(ROOT/'projects/c_type_home/cad/C型_原始户型数字化基准图.dxf'),
     'role': '原始基准图(黑墙=不可拆/白墙=可改造 的载体)'},
   'developer_plan_fcstd': {'file': str(ROOT/'projects/c_type_home/cad/C型_原始户型数字化基准模型.FCStd'),
     'sha256': sha(ROOT/'projects/c_type_home/cad/C型_原始户型数字化基准模型.FCStd'),
     'role': '现状对象几何权威(managed fcstd 来源)'},
   'measured_dxf': {'file': str(ROOT/'projects/c_type_home/cad/measured_working.dxf'),
     'sha256': sha(ROOT/'projects/c_type_home/cad/measured_working.dxf'),
     'role': '现状测绘底图(structure_only_source_sync 的父源)'},
   'structural_layer_dxf': {'file':str(STRUCT),'sha256':sha(STRUCT),'offset':[AX,AY],
     'structural_parts':len(struct_parts),'role':'S-S.WALL 结构/不可拆墙体层'},
   'design_blend': {'file': str(ROOT/'projects/vray_eval_v1/v15_house/V15_WORK.blend'),
     'sha256': sha(ROOT/'projects/vray_eval_v1/v15_house/V15_WORK.blend'),
     'role': '业主确认的最终设计目标(managed blender 来源)'},
   'geometry_snapshot': {'file':'derived/geometry_v05.json',
     'sha256': sha(CAD/'derived'/'geometry_v05.json'),
     'role': '本次映射消费的几何提取快照'}},
 'fc_wall_protection': {c:sum(1 for w in walls if w['protection']==c) for c in ('PROTECTED','PARTIAL','MODIFIABLE','DEMOL_PART')},
 'demolition_segments': demo_rows,
 'conflicts': conflicts,
 'design_relations': {r:sum(1 for d in design_rows if d['relation']==r)
                      for r in ('NEW_NO_OVERLAP','REPLACES_DEMOLISHED','OVERLAPS_RETAINED','PARTIAL_OVERLAP')},
 'coverage_anomalies':[{'object':w['object'],'note':'large wall with 0% structural coverage — coordinate or semantic gap',
                        'bbox':w['bbox']} for w in walls if w['prot_ratio']==0 and w['area']>800000],
 'verdict': 'BLOCK' if any(c['type']=='PROTECTED_WALL_DEMOLITION' for c in conflicts) else 'PASS_WITH_HOLDS'}
(CAD/'derived'/'three_source_mapping.json').write_text(
    json.dumps({'walls':walls,'design':design_rows,'summary':summary},ensure_ascii=False,indent=1))
print(json.dumps(summary,ensure_ascii=False,indent=1))
