#!/usr/bin/env python3
"""施工语义修正 (P1.5 任务一, P1.5.1 T1/T2): PROPOSED_NEW 不等于施工新建.

对 Blender 拟建件与现状保留墙做二维差集:
  retained_equiv = P ∩ retained_union   (现状墙的设计模型重画部分)
  actual_new     = P − retained_union   (真实新增施工)

P1.5.1:
- 每个对象标 component_type: WALL_PARTITION | COLUMN_PIER | SOFFIT_HEADER |
  STAIR_STEP | DOOR_OPENING | OTHER —— 台阶/窗头/吊顶不再计入新建砌墙面积.
- REMODELED_RETAINED 的差集残余不得静默隐藏: 逐碎片查"其他有效施工几何覆盖",
  有覆盖证据的记 covered_by, 无证据的进 uncovered_new_geoms 必须出图.
- 新增面积按构件类型做 unary_union 去重并集, 不做对象面积简单相加."""
import json, hashlib
from pathlib import Path
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

CAD = Path(__file__).resolve().parent
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())
MIN_AREA = 1000          # mm² 几何残片下限
RETAIN_EQUIV_T = 0.7     # >0.7 覆盖视作整段重画保留墙
NEW_T = 0.2              # <0.2 差集占比视作重画(无实质新增)
COVER_T = 0.8            # 碎片被其他施工几何覆盖>80% 记有证据

def classify(name):
    n = name.upper()
    if 'STEP' in n or 'STAIR' in n: return 'STAIR_STEP'
    if 'SOFFIT' in n or '_HEAD' in n or 'HEADER' in n or 'ABOVE_DOOR' in n:
        return 'SOFFIT_HEADER'
    if 'PIER' in n or 'RETURN' in n or 'JUNCTION' in n: return 'COLUMN_PIER'
    if n.startswith('DOOR') or '_DOOR' in n: return 'DOOR_OPENING'
    if 'WALL' in n or 'PARTITION' in n or 'DIVIDER' in n or 'REMAINDER' in n:
        return 'WALL_PARTITION'
    return 'OTHER'

retained_parts, demo_parts, pending_parts = [], [], []
for m in GEO['managed_entities']:
    if m['source'] != 'fcstd': continue
    for p in m['parts']:
        g = Polygon(p['exterior'])
        if m['design_status'] == 'EXISTING_RETAINED': retained_parts.append(g)
        elif m['design_status'] in ('UNVERIFIED','DESIGN_REVIEW_PENDING'):
            pending_parts.append((m['objects'][0],g))
    for p in m.get('demolished_parts',[]):
        demo_parts.append(Polygon(p))
ret_u = unary_union(retained_parts)
dem_u = unary_union(demo_parts)
pen_u = unary_union([g for _,g in pending_parts])

# 其他有效施工几何 = 全部 blender parts 并集(供覆盖证据查询)
def split_parts(poly):
    """返回 (parts, residual). 任意几何集合只取面积>MIN_AREA的多边形."""
    if poly.is_empty: return [], poly
    geoms = poly.geoms if hasattr(poly,'geoms') else [poly]
    parts = [g for g in geoms if g.geom_type=='Polygon' and g.area > MIN_AREA]
    kept = unary_union(parts) if parts else Polygon()
    return parts, poly.difference(kept)

rows = []
for m in GEO['managed_entities']:
    if m['source'] != 'blender': continue
    primary = m['objects'][0]
    ctype = classify(primary)
    for i, p in enumerate(m['parts']):
        poly = Polygon(p['exterior'])
        inter = poly.intersection(ret_u)
        dem = poly.intersection(dem_u)
        pen = poly.intersection(pen_u)
        diff = poly.difference(ret_u)
        i_ratio = inter.area/poly.area if poly.area>1 else 0
        n_ratio = diff.area/poly.area if poly.area>1 else 0
        d_ratio = dem.area/poly.area if poly.area>1 else 0
        ret_geoms, _ = split_parts(inter)
        new_geoms, res = split_parts(diff)
        if i_ratio > RETAIN_EQUIV_T:   cls = 'REMODELED_RETAINED'
        elif d_ratio > 0.5:          cls = 'REPLACES_DEMOLISHED'
        elif n_ratio < NEW_T:        cls = 'REMODELED_RETAINED'
        elif i_ratio > 0.15:         cls = 'SPLIT'
        else:                        cls = 'ACTUAL_NEW_CONSTRUCTION'
        rows.append({
          'object': primary if len(m['parts'])==1 else f'{primary}#p{i}',
          'design_status': m['design_status'],
          'component_type': ctype,
          'construction_class': cls,
          'area_total': round(poly.area),
          'area_retained_equiv': round(inter.area),
          'area_actual_new': round(diff.area),
          'area_over_demolished': round(dem.area),
          'area_over_pending': round(pen.area),
          'retained_geoms': [list(g.exterior.coords) for g in ret_geoms],
          'new_geoms': [list(g.exterior.coords) for g in new_geoms],
          'residual_area': round(res.area),
          'bbox': [round(v) for v in poly.bounds],
        })

