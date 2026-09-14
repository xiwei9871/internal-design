from pathlib import Path
from copy import deepcopy
import json, math, html
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent/'png_rebuild'
D = deepcopy(json.loads((BASE/'plan_geometry.json').read_text()))
PX = D['metres_per_pixel']
def rect(x,y,w,h): return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
def poly(p, **attrs):
    return '<polygon points="'+' '.join(f'{x},{y}' for x,y in p)+'" '+ ' '.join(f'{k.replace("_","-")}="{v}"' for k,v in attrs.items())+'/>'
def text(x,y,s,size=19,color='#314844',anchor='middle',weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}" font-family="PingFang SC,Arial,sans-serif">{html.escape(s)}</text>'
def box(x,y,w,h,fill,stroke='#a3a9a0',sw=1.5,rx=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def line(points,color='#7d918a',width=2,dash=None):
    return '<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def dim(x1,y1,x2,y2,label):
    a=line([(x1,y1),(x2,y2)],'#51756d',1.3)
    if y1==y2:
        a+=line([(x1,y1-5),(x1,y1+5)])+line([(x2,y2-5),(x2,y2+5)])
        a+=text((x1+x2)/2,y1-7,label,15)
    else:
        a+=line([(x1-5,y1),(x1+5,y1)])+line([(x2-5,y2),(x2+5,y2)])
        a+=f'<text x="{x1-7}" y="{(y1+y2)/2}" transform="rotate(-90 {x1-7} {(y1+y2)/2})" text-anchor="middle" font-family="PingFang SC,Arial" font-size="15" fill="#51756d">{label}</text>'
    return a

# Route-preserved correction: keep PNG wall and door geometry unchanged.
# Reassign the original cabinet row as a kitchen extension; the main route remains on its right.
remove_names={'冰箱','家政高柜','洗衣机','烘干机','餐桌','餐椅','客厅单椅','窗边椅','边几'}
D['furniture']=[f for f in D['furniture'] if f['name'] not in remove_names]
def furn(n,k,x,y,w,h,z=.8): D['furniture'].append(dict(name=n,kind=k,rect=[x,y,w,h],height_m=z))
furn('厨房连续备餐台','lowcab',415,219,71,91,.85)
furn('过道冰箱','appliance',592,322,63,91,1.8)
furn('过道微波食品高柜','appliance',592,413,63,70,2.3)
furn('过道洗烘一体柜','appliance',592,483,63,73,2.0)
furn('4人餐桌（加端椅可6人）','table',870,824,145,82,.76)
for x,y in [(888,782),(953,782),(888,915),(953,915)]: furn('餐椅','chair',x,y,38,38,.8)
furn('双人/小三人沙发','sofa',1030,1090,85,210,.83)
furn('电视矮柜','lowcab',792,1120,28,140,.5)
furn('沙发边几','table',1047,1038,42,42,.5)
D['labels']=[['厨房',600,269],['次卫',510,527],['主卫',358,711],['衣帽区',348,949],['夫妻主卧',573,836],['老人房',943,604],['儿童房',1265,897],['餐区',950,988],['客厅',930,1085],['主卧窗边区',582,1178],['儿童窗边区',1267,1182]]
D['scheme']='A route-preserved kitchen-extension correction'
D['change_notes']=['次卫墙线、门洞、门扇回转区全部沿用 PNG 原始位置；本版不再移动次卫门。','原家政柜列原位组织为服务墙：冰箱、微波+食品高柜、洗烘一体柜从上到下集中布置。','服务墙结束于 y=556，次卫门扇回转从 y=561 开始，家具不侵入门前区域。','原主通道右侧保持连续净宽约1.10m；标记3的转入位置不被家具占用。','厨房内释放原冰箱位，改为连续备餐台；厨房与过道共同承担备餐、冰箱、微波、食品收纳和洗烘功能。']
D['status']='Concept only; original PNG walls/doors preserved; utility relocation and plumbing not verified.'
(ROOT/'scheme_a_geometry.json').write_text(json.dumps(D,ensure_ascii=False,indent=2))
palette={'oak':'#eddfc4','tile':'#eeede4','wet':'#dcece9'}
defs='<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#c88738"/></marker><pattern id="dry" width="12" height="12" patternUnits="userSpaceOnUse"><path d="M0 12L12 0" stroke="#bfcec5" stroke-width=".6"/></pattern></defs>'
base=[defs,poly(D['outer'],fill='#f6f3ea',stroke='#88958e',stroke_width=2)]
for z in D['zones']: base.append(poly(z['polygon'],fill=palette[z['material']]))
base.append(box(430,554,150,87,'url(#dry)','none'))
for f in D['furniture']:
    x,y,w,h=f['rect'];k=f['kind']
    color={'bed':'#fbf8f0','cabinet':'#bda47c','lowcab':'#cdb795','table':'#bb9c70','chair':'#b4bcb0','lounge':'#b4bcb0','sofa':'#98aaa2','sink':'#f9fcfa','wc':'#f9fcfa','shower':'#dfedeb','appliance':'#d0d7d2'}[k]
    base.append(box(x,y,w,h,color,rx=5 if k in ['bed','sofa','wc','chair'] else 2))
    if k=='bed':
        base.append(line([(x+w-49,y+3),(x+w-49,y+h-3)],'#c1b59f',1))
        for yy in [y+12,y+h/2+4]: base.append(box(x+w-40,yy,30,h/2-22,'#fffef9','#d3c8b5',1,6))
    elif k=='sofa':
        base.append(box(x+13,y+13,w-24,h-26,'#acbbb1','#889d92',1,7))
        for yy in [y+h/3,y+2*h/3]: base.append(line([(x+14,yy),(x+w-12,yy)],'#889d92',1))
    elif k in ['cabinet','lowcab']:
        if w>h:
            for xx in range(int(x+50),int(x+w),50): base.append(line([(xx,y),(xx,y+h)],'#b09a76',1))
        else:
            for yy in range(int(y+50),int(y+h),50): base.append(line([(x,yy),(x+w,yy)],'#b09a76',1))
    if f['name']=='过道洗烘一体柜':
        base.append(f'<circle cx="{x+w/2}" cy="{y+h/2}" r="18" fill="#edf3ef" stroke="#93aaa0" stroke-width="1.5"/>')
        base.append(text(x+w/2,y+26,'洗烘',13,weight=600)); base.append(text(x+w/2,y+43,'一体',13,weight=600))
    elif f['name']=='次卫台盆柜':
        base.append(box(x+16,y+11,w-32,h-24,'white','#abbfb5',1,8))
    elif f['name']=='次卫坐便器': base.append(box(x+16,y+5,w-20,h-10,'white','#acbeb5',1,12))
    elif f['name']=='过道冰箱': base.append(text(x+w/2,y+h/2+6,'冰箱',13,weight=600))
    elif f['name']=='过道微波食品高柜': base.append(text(x+w/2,y+h/2-2,'微波',12,weight=600)); base.append(text(x+w/2,y+h/2+16,'食品',12,weight=600))
    elif f['name']=='过道洗烘一体柜': base.append(text(x+w/2,y+h/2-2,'洗烘',12,weight=600)); base.append(text(x+w/2,y+h/2+16,'一体',12,weight=600))
    elif '洗烘一体柜' in f['name']:
        base.append(f'<circle cx="{x+w/2}" cy="{y+h/2}" r="18" fill="#edf3ef" stroke="#93aaa0" stroke-width="1.5"/>')
        base.append(text(x+w/2,y+26,'洗烘',13,weight=600)); base.append(text(x+w/2,y+43,'一体',13,weight=600))
# Details on counter: sink and hob keep original positions.
base.extend([box(690,165,72,43,'#e4ece8','#889c93',1,7),box(530,168,85,38,'#737c74','#66756d',1,3)])
for x in [550,594]: base.append(f'<circle cx="{x}" cy="187" r="12" fill="none" stroke="#dce4dd" stroke-width="2"/>')
for w in D['walls']:
    base.append(poly(w['polygon'],fill='#148a82' if w.get('change')=='new' else '#414d4a'))
for w in D['windows']:
    x1,y1,x2,y2=w['segment']; base.append(line([(x1,y1),(x2,y2)],'#8db6b7',5))
for d in D['doors']:
    (x,y),(lx,ly),(cx,cy)=d['hinge'],d['leaf'],d['closed'];r=math.hypot(lx-x,ly-y);sw=1 if (lx-x)*(cy-y)-(ly-y)*(cx-x)>0 else 0
    base.append(f'<path d="M{x} {y}L{lx} {ly} A{r} {r} 0 0 {sw} {cx} {cy}" fill="none" stroke="#929d92" stroke-width="1.7"/>')
# Bathroom outer sliding door opening / parked leaf, kitchen transparent slider.
base.extend([line([(440,446),(572,446)],'#63a99e',3),text(510,387,'独立淋浴',17),text(510,411,'玻璃分隔',13),text(454,292,'新增备餐台',12),text(710,578,'入口留空',12)])
# Demolished partition only, not the original laundry furniture.

# Proposed flows remain off dining chairs and kitchen counters.
routes=[[(1154,717),(1068,717),(1068,972),(975,1027),(944,1140)],
        [(1027,717),(700,717),(700,368),(670,280)],
        [(794,603),(700,603),(700,510),(638,510)]]
for pts in routes:
    base.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+'" fill="none" stroke="#c88738" stroke-width="3" stroke-dasharray="9 8" marker-end="url(#arrow)"/>')
