#!/usr/bin/env python3
import ezdxf
from pathlib import Path
from ezdxf.enums import TextEntityAlignment
cad=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad')
sheets=['A103_平面布置图','A201_天花布置图','A202_地面铺装图','A302_电气点位图','A303_给排水点位图']
ROOMNAMES={'客厅','餐厅','厨房','玄关','生活阳台','主卧','母卧','客卧','书房','客卫','次卫','主卫','走廊','阳光房','阅读角','楼梯厅','楼梯厅·波浪楼梯','波浪楼梯(通下层)'}
# 剩余旧标签:精确坐标→新名
FIX=[('卧室',9415,2225,'主卧'),('衣帽间',9875,5475,'次卫'),('卧室',14400,8925,'书房'),('阳台',10150,12150,'阳光房'),
     ('玄关',2950,6225,'玄关'),('走廊',10550,6775,'走廊')]
for sh in sheets:
    p=cad/f'{sh}.dxf'
    doc=ezdxf.readfile(p); msp=doc.modelspace()
    try: doc.styles.new('HZTXT',dxfattribs={'font':'/System/Library/Fonts/STHeiti Medium.ttc'})
    except: pass
    # 1) 精确坐标改剩余旧名
    for old,x0,y0,new in FIX:
        for e in msp:
            if e.dxftype()=='TEXT' and e.dxf.text.strip()==old and abs(e.dxf.insert.x-x0)<300 and abs(e.dxf.insert.y-y0)<300:
                e.dxf.text=new
                if 'A-DESIGN' in [l.dxf.name for l in doc.layers]: e.dxf.layer='A-DESIGN'
                try: e.dxf.style='HZTXT'
                except: pass
    # 2) 去重:同文字标签保留第一个
    seen={}
    to_del=[]
    for e in msp:
        if e.dxftype()!='TEXT': continue
        t=e.dxf.text.strip()
        if t not in ROOMNAMES: continue
        if t in seen:
            # 距离近的才删(同房双标签)
            if abs(e.dxf.insert.x-seen[t][0])<2000 and abs(e.dxf.insert.y-seen[t][1])<2000:
                to_del.append(e)
            else: seen[t]=(e.dxf.insert.x,e.dxf.insert.y)
        else: seen[t]=(e.dxf.insert.x,e.dxf.insert.y)
    for e in to_del: msp.delete_entity(e)
    # 3) 补"阅读角"(x8050-9050窄条,竖排)
    if sh.startswith('A103'):
        msp.add_text('阅读角',height=220,dxfattribs={'layer':'A-DESIGN' if 'A-DESIGN' in [l.dxf.name for l in doc.layers] else 'A-TEXT','style':'HZTXT','rotation':90}).set_placement((8450,5550),align=TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(p)
    print(sh,'dedup',len(to_del))
