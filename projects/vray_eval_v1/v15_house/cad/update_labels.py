#!/usr/bin/env python3
# 冻结 A-SOURCE-REF + 房间名改新用途 + A103 加波浪楼梯符号
import ezdxf
from pathlib import Path
from ezdxf.enums import TextEntityAlignment
cad=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad')
sheets=['A103_平面布置图','A201_天花布置图','A202_地面铺装图','A302_电气点位图','A303_给排水点位图']
# 旧标签(文字,位置)→新名;None=删掉旧标签
REN={( '休闲厅',(8900,9300,6000,6500)):('楼梯厅·波浪楼梯',(7300,6000)),
     ( '衣帽间',(8400,8900,6300,6700)):('阅读角',(8500,5700)),
     ( '卧室',(9900,13000,0,4500)):('主卧',None),
     ( '主卧',(13000,16500,0,4500)):('母卧',None),
     ( '书房',(9900,13000,8000,11000)):('客卧',None),
     ( '卧室',(13000,16500,4000,6600)):('书房',None),
     ( '公卫',(8000,9700,8000,11000)):('客卫',None),
     ( '次卫',(7900,9100,10400,11000)):('客卫',None),
     ( '次卫',(13000,16500,6600,11000)):('书房',(14500,8800)),
     ( '阳台',(7900,9100,10400,11000)):('客卫',None),
     ( '玄关',(2700,3700,4500,8000)):('玄关',None),
     ( '休闲厅',(9100,9300,6100,6300)):('楼梯厅',(7300,6000))}
for sh in sheets:
    p=cad/f'{sh}.dxf'
    if not p.exists(): print('skip',sh); continue
    doc=ezdxf.readfile(p)
    # 冻结来源校核层
    for lname in ('A-SOURCE-REF','A-UNCERTAIN','A-ROOM'):
        if lname in [l.dxf.name for l in doc.layers]:
            lay=doc.layers.get(lname); lay.off()
    msp=doc.modelspace()
    try: doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
    except: pass
    done=set()
    for e in list(msp):
        if e.dxftype()!='TEXT' or e.dxf.layer!='A-TEXT': continue
        t=e.dxf.text.strip(); x,y=e.dxf.insert.x,e.dxf.insert.y
        for (old,(x0,x1,y0,y1)),(new,newpos) in REN.items():
            if t==old and x0<=x<=x1 and y0<=y<=y1 and (old,x0) not in done:
                e.dxf.text=new
                if newpos: e.dxf.insert=(newpos[0],newpos[1],0)
                e.dxf.layer='A-DESIGN' if 'A-DESIGN' in [l.dxf.name for l in doc.layers] else 'A-TEXT'
                try: e.dxf.style='HZTXT'
                except: pass
                done.add((old,x0)); break
    # A103 加波浪楼梯符号:踏步弧带+下行箭头
    if sh.startswith('A103'):
        for lay in ('A-FURN','A-DESIGN','A-NOTE'):
            if lay not in [l.dxf.name for l in doc.layers]:
                l=doc.layers.new(lay); l.color={'A-FURN':6,'A-DESIGN':1,'A-NOTE':7}[lay]
        # 踏步示意:3条弧线(南向开口), x6600-8200
        import math
        for i,r in enumerate((600,1100,1600)):
            pts=[(7200+r*math.cos(math.radians(a)), 4700+r*math.sin(math.radians(a))) for a in range(20,161,10)]
            msp.add_lwpolyline(pts,dxfattribs={'layer':'A-FURN'})
        msp.add_line((7400,6300),(7400,4900),dxfattribs={'layer':'A-DESIGN'})
        msp.add_line((7400,4900),(7200,5300),dxfattribs={'layer':'A-DESIGN'})
        msp.add_line((7400,4900),(7600,5300),dxfattribs={'layer':'A-DESIGN'})
        msp.add_text('下',height=260,dxfattribs={'layer':'A-DESIGN','style':'HZTXT'}).set_placement((7400,5100),align=TextEntityAlignment.MIDDLE_LEFT)
        msp.add_text('波浪楼梯(通下层)',height=240,dxfattribs={'layer':'A-DESIGN','style':'HZTXT'}).set_placement((7400,7100),align=TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(p)
    print(sh,'updated')
