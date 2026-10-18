#!/usr/bin/env python3
"""补充施工定位标注 (P1.5 任务三): 全部从模型几何计算, 不手填.
产出 derived/dims_extra.json: [{tag,p1,p2,axis,lay,src}] 供 A102/A103 共用."""
import json, hashlib
from pathlib import Path
from shapely.geometry import Polygon

CAD = Path(__file__).resolve().parent
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())
NC = json.loads((CAD/'derived'/'new_construction_v1.json').read_text())

dims = []
def add(tag,p1,p2,axis,lay,src):
    val = abs(p2[0]-p1[0]) if axis=='x' else abs(p2[1]-p1[1])
    dims.append({'tag':tag,'p1':[round(p1[0],1),round(p1[1],1)],
                 'p2':[round(p2[0],1),round(p2[1],1)],'axis':axis,
                 'lay':lay,'value':round(val,1),'src':src})

# 1) 4处设计确认拟拆段: 沿主轴长度标注 (位于拆除矩形外侧200)
for m in GEO['managed_entities']:
    for j,p in enumerate(m.get('demolished_parts',[])):
        g = Polygon(p); x0,y0,x1,y1 = g.bounds
        if (x1-x0) >= (y1-y0):
            y = y1+250
            add(f"demo_len_{m['objects'][0]}", (x0,y),(x1,y),'x',y+200,
                f"{m['objects'][0]}#demol{j} bbox")
        else:
            x = x1+250
            add(f"demo_len_{m['objects'][0]}", (x,y0),(x,y1),'y',x+200,
                f"{m['objects'][0]}#demol{j} bbox")

# 2) 关键新建隔墙定位: 最大3段ACTUAL_NEW + R3隔墙
cands = sorted([r for r in NC['rows'] if r['construction_class'] in
                ('ACTUAL_NEW_CONSTRUCTION','REPLACES_DEMOLISHED')],
               key=lambda r:-r['area_actual_new'])[:3]
for r in cands:
    x0,y0,x1,y1 = r['bbox']
    if (x1-x0) >= (y1-y0):
        add(f"new_pos_{r['object'].split('#')[0][:20]}", (x0,y0-250),(x1,y0-250),'x',
            y0-450, f"new_construction bbox {r['object']}")
    else:
        add(f"new_pos_{r['object'].split('#')[0][:20]}", (x0-250,y0),(x0-250,y1),'y',
            x0-450, f"new_construction bbox {r['object']}")

# 3) 门洞宽度: 9个洞口, 宽沿开向
for i,op in enumerate(GEO['door_openings']):
    x0,y0,x1,y1 = op['rect']; L=op['opening_len']
    if op['orient']=='V':
        add(f"door_w_{i+1:02d}", (x0,y1+150),(x0+L,y1+150),'x',y1+350,
            f"door rect {op['handle']}")
    else:
        add(f"door_w_{i+1:02d}", (x1+150,y0),(x1+150,y0+L),'y',x1+350,
            f"door rect {op['handle']}")

out = {'meta':{'sha_geometry':hashlib.sha256(
              (CAD/'derived'/'geometry_v05.json').read_bytes()).hexdigest(),
              'rule':'all values computed from model geometry, no manual input'},
       'dims':dims}
(CAD/'derived'/'dims_extra.json').write_text(json.dumps(out,ensure_ascii=False,indent=1))
print('extra dims:',len(dims))
for d in dims[:6]: print(' ',d['tag'],d['value'],d['src'])
