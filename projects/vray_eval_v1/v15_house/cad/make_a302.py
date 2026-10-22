#!/usr/bin/env python3
# A302 电气点位图 — 旧房改造,线路全部顶内敷设,墙面下引暗盒
import json, ezdxf
from pathlib import Path
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
G=json.loads((root/'cad/plan_geom.json').read_text())
doc=ezdxf.new('R2010'); doc.header['$INSUNITS']=4; doc.units=4
LAYERS=[('A-WALL',7,0.50),('A-ELEC',1,0.35),('A-ELEC-SW',3,0.35),
        ('A-TEXT',7,0.25),('A-TITLE',7,0.50),('A-WINDOW',2,0.25)]
for n,c,w in LAYERS:
    lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
msp=doc.modelspace()
def label(x,y,txt,h=180,layer='A-TEXT'):
    msp.add_text(txt,height=h,dxfattribs={'layer':layer,'style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def rect(b,layer):
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':layer})
# 图例符号
def socket(x,y,h,note=''):
    # 五孔插座：方框内三角
    msp.add_lwpolyline([(x-90,y-90),(x+90,y-90),(x,y+90)],close=True,dxfattribs={'layer':'A-ELEC'})
    label(x,y-260,f'H{h}',140,'A-ELEC')
    if note: label(x,y+160,note,130,'A-ELEC')
def network(x,y,h):
    msp.add_lwpolyline([(x-90,y-90),(x+90,y-90),(x+90,y+90),(x-90,y+90)],close=True,dxfattribs={'layer':'A-ELEC'})
    msp.add_line((x-90,y),(x+90,y),dxfattribs={'layer':'A-ELEC'})
    label(x,y-260,f'网络 H{h}',140,'A-ELEC')
def switch(x,y,gang=2):
    msp.add_circle((x,y),70,dxfattribs={'layer':'A-ELEC-SW'})
    for i in range(gang):
        msp.add_line((x,y),(x+140,y+60+i*40),dxfattribs={'layer':'A-ELEC-SW'})
    label(x,y-220,f'开关{gang}联 H1350',130,'A-ELEC-SW')
# ---- 墙体 ----
for it in G['items']['wall']: rect(it['bbox'],'A-WALL')
for it in G['items']['window']: rect(it['bbox'],'A-WINDOW')
# ============ 点位设计 ============
# (函数,x,y,高度,注释)
PTS=[
 # 客厅（北墙Y~11900,南墙靠走廊）
 (socket,4200,11600,300,'五孔'),(socket,4600,11600,300,'五孔'),(socket,5000,11600,300,'电视'),(network,5400,11600,300),
 (socket,2900,8800,300,'沙发边'),(socket,7600,10800,300,'落地灯'),
 (socket,7200,11600,2200,'空调16A'),
 # 餐厅/玄关
 (socket,3400,3600,300,'餐边'),(socket,3400,5600,300,'玄关'),
 # 厨房(南墙Y~400)
 (socket,6100,400,1200,'台面'),(socket,6600,400,1200,'台面'),(socket,7100,400,1200,'台面'),
 (socket,7600,400,1200,'台面'),(socket,6300,400,500,'水槽下'),(socket,8100,400,300,'冰箱'),
 (socket,7400,400,2200,'油烟机16A'),
 # 主卧（南墙Y~300）
 (socket,8900,300,700,'床头'),(socket,10500,300,700,'床头'),
 (socket,9700,4500,300,'电视'),(socket,9200,4500,300,'五孔'),(network,10200,4500,300),
 (socket,11400,4300,2200,'空调16A'),(socket,8200,300,300,'备用'),
 # 母卧
 (socket,12550,300,700,'床头'),(socket,14250,300,700,'床头'),
 (socket,13400,4500,300,'电视'),(socket,15600,4200,2200,'空调16A'),
 # 客卧（北墙Y~10700）
 (socket,10600,10700,700,'床头'),(socket,12200,10700,700,'床头'),
 (socket,11400,8300,300,'五孔'),(socket,12900,8500,2200,'空调16A'),
 # 书房
 (socket,14200,7000,300,'桌下'),(socket,14600,7000,300,'五孔'),(network,15000,7000,300),
 (socket,15600,8000,2200,'空调16A'),(socket,15200,10900,300,'备用'),
 # 次卫（北墙Y~6400）
 (socket,9600,6400,400,'智能马桶'),(socket,11200,6000,1400,'吹风机IPX4'),
 # 主卫
 (socket,14000,6200,400,'智能马桶'),(socket,15900,5600,1400,'吹风机IPX4'),
 # 客卫
 (socket,8200,10500,400,'智能马桶'),(socket,9700,10000,1400,'吹风机IPX4'),
 # 走廊/阳光房/阳台
 (socket,9000,6800,300,'吸尘器'),(socket,10400,13600,1300,'洗衣机'),
 (socket,2900,1000,300,'阳台备用'),
 # 开关（各房门边H1350）
 (switch,7600,6600,2),(switch,8800,4600,2),(switch,12000,4600,2),  # 客厅/主卧/母卧门口
 (switch,11500,7900,2),(switch,14400,6800,1),(switch,9200,8000,1),   # 客卧/书房/客卫
 (switch,12000,5000,1),(switch,15200,4800,1),(switch,3600,4800,1),   # 次卫/主卫/玄关
 (switch,9400,300,2),(switch,13100,300,2),(switch,11000,10700,2),    # 卧室床头双控
]
for fn,x,y,*a in PTS:
    fn(x,y,*a)
# 图例
lx=x0 if (x0:=200) else 200
legend=[('符号:',''),('▷ 五孔插座(方框三角)','H300一般/台面H1200/床头H700/空调H2200'),
 ('□ 网络口','H300'),('○ 开关','H1350,卧室床头双控'),('供电:','全部顶内桥架+墙面下引,PVC线管'),]
ty=-1800
for t,n in legend:
    msp.add_text(f'{t} {n}',height=200,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((400,ty),align=TextEntityAlignment.LEFT)
    ty-=350
allb=[it['bbox'] for k in ('wall','floor') for it in G['items'][k]]
x1=max(b[2] for b in allb); y0=min(b[1] for b in allb); x0=min(b[0] for b in allb)
label((x0+x1)/2,y0-700,'V15 电气点位图  A302   比例 1:50   单位:mm   版本 R1(待业主审核)',300,layer='A-TITLE')
doc.saveas(root/'cad/A302_电气点位图.dxf')
print('A302 saved, points:',len(PTS))
