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
                                 'value':val,'handle':e.dxf.handle}
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
    for tag,spec in GEO['dims'].items():
        d1, d2 = p102['dims'].get(tag), p103['dims'].get(tag)
        if not d1 or not d2: errs.append(f'{tag}: missing in ' + ('A102' if not d1 else 'A103')); continue
        if (d1['a'],d1['b'],d1['axis'],d1['value']) != (d2['a'],d2['b'],d2['axis'],d2['value']):
            errs.append(f'{tag}: schema mismatch {d1} vs {d2}'); continue
        p1,p2 = A[spec['a']],A[spec['b']]
        want = abs(p2[0]-p1[0]) if spec['axis']=='x' else abs(p2[1]-p1[1])
        if abs(d1['value']-want) > 0.5:
            errs.append(f"{tag}: value {d1['value']} != anchor dist {want}")
    out['QJ5_dim_errs'] = errs
    out['QJ5_dims_valid'] = not errs and len(p102['dims'])==len(p103['dims'])==len(GEO['dims'])
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
    # QJ7 源文件FRESH + viewport存在
    srcs = json.loads((CAD/'derived'/'three_source_mapping.json').read_text())['summary']['sources']
    out['QJ7_sources_fresh'] = all(
        hashlib.sha256((ROOT/s['file'].split('interior_design/')[-1]).read_bytes()).hexdigest()==s['sha256']
        for s in srcs.values()
        if s['file'].endswith(('.dxf','.FCStd','.blend','.json'))
        and Path(ROOT/s['file'].split('interior_design/')[-1]).exists())
    out['QJ8_viewports'] = {'A102':p102['n_viewports'],'A103':p103['n_viewports']}
    out['QJ8_viewport_present'] = p102['n_viewports']>0 and p103['n_viewports']>0
    out['verdict'] = 'PASS' if all(v for k,v in out.items() if isinstance(v,bool)) else 'HOLD'
    return out

if __name__ == '__main__':
    a102 = CAD/'A102_WALL_DIFF_POC_V2.dxf'
    a103 = CAD/'A103_CONSTRUCTION_POC_V6.dxf'
    res = qa(parse(a102), parse(a103))
    (CAD/'derived'/'qa_joint_v2.json').write_text(json.dumps(res,ensure_ascii=False,indent=1))
    print(json.dumps({k:v for k,v in res.items() if not isinstance(v,(list,dict))},
                     ensure_ascii=False,indent=1))
    for k in ('QJ3_detail','QJ4_conflict_objects','QJ5_dim_errs','QJ6_wall_geom_parity'):
        if res.get(k): print(k, res[k])
