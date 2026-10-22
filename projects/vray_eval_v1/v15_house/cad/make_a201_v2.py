#!/usr/bin/env python3
# A201 v2 — 天花布置图:像素级室内轮廓 + 分类灯具符号 + 标高/图例/检修口
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
L=json.loads(open(root/'cad/lights.json').read())
img=np.asarray(Image.open(root/'cad/topmap.png').convert('RGB')).astype(int)
R,Gc,B=img[...,0],img[...,1],img[...,2]
wall_px=(B>120)&(B>R+40)&(B>Gc+40)
SPAN,CX,CY,W,H=meta['span'],meta['cx']*1000,meta['cy']*1000,meta['W'],meta['H']
MM=SPAN*1000/W
def px2mm(x,y): return ((x-W/2)*MM+CX,(H/2-y)*MM+CY)
def mm2px(xm,ym): return ((xm-CX)/MM+W/2, H/2-(ym-CY)/MM)
# 包络(同A202)
parts=[box(*[it['bbox'][i] for i in (0,1,2,3)]) for it in G['items']['wall']+G['items']['window']
       if it['bbox'][2]-it['bbox'][0]>30 and it['bbox'][3]-it['bbox'][1]>30]
shell=unary_union(parts)
sp=list(shell.geoms) if shell.geom_type=='MultiPolygon' else [shell]
buff=unary_union([p.buffer(500) for p in sp])
bp=list(buff.geoms) if buff.geom_type=='MultiPolygon' else [buff]
envelope=unary_union([Polygon(p.exterior) for p in bp]).buffer(-500)
def raster(poly):
    im=Image.new('1',(W,H),0); d=ImageDraw.Draw(im)
    polys=list(poly.geoms) if poly.geom_type=='MultiPolygon' else [poly]
    for p in polys:
        d.polygon([mm2px(x,y) for x,y in p.exterior.coords],fill=1,outline=1)
        for r in p.interiors:
            d.polygon([mm2px(x,y) for x,y in r.coords],fill=0,outline=0)
    return np.asarray(im,dtype=bool)
wall_px=ndimage.binary_dilation(wall_px,iterations=1)
interior_px=raster(envelope)&~wall_px
def to_polys(msk,min_area=1.0):
    out=[]
    for c in measure.find_contours(msk.astype(float),0.5):
        p=Polygon([px2mm(x,y) for y,x in c])
        if p.is_valid and p.area/1e6>min_area: out.append(p.simplify(150,preserve_topology=True))
    return out
rooms=to_polys(interior_px)
# ---- DXF ----
doc=ezdxf.new('R2010'); doc.header['$INSUNITS']=4; doc.units=4
LAYERS=[('A-WALL',7,0.50),('A-CEIL',8,0.18),('A-LIGHT',1,0.25),('A-TEXT',7,0.25),('A-COVE',6,0.18)]
for n,c,w in LAYERS:
    lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
