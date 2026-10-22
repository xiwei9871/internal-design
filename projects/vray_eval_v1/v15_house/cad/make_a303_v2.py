#!/usr/bin/env python3
# A303 v2 — 给排水点位图:基准底图 + 实测洁具点位 + 走顶路由说明
import ezdxf, shutil
from pathlib import Path
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
base=Path('/Users/xiwei/interior_design/projects/c_type_home/cad/C型_原始户型数字化基准图.dxf')
dst=root/'cad/A303_给排水点位图.dxf'
shutil.copy(base,dst)
doc=ezdxf.readfile(dst)
for n,c,w in [('A-PLUM-C',5,0.30),('A-PLUM-H',1,0.30),('A-PLUM-D',6,0.35),('A-FIXT',4,0.20),('A-NOTE',7,0.25)]:
    if n not in [l.dxf.name for l in doc.layers]:
        lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
try: doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
except: pass
msp=doc.modelspace()
def label(x,y,txt,h=170,layer='A-NOTE'):
    msp.add_text(txt,height=h,dxfattribs={'layer':layer,'style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def cold(x,y):   # 冷水点
    msp.add_circle((x,y),80,dxfattribs={'layer':'A-PLUM-C'})
    msp.add_line((x-80,y),(x+80,y),dxfattribs={'layer':'A-PLUM-C'})
def hot(x,y):    # 热水点
    c=msp.add_circle((x,y),80,dxfattribs={'layer':'A-PLUM-H'})
    msp.add_line((x-80,y),(x+80,y),dxfattribs={'layer':'A-PLUM-H'})
def drain(x,y,d=110):  # 排水点
    r=90
    msp.add_lwpolyline([(x,y+r),(x+r,y),(x,y-r),(x-r,y)],close=True,dxfattribs={'layer':'A-PLUM-D'})
def floordrain(x,y):   # 地漏
    msp.add_circle((x,y),100,dxfattribs={'layer':'A-PLUM-D'})
    msp.add_circle((x,y),55,dxfattribs={'layer':'A-PLUM-D'})
def fixture(b,name,dy=-450):
    x0,y0,x1,y1=b[:4]
    msp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],close=True,dxfattribs={'layer':'A-FIXT'})
    label((x0+x1)/2,(y0+y1)/2+dy,name)
# ---- 洁具轮廓+点位 ----
# 次卫
fixture((9419,4774,10420,5274),'台盆',-700)
hot(9710,4774); cold(10120,4774); drain(9915,4774);
label(9915,4500,'冷热水H450/排水DN50墙排')
fixture((10764,4936,11364,5436),'马桶')
cold(11200,4936); drain(10964,4936,150)
label(10964,4300,'马桶坑距305/400待现场复尺',140)
floordrain(11170,6140); label(11170,6450,'地漏DN75',140)
fixture((9228,5925,10228,6425),'台盆2')
hot(9510,5925); cold(9950,5925); drain(9730,5925)
# 主卫
fixture((13139,5773,14338,6273),'台盆',-700)
hot(13380,5773); cold(14050,5773); drain(13730,5773)
fixture((14483,5936,14983,6586),'马桶')
cold(14983,6300); drain(14733,5936,150)
label(14733,5300,'马桶坑距305/400待现场复尺',140)
floordrain(15700,5400); label(15700,5100,'淋浴地漏DN75(位待现场)',140)
label(15600,6000,'淋浴区冷热水 H1050',150)
hot(15600,6200); cold(15600,5800); drain(15800,4800)
# 客卫(含淋浴+洗衣机)
fixture((7737,8312,8937,8912),'台盆')
hot(8200,8312); cold(8600,8312); drain(8400,8312)
fixture((7985,9121,8309,9868),'马桶')
cold(8309,9500); drain(8147,9121,150)
label(8147,10100,'马桶坑距待复尺',140)
fixture((9188,10399,9638,10849),'洗衣机',350)
cold(9413,10100); drain(9513,10649,120)
label(9413,10900,'洗衣机:冷水DN20+排水DN50',140)
msp.add_lwpolyline([(8034,9824),(9677,9824),(9677,9904),(8034,9904)],close=True,dxfattribs={'layer':'A-FIXT'})
label(8850,10050,'淋浴隔断上轨(湿区在北)',140)
floordrain(8850,10450); label(8850,10750,'淋浴地漏DN75',140)
hot(8300,10000); cold(8600,10000)
# 厨房
fixture((6195,85,6995,515),'水槽',-500)
hot(6350,85); cold(6750,85); drain(6550,85)
label(6550,-500,'水槽:冷热水+排水DN50',140)
# 生活阳台
label(3300,1525,'生活阳台:拖把池/备用水点待确认',150)
cold(5500,1500); drain(5300,1500)
# ---- 走顶路由示意(虚线干线) ----
routes=[(10964,4936,10964,6600),(14733,5936,14733,6600),(8147,9121,7800,9121),
 (9915,5274,9915,6600),(13730,6273,13730,6600),(8400,8912,8400,9200),
 (6550,85,6550,-200),(9413,10100,9413,10900)]
for x0,y0,x1,y1 in routes:
    ln=msp.add_line((x0,y0),(x1,y1),dxfattribs={'layer':'A-PLUM-D'})
# ---- 图例 ----
lg_x,lg_y=1300,-5400
msp.add_lwpolyline([(lg_x,lg_y),(lg_x+6800,lg_y),(lg_x+6800,lg_y+3000),(lg_x,lg_y+3000)],close=True,dxfattribs={'layer':'A-WALL'})
label(lg_x+3400,lg_y+2700,'图  例',300)
cold(lg_x+800,lg_y+2000); label(lg_x+2900,lg_y+2000,'冷水点 DN20 PPR',170)
hot(lg_x+800,lg_y+1300); label(lg_x+2900,lg_y+1300,'热水点 DN20 PPR',170)
drain(lg_x+800,lg_y+600); label(lg_x+2900,lg_y+600,'排水点 DN50/DN110',170)
floordrain(lg_x+5600,lg_y+2000); label(lg_x+5600,lg_y+1600,'地漏 DN75',170)
# ---- 说明 ----
notes=['给排水说明:','1. 全屋冷热水走吊顶内敷设,墙面下引,旧房改造',
 '2. 给水PPR DN20,热水套保温;排水PVC-U DN50(台盆/地漏)/DN110(马桶)',
 '3. 马桶坑距、主排水立管位置、水表井均须现场复尺后定',
 '4. 卫生间地面找坡1%向地漏,防水上翻墙面300(淋浴区1800)',
 '5. 热水管与冷水管间距>=150,左热右冷','6. 所有点位以现场结构实测为准']
ty=-2200
for t_ in notes:
    msp.add_text(t_,height=220,dxfattribs={'layer':'A-NOTE','style':'HZTXT'}).set_placement((8200,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label(8500,-1600,'V15 给排水点位图  A303   比例 1:50   版本 R2',280,'A-NOTE')
doc.saveas(dst)
print('saved')
