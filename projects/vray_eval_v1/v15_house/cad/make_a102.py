#!/usr/bin/env python3
# A102 墙体拆改图: 保留(细灰) + 拆除(红虚线) + 新建(粗黑)
import ezdxf, shutil
from pathlib import Path
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
base=Path('/Users/xiwei/interior_design/projects/c_type_home/cad/C型_原始户型数字化基准图.dxf')
dst=root/'cad/A102_墙体拆改图.dxf'
shutil.copy(base,dst)
doc=ezdxf.readfile(dst)
for n,c,w in [('A-EXIST',8,0.25),('A-DEMO',1,0.35),('A-NEW',7,0.50),('A-NOTE',7,0.25)]:
    if n not in [l.dxf.name for l in doc.layers]:
        lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
try: doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
except: pass
msp=doc.modelspace()
def bb(e):
    pts=[(float(p[0]),float(p[1])) for p in e.get_points('xy')]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return min(xs),min(ys),max(xs),max(ys)
def rect(x0,y0,x1,y1,layer,dash=False):
    at={'layer':layer}
    if dash: at['linetype']='DASHED'
    msp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],close=True,dxfattribs=at)
def label(x,y,txt,h=160,layer='A-NOTE'):
    msp.add_text(txt,height=h,dxfattribs={'layer':layer,'style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
# 1) 全部基准墙 → A-EXIST(细灰)
for e in msp:
    if e.dxftype()=='LWPOLYLINE' and e.dxf.layer=='A-WALL': e.dxf.layer='A-EXIST'
# 2) 拆除段:从保留层删掉整段,按拆除范围画红虚线
DEMO_FULL=[(2700,12750,7900,12950),(7900,13400,13000,13600)]  # 北墙旧带/阳光房北带整拆
DEMO_PART=[((5700,-150,5900,4700),(5700,1800,5900,3800)),      # 厨房西墙中段
           ((7800,4670,7900,13550),(7800,5000,7900,7800)),      # 走廊西墙中段
           ((1300,2400,5800,2560),(3300,2400,5800,2560))]       # 阳台北墙东段
for e in list(msp):
    if e.dxftype()!='LWPOLYLINE' or e.dxf.layer!='A-EXIST': continue
    b=bb(e)
    for d in DEMO_FULL:
        if all(abs(a-c)<300 for a,c in zip(b,d)):
            msp.delete_entity(e); rect(*d,'A-DEMO',True)
    for (whole,part) in DEMO_PART:
        if all(abs(a-c)<300 for a,c in zip(b,whole)):
            msp.delete_entity(e)
            # 剩余段(保留): whole minus part 按长轴拆
            x0,y0,x1,y1=whole; px0,py0,px1,py1=part
            if x1-x0 < y1-y0:  # 竖墙
                if y0<py0: rect(x0,y0,x1,py0,'A-EXIST')
                if py1<y1: rect(x0,py1,x1,y1,'A-EXIST')
            else:
                if x0<px0: rect(x0,y0,px0,y1,'A-EXIST')
                if px1<x1: rect(px1,y0,x1,y1,'A-EXIST')
            rect(*part,'A-DEMO',True)
# 3) 新建墙(粗黑)
NEW=[(9050,5120,9200,6450),(9209,4524,11400,4823),(9059,4507,9209,6507),(9200,6450,11400,6600),
 (9050,4942,9200,5150),(9050,5230,9200,6450),(11900,6400,13100,6600),
 (10850,7800,12900,8000),(8000,10900,9700,11100),(9900,10900,12900,11100),
 (13100,10900,13700,11100),(15600,10900,16200,11100),(13500,11100,13600,11700),
 (15700,11100,15800,11700),(13600,11700,15700,11800),(13100,11100,13500,11800),
 (2900,13000,3800,13200),(6900,13000,7800,13200),(7800,13000,8200,13400),
 (2700,13200,2900,14953),(3700,13790,7000,13900),(3600,13200,3700,13800),(7000,13200,7100,13800),
 (5900,0,7800,200),(8000,0,8600,200),(10800,0,11400,200),(11600,0,12200,200),(14700,0,15300,200),
 (8500,-700,10900,-600),(12100,-700,14800,-600),(8400,-600,8500,0),(10900,-600,11000,0),
 (12000,-600,12100,0),(14700,-600,14900,0),(7450,150,7800,500),(7400,200,7800,500)]
for nb in NEW: rect(*nb,'A-NEW')
# 4) 标注
label(5800,3300,'拆除',180,'A-DEMO'); label(7850,6600,'拆除',180,'A-DEMO')
label(4500,2500,'拆除',180,'A-DEMO'); label(5300,12850,'拆除',180,'A-DEMO')
label(10200,4700,'新建',180,'A-NEW'); label(10900,6750,'新建',180,'A-NEW')
label(11400,7900,'新建',180,'A-NEW'); label(5400,13150,'新建',180,'A-NEW')
# 5) 图例+说明+标题
lx,ly=1300,-5600
msp.add_lwpolyline([(lx,ly),(lx+7800,ly),(lx+7800,ly+2400),(lx,ly+2400)],close=True,dxfattribs={'layer':'A-EXIST'})
label(lx+3900,ly+2100,'图  例',300)
rect(lx+500,ly+1500,lx+1800,ly+1620,'A-DEMO',True); label(lx+4300,ly+1560,'拆除墙体',170)
rect(lx+500,ly+700,lx+1800,ly+880,'A-NEW'); label(lx+4300,ly+790,'新建墙体',170)
msp.add_lwpolyline([(lx+5800,ly+750),(lx+6600,ly+750)],dxfattribs={'layer':'A-EXIST'})
label(lx+7100,ly+750,'保留墙体',170,'A-NOTE')
notes=['墙体拆改说明:','1. 本图依据原户型基准图与改造设计模型比对生成,未标注墙体均为保留',
 '2. 拆除段: 厨房西墙中段(改开放式厨房)、走廊西墙中段(楼梯向走廊敞开)、阳台北墙东段、客厅北墙旧带、阳光房北带',
 '3. 新建段: 次卫四周隔墙及门垛、客卫/客卧北墙、书房/阳光房分格墙、走廊南墙东段、客厅北墙新线(中段为窗)',
 '4. 生活阳台西/南墙按原状保留(模型遗漏已更正)','5. 所有拆改须现场复尺确认结构后实施,承重构件严禁拆改',
 '6. 新增门洞/垛位以平面布置图A103为准']
ty=-2200
for t_ in notes:
    msp.add_text(t_,height=220,dxfattribs={'layer':'A-NOTE','style':'HZTXT'}).set_placement((8200,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label(8500,-1600,'V15 墙体拆改图  A102   比例 1:50   版本 R1',280)
doc.saveas(dst)
print('saved A102')
