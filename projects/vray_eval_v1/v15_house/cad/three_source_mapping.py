#!/usr/bin/env python3
"""三源对象映射 v2 (P1.4.1): 开发商结构层 + 现状对象 + 设计目标
修复: 未闭合 LWPOLYLINE 不得隐式闭合成面; HATCH 边界正确解析含孔洞;
      LINE 线网仅在形成真实闭合环时 polygonize; 大面/三角/自交异常剔除;
      未被结构层覆盖 != 可拆, 外墙/柱默认 ENVELOPE_REVIEW."""
import json, hashlib, math
from pathlib import Path
import ezdxf
from shapely.geometry import Polygon, MultiPolygon, LineString, box
from shapely.ops import unary_union, polygonize
from shapely.validation import make_valid

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
AX, AY = 1298172.0, -296458.0   # DWG->模型坐标偏移 (build_structure_only_cad.py 权威)
STRUCT = ROOT/'projects/c_type_home/cad/structure_only_source_sync.dxf'
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# ---------- 几何异常判定 ----------
def ring_to_poly(pts, handle, kind):
    """合法闭合点列 -> (Polygon, anomaly_or_None). 不合法 -> (None, anomaly)."""
    if len(pts) < 3:
        return None, {'handle':handle,'kind':kind,'reason':'DEGENERATE_<3PTS'}
    try:
        p = Polygon(pts)
    except Exception as ex:
        return None, {'handle':handle,'kind':kind,'reason':f'RING_FAIL:{ex}'}
    if not p.is_valid:
        p2 = make_valid(p)
        good = [g for g in (p2.geoms if hasattr(p2,'geoms') else [p2])
                if g.geom_type=='Polygon' and g.area>1000]
        if not good:
            return None, {'handle':handle,'kind':kind,'reason':'SELF_INTERSECT_UNREPAIRABLE'}
        return good[0] if len(good)==1 else MultiPolygon(good), \
               {'handle':handle,'kind':kind,'reason':'SELF_INTERSECT_REPAIRED'}
    return p, None

def face_anomaly(poly, handle, src):
    """跨房间大面/可疑三角: 最小旋转矩形短边>1200mm 且面积>2e6 mm² -> 非墙."""
    mrr = poly.minimum_rotated_rectangle
    xs=[c[0] for c in mrr.exterior.coords]; ys=[c[1] for c in mrr.exterior.coords]
    dx=max(xs)-min(xs); dy=max(ys)-min(ys)
    short = min(math.hypot(xs[1]-xs[0],ys[1]-ys[0]),
                math.hypot(xs[2]-xs[1],ys[2]-ys[1]))
    n_vert = len(poly.exterior.coords)-1
    if short > 1200 and poly.area > 2_000_000:
        return {'handle':handle,'kind':src,'reason':'LARGE_FACE_NOT_WALL',
                'area':round(poly.area),'short_side_mm':round(short)}
    if n_vert <= 4 and short > 800 and poly.area > 1_500_000:
        return {'handle':handle,'kind':src,'reason':'SUSPECT_TRIANGLE',
                'area':round(poly.area),'short_side_mm':round(short)}
    return None

