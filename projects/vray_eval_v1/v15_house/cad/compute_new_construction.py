#!/usr/bin/env python3
"""施工语义修正 (P1.5 任务一): PROPOSED_NEW 不等于施工新建.
对 Blender 拟建件与现状保留墙做二维差集:
  retained_equiv = P ∩ retained_union   (现状墙的设计模型重画部分)
  actual_new     = P − retained_union   (真实新增施工)
分类: ACTUAL_NEW_CONSTRUCTION | REMODELED_RETAINED | SPLIT |
      REPLACES_DEMOLISHED | MODEL_ONLY_NONWALL
禁止面积容差静默删墙: 任何>1000mm²残片都保留为几何或记 uncertainty."""
import json, hashlib
from pathlib import Path
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

CAD = Path(__file__).resolve().parent
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())
MIN_AREA = 1000          # mm² 几何残片下限
RETAIN_EQUIV_T = 0.7     # >0.7 覆盖视作整段重画保留墙
NEW_T = 0.2              # <0.2 差集占比视作重画(无实质新增)

retained_parts, demo_parts, pending_parts = [], [], []
for m in GEO['managed_entities']:
    if m['source'] != 'fcstd': continue
    for p in m['parts']:
        g = Polygon(p['exterior'])
        if m['design_status'] == 'EXISTING_RETAINED': retained_parts.append(g)
        elif m['design_status'] in ('UNVERIFIED','DESIGN_REVIEW_PENDING'):
            pending_parts.append((m['objects'][0],g))
    for p in m.get('demolished_parts',[]):
        demo_parts.append(g)
ret_u = unary_union(retained_parts)
dem_u = unary_union(demo_parts)
pen_u = unary_union([g for _,g in pending_parts])

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

stats = {}
for r in rows:
    stats[r['construction_class']] = stats.get(r['construction_class'],0)+1
out = {'meta': {
         'geometry_snapshot_sha256': hashlib.sha256(
             (CAD/'derived'/'geometry_v05.json').read_bytes()).hexdigest(),
         'retained_union_area': round(ret_u.area),
         'demolished_union_area': round(dem_u.area),
         'thresholds': {'retain_equiv':RETAIN_EQUIV_T,'new':NEW_T,'min_area_mm2':MIN_AREA},
         'rule': 'blender proposed − retained_union = actual_new; 无容差删墙'},
       'rows': rows, 'stats': stats}
(CAD/'derived'/'new_construction_v1.json').write_text(
    json.dumps(out, ensure_ascii=False, indent=1))
import csv
with open(CAD/'derived'/'new_construction_v1.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['object','construction_class','total','retained_equiv','actual_new',
                'over_demol','over_pending','residual'])
    for r in rows:
        w.writerow([r['object'],r['construction_class'],r['area_total'],
                    r['area_retained_equiv'],r['area_actual_new'],
                    r['area_over_demolished'],r['area_over_pending'],r['residual_area']])
print(json.dumps(stats,ensure_ascii=False))
print('total new wall area:',round(sum(r['area_actual_new'] for r in rows)),
      '| retained-equiv:',round(sum(r['area_retained_equiv'] for r in rows)))
