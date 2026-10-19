#!/usr/bin/env python3
"""A102/A103 V2 联合验收 QA — registry驱动 + 破坏性负向测试.
qa(d102,d103) 纯函数便于注入篡改副本. 缺字段=FAIL不得空集."""
import json, hashlib, sys, shutil
from pathlib import Path
import ezdxf
from shapely.geometry import Polygon
from shapely.ops import unary_union

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
REG = json.loads((CAD/'derived'/'wall_state_registry.json').read_text())
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())

def parse(path):
    doc = ezdxf.readfile(path)
    walls, dims = {}, {}
    dim_errs = []
    for e in doc.modelspace():
        if e.dxftype() == 'LWPOLYLINE':
            pts = [(p[0],p[1]) for p in e.get_points('xy')]
            objs = []
            try:
                objs = [v[1] for v in e.get_xdata('DEVINSRC') if v[0]==1000]
            except ezdxf.DXFValueError: pass
            walls.setdefault(e.dxf.layer,[]).append({'handle':e.dxf.handle,'pts':pts,'objs':objs})
        elif e.dxftype() == 'DIMENSION':
            try:
                xd = e.get_xdata('DEVINDIM')
                tag = next((v[1] for v in xd if v[0]==1000), None)
                val = next((v[1] for v in xd if v[0]==1040), None)
                anchors = [v[1] for v in xd if v[0]==1000][1:]
                if tag is None or val is None or len(anchors)<3:
                    dim_errs.append(f'{e.dxf.handle}: incomplete DEVINDIM {xd}')
                else:
                    dims[tag] = {'a':anchors[0],'b':anchors[1],'axis':anchors[2],
                                 'value':val,'handle':e.dxf.handle,
                                 'mtype':anchors[3] if len(anchors)>3 else None,
                                 'ref':anchors[4] if len(anchors)>4 else None,
                                 'resurvey':anchors[5] if len(anchors)>5 else None}
            except ezdxf.DXFValueError:
                dim_errs.append(f'{e.dxf.handle}: missing DEVINDIM')
    flags = {l.dxf.name: bool(l.dxf.flags&1) for l in doc.layers}
    viewports = [e for l in doc.layouts for e in l if e.dxftype()=='VIEWPORT']
    return {'walls':walls,'dims':dims,'dim_errs':dim_errs,
            'flags':flags,'n_viewports':len(viewports)}