msp=doc.modelspace()
def label(x,y,txt,h=200):
    msp.add_text(txt,height=h,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def sym_downlight(x,y):   # 筒灯: 小圆+十字
    msp.add_circle((x,y),90,dxfattribs={'layer':'A-LIGHT'})
    msp.add_line((x-90,y),(x+90,y),dxfattribs={'layer':'A-LIGHT'})
    msp.add_line((x,y-90),(x,y+90),dxfattribs={'layer':'A-LIGHT'})
def sym_spot(x,y):        # 射灯: 圆+斜向标记
    msp.add_circle((x,y),110,dxfattribs={'layer':'A-LIGHT'})
    msp.add_line((x-70,y-70),(x+70,y+70),dxfattribs={'layer':'A-LIGHT'})
def sym_pendant(x,y):     # 吊灯: 圆+X
    msp.add_circle((x,y),150,dxfattribs={'layer':'A-LIGHT'})
    msp.add_line((x-100,y-100),(x+100,y+100),dxfattribs={'layer':'A-LIGHT'})
    msp.add_line((x-100,y+100),(x+100,y-100),dxfattribs={'layer':'A-LIGHT'})
def sym_cove(x,y,dx,dy):  # 灯带: 双线
    import math; L=math.hypot(dx,dy); nx,ny=-dy/L*70,dx/L*70
    msp.add_line((x-dx+nx,y-dy+ny),(x+dx+nx,y+dy+ny),dxfattribs={'layer':'A-COVE'})
    msp.add_line((x-dx-nx,y-dy-ny),(x+dx-nx,y+dy-ny),dxfattribs={'layer':'A-COVE'})
def sym_lowlamp(x,y):     # 台灯/落地灯(非天花): 虚线圆
    c=msp.add_circle((x,y),120,dxfattribs={'layer':'A-LIGHT'}); c.dxf.linetype='DASHED'
def sym_mirrorbar(x,y,dx,dy):
    msp.add_line((x-dx,y-dy),(x+dx,y+dy),dxfattribs={'layer':'A-LIGHT'})
    msp.add_circle((x,y),60,dxfattribs={'layer':'A-LIGHT'})
# 墙线
for it in G['items']['wall']+G['items']['window']:
    b=it['bbox']
    if b[2]-b[0]>30 and b[3]-b[1]>30:
        msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':'A-WALL'})
# 天花轮廓(细线)
for p in rooms:
    msp.add_lwpolyline(list(p.exterior.coords),close=True,dxfattribs={'layer':'A-CEIL'})
# ---- 灯具放置 ----
for li in L:
    n,x,y,z=li['name'],li['x'],li['y'],li['z']
    if 'DAYLIGHT' in n or n=='SUN' or 'LD_Sun' in n: continue   # 自然光不画
    if x==0 and y==0: continue                                   # 残留原点灯
    if 'COVE' in n:
        sym_cove(x,y,700,0)
        label(x,y-350,'床头灯带' if 'HEADBOARD' in n else '洗墙灯带',150)
    elif 'MIRRORBAR' in n:   sym_mirrorbar(x,y,0,400)
    elif 'UNDERCABINET' in n:sym_cove(x,y,0,1100); label(x+500,y,'柜下灯带',150)
    elif 'Pendant' in n or 'Dining_warm' in n: sym_pendant(x,y)
    elif li['type']=='SPOT':  sym_downlight(x,y)
    elif li['type']=='POINT': sym_lowlamp(x,y)
    elif li['type']=='AREA' and 'LIGHT_' in n: sym_pendant(x,y)  # 旧面板灯按吸顶灯画
    else: sym_downlight(x,y)
# ---- 房间名+天花标高 ----
ROOMLBL=[(5000,9000,'客厅'),(4400,3400,'餐厅'),(4300,5700,'玄关'),(6600,2200,'厨房'),
 (3500,1500,'生活阳台'),(9700,2300,'主卧'),(13300,2300,'母卧'),(11400,9500,'客卧'),
 (14600,8800,'书房'),(10300,5500,'次卫'),(14600,5500,'主卫'),(8800,9500,'客卫'),
 (10500,7200,'走廊'),(10500,12000,'阳光房')]
WET=('次卫','主卫','客卫','厨房','生活阳台')
for ax,ay,an in ROOMPASS if False else ROOMLBL:
    pt=Point(ax,ay)
    for p in rooms:
        if p.buffer(200).contains(pt):
            wet=an in WET
            label(ax,ay,f'{an}')
            label(ax,ay-420,'H=2950 铝扣板' if wet else 'H=2950 石膏板')
            break
# ---- 检修口:厨卫吊顶 ----
for ax,ay in [(6600,4200),(8900,8600),(10300,5200),(14600,5200)]:
    msp.add_lwpolyline([(ax-150,ay-150),(ax+150,ay-150),(ax+150,ay+150),(ax-150,ay+150)],close=True,dxfattribs={'layer':'A-WALL'})
    label(ax,ay+380,'检修口300',140)
# ---- 图例 ----
lg_x,lg_y=1300,-5600
msp.add_lwpolyline([(lg_x,lg_y),(lg_x+7600,lg_y),(lg_x+7600,lg_y+3000),(lg_x,lg_y+3000)],close=True,dxfattribs={'layer':'A-WALL'})
label(lg_x+3800,lg_y+2700,'图  例',300)
sym_downlight(lg_x+700,lg_y+1900); label(lg_x+3400,lg_y+1900,'筒灯/射灯(嵌顶)',170)
sym_cove(lg_x+700,lg_y+1200,500,0); label(lg_x+3400,lg_y+1200,'灯带/柜下灯',170)
sym_pendant(lg_x+700,lg_y+500); label(lg_x+3400,lg_y+500,'吊灯/吸顶灯',170)
sym_lowlamp(lg_x+6200,lg_y+1900); label(lg_x+6200,lg_y+1500,'台灯/落地灯(非天花)',160)
sym_mirrorbar(lg_x+6200,lg_y+1100,0,300); label(lg_x+6200,lg_y+550,'镜前灯',160)
# ---- 说明 ----
notes=['天花布置说明:','1. 全屋石膏板吊顶下吊200,完成面H=2950(以现场原顶实测为准)',
 '2. 厨卫/阳台铝扣板吊顶H=2950,设检修口300x300','3. 无主灯设计:筒灯射灯+灯带+吊灯分层',
 '4. 水电管网全部走吊顶内,墙面下引暗盒','5. 生活区3000K,厨卫作业区4000K','6. 灯位均为模型实测坐标,开孔前现场复尺']
ty=-2200
for t_ in notes:
    msp.add_text(t_,height=220,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((8200,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label(8500,-1600,'V15 天花布置图  A201   比例 1:50   版本 R2')
# ---- 尺寸链 ----
def dim_h(x0,x1,y,txt=None):
    msp.add_line((x0,y),(x1,y),dxfattribs={'layer':'A-DIMS'}) if 'A-DIMS' in [l.dxf.name for l in doc.layers] else msp.add_line((x0,y),(x1,y))
    for xx in (x0,x1):
        msp.add_line((xx,y-80),(xx,y+80))
        msp.add_line((xx,y+80),(xx,y+500))  # 引出线
    label((x0+x1)/2,y+280,txt or str(int(x1-x0)),200)
def dim_v(y0,y1,x,txt=None):
    msp.add_line((x,y0),(x,y1))
    for yy in (y0,y1):
        msp.add_line((x-80,yy),(x+80,yy))
        msp.add_line((x+80,yy),(x+600,yy))
    msp.add_text(txt or str(int(y1-y0)),height=200,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x+350,(y0+y1)/2),align=TextEntityAlignment.MIDDLE_CENTER)
    # 旋转90标注
    for e in list(msp)[-1:]:
        e.dxf.rotation=90
# 总尺寸
allb=[it['bbox'] for it in G['items']['wall'] if it['bbox'][2]-it['bbox'][0]>30 and it['bbox'][3]-it['bbox'][1]>30]
bx0=min(b[0] for b in allb); bx1=max(b[2] for b in allb)
by0=min(b[1] for b in allb); by1=max(b[3] for b in allb)
dim_h(bx0,bx1,by0-900,'总宽 '+str(int(bx1-bx0)))
dim_v(by0,by1,bx0-900,'总深 '+str(int(by1-by0)))
# 横向分段尺寸:取竖向承重墙的x位置
vx=sorted({round((b[0]+b[2])/2) for b in allb if (b[2]-b[0])<350 and (b[3]-b[1])>1500})
vx=[v for i,v in enumerate(vx) if i==0 or v-vx[i-1]>800]
vx=[bx0]+vx+[bx1]
yD=by0-500
for i in range(len(vx)-1):
    msp.add_line((vx[i],yD-60),(vx[i],yD+60)); msp.add_line((vx[i+1],yD-60),(vx[i+1],yD+60))
    msp.add_line((vx[i],yD),(vx[i+1],yD))
    label((vx[i]+vx[i+1])/2,yD+220,str(vx[i+1]-vx[i]),160)
# 纵向分段
hy=sorted({round((b[1]+b[3])/2) for b in allb if (b[3]-b[1])<350 and (b[2]-b[0])>1500})
hy=[v for i,v in enumerate(hy) if i==0 or v-hy[i-1]>800]
hy=[by0]+hy+[by1]
xD=bx0-500
for i in range(len(hy)-1):
    msp.add_line((xD-60,hy[i]),(xD+60,hy[i])); msp.add_line((xD-60,hy[i+1]),(xD+60,hy[i+1]))
    msp.add_line((xD,hy[i]),(xD,hy[i+1]))
    label(xD-320,(hy[i]+hy[i+1])/2,str(hy[i+1]-hy[i]),160)
# ---- 引线材质标注 ----
def leader(x0,y0,x1,y1,txt):
    msp.add_line((x0,y0),(x1,y1),dxfattribs={'layer':'A-TEXT'})
    msp.add_line((x1,y1),(x1+900,y1),dxfattribs={'layer':'A-TEXT'})
    msp.add_text(txt,height=180,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x1+450,y1+320),align=TextEntityAlignment.MIDDLE_CENTER)
leader(5300,10000,5300,12500,'客厅 石膏板吊顶 H=2950')
leader(6600,2500,6600,-300,'厨房 铝扣板 H=2950')
leader(9700,2000,9700,-300,'主卧 石膏板吊顶 H=2950')
leader(14600,5300,15600,5300,'主卫 铝扣板 H=2950')
# ---- 灯具数量表 ----
from collections import Counter
cnt=Counter()
for li in L:
    n=li['name']
    if 'DAYLIGHT' in n or 'SUN' in n.upper() and 'SUNROOM' not in n: continue
    if li['x']==0 and li['y']==0: continue
    if 'COVE' in n or 'UNDERCABINET' in n: cnt['灯带']+=1
    elif 'MIRRORBAR' in n: cnt['镜前灯']+=1
    elif 'Pendant' in n or 'Dining_warm' in n or 'LIGHT_' in n: cnt['吊灯/吸顶灯']+=1
    elif li['type']=='SPOT': cnt['筒灯/射灯']+=1
    elif li['type']=='POINT': cnt['台灯/落地灯']+=1
tx,ty=17000,13500
msp.add_lwpolyline([(tx,ty),(tx+4400,ty),(tx+4400,ty+1800),(tx,ty+1800)],close=True,dxfattribs={'layer':'A-WALL'})
msp.add_line((tx,ty+1400),(tx+4400,ty+1400),dxfattribs={'layer':'A-WALL'})
label(tx+2200,ty+1600,'灯具数量表',220)
row=ty+1100
for k,v in cnt.items():
    label(tx+1500,row,k,170); label(tx+3600,row,f'{v} 套',170); row-=400
# ---- 标题栏 ----
tb_x,tb_y=15000,-5600
msp.add_lwpolyline([(tb_x,tb_y),(tb_x+6800,tb_y),(tb_x+6800,tb_y+1600),(tb_x,tb_y+1600)],close=True,dxfattribs={'layer':'A-WALL'})
for dy in (400,800,1200):
    msp.add_line((tb_x,tb_y+dy),(tb_x+6800,tb_y+dy),dxfattribs={'layer':'A-WALL'})
for tx_ in (tb_x+1200,tb_x+4200):
    msp.add_line((tx_,tb_y),(tx_,tb_y+1600),dxfattribs={'layer':'A-WALL'})
label(tb_x+600,tb_y+1400,'项目',150); label(tb_x+2700,tb_y+1400,'V15 旧房改造(成都)',150)
label(tb_x+5400,tb_y+1400,'比例 1:50',150)
label(tb_x+600,tb_y+1000,'图名',150); label(tb_x+2700,tb_y+1000,'天花布置图',150)
label(tb_x+5400,tb_y+1000,'图号 A201',150)
label(tb_x+600,tb_y+600,'单位',150); label(tb_x+2700,tb_y+600,'mm(毫米)',150)
label(tb_x+5400,tb_y+600,'版本 R2',150)
label(tb_x+600,tb_y+200,'日期',150); label(tb_x+2700,tb_y+200,'2026-10',150)
label(tb_x+5400,tb_y+200,'照明设计',150)
doc.saveas(root/'cad/A201_天花布置图.dxf')
print('saved, rooms',len(rooms),'dims',len(vx)-1,'x',len(hy)-1)