# ---------- 结构层提取 (可独立测试的纯函数) ----------
def extract_structural(msp, layer='S-S.WALL'):
    """返回 dict(polys=[(geom,handle,kind)], anomalies=[...], open_polylines=[...],
                stats={...}). 开放折线只贡献真实边段到线网, 绝不补边."""
    segs, polys, anomalies, open_lw = [], [], [], []
    n = {'line':0,'lw_closed':0,'lw_open':0,'hatch':0,'hatch_rings':0}
    for e in msp:
        if e.dxf.layer != layer: continue
        t = e.dxftype()
        if t == 'LINE':
            n['line'] += 1
            s, tt = e.dxf.start, e.dxf.end
            segs.append(LineString([(s.x-AX,s.y-AY),(tt.x-AX,tt.y-AY)]))
        elif t == 'LWPOLYLINE':
            pts = [(p[0]-AX,p[1]-AY) for p in e.get_points('xy')]
            if e.closed and len(pts) >= 3:
                n['lw_closed'] += 1
                p, an = ring_to_poly(pts, e.dxf.handle, 'LWP_CLOSED')
                if p is not None:
                    faces = p.geoms if p.geom_type=='MultiPolygon' else [p]
                    for f in faces:
                        fa = face_anomaly(f, e.dxf.handle, 'LWP_CLOSED')
                        (anomalies.append(fa) if fa else polys.append((f,e.dxf.handle,'LWP_CLOSED')))
                if an: anomalies.append(an)
            else:
                n['lw_open'] += 1
                open_lw.append({'handle':e.dxf.handle,'n_pts':len(pts),
                                'gap_mm':round(math.hypot(pts[0][0]-pts[-1][0],
                                            pts[0][1]-pts[-1][1])) if len(pts)>1 else 0,
                                'bbox':[round(min(q[0] for q in pts)),round(min(q[1] for q in pts)),
                                        round(max(q[0] for q in pts)),round(max(q[1] for q in pts))]})
                for i in range(len(pts)-1):   # 只贡献真实边, 不补首尾
                    segs.append(LineString([pts[i],pts[i+1]]))
        elif t == 'HATCH':
            n['hatch'] += 1
            rings = []
            for p in e.paths:
                n['hatch_rings'] += 1
                if type(p).__name__ == 'PolylinePath':
                    pts = [(v[0]-AX,v[1]-AY) for v in p.vertices]
                    if p.is_closed and len(pts) >= 3:
                        rings.append(pts)
                    else:   # hatch 未闭合路径 -> 边段入网
                        for i in range(len(pts)-1):
                            segs.append(LineString([pts[i],pts[i+1]]))
                else:  # EdgePath: 每条LineEdge进线网; 链连续且首尾闭合才成环
                    chain, cont, linear = [], True, True
                    for ed in p.edges:
                        if ed.EDGE_TYPE != 'LineEdge':
                            linear = False; continue
                        st = (ed.start[0]-AX, ed.start[1]-AY)
                        en = (ed.end[0]-AX, ed.end[1]-AY)
                        segs.append(LineString([st, en]))
                        if chain and math.hypot(st[0]-chain[-1][0],
                                                st[1]-chain[-1][1]) > 1:
                            cont = False
                        if not chain: chain.append(st)
                        chain.append(en)
                    if linear and cont and len(chain) >= 3 and \
                       math.hypot(chain[0][0]-chain[-1][0],
                                  chain[0][1]-chain[-1][1]) < 1:
                        rings.append(chain[:-1])
                    else:
                        anomalies.append({'handle':e.dxf.handle,'kind':'HATCH_EDGE',
                            'reason':'NONLINEAR_EDGE' if not linear
                                     else 'OPEN_EDGEPATH'})
            # 奇偶嵌套判定孔洞
            rpolys = []
            for r in rings:
                p, an = ring_to_poly(r, e.dxf.handle, 'HATCH_RING')
                if an: anomalies.append(an)
                if p is not None and p.geom_type=='Polygon': rpolys.append(p)
            rpolys.sort(key=lambda g: g.area, reverse=True)
            holes_of = {}   # outer_idx -> [inner_rings]
            for i, g in enumerate(rpolys):
                depth = sum(1 for h in rpolys if h is not g and h.contains(g))
                if depth % 2 == 1:   # 奇数深度=孔, 找最小偶数深度容器
                    for j in sorted(range(len(rpolys)),
                                    key=lambda j: rpolys[j].area):
                        h = rpolys[j]
                        dj = sum(1 for k in rpolys if k is not h and k.contains(h))
                        if dj % 2 == 0 and h.contains(g):
                            holes_of.setdefault(j, []).append(g); break
            for i, g in enumerate(rpolys):
                depth = sum(1 for h in rpolys if h is not g and h.contains(g))
                if depth % 2 == 0:
                    hs = holes_of.get(i, [])
                    face = Polygon(g.exterior.coords,
                                   [h.exterior.coords for h in hs]) if hs else g
                    if not face.is_valid: face = make_valid(face)
                    if face.geom_type == 'MultiPolygon':
                        face = max(face.geoms, key=lambda x: x.area)
                    if hs:
                        anomalies.append({'handle':e.dxf.handle,'kind':'HATCH',
                            'reason':'HOLES_SUBTRACTED','n_holes':len(hs)})
                    fa = face_anomaly(face, e.dxf.handle, 'HATCH')
                    (anomalies.append(fa) if fa else polys.append((face,e.dxf.handle,'HATCH')))
    faces = [f for f in polygonize(segs)]
    n['line_faces_raw'] = len(faces)
    for f in faces:
        fa = face_anomaly(f, 'LINE_NET', 'LINE_RING')
        if fa: anomalies.append(fa); continue
        if f.area > 1000: polys.append((f,'LINE_NET','LINE_RING'))
    u = unary_union([g for g,_,_ in polys])
    parts = list(u.geoms) if hasattr(u,'geoms') else [u]
    parts = [p for p in parts if p.area > 1000]
    return {'polys':polys,'union':unary_union(parts),'parts':parts,
            'anomalies':anomalies,'open_polylines':open_lw,'stats':n}

