#!/usr/bin/env python3
# A202 v6 — 像素级材质分割:缓冲封口包络 + 最近邻材质归属 + 轮廓矢量化
import json, numpy as np, ezdxf
from pathlib import Path
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import box, Polygon, LineString, Point
from shapely.ops import unary_union
from skimage import measure
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
G=json.loads((root/'cad/plan_geom.json').read_text())
meta=json.load(open(root/'cad/seg_meta.json'))
img=np.asarray(Image.open(root/'cad/topmap.png').convert('RGB')).astype(int)
R,Gc,B=img[...,0],img[...,1],img[...,2]
wood_px=(R>120)&(R>Gc+40)&(R>B+40)
tile_px=(Gc>120)&(Gc>R+40)&(Gc>B+40)
wall_px=(B>120)&(B>R+40)&(B>Gc+40)
SPAN,CX,CY,W,H=meta['span'],meta['cx']*1000,meta['cy']*1000,meta['W'],meta['H']
MM=SPAN*1000/W  # mm per px
def px2mm(x,y): return ((x-W/2)*MM+CX,(H/2-y)*MM+CY)
def mm2px(xm,ym): return ((xm-CX)/MM+W/2, H/2-(ym-CY)/MM)
# ---- 1. 缓冲500封口→外轮廓→蚀回 = 房屋包络 ----
parts=[]
for it in G['items']['wall']+G['items']['window']:
    b=it['bbox']
    if b[2]-b[0]>30 and b[3]-b[1]>30:
        parts.append(box(b[0],b[1],b[2],b[3]))
shell=unary_union(parts)
sp=list(shell.geoms) if shell.geom_type=='MultiPolygon' else [shell]
buff=unary_union([p.buffer(500) for p in sp])
bp=list(buff.geoms) if buff.geom_type=='MultiPolygon' else [buff]
envelope=unary_union([Polygon(p.exterior) for p in bp]).buffer(-500)
# ---- 2. 包络栅格化 + 室内掩码 ----
def raster(poly):
    im=Image.new('1',(W,H),0); d=ImageDraw.Draw(im)
    polys=list(poly.geoms) if poly.geom_type=='MultiPolygon' else [poly]
    for p in polys:
        d.polygon([mm2px(x,y) for x,y in p.exterior.coords],fill=1,outline=1)
        for r in p.interiors:
            d.polygon([mm2px(x,y) for x,y in r.coords],fill=0,outline=0)
    return np.asarray(im,dtype=bool)
env_px=raster(envelope)
wall_px=ndimage.binary_dilation(wall_px,iterations=1)
interior_px=env_px & ~wall_px
interior_px=ndimage.binary_opening(interior_px,iterations=1)
interior_px=ndimage.binary_closing(interior_px,iterations=2)
# ---- 3. 材质归属:other像素取最近材质 ----
known=(wood_px|tile_px)&interior_px
other=interior_px&~known
_,idx=ndimage.distance_transform_edt(other,return_indices=True)
lab=np.where(wood_px,'W','X'); lab=np.where(tile_px,'T',lab)
mat=np.full(lab.shape,'O',dtype='<U1')
mat[interior_px]=lab[interior_px]
mat[other]=lab[idx[0][other],idx[1][other]]
# 设计意图湿区强制为砖(模型地面是统一地板色,不代表真实面层)
INTENT_TILE=[(5900,0,7900,4600),(7900,10900,12950,13450)]
for x0,y0,x1,y1 in INTENT_TILE:
    px0,py0=mm2px(x0,y1); px1,py1=mm2px(x1,y0)
    box_m=np.zeros(mat.shape,dtype=bool)
    box_m[int(py0):int(py1),int(px0):int(px1)]=True
    mat[interior_px&box_m]='T'
wood_zone=interior_px&(mat=='W'); tile_zone=interior_px&(mat=='T')
# 清小碎块
for msk in (wood_zone,tile_zone):
    l,n=ndimage.label(msk)
    sizes=np.bincount(l.ravel())
    kill=np.where((sizes>0)&(sizes<300))[0]
    msk[np.isin(l,kill)]=False
