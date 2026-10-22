#!/usr/bin/env python3
# A302 v2 — 电气点位图:基准底图 + 家具定位的插座/开关/网口
import ezdxf, shutil
from pathlib import Path
from ezdxf.enums import TextEntityAlignment
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
base=Path('/Users/xiwei/interior_design/projects/c_type_home/cad/C型_原始户型数字化基准图.dxf')
dst=root/'cad/A302_电气点位图.dxf'
shutil.copy(base,dst)
doc=ezdxf.readfile(dst)
for n,c,w in [('A-ELEC-SOC',1,0.30),('A-ELEC-SW',2,0.25),('A-ELEC-NET',4,0.25),('A-FIXT',4,0.18),('A-NOTE',7,0.25)]:
    if n not in [l.dxf.name for l in doc.layers]:
        lay=doc.layers.new(n); lay.color=c; lay.lineweight=int(w*100)
try: doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
except: pass
msp=doc.modelspace()
def label(x,y,txt,h=150,layer='A-NOTE'):
    msp.add_text(txt,height=h,dxfattribs={'layer':layer,'style':'HZTXT'}).set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)
def socket(x,y,typ='普通',h=300):
    msp.add_lwpolyline([(x-90,y-90),(x+90,y-90),(x+90,y+90),(x-90,y+90)],close=True,dxfattribs={'layer':'A-ELEC-SOC'})
    msp.add_line((x-90,y),(x+90,y),dxfattribs={'layer':'A-ELEC-SOC'})
    tag={'普通':'','16A':'16A','台面':'台','马桶':'智','防水':'防','冰箱':'冰','洗衣':'洗','弱电':'弱','备用':'备'}.get(typ,typ)
    label(x+380,y+120,f'H{h}',130)
    if tag: label(x,y+250,tag,120)
def switch(x,y,label_=None):
    msp.add_lwpolyline([(x-70,y-70),(x+70,y-70),(x+70,y+70),(x-70,y+70)],close=True,dxfattribs={'layer':'A-ELEC-SW'})
    msp.add_lwpolyline([(x-70,y-70),(x+70,y+70)],dxfattribs={'layer':'A-ELEC-SW'})
    if label_: label(x+420,y,label_,130)
def netport(x,y):
    msp.add_circle((x,y),90,dxfattribs={'layer':'A-ELEC-NET'})
    label(x,y,'T',110)