# ---------- 旧算法(对比用): 所有>=3点折线强行闭合 ----------
def legacy_structural(msp):
    segs, polys = [], []
    for e in msp:
        if e.dxf.layer != 'S-S.WALL': continue
        if e.dxftype() == 'LINE':
            s,t = e.dxf.start, e.dxf.end
            segs.append(LineString([(s.x-AX,s.y-AY),(t.x-AX,t.y-AY)]))
        elif e.dxftype() == 'LWPOLYLINE':
            pts = [(p[0]-AX,p[1]-AY) for p in e.get_points('xy')]
            if len(pts) >= 3: polys.append(Polygon(pts))
            else: segs.append(LineString(pts))
        elif e.dxftype() == 'HATCH':
            for b in e.paths:
                try:
                    pts = [(v[0]-AX,v[1]-AY) for v in b.vertices]
                    if len(pts) >= 3: polys.append(Polygon(pts))
                except Exception: pass
    return unary_union([p for p in polygonize(segs) if p.area>1000]
                       + [p for p in polys if p.area>1000])

if __name__ == '__main__':
    doc = ezdxf.readfile(STRUCT)
    ext = extract_structural(doc.modelspace())
    legacy = legacy_structural(doc.modelspace())
    struct_polys = ext['union']
    print(f"structural: {ext['stats']} -> {len(ext['parts'])} union parts"
          f" | anomalies={len(ext['anomalies'])} open_lw={len(ext['open_polylines'])}")

    def ratio(poly, u): return 0 if poly.area < 1 else poly.intersection(u).area/poly.area
    protection_ratio = lambda p: ratio(p, struct_polys)
    legacy_ratio     = lambda p: ratio(p, legacy)

    def classify(o, r):
        if r > 0.6: return 'STRUCT_MARKED'
        if r > 0.1: return 'STRUCT_PARTIAL'
        if o.startswith(('W_EXT','W_BALC','W_BAY','COL_')): return 'ENVELOPE_REVIEW'
        return 'UNMARKED_INTERIOR'

    walls = []
    for m in GEO['managed_entities']:
        if m['source'] != 'fcstd': continue
        for o in m['objects']:
            if not o.startswith(('W_','COL_')): continue
            for p in m['parts']:
                sp = Polygon(p['exterior'])
                r, lr = protection_ratio(sp), legacy_ratio(sp)
                walls.append({'object':o,'status':m['design_status'],
                              'protection':classify(o,r),'prot_ratio':round(r,3),
                              'prot_ratio_legacy':round(lr,3),'area':round(sp.area),
                              'bbox':[round(v) for v in sp.bounds]})
            if not m['parts']:
                for p in m.get('demolished_parts',[]):
                    sp = Polygon(p)
                    r, lr = protection_ratio(sp), legacy_ratio(sp)
                    walls.append({'object':o,'status':m['design_status'],
                                  'protection':'DEMOL_PART','prot_ratio':round(r,3),
                                  'prot_ratio_legacy':round(lr,3),'area':round(sp.area),
                                  'bbox':[round(v) for v in sp.bounds]})
            break

    conflicts, demo_rows = [], []
    for m in GEO['managed_entities']:
        for p in m.get('demolished_parts',[]):
            sp = Polygon(p)
            r, lr = protection_ratio(sp), legacy_ratio(sp)
            demo_rows.append({'object':m['objects'][0],'decision':m.get('decision',''),
                              'demo_area':round(sp.area),'prot_ratio':round(r,3),
                              'prot_ratio_legacy':round(lr,3),
                              'bbox':[round(v) for v in sp.bounds]})
            if r > 0.5:
                conflicts.append({'type':'PROTECTED_WALL_DEMOLITION','object':m['objects'][0],
                    'prot_ratio':round(r,3),'bbox':[round(v) for v in sp.bounds],
                    'evidence':'demolished part covers >50% of VALIDATED structural fill',
                    'recommendation':'BLOCK until structural verification'})

    fc_polys = {}
    for m in GEO['managed_entities']:
        if m['source'] == 'fcstd':
            for p in m['parts']:
                fc_polys.setdefault(m['objects'][0],[]).append(Polygon(p['exterior']))
    for m in GEO['managed_entities']:
        if m['design_status'] != 'PROPOSED_NEW': continue
        for p in m['parts']:
            sp = Polygon(p['exterior'])
            eq = any(sp.intersection(fp).area/sp.area > 0.7
                     for fps in fc_polys.values() for fp in fps)
            r = protection_ratio(sp)
            if r > 0.5 and not eq:
                conflicts.append({'type':'NEW_WALL_ON_PROTECTED','object':m['objects'][0],
                    'prot_ratio':round(r,3),'prot_ratio_legacy':round(legacy_ratio(sp),3),
                    'bbox':[round(v) for v in sp.bounds],
                    'evidence':'genuinely-new wall covers >50% of VALIDATED structural fill',
                    'recommendation':'verify: 是替换/饰面还是覆盖误差'})

    design_rows = []
    for m in GEO['managed_entities']:
        if m['source'] != 'blender': continue
        for p in m['parts']:
            sp = Polygon(p['exterior'])
            best, hit = 0, None
            for w in walls:
                wb = box(*w['bbox'])
                i = sp.intersection(wb).area/sp.area
                if i > best: best, hit = i, w['object']
            rel = 'NEW_NO_OVERLAP' if best < 0.2 else 'REPLACES_DEMOLISHED' \
                  if hit and next((w2['status'] for w2 in walls if w2['object']==hit),'')=='EXISTING_DEMOLISHED' \
                  else 'OVERLAPS_RETAINED' if best>0.7 else 'PARTIAL_OVERLAP'
            design_rows.append({'object':m['objects'][0],'relation':rel,'overlap':round(best,3),
                                'matched_existing':hit,'bbox':[round(v) for v in sp.bounds]})
            break

    summary = {
     'algorithm': 'P1.4.1 — closed-boundary-only structural extraction',
     'sources': {
       'developer_plan_dxf': {'file': str(ROOT/'projects/c_type_home/cad/C型_原始户型数字化基准图.dxf'),
         'sha256': sha(ROOT/'projects/c_type_home/cad/C型_原始户型数字化基准图.dxf'),
         'role': '原始基准图(A-WALL/A-UNCERTAIN层, 无黑白墙分类字段)'},
       'developer_plan_fcstd': {'file': str(ROOT/'projects/c_type_home/cad/C型_原始户型数字化基准模型.FCStd'),
         'sha256': sha(ROOT/'projects/c_type_home/cad/C型_原始户型数字化基准模型.FCStd'),
         'role': '现状对象几何权威(managed fcstd 来源)'},
       'measured_dxf': {'file': str(ROOT/'projects/c_type_home/cad/measured_working.dxf'),
         'sha256': sha(ROOT/'projects/c_type_home/cad/measured_working.dxf'),
         'role': '现状测绘底图(structure_only_source_sync 的父源)'},
       'structural_layer_dxf': {'file':str(STRUCT),'sha256':sha(STRUCT),'offset':[AX,AY],
         'structural_parts':len(ext['parts']),'role':'S-S.WALL 结构层(HATCH填充=最强证据)'},
       'design_blend': {'file': str(ROOT/'projects/vray_eval_v1/v15_house/V15_WORK.blend'),
         'sha256': sha(ROOT/'projects/vray_eval_v1/v15_house/V15_WORK.blend'),
         'role': '业主确认的最终设计目标(managed blender 来源)'},
       'geometry_snapshot': {'file':'derived/geometry_v05.json',
         'sha256': sha(CAD/'derived'/'geometry_v05.json'),
         'role': '本次映射消费的几何提取快照'}},
     'extraction': {'stats':ext['stats'],'anomalies':ext['anomalies'],
                    'open_polylines':ext['open_polylines']},
     'fc_wall_protection': {c:sum(1 for w in walls if w['protection']==c)
                            for c in ('STRUCT_MARKED','STRUCT_PARTIAL','UNMARKED_INTERIOR','ENVELOPE_REVIEW','DEMOL_PART')},
     'demolition_segments': demo_rows,
     'conflicts': conflicts,
     'design_relations': {r:sum(1 for d in design_rows if d['relation']==r)
                          for r in ('NEW_NO_OVERLAP','REPLACES_DEMOLISHED','OVERLAPS_RETAINED','PARTIAL_OVERLAP')},
     'coverage_anomalies':[{'object':w['object'],'note':'large wall with 0% structural coverage — coordinate or semantic gap',
                            'bbox':w['bbox']} for w in walls if w['prot_ratio']==0 and w['area']>800000],
     'semantic_limits': [
       'S-S.WALL 来源于现状测绘同步件, 非开发商原图黑白墙字段的直接载体',
       '基准DXF仅有A-WALL/A-UNCERTAIN层, 无受保护/可改造分类数据',
       '未覆盖结构层 -> ENVELOPE_REVIEW(外墙/柱)或UNMARKED_INTERIOR(内墙), 不自动等于可拆',
       'HATCH填充=最强结构证据, LINE/LWP环=次级证据, 开放折线仅贡献边段'],
     'verdict': 'BLOCK' if any(c['type']=='PROTECTED_WALL_DEMOLITION' for c in conflicts)
                else 'HOLD_PENDING_STRUCTURE_VERIFY'}
    (CAD/'derived'/'three_source_mapping.json').write_text(
        json.dumps({'walls':walls,'design':design_rows,'summary':summary},ensure_ascii=False,indent=1))
    print(json.dumps({k:summary[k] for k in ('fc_wall_protection','conflicts','verdict')},
                     ensure_ascii=False,indent=1))
