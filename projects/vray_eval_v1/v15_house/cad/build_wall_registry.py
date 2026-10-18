#!/usr/bin/env python3
"""WALL_STATE_REGISTRY — A102/A103 共用的统一墙体状态表.
合并: 修正后结构覆盖(P1.4.1) + 设计状态(geometry_v05) + 证据分级.
结构证据分级: HATCH_FILL(最强, 剪力墙填充) > BOUNDARY_RING(闭合边界/线网环) > NONE.
开发商黑白墙原图无结构化字段 -> 结构层只能作证据代理, 权限判定独立 HOLD."""
import json, hashlib
from pathlib import Path
import ezdxf
from shapely.geometry import Polygon
from three_source_mapping import extract_structural, AX, AY, sha

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())
MAP = json.loads((CAD/'derived'/'three_source_mapping.json').read_text())

# --- 结构面按证据等级拆分 ---
ext = extract_structural(ezdxf.readfile(
    ROOT/'projects/c_type_home/cad/structure_only_source_sync.dxf').modelspace())
from shapely.ops import unary_union
hatch_u = unary_union([g for g,_,k in ext['polys'] if k=='HATCH']) \
          if any(k=='HATCH' for _,_,k in ext['polys']) else Polygon()
ring_u  = unary_union([g for g,_,k in ext['polys'] if k in ('LWP_CLOSED','LINE_RING')]) \
          if any(k!='HATCH' for _,_,k in ext['polys']) else Polygon()

def evidence(poly):
    """返回 (ratio, strongest_kind): HATCH_FILL > BOUNDARY_RING > NONE"""
    hr = poly.intersection(hatch_u).area/poly.area if poly.area>1 and not hatch_u.is_empty else 0
    rr = poly.intersection(ring_u).area/poly.area if poly.area>1 and not ring_u.is_empty else 0
    tot = poly.intersection(ext['union']).area/poly.area if poly.area>1 else 0
    kind = 'HATCH_FILL' if hr>0.5 else 'BOUNDARY_RING' if tot>0.1 else 'NONE'
    return round(tot,3), kind

prot = {w['object']: w for w in MAP['walls']}          # 现状墙 -> 保护分类
conf = {c['object']: c for c in MAP['summary']['conflicts']}

registry = []
def add(object_id, source, design_status, poly, note='', primary=None):
    primary = primary or object_id
    r, kind = evidence(poly) if poly is not None else (0,'NONE')
    p = prot.get(object_id, {})
    entry = {
        'object': object_id, 'source': source, 'design_status': design_status,
        'struct_ratio': r, 'struct_evidence': kind,
        'protection': p.get('protection','—'),
        'bbox': [round(v) for v in poly.bounds] if poly else None,
        'area': round(poly.area) if poly else 0,
        'note': note,
    }
    # --- A102 角色 ---
    if design_status == 'EXISTING_DEMOLISHED':
        if primary == 'W_EXT_N_BAL':
            entry['a102_role'] = 'DEMOLITION_HOLD'
            entry['note'] = (note+' | 修正后结构覆盖0%, 但开发商黑白语义未核实 -> '
                             '预防性HOLD, 不得发布为已批拆除').strip(' |')
        elif r <= 0.5:
            entry['a102_role'] = 'DEMOLISHED_CONFIRMED'
        else:
            entry['a102_role'] = 'DEMOLITION_HOLD'
            entry['note'] = (note+' | 拆除段与结构面重叠>50%').strip(' |')
    elif design_status == 'EXISTING_RETAINED':
        entry['a102_role'] = 'RETAINED_STRUCT' if r > 0.6 else 'RETAINED'
    elif design_status == 'PROPOSED_NEW':
        entry['a102_role'] = 'NEW'
    else:
        entry['a102_role'] = 'PENDING_REVIEW'
    # --- A103 角色 ---
    entry['a103_role'] = {'RETAINED_STRUCT':'DRAW_RETAINED','RETAINED':'DRAW_RETAINED',
        'DEMOLISHED_CONFIRMED':'SUPPRESS','DEMOLITION_HOLD':'SUPPRESS_HOLD',
        'NEW':'DRAW_NEW','PENDING_REVIEW':'DRAW_REVIEW_LAYER'}.get(entry['a102_role'],'SUPPRESS')
    # --- 开发商语义映射可信度 ---
    if kind == 'NONE' and design_status in ('EXISTING_DEMOLISHED','UNVERIFIED',
                                            'DESIGN_REVIEW_PENDING'):
        entry['classification'] = 'CLASSIFICATION_UNVERIFIED'
    elif kind == 'NONE' and entry['protection'] == 'ENVELOPE_REVIEW':
        entry['classification'] = 'CLASSIFICATION_UNVERIFIED'
    elif kind in ('HATCH_FILL','BOUNDARY_RING'):
        entry['classification'] = 'STRUCT_EVIDENCE_'+kind
    else:
        entry['classification'] = 'NO_STRUCT_OVERLAP'
    # --- 拟建重叠子分类 ---
    c = conf.get(object_id)
    if c and c['type'] == 'NEW_WALL_ON_PROTECTED':
        entry['overlap_class'] = 'STRUCT_HATCH_CONFLICT' if kind=='HATCH_FILL' \
                                 else 'BOUNDARY_OVERLAP_REVIEW'
        entry['note'] = (entry.get('note','') +
            f" | 拟建墙与{kind}覆盖{entry['struct_ratio']}: "
            f"{'骑跨剪力墙/柱-真实冲突' if kind=='HATCH_FILL' else '边界线重合-贴建或误差'}").strip(' |')
    return entry