print('zones wood_px',wood_zone.sum(),'tile_px',tile_zone.sum())
# ---- 4. 矢量化 ----
def to_polys(msk,min_area=0.3):
    polys=[]
    for c in measure.find_contours(msk.astype(float),0.5):
        if len(c)<6: continue
        pts=[px2mm(x,y) for y,x in c]
        p=Polygon(pts)
        if p.is_valid and p.area/1e6>min_area:
            polys.append(p.simplify(150,preserve_topology=True))
    return polys
wood_polys=to_polys(wood_zone); tile_polys=to_polys(tile_zone)
print('polys wood',len(wood_polys),[round(p.area/1e6,1) for p in wood_polys])
print('polys tile',len(tile_polys),[round(p.area/1e6,1) for p in tile_polys])
# ---- 5. DXF ----
import shutil
base=Path('/Users/xiwei/interior_design/projects/c_type_home/cad/C型_原始户型数字化基准图.dxf')
dst=root/'cad/A202_地面铺装图.dxf'
shutil.copy(base,dst)
doc=ezdxf.readfile(dst); doc.header['$INSUNITS']=4; doc.units=4
LAYERS=[('A-WALL',7,0.50),('A-HATCH-WOOD',8,0.18),('A-HATCH-TILE',4,0.18),('A-TEXT',7,0.25)]
for n,c,w in LAYERS:
    if n in [l.dxf.name for l in doc.layers]: continue
    lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
try: doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
except: pass
msp=doc.modelspace()
def label(x,y,txt,h=230):
    msp.add_text(txt,height=h,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def segs_in(p,spacing,vertical,layer):
    minx,miny,maxx,maxy=p.bounds
    rng=np.arange(miny+spacing,maxy,spacing) if not vertical else np.arange(minx+spacing,maxx,spacing)
    for v in rng:
        ln=LineString([(minx-10,v),(maxx+10,v)]) if not vertical else LineString([(v,miny-10),(v,maxy+10)])
        seg=p.intersection(ln)
        for g in getattr(seg,'geoms',[seg]):
            if g.geom_type=='LineString' and g.length>300:
                msp.add_line(g.coords[0],g.coords[-1],dxfattribs={'layer':layer})
for it in G['items']['wall']+G['items']['window']:
    b=it['bbox']
    if b[2]-b[0]>30 and b[3]-b[1]>30:
        msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':'A-WALL'})
for p in wood_polys: segs_in(p,150,True,'A-HATCH-WOOD')
for p in tile_polys:
    segs_in(p,600,True,'A-HATCH-TILE'); segs_in(p,600,False,'A-HATCH-TILE')
# ---- 门槛石:门洞两侧材质不同才画 ----
def mat_at(xm,ym):
    x,y=mm2px(xm,ym)
    x=int(x);y=int(y)
    if 0<=x<W and 0<=y<H: return mat[y,x]
    return 'O'
# (开口矩形, 方向'h'=横墙开口/'v'=竖墙开口)
DOORS=[(12900,4800,13100,5550,'v','主卫门'),(12900,6700,13100,7550,'v','书房门'),
 (11950,6400,12850,6600,'h','次卫门'),(8850,7800,9600,8000,'h','客卫门'),
 (10000,7800,10850,8000,'h','客卧门'),(8150,4500,9060,4700,'h','主卧门'),
 (7800,11800,7950,12650,'v','阳光房门'),(9060,5910,9260,6610,'v','次卫门')]
def probe(xm,ym,dr,sign):
    ms=set()
    for d in (250,600,1000):
        if dr=='h': ms.add(mat_at(xm,ym+sign*d))
        else: ms.add(mat_at(xm+sign*d,ym))
    return ms
for x0,y0,x1,y1,dr,dn in DOORS:
    cxm,cym=(x0+x1)/2,(y0+y1)/2
    if dr=='h':
        a=probe(cxm,y0,dr,-1); b=probe(cxm,y1,dr,1)
        if 'W' in a and 'T' in b or 'T' in a and 'W' in b:
            msp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],close=True,dxfattribs={'layer':'A-WALL'})
            label(cxm,cym,'门槛石',160)
            print('THRESH',dn,a,b)
    else:
        a=probe(x0,cym,dr,-1); b=probe(x1,cym,dr,1)
        if 'W' in a and 'T' in b or 'T' in a and 'W' in b:
            msp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],close=True,dxfattribs={'layer':'A-WALL'})
            label(x0-350,cym,'门槛石',160)
            print('THRESH',dn,a,b)
