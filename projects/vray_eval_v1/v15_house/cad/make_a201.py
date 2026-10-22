#!/usr/bin/env python3
# A201 天花布置图 — 大平顶200mm下吊 + 无主灯灯具定位
import json, ezdxf, math
from pathlib import Path
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
G=json.loads((root/'cad/plan_geom.json').read_text())
L=json.loads((root/'cad/lights.json').read_text())
doc=ezdxf.new('R2010'); doc.header['$INSUNITS']=4; doc.units=4
LAYERS=[('A-WALL',7,0.50),('A-CEIL',5,0.35),('A-ELEC',1,0.35),
        ('A-DIMS',1,0.18),('A-TEXT',7,0.25),('A-TITLE',7,0.50),('A-WINDOW',2,0.25)]
for n,c,w in LAYERS:
    lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
msp=doc.modelspace()
def rect(b,layer):
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':layer})
def label(x,y,txt,h=250,layer='A-TEXT'):
    msp.add_text(txt,height=h,dxfattribs={'layer':layer,'style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def downlight(x,y):
    msp.add_circle((x,y),80,dxfattribs={'layer':'A-ELEC'})
    msp.add_line((x-110,y),(x+110,y),dxfattribs={'layer':'A-ELEC'})
    msp.add_line((x,y-110),(x,y+110),dxfattribs={'layer':'A-ELEC'})
def cove(x0,y0,x1,y1):
    msp.add_line((x0,y0),(x1,y1),dxfattribs={'layer':'A-CEIL','linetype':'DASHED'})
    msp.add_lwpolyline([(x0,y0),(x1,y1)],dxfattribs={'layer':'A-CEIL'})
def spot(x,y):
    msp.add_circle((x,y),60,dxfattribs={'layer':'A-ELEC'})
    msp.add_circle((x,y),100,dxfattribs={'layer':'A-ELEC'})
def pendant(x,y):
    msp.add_circle((x,y),90,dxfattribs={'layer':'A-ELEC'})
    msp.add_line((x-90,y-90),(x+90,y+90),dxfattribs={'layer':'A-ELEC'})
# ---- 墙体外轮廓 ----
for it in G['items']['wall']: rect(it['bbox'],'A-WALL')
for it in G['items']['window']: rect(it['bbox'],'A-WINDOW')
# ---- 房名 ----
ROOMS=[('主卧',9700,2350),('母卧',13450,2350),('客卧',11400,9450),('次卫',10305,5635),
 ('主卫',14650,5550),('客卫',8850,9450),('书房',14650,8750),('走廊',10600,7200),
 ('厨房',6800,2200),('客厅',5300,9300),('餐厅',4300,3500),('玄关',4300,5600),
 ('生活阳台',3600,1500),('阳光房',10400,12300)]
for rn,x,y in ROOMS: label(x,y,rn,300)
# ---- 灯具 ----
LAMP_CN={'DL':'筒灯','SPOT':'射灯','COVE':'灯带','MIRRORBAR':'镜前灯','FLOORLAMP':'落地灯',
 'DESKLAMP':'台灯','LAMP':'床头灯','Pendant':'吊灯','Dining':'餐吊灯'}
placed={}
for l in L:
    n=l['name']; x,y=l['pos'][0],l['pos'][1]
    if abs(x)<10 and abs(y)<10: continue
    key=(round(x),round(y))
    if key in placed: continue
    placed[key]=True
    if l['type']=='SUN': continue
    if n.startswith('DAYLIGHT_') or 'DAYLIGHT_THROUGH' in n: continue
    if '_DL' in n or n.endswith('_DL'): downlight(x,y); tag='筒灯'
    elif 'SPOT' in n: spot(x,y); tag='射灯'
    elif 'COVE' in n: spot(x,y); tag='灯带(槽)'
    elif 'MIRRORBAR' in n: cove(x-300,y,x+300,y); tag='镜前灯带'
    elif 'FLOORLAMP' in n or 'DESKLAMP' in n or 'LAMP_' in n: pendant(x,y); tag='台灯/落地灯'
    elif 'Pendant' in n or 'Dining' in n: pendant(x,y); tag='吊灯'
    elif n.startswith('LIGHT_'): downlight(x,y); tag='环境补光'
    else: downlight(x,y); tag='灯'
# ---- 设计说明 ----
allb=[it['bbox'] for k in ('wall','floor') for it in G['items'][k]]
x1=max(b[2] for b in allb); y0=min(b[1] for b in allb); x0=min(b[0] for b in allb)
notes=[
 '天花说明:',
 '1. 全屋大平顶下吊200mm,完成面净高以现场复尺为准(原顶~2950,完成~2750)',
 '2. 所有筒灯/射灯内嵌吊顶,磁吸轨道备选',
 '3. 灯带暗藏于吊顶边槽/床头板后/镜前',
 '4. 水电走线全部顶内敷设,厨卫吊顶留检修口400x400',
 '5. 灯具回路:客餐厅1路/卧室各1路/厨卫各1路(漏电保护)',
 '6. 色温:居室3000K,厨卫4000K',
]
ty=y0-1400
for t in notes:
    msp.add_text(t,height=220,dxfattribs={'layer':'A-TEXT','style':'HZTXT'}).set_placement((x0,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label((x0+x1)/2,y0-700,'V15 天花布置图  A201   比例 1:50   单位:mm   版本 R1',300,layer='A-TITLE')
doc.saveas(root/'cad/A201_天花布置图.dxf')
print('A201 saved, lamps placed:',len(placed))