for label,x,y in D['labels']: base.append(text(x,y,label,22,weight=500))
base.append(text(665,686,'去厨房 / 次卫',13,color='#9a6b31'))
# Numbered location markers, exact description stays outside plan in browser.
for n,x,y in [(1,450,257),(2,650,440),(3,698,611)]:
    base.append(f'<circle cx="{x}" cy="{y}" r="17" fill="#148a82" stroke="white" stroke-width="2"/>')
    base.append(text(x,y+6,str(n),18,'white',weight=600))
diagram='\n'.join(base)
main='<svg xmlns="http://www.w3.org/2000/svg" width="1663" height="1485" viewBox="0 0 1663 1485"><rect width="1663" height="1485" fill="#fcfcf8"/>'+diagram
main+=text(200,83,'方案 A4 · 厨房与家政服务墙',31,anchor='start',weight=600)
main+=text(200,111,'3 卧室 · 餐客厅 · 1 厨房 · 2 卫生间 · 原墙原门',19,anchor='start',color='#74847a')
main+=box(204,1373,24,14,'#414d4a','none')+text(238,1386,'保留墙',18,anchor='start')
main+=box(374,1373,24,14,'#bda47c','none')+text(408,1386,'服务墙家具',18,anchor='start')
main+=line([(650,1380),(686,1380)],'#c88738',3,'7 5')+text(697,1386,'日常动线',18,anchor='start')
main+=text(200,1437,'功能布局讨论稿｜尺寸按 PNG 标注及比例估算；设备尺寸与开门空间需按选型细化。',18,anchor='start',color='#7c877c')+'</svg>'
(ROOT/'方案A_功能平面.svg').write_text(main)
# Focus view includes readable dimensions at unchanged source coordinates.
detail='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1500" viewBox="365 110 470 587.5"><rect x="365" y="110" width="470" height="587.5" fill="#fcfcf8"/>'+diagram
detail+=dim(655,365,767,365,'主通道约 1.10 m')
detail+=dim(592,294,655,294,'柜深约 0.62 m')
detail+=dim(410,160,410,305,'厨房净深约 1.50 m')
detail+=box(370,672,460,20,'#fcfcf8','none')+text(600,686,'① 新增备餐台　② 原柜列重组　③ 入口留空',12)
detail+='</svg>'
(ROOT/'方案A_厨卫放大.svg').write_text(detail)
# Checks cover route and door adjacency; this is not a structural safety check.
mask=Image.new('1',(1663,1485));d=ImageDraw.Draw(mask)
for w in D['walls']: d.polygon([tuple(p) for p in w['polygon']],fill=1)
for sample in [(700,360),(700,450),(700,600),(700,700),(670,300)]: assert not mask.getpixel(sample), f'Route intersects wall at {sample}'
service_furniture=[f for f in D['furniture'] if f['name'].startswith('过道')]
assert service_furniture and all(f['rect'][0] + f['rect'][2] <= 655 for f in service_furniture), 'Service wall must stay left of the 1.10m passage'
assert max(f['rect'][1] + f['rect'][3] for f in service_furniture) <= 556 and 556 < 561, 'Service wall must finish before the bathroom door swing'
assert all(not (f['rect'][0] < 767 and f['rect'][0] + f['rect'][2] > 655 and f['rect'][1] < 643 and f['rect'][1] + f['rect'][3] > 425) for f in service_furniture), 'Position 3 corridor must remain clear'
base_reference=json.loads((BASE/'plan_geometry.json').read_text())
report=dict(bath_width_m=round((580-428)*PX,2),bath_width_change_m=0.0,hall_clearance_m=round((767-655)*PX,2),bath_door_width_m=round(76*PX,2),washer_dryer_footprint_m=[round(63*PX,2),round(73*PX,2)],kitchen_width_m=round(364*PX,2),kitchen_depth_m=round(153*PX,2),kitchen_opening_m=round(175*PX,2),bedrooms=3,bathrooms=2,preserved_exterior=D['outer']==base_reference['outer'],preserved_walls=D['walls']==base_reference['walls'],preserved_bathroom_door=any(d['name']=='次卫门' and d['hinge']==[580,637] for d in D['doors']),service_wall_modules=['fridge','microwave_food_cabinet','washer_dryer_combo'],service_wall_finish_before_door_swing=True,position_3_clear=True,status='Route-preserved concept; original wall and door geometry checked')
(ROOT/'layout_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
