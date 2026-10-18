#!/usr/bin/env python3
"""A102 墙体拆改图 POC V2 — 数据源: wall_state_registry.json + geometry_v05.json
P1.4.3: 统一DEVINDIM标注schema | 设计确认拟拆!=施工批准 | 真A1 VIEWPORT 1:50."""
import json, sys
from pathlib import Path
import ezdxf
from three_source_mapping import sha, extract_structural

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
REG = json.loads((CAD/'derived'/'wall_state_registry.json').read_text())
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())
OUT = CAD / 'A102_WALL_DIFF_POC_V2.dxf'

doc = ezdxf.new('R2010', setup=True)
msp = doc.modelspace()
for appid in ('DEVINSRC','DEVINDIM'): doc.appids.new(appid)

LAYERS = [('A-STRUCT-UNDERLAY',8),('A-WALL-RETAIN',7),('A-WALL-RETAIN-STRUCT',7),
          ('A-WALL-DEMO-DESIGN',1),('A-WALL-HOLD',6),('A-WALL-NEW',5),
          ('A-WALL-REVIEW',30),('A-DOOR',2),('A-WINDOW',4),('A-DIMS',3),('A-TEXT',7)]
for n,c in LAYERS: doc.layers.new(n, dxfattribs={'color':c})

ext = extract_structural(ezdxf.readfile(
    ROOT/'projects/c_type_home/cad/structure_only_source_sync.dxf').modelspace())
for g,_,k in ext['polys']:
    msp.add_lwpolyline(list(g.exterior.coords), close=True,
                       dxfattribs={'layer':'A-STRUCT-UNDERLAY'})
    for h in g.interiors:
        msp.add_lwpolyline(list(h.coords), close=True,
                           dxfattribs={'layer':'A-STRUCT-UNDERLAY'})

ROLE_LAYER = {'RETAINED':'A-WALL-RETAIN','RETAINED_STRUCT':'A-WALL-RETAIN-STRUCT',
              'NEW':'A-WALL-NEW','PENDING_REVIEW':'A-WALL-REVIEW',
              'DESIGN_APPROVED_DEMO':'A-WALL-DEMO-DESIGN','DEMOLITION_HOLD':'A-WALL-HOLD'}
polys = {}
for m in GEO['managed_entities']:
    polys[m['objects'][0]] = {'parts':[p['exterior'] for p in m['parts']],
                              'demol':[p for p in m.get('demolished_parts',[])]}
counts = {}
for e in REG['entries']:
    role = e['a102_role']; counts[role] = counts.get(role,0)+1
    obj, _, suffix = e['object'].partition('#')
    if suffix.startswith('demol'):
        i = int(suffix[5:]); pts_list=[polys[obj]['demol'][i]] if i<len(polys[obj]['demol']) else None
    elif suffix.startswith('p'):
        i = int(suffix[1:]); pts_list=[polys[obj]['parts'][i]] if i<len(polys[obj]['parts']) else None
    else:
        pts_list = polys.get(obj,{}).get('parts')
    if not pts_list: continue
    for pts in pts_list:
        ent = msp.add_lwpolyline([(float(x),float(y)) for x,y in pts], close=True,
                               dxfattribs={'layer':ROLE_LAYER[role]})
        ent.set_xdata('DEVINSRC',[(1000,e['object']),(1000,role),
                                  (1000,e['classification']),
                                  (1000,e.get('design_intent') or '-'),
                                  (1000,e.get('construction_authorization') or '-')])
        if role in ('DESIGN_APPROVED_DEMO','DEMOLITION_HOLD'):
            xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
            msp.add_line((min(xs),min(ys)),(max(xs),max(ys)),
                         dxfattribs={'layer':ROLE_LAYER[role]})
            msp.add_line((min(xs),max(ys)),(max(xs),min(ys)),
                         dxfattribs={'layer':ROLE_LAYER[role]})
        if role == 'DEMOLITION_HOLD':
            msp.add_text('HOLD: 拆除实施未批-待结构核实', height=120,
                dxfattribs={'layer':'A-WALL-HOLD'}).set_placement((min(xs),max(ys)+150))

for op in GEO['door_openings']:
    x0,y0,x1,y1 = op['rect']
    msp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)], close=False,
                       dxfattribs={'layer':'A-DOOR'})

# --- 标注: 统一 DEVINDIM schema [tag, anchorA, anchorB, axis, value] ---
A = {a['id']:(a['x'],a['y']) for a in GEO['anchors']}
DS='STD-ARCH'
doc.dimstyles.new(DS, dxfattribs={'dimtxsty':'HZTXT' if 'HZTXT' in doc.styles else 'Standard',
                                  'dimtxt':180,'dimasz':140,'dimdec':0,'dimtad':1})
LAY={'south_total':-1600,'kitchen_face':-1000,'master_clear':-1600,
     'living_window':14200,'balcony_north':14200,'west_total':700,
     'bath2_depth':8700,'kitchen_open':5450,'stair_width':4300,
     'bath2_width':4300,'bath2_envelope_w':4300,'bath2_net_w':4800}
for tag,spec in GEO['dims'].items():
    p1,p2 = A[spec['a']],A[spec['b']]
    val = abs(p2[0]-p1[0]) if spec['axis']=='x' else abs(p2[1]-p1[1])
    if spec['axis']=='x':
        off=LAY.get(tag,min(p1[1],p2[1])-800); base,ang=((p1[0]+p2[0])/2,off),0
    else:
        off=LAY.get(tag,min(p1[0],p2[0])-800); base,ang=(off,(p1[1]+p2[1])/2),90
    d=msp.add_linear_dim(base=base,p1=p1,p2=p2,angle=ang,dimstyle=DS,
                         dxfattribs={'layer':'A-DIMS'})
    d.render(); d.commit()
    d.dimension.set_xdata('DEVINDIM',[(1000,tag),(1000,spec['a']),(1000,spec['b']),
                                    (1000,spec['axis']),(1040,round(val,1))])

msp.add_text('A102 墙体拆改图 POC V2 | registry驱动 | 红=设计确认拟拆(施工待批) 品红=HOLD',height=250,
             dxfattribs={'layer':'A-TEXT'}).set_placement((13500,14800))

# --- 真 A1 纸空间 + VIEWPORT 1:50 ---
lay = doc.layout('Layout1') if 'Layout1' in doc.layouts else doc.layouts.new('Layout1')
for _e in list(lay):
    if _e.dxftype() in ('LWPOLYLINE','TEXT','MTEXT','VIEWPORT'): _e.destroy()
lay.add_lwpolyline([(0,0),(841,0),(841,594),(0,594)],close=True)
lay.add_lwpolyline([(560,20),(821,20),(821,80),(560,80)],close=True)
lay.add_text('A102 墙体拆改图 — POC V2 | 1:50 | A1 | 非正式施工图',height=9).dxf.insert=(566,55)
lay.add_text('数据源: wall_state_registry.json + geometry_v05.json',height=6).dxf.insert=(566,35)
mx, my = (0+16500)/2, (-200+14200)/2     # 模型范围中心
vp = lay.add_viewport(center=(420,320), size=(780,520),
                      view_center_point=(mx,my), view_height=520*50)
vp.dxf.status = 1
doc.saveas(OUT)
print('A102 V2 generated:',OUT.name,'| roles:',counts)