for m in GEO['managed_entities']:
    primary = m['objects'][0]
    for i, p in enumerate(m['parts']):
        poly = Polygon(p['exterior'])
        registry.append(add(primary if len(m['parts'])==1 else f"{primary}#p{i}",
                            m['source'], m['design_status'], poly))
    for j, p in enumerate(m.get('demolished_parts',[])):
        registry.append(add(f"{primary}#demol{j}", m['source'], 'EXISTING_DEMOLISHED',
                            Polygon(p), primary=primary))

reg = {
 'meta': {
   'algorithm': 'P1.4.2 — unified wall state registry (struct evidence + design status)',
   'geometry_snapshot': {'file':'derived/geometry_v05.json',
                         'sha256': sha(CAD/'derived'/'geometry_v05.json')},
   'mapping_snapshot': {'file':'derived/three_source_mapping.json',
                        'sha256': sha(CAD/'derived'/'three_source_mapping.json')},
   'structural_source_sha256': sha(ROOT/'projects/c_type_home/cad/structure_only_source_sync.dxf'),
   'holds': ['W_EXT_N_BAL demolition (DEMOLITION_HOLD)',
             'structural/legal verification', 'site re-measure', 'balcony glazing compliance'],
 },
 'entries': registry,
 'stats': {
   'a102_roles': {},
   'a103_roles': {},
   'classifications': {},
   'overlap_classes': {c['overlap_class']:0 for c in registry if 'overlap_class' in c},
 }
}
for e in registry:
    reg['stats']['a102_roles'][e['a102_role']] = reg['stats']['a102_roles'].get(e['a102_role'],0)+1
    reg['stats']['a103_roles'][e['a103_role']] = reg['stats']['a103_roles'].get(e['a103_role'],0)+1
    reg['stats']['classifications'][e['classification']] = \
        reg['stats']['classifications'].get(e['classification'],0)+1
for e in registry:
    if 'overlap_class' in e:
        reg['stats']['overlap_classes'][e['overlap_class']] += 1

(CAD/'derived'/'wall_state_registry.json').write_text(
    json.dumps(reg, ensure_ascii=False, indent=1))
import csv
with open(CAD/'derived'/'wall_state_registry.csv','w',newline='') as f:
    w = csv.writer(f)
    w.writerow(['object','source','design_status','struct_ratio','struct_evidence',
                'protection','classification','a102_role','a103_role','overlap_class','note'])
    for e in registry:
        w.writerow([e['object'],e['source'],e['design_status'],e['struct_ratio'],
                    e['struct_evidence'],e['protection'],e['classification'],
                    e['a102_role'],e['a103_role'],e.get('overlap_class',''),e['note']])
print(json.dumps(reg['stats'], ensure_ascii=False, indent=1))
print('entries:', len(registry))
