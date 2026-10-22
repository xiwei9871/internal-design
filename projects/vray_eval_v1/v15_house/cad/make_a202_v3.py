#!/usr/bin/env python3
# A202 v3 — 房间矩形候选 ∩ 墙体模具裁切 = 真实可铺区域
import json, ezdxf
from pathlib import Path
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
G=json.loads((root/'cad/plan_geom.json').read_text())
# 墙壳并集:墙+窗(封外沿)。门不含——门洞开口保留在洞内
shell_parts=[]
for k in ('wall','window'):
    for it in G['items'][k]:
        b=it['bbox']; shell_parts.append(box(b[0],b[1],b[2],b[3]))
shell=unary_union(shell_parts)
if shell.geom_type=='MultiPolygon': shell=max(shell.geoms,key=lambda p:p.area)
# 洞=房间内部;取所有洞并集为室内净区
holes=[Polygon(r) for r in shell.interiors]
interior=unary_union(holes)
mask=shell
# ---- 房间候选:矩形+材料（按真实房间范围,允许比房间略大,由墙裁掉) ----
ROOMS=[
 ('客厅',(1600,7800,8300,12000),'wood'),('餐厅',(3200,2800,6200,6800),'wood'),
 ('玄关',(1600,3800,3400,6600),'wood'),('厨房',(6000,200,8200,4000),'tile'),
 ('生活阳台',(1600,200,5600,2800),'tile'),
 ('主卧',(8000,200,11400,4500),'wood'),('母卧',(11600,200,15300,4500),'wood'),
 ('客卧',(9900,8000,12900,10900),'wood'),('书房',(13100,6600,16200,10900),'wood'),
 ('次卫',(9200,4800,11400,6450),'tile'),('主卫',(13100,4700,16200,6400),'tile'),
 ('客卫',(8000,8000,9700,10900),'tile'),('走廊',(8100,6600,13100,7800),'wood'),
 ('阳光房',(9900,10900,13100,13700),'tile'),('北阳台外',(8200,11200,13100,13900),'tile'),
]
doc=ezdxf.new('R2010'); doc.header['$INSUNITS']=4; doc.units=4
LAYERS=[('A-WALL',7,0.50),('A-HATCH-WOOD',8,0.18),('A-HATCH-TILE',4,0.18),
        ('A-TEXT',7,0.25),('A-TITLE',7,0.50)]
for n,c,w in LAYERS:
    lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
msp=doc.modelspace()
def label(x,y,txt,h=260):
    msp.add_text(txt,height=h,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def segs_in(p,vertical,spacing,layer):
    from shapely.geometry import LineString
    minx,miny,maxx,maxy=p.bounds
    if vertical:
        x=minx+spacing
        while x<maxx:
            seg=p.intersection(LineString([(x,miny-10),(x,maxy+10)]))
            for g in getattr(seg,'geoms',[seg]):
                if g.length>300: msp.add_line(g.coords[0],g.coords[-1],dxfattribs={'layer':layer})
            x+=spacing
    else:
        y=miny+spacing
        while y<maxy:
            seg=p.intersection(LineString([(minx-10,y),(maxx+10,y)]))
            for g in getattr(seg,'geoms',[seg]):
                if g.length>300: msp.add_line(g.coords[0],g.coords[-1],dxfattribs={'layer':layer})
            y+=spacing
def polys(p):
    return [p] if p.geom_type=='Polygon' else list(p.geoms)
# 墙
for it in G['items']['wall']:
    b=it['bbox']
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':'A-WALL'})
for it in G['items']['window']:
    b=it['bbox']
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':'A-WALL'})
for name,(x0,y0,x1,y1),kind in ROOMS:
    room=box(x0,y0,x1,y1).intersection(interior)
    parts=[p for p in polys(room) if p.area>50000]
    if not parts: print('EMPTY',name); continue
    main=max(parts,key=lambda p:p.area)
    for p in parts:
        if kind=='tile':
            segs_in(p,True,600,'A-HATCH-TILE'); segs_in(p,False,600,'A-HATCH-TILE')
        else:
            segs_in(p,False,120,'A-HATCH-WOOD')
    c=main.representative_point()
    label(c.x,c.y,f'{name}\n{main.area/1e6:.1f}m²',230)
    print('ROOM',name,round(main.area/1e6,1))
allb=[it['bbox'] for it in G['items']['wall']]
ax0=min(b[0] for b in allb); ay0=min(b[1] for b in allb); ax1=max(b[2] for b in allb)
notes=['地面铺装说明:','1. 粉线=白蜡木实木复合地板(南北向),起铺点客厅西南角',
 '2. 蓝格=防滑地砖600x600,卫生间找坡1%向地漏','3. 厨卫门口大理石门槛石',
 '4. 踢脚线白蜡木同色60高','5. 面积标注供复核,现场复尺为准']
ty=ay0-1400
for t in notes:
    msp.add_text(t,height=220,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((ax0,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label((ax0+ax1)/2,ay0-700,'V15 地面铺装图  A202   比例 1:50   版本 R3')
doc.saveas(root/'cad/A202_地面铺装图.dxf')
print('saved')
