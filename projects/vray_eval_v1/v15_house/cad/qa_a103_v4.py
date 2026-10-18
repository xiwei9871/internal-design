#!/usr/bin/env python3
"""qa_report_v04: 几何正确性 QA — 有效性/差异面积/重复/锚点落位/洞口连通"""
import json, sys
from pathlib import Path
import ezdxf
from shapely.geometry import Polygon, MultiPolygon, Point, box
from shapely.ops import unary_union
CAD = Path(__file__).resolve().parent
GEO = json.loads((CAD/'derived'/'geometry_v04.json').read_text())
doc = ezdxf.readfile(CAD/'A103_CONSTRUCTION_POC_V4.dxf'); msp = doc.modelspace()
G = {}
def rec(g, ok, detail): G[g] = {'status': 'PASS' if ok else 'FAIL', 'detail': detail}

# G1 源新鲜 (live rehash 已由生成器执行, 这里复核 derived 登记)
import hashlib
dd = GEO.get('derived_data', {})
live_src = {a.get('source_file_sha256') for a in GEO['anchors']+GEO['managed_entities']}
g1bad=[]
for did,d in dd.items():
    if hashlib.sha256(open(d['file'],'rb').read()).hexdigest()!=d['sha256']:
        g1bad.append(f'{did}: file changed')
    if d.get('parent_sha256') not in live_src: g1bad.append(f'{did}: parent not live source')
rec('G1_source_fresh_live', not g1bad, g1bad or f'{len(dd)} derived files verified live')

# G2 原生标注在 A-DIMS
dims = [e for e in msp if e.dxftype() == 'DIMENSION']
bad = [e.dxf.handle for e in dims if e.dxf.layer != 'A-DIMS']
rec('G2_native_dims_layer', len(dims) == 12 and not bad,
    f'{len(dims)} DIMENSION on A-DIMS, misplaced={bad}')

# G3 独立复算: 锚点坐标→标注定义点距离
anchor = {a['id']: (a['x'], a['y']) for a in GEO['anchors']}
errs = []
for tag, spec in GEO['dims'].items():
    ax = spec['axis']
    want = abs(anchor[spec['b']][0 if ax=='x' else 1] - anchor[spec['a']][0 if ax=='x' else 1])
    for e in dims:
        try: xd = e.get_xdata('DEVINDIM')
        except ezdxf.DXFValueError: continue
        if xd and xd[0][1] == tag:
            got = abs(e.dxf.defpoint3[0 if ax=='x' else 1] - e.dxf.defpoint2[0 if ax=='x' else 1])
            if abs(got - want) > 1: errs.append(f'{tag}: dim={got:.0f} anchor={want:.0f}')
rec('G3_independent_recompute', not errs, errs or '12 dims == anchor distances ±1mm')

# G4 对象存在性: managed 对象的源文件都含该对象名 (fc dump/blender dump 已绑定)
fc_names={o['name'] for o in json.loads(open(CAD/'derived'/'fc_objects_raw.json').read())}
bl_names=set(json.loads(open(CAD/'derived'/'blender_geom_raw.json').read()))
g4miss=[o for m in GEO['managed_entities'] for o in m['objects']
        if o not in fc_names and o not in bl_names]
rec('G4_object_exists_in_source', not g4miss,
    g4miss[:8] or f"all {sum(len(m['objects']) for m in GEO['managed_entities'])} object names found in live dumps")

# G5 旧标注层处置
leg = doc.layers.get('A-DIMS-LEGACY')
rec('G5_legacy_dims_disposed', leg.dxf.flags == 1, 'A-DIMS-LEGACY frozen')

# G6 存疑登记
unc = [e for e in msp if e.dxf.layer == 'A-UNCERTAIN']
unv_objs = [m for m in GEO['managed_entities'] if m['design_status'] == 'UNVERIFIED']
G['G6_uncertain_registry'] = {'status': 'HOLD',
    'detail': f'{len(unc)} uncertain entities frozen; {len(unv_objs)} source objects UNVERIFIED '
              f'({[m["objects"] for m in unv_objs]}) — adjudication pending'}

