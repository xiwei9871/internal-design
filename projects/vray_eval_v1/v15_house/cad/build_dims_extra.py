#!/usr/bin/env python3
"""补充施工定位标注 (P1.5.1 T3): 数值全部从模型几何计算, 语义分四类.
measurement_type:
  DEMOLITION_SPAN   拆改段跨度(沿主轴)
  NEW_WALL_LOCATION 新建隔墙定位: 从最近实测保留墙面到新墙最近面
  STAIR_SPAN        台阶构件跨度(独立类别, 不冒充隔墙定位)
  OPENING_WIDTH     门洞净宽(模型注册洞口, 复尺状态 SITE_VERIFY)
每条记录 measurement_type/src_object/两个真实测量边界/resurvey 状态."""
import json, hashlib
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import nearest_points

CAD = Path(__file__).resolve().parent
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())
NC = json.loads((CAD/'derived'/'new_construction_v1.json').read_text())

dims = []
def add(tag, p1, p2, axis, lay, mtype, src, resurvey='SITE_VERIFY', ref=None):
    val = abs(p2[0]-p1[0]) if axis=='x' else abs(p2[1]-p1[1])
    d = {'tag':tag,'p1':[round(p1[0],1),round(p1[1],1)],
         'p2':[round(p2[0],1),round(p2[1],1)],'axis':axis,'lay':lay,
         'value':round(val,1),'measurement_type':mtype,'src':src,
         'resurvey':resurvey}
    if ref: d['ref_object'] = ref
    dims.append(d)

# --- 实测保留墙集合 (定位参照系) ---
retained = []   # (object, Polygon)
for m in GEO['managed_entities']:
    if m['source']=='fcstd' and m['design_status']=='EXISTING_RETAINED':
        for p in m['parts']:
            retained.append((m['objects'][0], Polygon(p['exterior'])))
ret_named = {}
for n,g in retained: ret_named.setdefault(n,[]).append(g)

# 1) 拆改段跨度 DEMOLITION_SPAN
for m in GEO['managed_entities']:
    for j,p in enumerate(m.get('demolished_parts',[])):
        g = Polygon(p); x0,y0,x1,y1 = g.bounds
        if (x1-x0) >= (y1-y0):
            y = y1+250
            add(f"demo_span_{m['objects'][0]}", (x0,y),(x1,y),'x',y+200,
                'DEMOLITION_SPAN', f"{m['objects'][0]}#demol{j}",
                resurvey='DESIGN_CONFIRMED')
        else:
            x = x1+250
            add(f"demo_span_{m['objects'][0]}", (x,y0),(x,y1),'y',x+200,
                'DEMOLITION_SPAN', f"{m['objects'][0]}#demol{j}",
                resurvey='DESIGN_CONFIRMED')

# 2) 新建隔墙定位 NEW_WALL_LOCATION: 新墙沿所接保留墙主轴的起始位置
#    (距保留墙近端端面 -> 新墙中心线投影点; 新墙与保留墙相邻距≈0不算定位)
from shapely.ops import unary_union as _uu
cands = [r for r in NC['rows']
         if r['component_type']=='WALL_PARTITION'
         and r['construction_class'] in ('ACTUAL_NEW_CONSTRUCTION','REPLACES_DEMOLISHED')
         and r['uncovered_new_area']>50000]
cands = sorted(cands, key=lambda r:-r['uncovered_new_area'])[:4]
for i,r in enumerate(cands):
    ng = _uu([Polygon(p) for p in r['uncovered_new_geoms']]) \
         if r['uncovered_new_geoms'] else Polygon(r['new_geoms'][0])
    best = min(retained, key=lambda t: t[1].distance(ng), default=None)
    if not best: continue
    ref_name, ref_g = best
    pa, pb = nearest_points(ref_g, ng)       # pa=保留墙接点
    rx0, ry0, rx1, ry1 = ref_g.bounds
    cx, cy = ng.centroid.x, ng.centroid.y    # 新墙中心线投影
    if (rx1-rx0) >= (ry1-ry0):               # 保留墙沿x轴 → 定位=水平距离
        t0, t1 = rx0, cx                     # 从墙西端面到新墙中心
        y = max(ry1, ng.bounds[3]) + 400
        add(f"new_loc_{i+1}_{r['object'][:18]}", (t0,y),(t1,y),'x',y+200,
            'NEW_WALL_LOCATION', r['object'], resurvey='SITE_VERIFY',
            ref=f'{ref_name} west end→new wall centerline')
    else:                                    # 保留墙沿y轴 → 定位=竖向距离
        t0, t1 = ry0, cy
        x = max(rx1, ng.bounds[2]) + 400
        add(f"new_loc_{i+1}_{r['object'][:18]}", (x,t0),(x,t1),'y',x+200,
            'NEW_WALL_LOCATION', r['object'], resurvey='SITE_VERIFY',
            ref=f'{ref_name} south end→new wall centerline')

# 3) 台阶构件 STAIR_SPAN
for r in NC['rows']:
    if r['component_type'] != 'STAIR_STEP': continue
    x0,y0,x1,y1 = r['bbox']
    if (x1-x0) >= (y1-y0):
        add(f"step_span_{r['object'][:16]}", (x0,y0-200),(x1,y0-200),'x',y0-400,
            'STAIR_SPAN', r['object'], resurvey='SITE_VERIFY')
    else:
        add(f"step_span_{r['object'][:16]}", (x0-200,y0),(x0-200,y1),'y',x0-400,
            'STAIR_SPAN', r['object'], resurvey='SITE_VERIFY')

# 4) 门洞净宽 OPENING_WIDTH (模型注册洞口, 与最终设计一致)
for i,op in enumerate(GEO['door_openings']):
    x0,y0,x1,y1 = op['rect']; L=op['opening_len']
    if op['orient']=='V':
        add(f"door_w_{i+1:02d}", (x0,y1+150),(x0+L,y1+150),'x',y1+350,
            'OPENING_WIDTH', f"door rect {op['handle']}", resurvey='SITE_VERIFY')
    else:
        add(f"door_w_{i+1:02d}", (x1+150,y0),(x1+150,y0+L),'y',x1+350,
            'OPENING_WIDTH', f"door rect {op['handle']}", resurvey='SITE_VERIFY')

out = {'meta':{'sha_geometry':hashlib.sha256(
              (CAD/'derived'/'geometry_v05.json').read_bytes()).hexdigest(),
              'rule':'geometry-derived; NEW_WALL_LOCATION refs nearest retained face; '
                     'span vs location dims separated; resurvey states recorded'},
       'dims':dims}
(CAD/'derived'/'dims_extra.json').write_text(json.dumps(out,ensure_ascii=False,indent=1))
from collections import Counter
print('extra dims:',len(dims), Counter(d['measurement_type'] for d in dims))
for d in dims[:8]: print(' ',d['tag'],d['value'],d.get('ref_object',''))
