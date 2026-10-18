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
          ('A-WALL-RETAIN-EQUIV',8),
          ('A-WALL-DEMO-DESIGN',1),('A-WALL-HOLD',6),('A-WALL-NEW',5),
          ('A-STAIR-NEW',8),('A-SOFFIT-NEW',8),('A-MISC-NEW',30),
          ('A-WALL-REVIEW',30),('A-DOOR',2),('A-WINDOW',4),('A-DIMS',3),('A-TEXT',7)]
for n,c in LAYERS: doc.layers.new(n, dxfattribs={'color':c})
# Blender重画副本与实测保留墙重合 -> 冻结层留痕, 不重复可见绘制
doc.layers.get('A-WALL-RETAIN-EQUIV').dxf.flags = 1
# 非墙构件轻线; 上部构件虚线感(轻线+浅灰)
for _l in ('A-STAIR-NEW','A-SOFFIT-NEW'):
    doc.layers.get(_l).dxf.lineweight = 18

NC = {r['object']:r for r in
      json.loads((CAD/'derived'/'new_construction_v1.json').read_text())['rows']}
def comp_layer(obj):
    r = NC.get(obj)
    ct = r['component_type'] if r else 'OTHER'
    return {'WALL_PARTITION':'A-WALL-NEW','COLUMN_PIER':'A-WALL-NEW',
            'DOOR_OPENING':'A-WALL-NEW','STAIR_STEP':'A-STAIR-NEW',
            'SOFFIT_HEADER':'A-SOFFIT-NEW','OTHER':'A-MISC-NEW'}.get(ct,'A-MISC-NEW')

ext = extract_structural(ezdxf.readfile(
    ROOT/'projects/c_type_home/cad/structure_only_source_sync.dxf').modelspace())
for g,_,k in ext['polys']:
    msp.add_lwpolyline(list(g.exterior.coords), close=True,
                       dxfattribs={'layer':'A-STRUCT-UNDERLAY'})
    for h in g.interiors:
        msp.add_lwpolyline(list(h.coords), close=True,
                           dxfattribs={'layer':'A-STRUCT-UNDERLAY'})

ROLE_LAYER = {'RETAINED':'A-WALL-RETAIN','RETAINED_STRUCT':'A-WALL-RETAIN-STRUCT',
              'NEW':'A-WALL-NEW','NEW_REPLACES_DEMO':'A-WALL-NEW',
              'RETAINED_MODEL_EQUIV':'A-WALL-RETAIN-EQUIV',
              'PENDING_REVIEW':'A-WALL-REVIEW',
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
    if role == 'SPLIT_PARTIAL_NEW':
        # 分段: 保留等价→浅灰底图, 实际新增段→构件类型对应新建层; 不整段重复画
        nc = NC.get(obj)
        if not nc: continue
        for pts in nc.get('retained_geoms',[]):
            ent = msp.add_lwpolyline([(float(x),float(y)) for x,y in pts],
                close=True, dxfattribs={'layer':'A-STRUCT-UNDERLAY'})
            ent.set_xdata('DEVINSRC',[(1000,e['object']),(1000,'RETAINED_EQUIV_PART'),
                                      (1000,e['classification'])])
        for pts in nc.get('new_geoms',[]):
            ent = msp.add_lwpolyline([(float(x),float(y)) for x,y in pts],
                close=True, dxfattribs={'layer':comp_layer(obj)})
            ent.set_xdata('DEVINSRC',[(1000,e['object']),(1000,'ACTUAL_NEW_PART'),
                                      (1000,nc['component_type']),
                                      (1000,e['classification'])])
        continue
    if role == 'RETAINED_MODEL_EQUIV':
        # 整段=保留墙重画副本→冻结层留痕; 残余新增必须按覆盖证据处理
        nc = NC.get(obj)
        for pts in pts_list or []:
            ent = msp.add_lwpolyline([(float(x),float(y)) for x,y in pts],
                close=True, dxfattribs={'layer':'A-WALL-RETAIN-EQUIV'})
            ent.set_xdata('DEVINSRC',[(1000,e['object']),(1000,role),
                                      (1000,e['classification'])])
        if nc:
            for c in nc.get('covered_new_geoms',[]):
                ent = msp.add_lwpolyline([(float(x),float(y)) for x,y in c['geom']],
                    close=True, dxfattribs={'layer':'A-WALL-RETAIN-EQUIV'})
                ent.set_xdata('DEVINSRC',[(1000,e['object']),(1000,'COVERED_NEW_PART'),
                    (1000,'covered_by:'+','.join(c['covered_by']))])
            for pts in nc.get('uncovered_new_geoms',[]):
                ent = msp.add_lwpolyline([(float(x),float(y)) for x,y in pts],
                    close=True, dxfattribs={'layer':comp_layer(obj)})
                ent.set_xdata('DEVINSRC',[(1000,e['object']),(1000,'RESIDUAL_NEW_UNCOVERED'),
                                          (1000,nc['component_type'])])
        continue
    if not pts_list: continue
    for pts in pts_list:
        lay = comp_layer(obj) if role in ('NEW','NEW_REPLACES_DEMO') else ROLE_LAYER[role]
        ent = msp.add_lwpolyline([(float(x),float(y)) for x,y in pts], close=True,
                               dxfattribs={'layer':lay})
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

# --- 补充施工定位标注 (dims_extra, 坐标直算; 与 A103 共用同一份 JSON) ---
EXTRA_DIMS = json.loads((CAD/'derived'/'dims_extra.json').read_text())['dims']
for _d in EXTRA_DIMS:
    p1,p2 = tuple(_d['p1']),tuple(_d['p2'])
    if _d['axis']=='x':
        base,ang=((p1[0]+p2[0])/2,_d['lay']),0
    else:
        base,ang=(_d['lay'],(p1[1]+p2[1])/2),90
    _dd=msp.add_linear_dim(base=base,p1=p1,p2=p2,angle=ang,dimstyle=DS,
                           dxfattribs={'layer':'A-DIMS'})
    _dd.render(); _dd.commit()
    _dd.dimension.set_xdata('DEVINDIM',[(1000,_d['tag']),
        (1000,f"geo:{p1[0]},{p1[1]}"),(1000,f"geo:{p2[0]},{p2[1]}"),
        (1000,_d['axis']),(1040,round(_d['value'],1)),
        (1000,_d.get('measurement_type','UNSPEC')),
        (1000,(_d.get('ref_object') or _d.get('src',''))[:200]),
        (1000,_d.get('resurvey',''))])

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