# ---- 点位表 ----
# 客厅(沙发x3404-4854 y8000-10900, TV墙东侧x7750-8000)
for i in range(4): socket(7600,9300+i*400,'普通',300)
netport(7600,10900); label(7300,11200,'电视墙:4位+网+TV',140)
socket(3050,8500,'普通',700); socket(3050,10500,'普通',700)  # 沙发两侧
socket(7700,11500,'16A',2200)  # 客厅空调
socket(5300,13200,'普通',300)  # 北窗边备用
# 餐厅/玄关
socket(3000,4700,'普通',300); socket(5600,4400,'台面',1200)  # 餐边柜+备用
socket(2950,6400,'弱电',1300); label(3500,6400,'弱电箱(原位待确认)',140)
socket(2950,4300,'16A',2200)  # 餐厅空调
# 厨房(东柜x7420-7800 y535-3750)
for i,yy in enumerate((1000,1800,2700,3600)): socket(7300,yy,'台面',1200)
socket(6300,3600,'冰箱',500); socket(7500,2900,'16A',2200); label(7500,2500,'油烟机16A',140)
socket(6550,700,'防水',500); label(6550,400,'水槽下(净水器)',130)
# 主卧(床x9137-11267头南, TV柜x8020-8480西墙)
socket(9050,800,'普通',700); socket(11350,800,'普通',700)
switch(9050,500,'双控'); switch(8150,4600)
for i in range(2): socket(8100,1600+i*300,'普通',300)
netport(8100,2200); label(8300,2600,'TV位+网',130)
socket(8300,4400,'16A',2200)
# 母卧(床x13058-15188头南, 梳妆台x12130-12580)
socket(12750,800,'普通',700); socket(15250,800,'普通',700)
switch(12900,600,'双控')
socket(12130,1050,'普通',700); label(12355,1400,'梳妆台位',130)
socket(15200,4400,'16A',2200)
# 客卧(x9900-12900 y8000-10900,床头朝北)
socket(10750,10600,'普通',700); socket(12050,10600,'普通',700)
switch(10500,7800)
socket(12800,8500,'16A',2200); socket(10100,8300,'普通',300)
# 书房(桌x14210-15010 y7580-9580)
socket(15100,8300,'普通',300); socket(15100,8900,'普通',300); netport(15100,9500)
socket(16100,7400,'16A',2200); socket(16100,9000,'普通',300)
label(15600,9800,'书桌区:2位+网口',140)
# 三个卫生间
socket(11200,5600,'马桶',400); label(11200,5900,'智能马桶(待确认)',130)
socket(10600,6100,'防水',1400); label(10600,6400,'吹风机IPX4距淋>600',130)
socket(15000,5900,'马桶',400); socket(13900,5400,'防水',1400)
socket(8400,8600,'马桶',400); socket(9000,8800,'防水',1400)
socket(9400,10100,'洗衣',1300); label(9413,10700,'洗衣机位',130)
# 走廊/阳光房/阳台
socket(10500,7900,'普通',300); label(10500,7700,'夜灯/吸尘备用',130)
socket(9300,11000,'普通',300); socket(12500,13000,'普通',300)
socket(5500,1200,'洗衣',1300); label(5500,1700,'阳台备用(挂烫/晾衣机)',130)
# 配电箱(入户)
msp.add_lwpolyline([(2750,6600),(2950,6600),(2950,7000),(2750,7000)],close=True,dxfattribs={'layer':'A-ELEC-SOC'})
label(3700,6800,'配电箱H1600(原位待确认)',150)
# 开关(每门一盏)
for sx,sy,t in [(2950,5500,'玄关总控'),(5800,1600,'厨房'),(8300,4300,'主卧'),(12900,4300,'母卧'),
                (10200,7900,'客卧'),(12900,6800,'书房'),(9100,6300,'次卫'),(12900,5100,'主卫'),(8500,7900,'客卫')]:
    switch(sx,sy,t)
# ---- 图例 ----
lg_x,lg_y=1300,-5400
msp.add_lwpolyline([(lg_x,lg_y),(lg_x+7800,lg_y),(lg_x+7800,lg_y+3000),(lg_x,lg_y+3000)],close=True,dxfattribs={'layer':'A-WALL'})
label(lg_x+3900,lg_y+2700,'图  例',300)
socket(lg_x+700,lg_y+2100); label(lg_x+3200,lg_y+2100,'插座(高度标注H)',170)
switch(lg_x+700,lg_y+1400); label(lg_x+3200,lg_y+1400,'开关 H1300',170)
netport(lg_x+700,lg_y+700); label(lg_x+3200,lg_y+700,'网络/弱电口 H300',170)
label(lg_x+5800,lg_y+2100,'标"防"=IPX4防溅盒',170)
label(lg_x+5800,lg_y+1400,'标"16A"=空调/油烟机',170)
label(lg_x+5800,lg_y+700,'标"智"=智能马桶专用',170)
# ---- 说明 ----
notes=['电气点位说明:','1. 全屋电/网走吊顶内敷设,墙面下引暗盒(旧房改造)',
 '2. 普通插座H300,台面H1200,床头H700,空调/烟机16A H2200,智能马桶H400,洗衣机H1300',
 '3. 卫生间插座距淋浴区>=600且带防溅盒','4. 每间卧室床头双控(门口+床头)',
 '5. 配电箱/弱电箱位置沿用原位,开工现场复尺确认','6. GB50096:每居室插座>=3,厨房独立回路>=4']
ty=-2200
for t_ in notes:
    msp.add_text(t_,height=220,dxfattribs={'layer':'A-NOTE','style':'HZTXT'}).set_placement((8200,ty),align=TextEntityAlignment.LEFT)
    ty-=400
label(8500,-1600,'V15 电气点位图  A302   比例 1:50   版本 R2',280,'A-NOTE')
doc.saveas(dst)
print('saved')
