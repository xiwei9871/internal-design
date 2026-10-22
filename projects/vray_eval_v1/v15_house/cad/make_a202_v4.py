#!/usr/bin/env python3
# A202 v4 — z过滤墙体掩码 + 环洞室内区 + 手动阳台补区
import json, ezdxf
from pathlib import Path
from shapely.geometry import box, Polygon, LineString
from shapely.ops import unary_union
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
G=json.loads((root/'cad/plan_geom.json').read_text())
# 结构墙掩码:z起点<=500的墙(排除吊柜/过梁/窗头), +全部窗(薄边界封口)
shell_parts=[]
for it in G['items']['wall']:
    b=it['bbox']
    if b[4]<=500 and b[2]-b[0]>30 and b[3]-b[1]>30:
        shell_parts.append(box(b[0],b[1],b[2],b[3]))
for it in G['items']['window']:
    b=it['bbox']
    if b[2]-b[0]>30 and b[3]-b[1]>30:
        shell_parts.append(box(b[0],b[1],b[2],b[3]))
shell=unary_union(shell_parts)
polys=list(shell.geoms) if shell.geom_type=='MultiPolygon' else [shell]
holes=[Polygon(r) for p in polys for r in p.interiors]
interior=unary_union(holes)
mask=shell
# 房间表:(名, 矩形, 材料, 是否洞外补区)
ROOMS=[
 ('客厅',(2900,6800,8300,13900),'wood',False),
 ('餐厅',(2950,2300,5900,4550),'wood',False),
 ('玄关',(2900,4700,5900,6800),'wood',False),
 ('厨房',(5900,200,7800,4500),'tile',False),
 ('生活阳台',(1520,700,5900,2300),'tile',True),
 ('主卧',(8000,200,11400,4500),'wood',False),
 ('母卧',(11400,200,15300,6400),'wood',False),
 ('客卧',(9900,8000,12900,10900),'wood',False),
 ('书房',(13100,6600,16200,10900),'wood',False),
 ('次卫',(9200,4500,11400,6450),'tile',False),
 ('主卫',(13100,4500,16200,6400),'tile',False),
 ('客卫',(8000,8000,9700,10900),'tile',False),
 ('走廊',(8000,4500,13100,8000),'wood',False),
 ('阳光房',(8000,10900,12900,13400),'tile',False),
]
doc=ezdxf.new('R2010'); doc.header['$INSUNITS']=4; doc.units=4
LAYERS=[('A-WALL',7,0.50),('A-HATCH-WOOD',8,0.18),('A-HATCH-TILE',4,0.18),
        ('A-TEXT',7,0.25),('A-TITLE',7,0.50)]
for n,c,w in LAYERS:
    lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
msp=doc.modelspace()
def label(x,y,txt,h=230):
    msp.add_text(txt,height=h,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def segs_in(p,vertical,spacing,layer):
    minx,miny,maxx,maxy=p.bounds
    n=int((maxx-minx)/spacing)+2 if vertical else int((maxy-miny)/spacing)+2
    for i in range(n):
        if vertical:
            ln=LineString([(minx+i*spacing,miny-10),(minx+i*spacing,maxy+10)])
        else:
            ln=LineString([(minx-10,miny+i*spacing),(maxx+10,miny+i*spacing)])
        seg=p.intersection(ln)
        for g in getattr(seg,'geoms',[seg]):
            if g.length>300: msp.add_line(g.coords[0],g.coords[-1],dxfattribs={'layer':layer})
def polys_of(g):
    if g.geom_type=='Polygon': return [g]
    if g.geom_type=='MultiPolygon': return list(g.geoms)
    return []
# 墙体描边(画所有结构墙)
for it in G['items']['wall']:
    b=it['bbox']
    if b[4]<=500 and b[2]-b[0]>30 and b[3]-b[1]>30:
        msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':'A-WALL'})
for it in G['items']['window']:
    b=it['bbox']
    if b[2]-b[0]>30 and b[3]-b[1]>30:
        msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':'A-WALL'})
report=[]
for name,(x0,y0,x1,y1),kind,extra in ROOMS:
    base=box(x0,y0,x1,y1)
    room=base.difference(mask) if extra else base.intersection(interior)
    parts=[p for p in polys_of(room) if p.area>50000]
    if not parts: print('EMPTY',name); report.append((name,0)); continue
    main=max(parts,key=lambda p:p.area)
    for p in parts:
        if kind=='tile':
            segs_in(p,True,600,'A-HATCH-TILE'); segs_in(p,False,600,'A-HATCH-TILE')
        else:
            segs_in(p,False,120,'A-HATCH-WOOD')
    c=main.representative_point()
    label(c.x,c.y,f'{name} {main.area/1e6:.1f}m²')
    report.append((name,round(main.area/1e6,1))); print('ROOM',name,round(main.area/1e6,1))
allb=[it['bbox'] for it in G['items']['wall']]
ax0=min(b[0] for b in allb if b[2]>b[0]); ay0=min(b[1] for b in allb if b[3]>b[1]); ax1=max(b[2] for b in allb)
notes=['地面铺装说明:','1. 粉线=白蜡木实木复合地板(南北向通铺),起铺点客厅西南角',
 '2. 蓝格=防滑地砖600x600,卫生间找坡1%向地漏','3. 厨卫门口大理石门槛石,宽同门洞',
 '4. 踢脚线白蜡木同色60高','5. 面积标注供复核,现场复尺为准']
ty=ay0-1400
for t in notes:
    msp.add_text(t,height=220,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((ax0,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label((ax0+ax1)/2,ay0-700,'V15 地面铺装图  A202   比例 1:50   版本 R4')
doc.saveas(root/'cad/A202_地面铺装图.dxf')
json.dump(report,open(root/'cad/a202_report.json','w'))
print('saved')