# --- T2: REMODELED_RETAINED 残余新增几何覆盖证据 ---
# 对每个对象的每片 new_geom: 查"除自身外"的全部 blender 施工几何并集是否覆盖.
all_blender = []
for m in GEO['managed_entities']:
    if m['source'] == 'blender':
        for p in m['parts']:
            all_blender.append((m['objects'][0], Polygon(p['exterior'])))
for r in rows:
    if r['construction_class'] not in ('REMODELED_RETAINED',): continue
    base = r['object'].split('#')[0]
    others = unary_union([g for n,g in all_blender if n != base]) if all_blender else Polygon()
    uncovered, covered = [], []
    for pts in r['new_geoms']:
        frag = Polygon(pts)
        ov = frag.intersection(others).area / frag.area if frag.area > 1 else 1.0
        if ov >= COVER_T:
            by = sorted({n for n,g in all_blender
                         if n != base and frag.intersection(g).area/frag.area > 0.3})
            covered.append({'geom':pts,'cover_ratio':round(ov,3),'covered_by':by})
        else:
            uncovered.append(pts)
    r['uncovered_new_geoms'] = uncovered
    r['covered_new_geoms'] = covered
    r['uncovered_new_area'] = round(sum(Polygon(p).area for p in uncovered))
for r in rows:
    r.setdefault('uncovered_new_geoms', r['new_geoms'])
    r.setdefault('covered_new_geoms', [])
    r.setdefault('uncovered_new_area', r['area_actual_new'])

# --- T1: 分构件类型去重并集面积 ---
type_union = {}
for r in rows:
    ct = r['component_type']
    type_union.setdefault(ct, {'new':[], 'retained':[], 'objects':0})
    type_union[ct]['objects'] += 1
    for pts in r.get('uncovered_new_geoms', []):
        type_union[ct]['new'].append(Polygon(pts))
    for pts in r['retained_geoms']:
        type_union[ct]['retained'].append(Polygon(pts))
area_by_type = {}
for ct, d in type_union.items():
    area_by_type[ct] = {
        'objects': d['objects'],
        'new_union_mm2': round(unary_union(d['new']).area) if d['new'] else 0,
        'retained_equiv_union_mm2': round(unary_union(d['retained']).area) if d['retained'] else 0}

stats = {}
for r in rows:
    stats[r['construction_class']] = stats.get(r['construction_class'],0)+1
out = {'meta': {
         'geometry_snapshot_sha256': hashlib.sha256(
             (CAD/'derived'/'geometry_v05.json').read_bytes()).hexdigest(),
         'retained_union_area': round(ret_u.area),
         'demolished_union_area': round(dem_u.area),
         'thresholds': {'retain_equiv':RETAIN_EQUIV_T,'new':NEW_T,'min_area_mm2':MIN_AREA,
                        'cover':COVER_T},
         'rule': 'blender proposed − retained_union = actual_new; '
                 'REMODELED残余须覆盖证据否则必须出图; 面积按component_type去重并集'},
       'area_by_component_type': area_by_type,
       'rows': rows, 'stats': stats}
(CAD/'derived'/'new_construction_v1.json').write_text(
    json.dumps(out, ensure_ascii=False, indent=1))
import csv
with open(CAD/'derived'/'new_construction_v1.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['object','component_type','construction_class','total','retained_equiv',
                'actual_new','uncovered_new','over_demol','over_pending','residual'])
    for r in rows:
        w.writerow([r['object'],r['component_type'],r['construction_class'],
                    r['area_total'],r['area_retained_equiv'],r['area_actual_new'],
                    r['uncovered_new_area'],r['area_over_demolished'],
                    r['area_over_pending'],r['residual_area']])
print(json.dumps(stats,ensure_ascii=False))
print('area_by_component_type:',json.dumps(area_by_type,ensure_ascii=False,indent=1))
