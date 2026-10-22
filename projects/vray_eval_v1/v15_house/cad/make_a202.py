#!/usr/bin/env python3
# A202 地面铺装图
import json, ezdxf, re
from pathlib import Path
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
G=json.loads((root/'cad/plan_geom.json').read_text())
doc=ezdxf.new('R2010'); doc.header['$INSUNITS']=4; doc.units=4
LAYERS=[('A-WALL',7,0.50),('A-HATCH-WOOD',8,0.18),('A-HATCH-TILE',4,0.18),
        ('A-TEXT',7,0.25),('A-TITLE',7,0.50),('A-DIMS',1,0.18),('A-FIXT',4,0.30)]
for n,c,w in LAYERS:
    lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
msp=doc.modelspace()
def label(x,y,txt,h=280,layer='A-TEXT'):
    msp.add_text(txt,height=h,dxfattribs={'layer':layer,'style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def rect(b,layer):
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':layer})
def hatch_rect(b,spacing,vertical=True,layer='A-HATCH-WOOD'):
    # 简化铺装线：平行线填充
    x0,y0,x1,y1=b[:4]
    if vertical:
        x=x0+spacing
        while x<x1:
            msp.add_line((x,y0),(x,y1),dxfattribs={'layer':layer}); x+=spacing
    else:
        y=y0+spacing
        while y<y1:
            msp.add_line((x0,y),(x1,y),dxfattribs={'layer':layer}); y+=spacing
def tile_grid(b,cell=600):
    hatch_rect(b,cell,True,'A-HATCH-TILE'); hatch_rect(b,cell,False,'A-HATCH-TILE')
# ---- 墙体 ----
for it in G['items']['wall']: rect(it['bbox'],'A-WALL')
# ---- 已知的房间地板矩形 ----
TILE_ROOMS=re.compile('bath|kitchen|balcony|sunroom',re.I)
for it in G['items']['floor']:
    n=it['name']; b=it['bbox']
    if not (n.startswith('PRESENTATION_') or n=='R3_BATH_FLOOR'): continue
    if TILE_ROOMS.search(n):
        tile_grid(b);
    else:
        hatch_rect(b,120,False,'A-HATCH-WOOD')
# ---- 手工补充:左半区房间(模型无独立地板对象) ----
EXTRA=[((1800,8000,8200,11900),'wood'),   # 客厅
       ((3400,3000,6100,6600),'wood'),   # 餐厅
       ((6100,300,8100,3900),'tile'),    # 厨房
       ((3400,4800,6100,6600),'wood'),   # 玄关(并入餐区边界内示意)
       ((1600,300,5600,2700),'tile'),   # 生活阳台
       ((1600,3900,3400,6600),'wood'),  # 玄关前厅
       ((6100,6600,8100,8000),'wood'),  # 客厅南侧过渡带
       ((9900,11000,13100,13700),'tile'),# 阳光房/北阳台
       ((8000,4500,8600,4800),'wood'),  # 主卧进门凹位
       ((6100,3900,8100,4800),'wood')]  # 厨餐过渡/玄关东段
for b,kind in EXTRA:
    if kind=='tile': tile_grid(list(b))
    else: hatch_rect(list(b),120,False,'A-HATCH-WOOD')
# ---- 材料标注（房中心） ----
MATS=[('主卧\n白蜡木实木复合地板',9700,2350),('母卧\n白蜡木实木复合地板',13450,2350),
 ('客卧\n白蜡木实木复合地板',11400,9450),('次卫\n防滑地砖 600x600',10305,5635),
 ('主卫\n防滑地砖 600x600',14650,5550),('客卫\n防滑地砖 600x600',8850,9450),
 ('书房\n白蜡木实木复合地板',14650,8750),('走廊\n白蜡木实木复合地板',10600,7200),
 ('厨房\n防滑地砖 600x600',6800,2200),('客厅\n白蜡木实木复合地板',5300,9300),
 ('餐厅\n白蜡木实木复合地板',4300,3500),('玄关\n地砖 600x600',4300,5600),
 ('生活阳台\n防滑地砖',3600,1500),('阳光房\n木纹砖/户外砖',10400,12300)]
for t,x,y in MATS: label(x,y,t,240)
# ---- 门槛石（门口示意，按door对象中心） ----
for it in G['items']['door'][:200]:
    b=it['bbox']
    w=b[2]-b[0]; h=b[3]-b[1]
    if w<200 or h<200 or w>1500 or h>1500: continue
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,
        dxfattribs={'layer':'A-FIXT','linetype':'DASHED'})
# ---- 说明 ----
allb=[it['bbox'] for k in ('wall','floor') for it in G['items'][k]]
x0=min(b[0] for b in allb); y0=min(b[1] for b in allb); x1=max(b[2] for b in allb)
notes=[
 '地面说明:',
 '1. 居室白蜡木实木复合地板通铺(方向同南北向),起铺点客厅西南角',
 '2. 厨卫阳台防滑地砖600x600,卫生间找坡1%向地漏',
 '3. 门槛石:厨卫门口大理石门槛石,宽同门洞',
 '4. 地暖无(成都),木地板垫层2mm',
 '5. 踢脚线:白蜡木同色T型条,高60',
]
ty=y0-1400
for t in notes:
    msp.add_text(t,height=220,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x0,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label((x0+x1)/2,y0-700,'V15 地面铺装图  A202   比例 1:50   单位:mm   版本 R1',300,layer='A-TITLE')
doc.saveas(root/'cad/A202_地面铺装图.dxf')
print('A202 saved')
