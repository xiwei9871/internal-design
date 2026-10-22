#!/usr/bin/env python3
# A202 v5 — 顶视材质编码图 + 墙壳外轮廓包络 = 真实室内边界
import json, numpy as np, ezdxf
from pathlib import Path
from PIL import Image
from scipy import ndimage
from shapely.geometry import box, Polygon, MultiPolygon, LineString
from shapely.ops import unary_union
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
G=json.loads((root/'cad/plan_geom.json').read_text())
meta=json.load(open(root/'cad/seg_meta.json'))
img=np.asarray(Image.open(root/'cad/topmap.png').convert('RGB')).astype(int)
R,Gc,B=img[...,0],img[...,1],img[...,2]
wood_px=(R>120)&(R>Gc+40)&(R>B+40)
tile_px=(Gc>120)&(Gc>R+40)&(Gc>B+40)
# ---- 1. 包络:每个墙壳块的外轮廓填充 ----
parts=[]
for it in G['items']['wall']+G['items']['window']:
    b=it['bbox']
    if b[2]-b[0]>30 and b[3]-b[1]>30:
        parts.append(box(b[0],b[1],b[2],b[3]))
shell=unary_union(parts)
sp=list(shell.geoms) if shell.geom_type=='MultiPolygon' else [shell]
envelope=unary_union([Polygon(p.exterior) for p in sp])
wallmask=shell
interior=envelope.difference(wallmask)
comps=list(interior.geoms) if interior.geom_type=='MultiPolygon' else [interior]
comps=[p for p in comps if p.area>400000]
print('COMPS',len(comps),[round(p.area/1e6,1) for p in comps])
# ---- 2. 像素→mm 材质判定 ----
SPAN,CX,CY,W,H=meta['span'],meta['cx']*1000,meta['cy']*1000,meta['W'],meta['H']
def mm2px(xm,ym): return (int((xm-CX)/(SPAN*1000)*W+W/2), int(H/2-(ym-CY)/(SPAN*1000)*H))
def classify(poly):
    rp=poly.representative_point(); x,y=mm2px(rp.x,rp.y)
    # 区内采样:在poly内均匀取点,统计 wood/tile 像素
    minx,miny,maxx,maxy=poly.bounds
    pts=[]
    for xx in np.linspace(minx,maxx,8):
        for yy in np.linspace(miny,maxy,8):
            if poly.contains(box(xx-1,yy-1,xx+1,yy+1).centroid): pts.append(mm2px(xx,yy))
    w=t=0
    for px,py in pts:
        if 0<=px<W and 0<=py<H:
            if wood_px[py,px]: w+=1
            if tile_px[py,px]: t+=1
    return 'tile' if t>w else 'wood', w, t
# ---- 3. 命名锚点 ----
ANCHORS=[(5000,9000,'客厅'),(4400,3400,'餐厅'),(4300,5700,'玄关'),(6600,2200,'厨房'),
 (3500,1500,'生活阳台'),(9700,2300,'主卧'),(13300,2300,'母卧'),(11400,9500,'客卧'),
 (14600,8800,'书房'),(10300,5500,'次卫'),(14600,5500,'主卫'),(8800,9500,'客卫'),
 (10500,7200,'走廊'),(10500,12000,'阳光房')]
doc=ezdxf.new('R2010'); doc.header['$INSUNITS']=4; doc.units=4
LAYERS=[('A-WALL',7,0.50),('A-HATCH-WOOD',8,0.18),('A-HATCH-TILE',4,0.18),('A-TEXT',7,0.25)]
for n,c,w in LAYERS:
    lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
msp=doc.modelspace()
def label(x,y,txt,h=230):
    msp.add_text(txt,height=h,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def segs_in(p,spacing,vertical,layer):
    minx,miny,maxx,maxy=p.bounds
    a,b,n=(minx,maxx,int((maxx-minx)/spacing)+1) if vertical else (miny,maxy,int((maxy-miny)/spacing)+1)
    for i in range(1,n):
        v=a+i*spacing
        ln=LineString([(v,miny-10),(v,maxy+10)]) if vertical else LineString([(minx-10,v),(maxx+10,v)])
        seg=p.intersection(ln)
        for g in getattr(seg,'geoms',[seg]):
            if g.geom_type=='LineString' and g.length>300:
                msp.add_line(g.coords[0],g.coords[-1],dxfattribs={'layer':layer})
for it in G['items']['wall']+G['items']['window']:
    b=it['bbox']
    if b[2]-b[0]>30 and b[3]-b[1]>30:
        msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':'A-WALL'})
for p in comps:
    kind,w,t=classify(p)
    c=p.centroid
    name=''
    for ax,ay,an in ANCHORS:
        if p.contains(box(ax-1,ay-1,ax+1,ay+1).centroid): name=an; break
    if kind=='tile':
        segs_in(p,600,True,'A-HATCH-TILE'); segs_in(p,600,False,'A-HATCH-TILE')
    else:
        segs_in(p,120,False,'A-HATCH-WOOD')
    label(c.x,c.y,f'{name or "区域"} {p.area/1e6:.1f}m²')
    print('ZONE',name or '?',kind,round(p.area/1e6,1),'w/t',w,t)
notes=['地面铺装说明:','1. 粉线=白蜡木实木复合地板(南北向通铺),起铺点客厅西南角',
 '2. 蓝格=防滑地砖600x600,卫生间找坡1%向地漏','3. 厨卫门口大理石门槛石,宽同门洞',
 '4. 踢脚线白蜡木同色60高','5. 面积标注供复核,现场复尺为准']
ty=-2200
for t_ in notes:
    msp.add_text(t_,height=220,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((1300,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label(8500,-1600,'V15 地面铺装图  A202   比例 1:50   版本 R5')
doc.saveas(root/'cad/A202_地面铺装图.dxf')
print('saved')