# ---- 地漏:卫生间湿区 ----
import math
for dx,dy in [(11170,6140)]:
    msp.add_circle((dx,dy),110,dxfattribs={'layer':'A-WALL'})
    msp.add_line((dx-160,dy+160),(dx,dy),dxfattribs={'layer':'A-WALL'})
# ---- 标高 ----
for xm,ym,txt in [(5000,9000,'±0.000'),(6600,2200,'±0.000'),(8800,9500,'-0.015'),(14600,5500,'-0.015'),(10300,5500,'-0.015'),(10500,12000,'±0.000')]:
    label(xm,ym-450,txt,180)
# ---- 起铺点(客厅西南角) ----
msp.add_circle((3050,6900),120,dxfattribs={'layer':'A-WALL'})
msp.add_lwpolyline([(3050-180,6900),(3050,6900+180),(3050+180,6900),(3050,6900-180)],close=True,dxfattribs={'layer':'A-WALL'})
label(3050,7250,'起铺点',160)
ANCHORS=[(5000,9000,'客厅'),(4400,3400,'餐厅'),(4300,5700,'玄关'),(6600,2200,'厨房'),
 (3500,1500,'生活阳台'),(9700,2300,'主卧'),(13300,2300,'母卧'),(11400,9500,'客卧'),
 (14600,8800,'书房'),(10300,5500,'次卫'),(14600,5500,'主卫'),(8800,9500,'客卫'),
 (10500,7200,'走廊'),(10500,12000,'阳光房')]
for ax,ay,an in ANCHORS:
    pt=Point(ax,ay)
    for p in wood_polys+tile_polys:
        if p.contains(pt) or p.buffer(300).contains(pt):
            label(ax,ay,an); break
# 图例框(左下)
lg_x,lg_y=1300,-5200
msp.add_lwpolyline([(lg_x,lg_y),(lg_x+6800,lg_y),(lg_x+6800,lg_y+2400),(lg_x,lg_y+2400)],close=True,dxfattribs={'layer':'A-WALL'})
label(lg_x+3400,lg_y+2100,'图  例',300)
msp.add_line((lg_x+500,lg_y+1600),(lg_x+3500,lg_y+1600),dxfattribs={'layer':'A-HATCH-WOOD'})
msp.add_line((lg_x+500,lg_y+1300),(lg_x+3500,lg_y+1300),dxfattribs={'layer':'A-HATCH-WOOD'})
msp.add_line((lg_x+500,lg_y+1000),(lg_x+3500,lg_y+1000),dxfattribs={'layer':'A-HATCH-WOOD'})
label(lg_x+5000,lg_y+1300,'白蜡木实木复合地板 150宽',180)
for gx in (lg_x+500,lg_x+1700,lg_x+2900,lg_x+4100):
    msp.add_line((gx,lg_y+200),(gx,lg_y+800),dxfattribs={'layer':'A-HATCH-TILE'})
msp.add_line((lg_x+500,lg_y+500),(lg_x+4100,lg_y+500),dxfattribs={'layer':'A-HATCH-TILE'})
msp.add_line((lg_x+500,lg_y+200),(lg_x+4100,lg_y+200),dxfattribs={'layer':'A-HATCH-TILE'})
label(lg_x+5000,lg_y+500,'防滑地砖 600x600',180)
notes=['地面铺装说明:','1. 竖向线=白蜡木实木复合地板,南北向通铺,起铺点客厅西南角',
 '2. 蓝格=防滑地砖600x600,卫生间找坡1%向地漏','3. 厨卫门口大理石门槛石,宽同门洞',
 '4. 踢脚线白蜡木同色60高','5. 区域边界由模型顶视材质分割生成,现场复尺为准']
ty=-2200
for t_ in notes:
    msp.add_text(t_,height=220,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((1300,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label(8500,-1600,'V15 地面铺装图  A202   比例 1:50   版本 R6')
doc.saveas(root/'cad/A202_地面铺装图.dxf')
print('saved')
