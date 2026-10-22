#!/usr/bin/env python3
# A202 v2 — 用墙体模具扣出真实房间区域再铺装
import json, ezdxf, math
from pathlib import Path
from shapely.geometry import box, Polygon, MultiPolygon, LineString
from shapely.ops import unary_union, polygonize
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
G=json.loads((root/'cad/plan_geom.json').read_text())

# ---- 1. 墙+门洞做阻隔模具 ----
blockers=[]
for it in G['items']['wall']:
    b=it['bbox']; blockers.append(box(b[0],b[1],b[2],b[3]))
for it in G['items']['door']:
    b=it['bbox']
    if (b[2]-b[0])>150 and (b[3]-b[1])>150: blockers.append(box(b[0],b[1],b[2],b[3]))
mask=unary_union(blockers)
x0=min(b[0] for b in [it['bbox'] for it in G['items']['wall']])
y0=min(b[1] for b in [it['bbox'] for it in G['items']['wall']])
x1=max(b[2] for b in [it['bbox'] for it in G['items']['wall']])
y1=max(b[3] for b in [it['bbox'] for it in G['items']['wall']])
site=box(x0,y0,x1,y1)
interior=site.difference(mask)
# 收集连通区
if interior.geom_type=='Polygon': comps=[interior]
else: comps=list(interior.geoms)
comps=[p for p in comps if p.area>800000]  # >0.8m²
print('ROOMS',len(comps),[round(p.area/1e6,1) for p in comps])
# ---- 2. 房间材料判定：含厨卫洁具→砖，含阳台/淋浴/洗衣机→砖 ----
TILE_KW=('TOILET','SINK','SHOWER','HOB','STOVE','WASHER','BALCONY','TAP','VANITY','DRAIN')
def zone_material(p):
    for it in G['items']['fixture']:
        b=it['bbox']; cx=(b[0]+b[2])/2; cy=(b[1]+b[3])/2
        if p.contains(box(cx-1,cy-1,cx+1,cy+1).centroid):
            for k in TILE_KW:
                if k in it['name']: return 'tile'
    return 'wood'
# ---- 3. DXF ----
doc=ezdxf.new('R2010'); doc.header['$INSUNITS']=4; doc.units=4
LAYERS=[('A-WALL',7,0.50),('A-HATCH-WOOD',8,0.18),('A-HATCH-TILE',4,0.18),
        ('A-TEXT',7,0.25),('A-TITLE',7,0.50),('A-ROOM',3,0.35)]
for n,c,w in LAYERS:
    lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
msp=doc.modelspace()
def label(x,y,txt,h=280):
    msp.add_text(txt,height=h,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def draw_poly(p,layer):
    for ring in [p.exterior]+list(p.interiors):
        msp.add_lwpolyline(list(ring.coords),close=True,dxfattribs={'layer':layer})
def hatch_lines(p,spacing,layer):
    minx,miny,maxx,maxy=p.bounds
    y=miny+spacing
    while y<maxy:
        seg=p.intersection(LineString([(minx-10,y),(maxx+10,y)]))
        for g in getattr(seg,'geoms',[seg]):
            if g.length>200:
                msp.add_line(g.coords[0],g.coords[-1],dxfattribs={'layer':layer})
        y+=spacing
def tile_grid(p,cell=600):
    minx,miny,maxx,maxy=p.bounds
    x=minx
    while x<maxx:
        seg=p.intersection(LineString([(x,miny-10),(x,maxy+10)]))
        for g in getattr(seg,'geoms',[seg]):
            if g.length>200: msp.add_line(g.coords[0],g.coords[-1],dxfattribs={'layer':'A-HATCH-TILE'})
        x+=cell
    hatch_lines(p,cell,'A-HATCH-TILE')
# 墙体描边
for it in G['items']['wall']:
    b=it['bbox']
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':'A-WALL'})
for it in G['items']['window']:
    b=it['bbox']
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':'A-WALL'})
# 区域填充
for p in comps:
    kind=zone_material(p)
    draw_poly(p,'A-ROOM')
    if kind=='tile': tile_grid(p)
    else: hatch_lines(p,120,'A-HATCH-WOOD')
    cx,cy=p.representative_point().x,p.representative_point().y
    label(cx,cy,f'{p.area/1e6:.1f}m²',200)
# 说明
notes=['地面铺装说明:','1. 粉色线=白蜡木实木复合地板(南北向),起铺点客厅西南角',
 '2. 蓝色网格=防滑地砖600x600,卫生间找坡1%向地漏','3. 门槛石厨卫门口大理石,宽同门洞',
 '4. 踢脚线白蜡木同色60高','5. 房间面积标注供复核,现场复尺为准']
ty=y0-1400
for t in notes:
    msp.add_text(t,height=220,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x0,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label((x0+x1)/2,y0-700,'V15 地面铺装图  A202   比例 1:50   版本 R2')
doc.saveas(root/'cad/A202_地面铺装图.dxf')
print('A202 v2 saved')
