#!/usr/bin/env python3
# A103 平面布置图 — 从 plan_geom.json 出 DXF
import json, ezdxf, re
from ezdxf.enums import TextEntityAlignment
from pathlib import Path
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
G=json.loads((root/'cad/plan_geom.json').read_text())
doc=ezdxf.new('R2010')
doc.header['$INSUNITS']=4  # mm
doc.units=4
# ---- 图层 ----
LAYERS=[('A-WALL',7,0.50),('A-FURN',8,0.25),('A-FIXT',4,0.35),
        ('A-DOOR',3,0.25),('A-WINDOW',2,0.25),('A-DIMS',1,0.18),
        ('A-TEXT',7,0.25),('A-HATCH',9,0.18),('A-TITLE',7,0.50)]
for n,c,w in LAYERS:
    lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
msp=doc.modelspace()
def rect(b,layer):
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':layer})
def label(x,y,txt,h=250,layer='A-TEXT',align=TextEntityAlignment.MIDDLE_CENTER):
    t=msp.add_text(txt,height=h,dxfattribs={'layer':layer,'style':'HZTXT'})
    t.set_placement((x,y),align=align)
# ---- 墙体：投影box填充 ----
for it in G['items']['wall']:
    rect(it['bbox'],'A-WALL')
    msp.add_hatch(color=9,dxfattribs={'layer':'A-HATCH'}).paths.add_polyline_path(
        [(it['bbox'][0],it['bbox'][1]),(it['bbox'][2],it['bbox'][1]),(it['bbox'][2],it['bbox'][3]),(it['bbox'][0],it['bbox'][3])],is_closed=True)
# ---- 房间地板轮廓 + 房名 ----
ROOM_CN={'couple_bedroom':'主卧','mother_bedroom':'母卧','guest_bedroom':'客卧',
 'secondary_bath':'次卫','master_bath':'主卫','guest_bath':'客卫','study':'书房',
 'hallway':'走廊','kitchen':'厨房','living':'客厅','service_balcony':'生活阳台',
 'entry':'玄关','dining':'餐厅','sunroom':'阳光房','north_sunroom':'北阳光房'}
def roomname(n):
    for k,v in ROOM_CN.items():
        if k in n: return v
    return n.replace('PRESENTATION_FLOOR_','').replace('PRESENTATION_TILE_','')
ROOMS=[('主卧',9700,2350),('母卧',13450,2350),('客卧',11400,9450),('次卫',10305,5635),
 ('主卫',14650,5550),('客卫',8850,9450),('书房',14650,8750),('走廊',10600,7200),
 ('厨房',6800,2200),('客厅',5300,9300),('餐厅',4300,3500),('玄关',4300,5600),
 ('生活阳台',3600,1500),('阳光房',10400,12300)]
for rn,cx,cy in ROOMS: label(cx,cy,rn,350)
# ---- 门窗 ----
for it in G['items']['window']: rect(it['bbox'],'A-WINDOW')
for it in G['items']['door']: rect(it['bbox'],'A-DOOR')
# ---- 洁具设备 ----
FIX_CN={'TOILET':'马桶','SINK':'台盆','SHOWER_TRAY':'淋浴','SHOWER_DRAIN':'地漏',
 'BATHTUB':'浴缸','VANITY':'浴室柜','WASHER':'洗衣机','MACHINE':'机','HOB':'灶',
 'STOVE':'灶','FRIDGE':'冰箱','REFRIGERATOR':'冰箱','OVEN':'烤箱','AC':'空调','RADIATOR':'暖气'}
def fixname(n):
    for k,v in FIX_CN.items():
        if k in n: return v
    return ''
for it in G['items']['fixture']:
    b=it['bbox']; rect(b,'A-FIXT')
    fn=fixname(it['name'])
    if fn: label((b[0]+b[2])/2,(b[1]+b[3])/2-60,fn,140)
# ---- 家具 ----
FURN_CN={'SOFA':'沙发','CHAIS':'躺椅','_BED':'床','CHAIR':'椅','TABLE':'桌','COFFEE':'茶几',
 'CONSOLE':'柜','DRESSER':'柜','SHELF':'架','CABINET':'柜','WARDROBE':'衣柜','DESK':'书桌',
 'BENCH':'凳','STOOL':'凳','POUF':'墩','HEADBOARD':'床头','NIGHTSTAND':'床头柜','TV':'电视',
 'CARPET':'地毯','CURTAIN':'窗帘','PLANT':'绿植','MIRROR':'镜','BOOKS':'书','VASE':'花瓶','BOWL':'碗'}
SKIP=re.compile('WELT|PIPING|SEAM|SUPPORT|SLAT|LEG|RAIL|DECK|ARM|UPRIGHT|PAD|CUSHION|FRAME',re.I)
def furname(n):
    for k,v in FURN_CN.items():
        if k in n: return v
    return ''
drawn=[]
for it in G['items']['furniture']:
    if SKIP.search(it['name']) or it['type']!='MESH': continue
    b=it['bbox']; rect(b,'A-FURN')
# ---- 外包尺寸链 ----
allb=[it['bbox'] for k in ('wall','floor') for it in G['items'][k]]
x0=min(b[0] for b in allb); y0=min(b[1] for b in allb)
x1=max(b[2] for b in allb); y1=max(b[3] for b in allb)
off=700
msp.add_aligned_dim(p1=(x0,y0-off),p2=(x1,y0-off),distance=-300,dxfattribs={'layer':'A-DIMS'}).render()
msp.add_aligned_dim(p1=(x1+off,y0),p2=(x1+off,y1),distance=300,dxfattribs={'layer':'A-DIMS'}).render()
# ---- 图签 ----
label((x0+x1)/2,y0-1600,'V15 全屋平面布置图  A103   比例 1:50   单位:mm   版本 R1   2026-10-16',300,layer='A-TITLE')
label((x0+x1)/2,y0-2100,'几何来源:V15_PBR.blend 锁定底模 | 家具为购买/定制示意,以产品为准 | 现场复尺确认',200)
doc.saveas(root/'cad/A103_平面布置图.dxf')
print('DXF saved')
