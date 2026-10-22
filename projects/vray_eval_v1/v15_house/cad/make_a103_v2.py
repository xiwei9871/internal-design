#!/usr/bin/env python3
# A103 v2 — 基准户型图(C型FCStd DXF)为底 + 设计家具/洁具叠加
import json, ezdxf, shutil
from pathlib import Path
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
base=Path('/Users/xiwei/interior_design/projects/c_type_home/cad/C型_原始户型数字化基准图.dxf')
dst=root/'cad/A103_平面布置图.dxf'
shutil.copy(base,dst)
doc=ezdxf.readfile(dst)
G=json.loads((root/'cad/plan_geom.json').read_text())
for n,c,w in [('A-FURN',8,0.18),('A-FIXT',4,0.25),('A-DESIGN',1,0.30)]:
    if n not in [l.dxf.name for l in doc.layers]:
        lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
try: doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
except: pass
msp=doc.modelspace()
def label(x,y,txt,h=230,layer='A-TEXT'):
    msp.add_text(txt,height=h,dxfattribs={'layer':layer,'style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
# 家具轮廓(过滤原点/零尺寸/灯具对象)
SKIP=('LIGHT_','DAYLIGHT','LAMP_','_LAMP','MIRROR')
placed=0
for it in G['items']['furniture']:
    b=it['bbox']; w,h=b[2]-b[0],b[3]-b[1]
    if w<150 or h<150 or (b[0]==0 and b[2]==0): continue
    if any(k in it['name'] for k in SKIP): continue
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':'A-FURN'})
    placed+=1
for it in G['items']['fixture']:
    b=it['bbox']; w,h=b[2]-b[0],b[3]-b[1]
    if w<150 or h<150 or (b[0]==0 and b[2]==0): continue
    msp.add_lwpolyline([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])],close=True,dxfattribs={'layer':'A-FIXT'})
    placed+=1
# 设计房间名(布局改动区):基准名->设计名
DESIGN=[(5025,10325,'客厅'),(4000,5230,'餐厅/玄关'),(3300,1525,'生活阳台'),
 (6525,2225,'厨房'),(9415,2225,'主卧'),(13150,2225,'母卧'),
 (11075,9350,'客卧'),(14400,8925,'书房'),(8475,9350,'客卫'),
 (14400,5475,'主卫'),(10150,12150,'阳光房'),(10250,5400,'次卫/干区')]
for x,y,t in DESIGN: label(x,y+350,t,260,'A-DESIGN')
label(8500,-1400,'V15 平面布置图  A103   比例 1:50   底图:C型原始户型数字化基准',280,'A-TEXT')
doc.saveas(dst)
print('A103 v2 saved, furn+fixt outlines:',placed)