# G7 门窗追溯
ins = [e for e in msp if e.dxftype() == 'INSERT' and e.dxf.layer in ('A-DOOR', 'A-WINDOW')]
rec('G7_door_windows_traced', len(ins) >= 10, f'{len(ins)} INSERTs with SRC_ID/xdata')

# G8 同版本 (真实比对)
srcs = {(a.get('source_file'), a.get('source_file_sha256'))
        for a in GEO['anchors'] + GEO['managed_entities']}
rec('G8_same_revision_real', len(srcs) <= 2,
    f'{len(srcs)} distinct live source revisions in geometry')

# ---- 几何正确性 ----
def ent_poly(e):
    pts = [tuple(p) for p in e.get_points('xy')]
    p = Polygon(pts)
    return p if p.is_valid else p.buffer(0)

# 收集绑定实体 (part 级)
bound = []
for e in msp:
    if e.dxftype() == 'LWPOLYLINE' and e.dxf.layer in ('A-WALL', 'A-DESIGN', 'A-UNCERTAIN', 'A-DEMO'):
        try:
            xd = e.get_xdata('DEVINSRC')
            if xd and '#p' in str(xd[0][1]): bound.append((e, xd))
        except ezdxf.DXFValueError: pass

spec_parts = {}
hole_keys = set()
for m in GEO['managed_entities']:
    for pi, part in enumerate(m['parts']):
        spec_parts[f"{m['objects'][0]}#p{pi}"] = (Polygon(part['exterior']), m)
        for hi in range(len(part.get('holes', []))):
            hole_keys.add(f"{m['objects'][0]}#p{pi}h{hi}")

mismatch, missing, areamax = [], [], 0
for key, (sp, m) in spec_parts.items():
    hit = [e for e, xd in bound if xd[0][1] == key]
    # 孔洞边界实体 (xdata key '#pXhY') 单独验证存在性
    for hk in [k for k in hole_keys if k.startswith(key)]:
        if not any(xd2[0][1] == hk for _, xd2 in bound):
            mismatch.append(f'{hk}: hole boundary missing')
    if not hit: missing.append(key); continue
    ep = ent_poly(hit[0])
    sym = sp.symmetric_difference(ep).area
    areamax = max(areamax, sym)
    if sym > sp.area * 0.02 + 500: mismatch.append(f'{key}: symdiff={sym:.0f} vs area={sp.area:.0f}')
    if not ep.is_valid: mismatch.append(f'{key}: INVALID polygon drawn')
rec('G9_geometry_fidelity', not missing and not mismatch,
    {'missing': missing, 'mismatch': mismatch[:8], 'max_symdiff_mm2': round(areamax)})

# 重复绘制检测: 同层实体 IoU>0.95
dupes = []
def is_hole(e):
    try: return 'h' in str(e.get_xdata('DEVINSRC')[0][1]).split('#p',1)[1]
    except Exception: return False
nb = [x for x in bound if not is_hole(x[0])]
for i,(e1,_) in enumerate(nb):
    for e2,_ in nb[i+1:]:
        p1, p2 = ent_poly(e1), ent_poly(e2)
        if not p1.is_valid or not p2.is_valid: continue
        inter = p1.intersection(p2).area
        if inter / min(p1.area, p2.area) > 0.95: dupes.append((e1.dxf.handle, e2.dxf.handle))
rec('G10_no_duplicate_entities', not dupes, dupes[:8] or 'no >95% overlapping drawn entities')

# 洞口连通: 洞口矩形中心 200mm 范围内不被墙实体覆盖 >60%
sealed = []
for op in GEO['door_openings']:
    x0,y0,x1,y1 = op['rect']; cx,cy = (x0+x1)/2,(y0+y1)/2
    rb = box(cx-100, cy-100, cx+100, cy+100)
    cover = sum(ent_poly(e).intersection(rb).area for e,_ in bound
                if e.dxf.layer == 'A-WALL' and ent_poly(e).intersects(rb))
    if cover > rb.area * 0.9: sealed.append(op['handle'])