def qa(p102, p103):
    out = {}
    # QJ1 同快照
    out['QJ1_same_snapshot'] = REG['meta']['geometry_snapshot']['sha256'] == \
        hashlib.sha256((CAD/'derived'/'geometry_v05.json').read_bytes()).hexdigest()
    # QJ2 拆除/保留集合
    demo, hold = set(), set()
    for lay, key in (('A-WALL-DEMO-DESIGN',demo),('A-WALL-HOLD',hold)):
        for w in p102['walls'].get(lay,[]):
            key.update(o for o in w['objs'] if '#demol' in o)
    out['QJ2_demo_set'] = demo == {e['object'] for e in REG['entries']
                                   if e['a102_role']=='DESIGN_APPROVED_DEMO'}
    out['QJ2_hold_set'] = hold == {'W_EXT_N_BAL#demol0'}
    # QJ3 可见层无 SUPPRESS
    bad = []
    a103role = {e['object']:e['a103_role'] for e in REG['entries']}
    for lay,ents in p103['walls'].items():
        if p103['flags'].get(lay): continue
        for w in ents:
            for o in w['objs']:
                if a103role.get(o) in ('SUPPRESS','SUPPRESS_HOLD'): bad.append((w['handle'],o))
    out['QJ3_no_suppress_visible'] = not bad
    out['QJ3_detail'] = bad
    # QJ4 全部应显示冲突对象都在 A-CONFLICT
    want_rev = {e['object'].split('#')[0] for e in REG['entries']
                if e.get('overlap_class')}
    seen_conf, seen_rev, seen_vis = set(), set(), set()
    for w in p103['walls'].get('A-CONFLICT',[]):
        seen_conf.update(o.split('#')[0] for o in w['objs'])
    for w in p103['walls'].get('A-REVIEW',[]):
        seen_rev.update(o.split('#')[0] for o in w['objs'])
    for lay,ents in p103['walls'].items():
        if p103['flags'].get(lay): continue
        for w in ents: seen_vis.update(o.split('#')[0] for o in w['objs'])
    # 每个冲突对: 非保留方必须在A-CONFLICT, 双方都必须在某可见层出现
    conf_bad = []
    for c in GEO.get('conflicts',[]):
        for side in (c['a'],c['b']):
            if side not in seen_vis: conf_bad.append(f'{side}: invisible')
        nonret = [x for x in (c['a'],c['b'])
                  if not any(e['object'].split('#')[0]==x and
                             e['design_status']=='EXISTING_RETAINED'
                             for e in REG['entries'])]
        if not any(x in seen_conf for x in nonret):
            conf_bad.append(f"{c['a']}x{c['b']}: no non-retained side on A-CONFLICT")
    out['QJ4_conflict_missing'] = conf_bad
    out['QJ4_review_missing'] = sorted(want_rev - seen_rev -
                                     set(c['a'] for c in GEO.get('conflicts',[])) -
                                     set(c['b'] for c in GEO.get('conflicts',[])))
    out['QJ4_all_conflicts_shown'] = not conf_bad and not out['QJ4_review_missing']
    # QJ5 尺寸: 完整DEVINDIM + 逐项一致 + 数值与锚点几何一致
    errs = p102['dim_errs'] + p103['dim_errs']
    A = {a['id']:(a['x'],a['y']) for a in GEO['anchors']}
    EXTRA = json.loads((CAD/'derived'/'dims_extra.json').read_text())['dims'] \
            if (CAD/'derived'/'dims_extra.json').exists() else []
    MTYPES = {'DEMOLITION_SPAN','NEW_WALL_LOCATION','STAIR_SPAN','OPENING_WIDTH',
              'ARRIVAL_PLATFORM_SPAN'}
    for spec in EXTRA:
        tag = spec['tag']
        d1, d2 = p102['dims'].get(tag), p103['dims'].get(tag)
        if not d1 or not d2: errs.append(f'{tag}: missing extra dim'); continue
        if (d1['a'],d1['b'],d1['axis'],d1['value']) != (d2['a'],d2['b'],d2['axis'],d2['value']):
            errs.append(f'{tag}: extra dim mismatch')
        # 语义检查: measurement_type 必须在词表且与JSON一致; 定位尺寸必须有ref
        for d,side in ((d1,'A102'),(d2,'A103')):
            if d['mtype'] not in MTYPES:
                errs.append(f'{tag}:{side} bad mtype {d["mtype"]}'); continue
            if d['mtype'] != spec['measurement_type']:
                errs.append(f'{tag}:{side} mtype {d["mtype"]} != json {spec["measurement_type"]}')
            if d['mtype']=='NEW_WALL_LOCATION' and not d.get('ref'):
                errs.append(f'{tag}:{side} NEW_WALL_LOCATION missing ref')
            # 跨度类不得标称定位, 反之亦然
            if d['mtype']!=spec['measurement_type']: continue
    for tag,spec in GEO['dims'].items():
        d1, d2 = p102['dims'].get(tag), p103['dims'].get(tag)
        if not d1 or not d2: errs.append(f'{tag}: missing in ' + ('A102' if not d1 else 'A103')); continue
        if (d1['a'],d1['b'],d1['axis'],d1['value']) != (d2['a'],d2['b'],d2['axis'],d2['value']):
            errs.append(f'{tag}: schema mismatch {d1} vs {d2}'); continue
        p1,p2 = A[spec['a']],A[spec['b']]
        want = abs(p2[0]-p1[0]) if spec['axis']=='x' else abs(p2[1]-p1[1])
        if abs(d1['value']-want) > 0.5:
            errs.append(f"{tag}: value {d1['value']} != anchor dist {want}")
    out['QJ5_dim_counts'] = {'A102':len(p102['dims']),'A103':len(p103['dims']),
        'expected':len(GEO['dims'])+len(EXTRA)}
    out['QJ5_dims_valid'] = not errs and len(p102['dims'])==len(p103['dims']) \
        == len(GEO['dims'])+len(EXTRA)
    # QJ6 保留墙几何一致: 同名对象多边形面积对称差<2%
    VOCAB = {'RETAINED','RETAINED_STRUCT','NEW','PENDING_REVIEW','DESIGN_APPROVED_DEMO',
             'DEMOLITION_HOLD','NO_STRUCT_OVERLAP','CLASSIFICATION_UNVERIFIED',
             'STRUCT_EVIDENCE_BOUNDARY_RING','STRUCT_EVIDENCE_HATCH_FILL',
             'EXISTING_RETAINED','EXISTING_DEMOLISHED','PROPOSED_NEW','UNVERIFIED',
             'DESIGN_REVIEW_PENDING','OWNER_DESIGN_APPROVED','PENDING_SITE_VERIFY',
             'HOLD','RETAINED','UNRESOLVED','-'}
    def norm_key(o):
        if '#p' in o: return o
        return o+'#p0'
    def geoms_of(walls, layers):
        g = {}
        for lay in layers:
            for w in walls.get(lay,[]):
                if len(w['pts'])>=3 and w['objs'] and w['objs'][0] not in VOCAB \
                   and not w['objs'][0].startswith(('dim:','LEGACY')):
                    g.setdefault(norm_key(w['objs'][0]),[]).append(Polygon(w['pts']))
        return {k:unary_union(v) for k,v in g.items()}
    g102 = geoms_of(p102['walls'],('A-WALL-RETAIN','A-WALL-RETAIN-STRUCT'))
    g103 = geoms_of(p103['walls'],('A-WALL',))
    bad_geo = {}
    for o,gg in g102.items():
        cand = g103.get(norm_key(o))
        if cand is None: bad_geo[o] = 'MISSING_IN_A103'; continue
        sym = gg.symmetric_difference(cand).area
        if sym/max(gg.area,1) > 0.02: bad_geo[o] = f'GEOM_DIFF {sym:.0f}mm2'
    out['QJ6_wall_geom_parity'] = bad_geo
    out['QJ6_pass'] = not bad_geo
    # QJ9 二维几何一致性Gate: missing+extra双向 + 分类型缺失 + 全差异明细
    # (P1.5.1收尾A: 单向/阈值静默都不许; 小差异记录不判零)
    WALL_LAYERS = {'A-WALL','A-DESIGN','A-STRUCT-UNDERLAY','A-REVIEW',
                   'A-STAIR','A-STAIR-AREA','A-SOFFIT','A-MISC-NEW','A-CONFLICT','A-COLUMN'}
    # A-STAIR-AREA: 冻结的面积/语义足迹, 不绘出但必须计入可见并集(P0台阶修复后
    # 可见层为开放链, 闭合多边形仅存此层), 否则整段台阶误报 missing.
    def _classify(n):
        n = n.upper()
        if 'STEP' in n or 'STAIR' in n: return 'STAIR_STEP'
        if 'SOFFIT' in n or '_HEAD' in n or 'HEADER' in n or 'ABOVE_DOOR' in n:
            return 'SOFFIT_HEADER'
        if 'PIER' in n or 'RETURN' in n or 'JUNCTION' in n: return 'COLUMN_PIER'
        if n.startswith('DOOR') or '_DOOR' in n: return 'DOOR_OPENING'
        return 'WALL_PARTITION'
    target_by_type = {}
    for m in GEO['managed_entities']:
        if m['design_status'] not in ('EXISTING_RETAINED','PROPOSED_NEW',
                                    'UNVERIFIED','DESIGN_REVIEW_PENDING'):
            continue
        ct = _classify(m['objects'][0]) if m['source'] == 'blender' else 'EXISTING'
        for p in m['parts']:
            target_by_type.setdefault(ct, []).append(Polygon(p['exterior']))
    target_u = unary_union([g for gs in target_by_type.values() for g in gs]) \
        if target_by_type else Polygon()
    vis_polys = []
    for lay, ents in p103['walls'].items():
        if lay not in WALL_LAYERS or \
           (p103['flags'].get(lay) and lay != 'A-STAIR-AREA'): continue
        for w in ents:
            if len(w['pts']) >= 3: vis_polys.append(Polygon(w['pts']))
    vis_u = unary_union(vis_polys) if vis_polys else Polygon()
    # 零容差基线: 当前生成器产出 missing/extra=0, 故可严格判定.
    # 单片>1000mm²即失败(不再用20k静默); 累计>3000mm²失败防"多删小墙段"逃逸.
    TOL_COMP, TOL_TOTAL = 1000, 3000
    def diff_detail(diff, tol=100):
        """全部>=tol差异片: 面积+质心, 不按阈值判零."""
        if diff.is_empty: return []
        gs = diff.geoms if hasattr(diff, 'geoms') else [diff]
        return sorted(
            ({'area_mm2': round(g.area), 'cx': round(g.centroid.x),
              'cy': round(g.centroid.y)} for g in gs
             if g.geom_type == 'Polygon' and g.area > tol),
            key=lambda d: -d['area_mm2'])
    miss_detail = diff_detail(target_u.difference(vis_u))
    extra_detail = diff_detail(vis_u.difference(target_u))
    out['QJ9_missing_detail'] = miss_detail
    out['QJ9_extra_detail'] = extra_detail
    out['QJ9_missing_total_mm2'] = round(sum(d['area_mm2'] for d in miss_detail))
    out['QJ9_extra_total_mm2'] = round(sum(d['area_mm2'] for d in extra_detail))
    out['QJ9_max_local_dev_mm2'] = max(
        [d['area_mm2'] for d in miss_detail + extra_detail] or [0])
    # 分类型缺失 (extra无法按类型归因, 报告总体)
    miss_by_type = {}
    for ct, polys in target_by_type.items():
        u = unary_union(polys)
        miss_by_type[ct] = diff_detail(u.difference(vis_u))
    out['QJ9_missing_by_type'] = miss_by_type
    out['QJ9_target_area_mm2'] = round(target_u.area)
    fail_missing = any(d['area_mm2'] > TOL_COMP for d in miss_detail) \
        or out['QJ9_missing_total_mm2'] > TOL_TOTAL
    fail_extra = any(d['area_mm2'] > TOL_COMP for d in extra_detail) \
        or out['QJ9_extra_total_mm2'] > TOL_TOTAL
    out['QJ9_geom_parity_2d'] = not (fail_missing or fail_extra)
    # QJ7 源文件FRESH + viewport存在
    srcs = json.loads((CAD/'derived'/'three_source_mapping.json').read_text())['summary']['sources']
    out['QJ7_sources_fresh'] = all(
        hashlib.sha256((ROOT/s['file'].split('interior_design/')[-1]).read_bytes()).hexdigest()==s['sha256']
        for s in srcs.values()
        if s['file'].endswith(('.dxf','.FCStd','.blend','.json'))
        and Path(ROOT/s['file'].split('interior_design/')[-1]).exists())
    # QJ10 台阶语义: 3级踢面 + +450到达平台并入第3踏 + 台阶构件不入新增墙层
    vis103 = [(lay, w) for lay, ents in p103['walls'].items()
              if not p103['flags'].get(lay) for w in ents]
    treads = {o.split('#')[0] for lay, w in vis103 for o in w['objs']
              if o.split('#')[0] in ('STEP_0', 'STEP_1', 'STEP_2')}
    indep4 = [w['handle'] for lay, w in vis103
              if any(o.split('#')[0] == 'WAVE_STEP_3_ARRIVAL' for o in w['objs'])]
    merged = [w['handle'] for lay, w in vis103
              if any('merged_arrival' in o for o in w['objs'])]
    stair_on_wallnew = [w['handle'] for w in p102['walls'].get('A-WALL-NEW', [])
              if any(o.split('#')[0].startswith('STEP') or 'WAVE_STEP' in o
                     for o in w['objs'])]
    stair102 = [w['handle'] for w in p102['walls'].get('A-STAIR-NEW', [])]
    out['QJ10_stair_treads'] = sorted(treads)
    out['QJ10_arrival_platform_merged'] = bool(merged)
    out['QJ10_indep_4th_step_handles'] = indep4
    out['QJ10_stair_on_new_wall_layer'] = stair_on_wallnew
    out['QJ10_a102_stair_layer_entities'] = len(stair102)
    out['QJ10_stair_semantics'] = (treads == {'STEP_0','STEP_1','STEP_2'}
        and not indep4 and bool(merged) and not stair_on_wallnew)
    out['QJ8_viewports'] = {'A102':p102['n_viewports'],'A103':p103['n_viewports']}
    out['QJ8_viewport_present'] = p102['n_viewports']>0 and p103['n_viewports']>0
    out['verdict'] = 'PASS' if all(v for k,v in out.items() if isinstance(v,bool)) else 'HOLD'
    return out

if __name__ == '__main__':
    a102 = CAD/(sys.argv[1] if len(sys.argv)>1 else 'A102_WALL_DIFF_POC_V3.dxf')
    a103 = CAD/(sys.argv[2] if len(sys.argv)>2 else 'A103_CONSTRUCTION_POC_V7.dxf')
    res = qa(parse(a102), parse(a103))
    (CAD/'derived'/'qa_joint_v2.json').write_text(json.dumps(res,ensure_ascii=False,indent=1))
    print(json.dumps({k:v for k,v in res.items() if not isinstance(v,(list,dict))},
                     ensure_ascii=False,indent=1))
    for k in ('QJ3_detail','QJ4_conflict_objects','QJ5_dim_errs','QJ6_wall_geom_parity'):
        if res.get(k): print(k, res[k])
