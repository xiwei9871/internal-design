#!/usr/bin/env python3
# A103_CONSTRUCTION_POC: 原生 DIMENSION + INSERT 块 + 锚点溯源
import ezdxf, shutil, json, csv, math
from pathlib import Path
from ezdxf.enums import TextEntityAlignment
cad=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad')
src=cad/'A103_平面布置图.dxf'; dst=cad/'A103_CONSTRUCTION_POC.dxf'
shutil.copy(src,dst)
doc=ezdxf.readfile(dst); msp=doc.modelspace()
geo=json.load(open(cad/'derived/geometry_v01.json'))
A={a['id']:(a['x'],a['y']) for a in geo['anchors']}
# ---- 样式 ----
style=json.load(open(cad/'cad_style.json'))
try: doc.styles.new('HZTXT',dxfattribs={'font':style['text']['font_candidates'][0]})
except: pass
DS='STD-ARCH'
try:
    doc.dimstyles.new(DS,dxfattribs={'dimtxsty':'HZTXT','dimtxt':180,'dimasz':140,'dimexo':300,'dimexe':200,'dimdec':0,'dimtad':1,'dimblk':'ARCHTICK','dimblk1':'ARCHTICK','dimblk2':'ARCHTICK'})
except Exception as e:
    try: doc.dimstyles.new(DS,dxfattribs={'dimtxsty':'HZTXT','dimtxt':180,'dimdec':0,'dimtad':1})
    except: pass
# ---- 原生标注 ----
dreport=[]
def hdim(p1,p2,base_y,tag):
    d=msp.add_linear_dim(base=( (A[p1][0]+A[p2][0])/2, base_y),p1=A[p1],p2=A[p2],angle=0,dimstyle=DS)
    try: d.render()
    except Exception as e: dreport.append((tag,'render_err',str(e)))
    dreport.append((tag,'ok',round(math.dist(A[p1],A[p2]),1)))
def vdim(p1,p2,base_x,tag):
    d=msp.add_linear_dim(base=(base_x,(A[p1][1]+A[p2][1])/2),p1=A[p1],p2=A[p2],angle=90,dimstyle=DS)
    try: d.render()
    except Exception as e: dreport.append((tag,'render_err',str(e)))
    dreport.append((tag,'ok',round(math.dist(A[p1],A[p2]),1)))
# 南立面总宽 + 关键分段(去噪取主要交点)
hdim('S-X00','S-X25',-1600,'south_total')            # 5700..15600
hdim('S-X02','S-X08',-1000,'seg_kitchen')            # 5700..7800 厨房面宽
hdim('S-X08','S-X14',-1000,'seg_master')             # 7800..11400 主卧面宽
hdim('S-X14','S-X24',-1000,'seg_mother')             # 11400..15600 母卧面宽
# 西立面总深
vdim('W-Y00','W-Y08',700,'west_total')               # 450..14953
vdim('W-Y03','W-Y05',1200,'seg_dining')              # 2400..13000 主体进深
# 内部关键定位
hdim('STAIR-SW','STAIR-SE',4300,'stair_width')       # 波浪台阶宽
vdim('STAIR-SW','STAIR-NW',5050,'stair_depth')       # 台阶进深
hdim('BATH2-SW','BATH2-SE',4300,'bath2_width')       # 次卫面宽
vdim('BATH2-SW','BATH2-NW',8800,'bath2_depth')       # 次卫进深
hdim('KIT-OPEN-S','KIT-OPEN-E',2050,'kitchen_wall')  # 厨房残墙宽
vdim('KIT-OPEN-S','KIT-OPEN-SN',5500,'kitchen_open') # 开放式厨房洞口
hdim('LIV-WIN-W','LIV-WIN-E',13500,'living_window')  # 客厅北窗宽
# ---- 门窗符号块 ----
def mkblock(name,builder):
    if name in [b.name for b in doc.blocks]: doc.blocks.delete(name)
    blk=doc.blocks.new(name); builder(blk); return blk
def door_sym(b):
    b.add_lwpolyline([(0,0),(0,900)],dxfattribs={'layer':'A-DOOR'})
    import math as m
    pts=[(900*m.sin(m.radians(a)),900*m.cos(m.radians(a))) for a in range(0,91,10)]
    b.add_lwpolyline(pts,dxfattribs={'layer':'A-DOOR'})
    b.add_attdef('SRC_ID',insert=(0,-150),height=120)
def win_sym(b):
    for yy in (-80,0,80): b.add_line((0,yy),(900,yy),dxfattribs={'layer':'A-WINDOW'})
    b.add_attdef('SRC_ID',insert=(0,-250),height=120)
mkblock('SYM-DOOR-SWING',door_sym); mkblock('SYM-WINDOW-3LINE',win_sym)
DOORS=[('D-107-主卧',8150,4500,0),('D-客卫',8780,7800,0),('D-客卧',9930,7800,0),('D-次卫',9060,5150,90),('D-主卫',11950,6400,0)]
for tag,x,y,rot in DOORS:
    ins=msp.add_blockref('SYM-DOOR-SWING',(x,y),dxfattribs={'layer':'A-DOOR','rotation':rot})
    ins.add_attrib('SRC_ID',tag,dxfattribs={'invisible':True})
WINS=[('WIN-客厅北',3900,13020,0),('WIN-南主卧',9137,0,0),('WIN-南母卧',13058,0,0)]
for tag,x,y,rot in WINS:
    ins=msp.add_blockref('SYM-WINDOW-3LINE',(x,y),dxfattribs={'layer':'A-WINDOW','rotation':rot})
    ins.add_attrib('SRC_ID',tag,dxfattribs={'invisible':True})
doc.saveas(dst)
# ---- 验收:重载核对 ----
d2=ezdxf.readfile(dst); m2=d2.modelspace()
dims=[e for e in m2 if e.dxftype()=='DIMENSION']
inserts=[e for e in m2 if e.dxftype()=='INSERT']
qa={'sheet':'A103_CONSTRUCTION_POC','dxf_version':d2.dxfversion,'dimension_count':len(dims),
    'insert_count':len(inserts),'report':dreport,
    'dim_values':[{'tag':e.dxf.tag if hasattr(e.dxf,'tag') else '', 'measurement':round(e.get_measurement(),2) if hasattr(e,'get_measurement') else None} for e in dims]}
json.dump(qa,open(cad/'qa_report.json','w'),ensure_ascii=False,indent=1)
with open(cad/'object_mapping.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['sheet_entity','source_object_id','source','evidence'])
    for a in geo['anchors']: w.writerow(['dim_anchor',a['id'],a['source'],a['evidence']])
    for tag,x,y,r in DOORS: w.writerow(['INSERT SYM-DOOR-SWING',tag,'model objects','door casing/leaf objects'])
    for tag,x,y,r in WINS: w.writerow(['INSERT SYM-WINDOW-3LINE',tag,'baseline/model','window band'])
print('dims:',len(dims),'inserts:',len(inserts))
for r in dreport: print(' ',r)