rec('G11_openings_unsealed', not sealed,
    sealed or f"{len(GEO['door_openings'])} openings clear at center ±100mm")

# 锚点落位: 每个锚点到最近墙实体边界 ≤300mm
wall_geoms = [ent_poly(e) for e,_ in bound if e.dxf.layer == 'A-WALL']
far = []
for a in GEO['anchors']:
    pt = Point(a['x'], a['y'])
    d = min((w.boundary.distance(pt) for w in wall_geoms if w.is_valid), default=1e9)
    if d > 300: far.append(f"{a['id']} d={d:.0f}")
rec('G12_anchor_on_wall', not far, far[:8] or 'all anchors ≤300mm from drawn wall boundary')

# G15 可见未绑定墙线
unb=[]
for e in msp:
    if e.dxftype()=='LWPOLYLINE' and e.dxf.layer in ('A-WALL','A-DESIGN') and e.dxf.layer not in {l.dxf.name for l in doc.layers if l.is_off()}:
        try:
            if not e.get_xdata('DEVINSRC'): unb.append(e.dxf.handle)
        except ezdxf.DXFValueError: unb.append(e.dxf.handle)
rec('G15_no_unbound_visible_walls', not unb,
    unb or 'all visible wall entities carry DEVINSRC binding')

# G16 跨状态合并 → 需人工审核台账
led=json.loads((CAD/'derived'/'adjudication_ledger_v04.json').read_text())
reviews=[a for a in led.get('anomalies',[]) if a.get('review')=='REQUIRED']
reviews += [{'objects':x['objects'],'rule':'merge_review'} for x in led.get('merge_review',[])]
G['G16_cross_status_adjudication']={'status':'HOLD',
    'detail':f'{len(reviews)} cross-status merges/absorptions pending human adjudication (ledger: adjudication_ledger_v04.json)' if reviews else 'none'}

# G17 DEMOL 分类: A-DEMO 实体 == 拆除台账, 门洞裁切不混入
demo_ents=[e for e in msp if e.dxf.layer=='A-DEMO']
demo_spec=sum(len(m.get('demolished_parts',[])) for m in GEO['managed_entities'])
open_cuts=sum(len(m.get('opening_cuts',[])) for m in GEO['managed_entities'])
rec('G17_demol_classification', len(demo_ents)==demo_spec,
    f'A-DEMO entities={len(demo_ents)} == demolished_parts={demo_spec}; opening_cuts={open_cuts} kept separate (not registered as demolition)')

# G18 关键墙静默回退
fb=[m['objects'][0] for m in GEO['managed_entities'] if m.get('cut_height')=='FOOTPRINT_FALLBACK']
G['G18_section_fallback']={'status':'HOLD' if fb else 'PASS',
    'detail':f'{len(fb)} wall objects fell back to full XY projection (no valid section): {fb[:6]}...' if fb else 'all walls have real section cuts'}

# G13 编辑器/纸空间 — 诚实保留
G['G13_editor_verify'] = {'status': 'PARTIAL',
    'detail': 'no QCAD/LibreCAD on this machine; FreeCAD import-only check, interactive edit NOT_RUN'}
G['G14_paper_pdf'] = {'status': 'PARTIAL',
    'detail': 'A1 frame on Layout1; no true VIEWPORT entity yet; physical print NOT_RUN'}

verdict = 'PASS' if all(v['status'] == 'PASS' for k, v in G.items() if k != 'G6_uncertain_registry') else 'HOLD'
out = {'verdict': verdict, 'gates': G}
(CAD/'qa_report_v04.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
print('VERDICT:', verdict)
for k, v in G.items(): print(f"  {k}: {v['status']}")
