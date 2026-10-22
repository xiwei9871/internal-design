#!/usr/bin/env python3
# A303 给排水点位图 — 顶内敷设给水管,排水按现状
import json, ezdxf, re
from pathlib import Path
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
G=json.loads((root/'cad/plan_geom.json').read_text())
doc=ezdxf.new('R2010'); doc.header['$INSUNITS']=4; doc.units=4
LAYERS=[('A-WALL',7,0.50),('A-PLUM-CW',5,0.35),('A-PLUM-HW',1,0.35),
        ('A-PLUM-DW',4,0.35),('A-FIXT',7,0.30),('A-TEXT',7,0.25),('A-TITLE',7,0.50)]
for n,c,w in LAYERS:
    lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
msp=doc.modelspace()
def label(x,y,txt,h=170,layer='A-TEXT'):
    msp.add_text(txt,height=h,dxfattribs={'layer':layer,'style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def rect(b,layer):
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':layer})
def cw(x,y,t='冷水'):   # 冷水点
    msp.add_circle((x,y),70,dxfattribs={'layer':'A-PLUM-CW'})
    msp.add_line((x-70,y),(x+70,y),dxfattribs={'layer':'A-PLUM-CW'})
def hw(x,y,t=''):      # 热水点
    msp.add_circle((x,y),70,dxfattribs={'layer':'A-PLUM-HW'})
    msp.add_line((x-70,y-70),(x+70,y+70),dxfattribs={'layer':'A-PLUM-HW'})
def dw(x,y,dia='DN50'): # 排水点
    msp.add_circle((x,y),90,dxfattribs={'layer':'A-PLUM-DW'})
    msp.add_circle((x,y),40,dxfattribs={'layer':'A-PLUM-DW'})
    label(x,y-240,dia,130,'A-PLUM-DW')
def tag(x,y,t): label(x,y-150,t,140)
for it in G['items']['wall']: rect(it['bbox'],'A-WALL')
for it in G['items']['fixture']: rect(it['bbox'],'A-FIXT')
# ---- 点位（按模型洁具位置） ----
# 次卫 (X9210-11400, Y4820-6450): 淋浴西北角,地漏11.1,6.1; 马桶~9.8,5.6; 台盆9.5,6.3
PTS=[
 # 次卫
 (cw,9550,6300,'台盆'),(hw,9700,6300,''),(dw,9625,6300,'DN50台盆下'),
 (cw,9800,5600,'马桶进水'),(dw,9800,5650,'DN110马桶'),
 (cw,11150,5600,'淋浴冷'),(hw,11150,5750,'淋浴热'),(dw,11170,6135,'DN75地漏'),
 # 主卫
 (cw,14200,6200,'台盆'),(hw,14350,6200,''),(dw,14275,6200,'DN50'),
 (cw,13700,5000,'马桶'),(dw,13700,5050,'DN110'),
 (cw,15500,5600,'淋浴冷'),(hw,15500,5750,'淋浴热'),(dw,15450,5100,'DN75地漏'),
 # 客卫
 (cw,9400,10400,'台盆'),(hw,9550,10400,''),(dw,9475,10400,'DN50'),
 (cw,8800,9800,'马桶'),(dw,8800,9850,'DN110'),
 # 厨房
 (cw,6300,400,'水槽冷'),(hw,6300,550,'水槽热'),(dw,6300,480,'DN50水槽'),
 (cw,8100,400,'冰箱净水?'),
 # 阳台洗衣
 (cw,10400,13600,'洗衣机冷'),(dw,10400,13650,'DN50洗衣排'),
 (dw,2900,800,'DN50阳台地漏'),
]
for fn,x,y,*a in PTS: fn(x,y,*a)
allb=[it['bbox'] for k in ('wall','floor') for it in G['items'][k]]
x0=min(b[0] for b in allb); y0=min(b[1] for b in allb); x1=max(b[2] for b in allb)
notes=[
 '给排水说明:',
 '1. 冷热水管全部顶内敷设,PPR热水管保温,下引至墙面点位',
 '2. 马桶坑距按现状(估计305/400),移位器如需>100mm需抬高地面或改排污',
 '3. 淋浴地漏DN75,洗衣机/水槽DN50,全部留沉水弯',
 '4. 卫生间做等电位联结LEB',
 '5. 冷热水间距150,左热右冷',
]
ty=y0-1400
for t in notes:
    msp.add_text(t,height=220,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x0,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label((x0+x1)/2,y0-700,'V15 给排水点位图  A303   比例 1:50   单位:mm   版本 R1',300,layer='A-TITLE')
doc.saveas(root/'cad/A303_给排水点位图.dxf')
print('A303 saved, points:',len(PTS))
