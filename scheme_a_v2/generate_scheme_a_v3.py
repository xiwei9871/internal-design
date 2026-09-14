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

# Scheme A3: keep the original clear route; repurpose the original left-side cabinet row as kitchen extension.
removed_wall = next(w for w in D['walls'] if w['name']=='次卫家政隔墙')
D['walls'] = [w for w in D['walls'] if w['name']!='次卫家政隔墙']
newwalls = [
    dict(name='次卫东扩上段',polygon=rect(600,334,12,227),change='new'),
    dict(name='次卫东扩下段',polygon=rect(600,637,12,6),change='new'),
    dict(name='儿童窗边区独立轻隔墙（方案建议）',polygon=rect(1128,1151,12,163),change='new'),
]
D['walls'].extend(newwalls)
for z in D['zones']:
    if z['name']=='次卫': z['polygon']=rect(428,334,172,309)
remove_names={'家政高柜','洗衣机','烘干机','冰箱','次卫台盆','次卫马桶','次卫淋浴','餐桌','餐椅','客厅单椅','窗边椅','边几'}
D['furniture']=[f for f in D['furniture'] if f['name'] not in remove_names]
def furn(n,k,x,y,w,h,z=.8): D['furniture'].append(dict(name=n,kind=k,rect=[x,y,w,h],height_m=z))
furn('厨房连续备餐台','lowcab',415,219,71,91,.85)
furn('过道冰箱','appliance',612,334,63,91,1.8)
furn('过道微波高柜','appliance',612,425,63,64,2.3)
furn('过道食品储物柜','cabinet',612,489,63,67,2.3)
furn('次卫淋浴区','shower',438,343,168,101,.03)
furn('次卫坐便器','wc',440,474,66,43,.43)
furn('次卫台盆柜','sink',439,584,90,55,.83)
furn('洗烘叠放柜','appliance',542,570,65,71,2.0)
furn('4人餐桌（加端椅可6人）','table',870,824,145,82,.76)
for x,y in [(888,782),(953,782),(888,915),(953,915)]: furn('餐椅','chair',x,y,38,38,.8)
furn('双人/小三人沙发','sofa',1030,1090,85,210,.83)
furn('电视矮柜','lowcab',792,1120,28,140,.5)
furn('沙发边几','table',1047,1038,42,42,.5)
for d in D['doors']:
    if d['name']=='次卫门':
        d['hinge']=[600,637]; d['leaf']=[524,637]; d['closed']=[600,561]
D['windows']=[w for w in D['windows'] if w['name']!='客厅窗边移门']
D['labels']=[
    ['厨房',600,269],['次卫',566,527],['主卫',358,711],['衣帽区',348,949],
    ['夫妻主卧',573,836],['老人房',943,604],['儿童房',1265,897],['餐区',950,988],['客厅',930,1085],
    ['主卧窗边区',582,1178],['儿童学习区',1267,1182],
]
D['scheme']='A3 original-route kitchen-extension layout'
D['change_notes']=[
    '次卫净宽由约1.49m扩大至约1.69m，东扩约0.20m；仅做适度扩展，不再挤压原主通道。',
    '洗烘叠放放在次卫南端干区柜内；淋浴在北侧并设玻璃分隔。次卫改东侧外滑门。',
    '厨房内取消冰箱占位，恢复连续橱柜；冰箱、微波炉和食品储物放回原来靠次卫一侧的柜列。',
    '次卫门洞沿用原来东南侧位置，门扇回转区位于次卫内；柜列在门洞上方结束，不再挡门。',
    '主通道右侧保持完整贯通，柜列只占原家政柜的左侧范围；标记 3 的转入空间保留。',
    '餐桌1.42×0.81m，平时4人，临时增加两端椅；客厅配置约2.06m长沙发。',
]
D['status']='Concept only; wall construction, drainage, waterproofing, vent and ceiling heights unverified.'
(ROOT/'scheme_a_geometry.json').write_text(json.dumps(D,ensure_ascii=False,indent=2))
palette={'oak':'#eddfc4','tile':'#eeede4','wet':'#dcece9'}
defs='<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#c88738"/></marker><pattern id="dry" width="12" height="12" patternUnits="userSpaceOnUse"><path d="M0 12L12 0" stroke="#bfcec5" stroke-width=".6"/></pattern></defs>'
base=[defs,poly(D['outer'],fill='#f6f3ea',stroke='#88958e',stroke_width=2)]
for z in D['zones']: base.append(poly(z['polygon'],fill=palette[z['material']]))
base.append(box(430,554,184,87,'url(#dry)','none'))
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
    if f['name']=='洗烘叠放柜':
        base.append(f'<circle cx="{x+w/2}" cy="{y+h/2}" r="18" fill="#edf3ef" stroke="#93aaa0" stroke-width="1.5"/>')
        base.append(text(x+w/2,y+26,'洗烘',13,weight=600)); base.append(text(x+w/2,y+43,'叠放',13,weight=600))
    elif f['name']=='次卫台盆柜':
        base.append(box(x+16,y+11,w-32,h-24,'white','#abbfb5',1,8))
    elif f['name']=='次卫坐便器': base.append(box(x+16,y+5,w-20,h-10,'white','#acbeb5',1,12))
    elif f['name']=='过道冰箱': base.append(text(x+w/2,y+h/2+6,'冰箱',13,weight=600))
    elif f['name']=='过道微波高柜': base.append(text(x+w/2,y+48,'微波',13,weight=600))
    elif f['name']=='过道食品储物柜': base.append(text(x+w/2,y+h/2+6,'储物',13,weight=600))
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
base.extend([line([(440,446),(588,446)],'#63a99e',3),text(510,387,'独立淋浴',17),text(510,411,'玻璃分隔',13),text(660,285,'通透移门',14),text(694,326,'原位厨房扩展柜列',13),text(638,620,'次卫门洞保持原侧',13)])
# Demolished partition only, not the original laundry furniture.
base.append(poly(removed_wall['polygon'],fill='none',stroke='#d75e52',stroke_width=2,stroke_dasharray='7 5'))
# Proposed flows remain off dining chairs and kitchen counters.
routes=[[(1154,717),(1068,717),(1068,972),(975,1027),(944,1140)],
        [(1027,717),(700,717),(700,368),(670,280)],
        [(794,603),(700,603),(700,510),(638,510)]]
for pts in routes:
    base.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+'" fill="none" stroke="#c88738" stroke-width="3" stroke-dasharray="9 8" marker-end="url(#arrow)"/>')
for label,x,y in D['labels']: base.append(text(x,y,label,22,weight=500))
base.append(text(665,686,'去厨房 / 次卫',13,color='#9a6b31'))
# Numbered location markers, exact description stays outside plan in browser.
for n,x,y in [(1,694,430),(2,650,420),(3,694,589),(4,1149,1218)]:
    base.append(f'<circle cx="{x}" cy="{y}" r="17" fill="#148a82" stroke="white" stroke-width="2"/>')
    base.append(text(x,y+6,str(n),18,'white',weight=600))
diagram='\n'.join(base)
main='<svg xmlns="http://www.w3.org/2000/svg" width="1663" height="1485" viewBox="0 0 1663 1485"><rect width="1663" height="1485" fill="#fcfcf8"/>'+diagram
main+=text(200,83,'方案 A3 · 保持原动线的厨房扩展',31,anchor='start',weight=600)
main+=text(200,111,'3 卧室 · 餐客厅 · 1 厨房 · 2 卫生间 · A3',19,anchor='start',color='#74847a')
main+=box(204,1373,24,14,'#414d4a','none')+text(238,1386,'保留墙',18,anchor='start')
main+=box(374,1373,24,14,'#148a82','none')+text(408,1386,'建议新墙',18,anchor='start')
main+=line([(583,1380),(617,1380)],'#d75e52',3,'7 5')+text(632,1386,'建议拆墙',18,anchor='start')
main+=line([(805,1380),(841,1380)],'#c88738',3,'7 5')+text(852,1386,'日常动线',18,anchor='start')
main+=text(200,1437,'尺寸按 PNG 比例估算；墙体与水电条件待复核。本版用于功能布局讨论。',18,anchor='start',color='#7c877c')+'</svg>'
(ROOT/'方案A_功能平面.svg').write_text(main)
# Focus view includes readable dimensions at unchanged source coordinates.
detail='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1420" viewBox="365 110 470 556"><rect x="365" y="110" width="470" height="556" fill="#fcfcf8"/>'+diagram
detail+=dim(428,455,600,455,'次卫净宽约 1.69 m')
detail+=dim(675,365,767,365,'主通道净宽约 0.9 m')
detail+=dim(410,160,410,305,'厨房净深约 1.50 m')
detail+=text(694,653,'原柜列内：冰箱＋微波＋食品储物；右侧主通道保持畅通',13)
detail+='</svg>'
(ROOT/'方案A_厨卫放大.svg').write_text(detail)
# Geometric checks are at layout level. They are not a structural safety check.
mask=Image.new('1',(1663,1485));d=ImageDraw.Draw(mask)
for w in D['walls']:d.polygon([tuple(p) for p in w['polygon']],fill=1)
for sample in [(700,360),(700,450),(700,600),(606,500),(606,600),(671,300)]:
    assert not mask.getpixel(sample),f'Route intersects wall at {sample}'
for sample in [(586,432),(586,550)]:
    assert not mask.getpixel(sample),'Removed partition still exists'
report=dict(bath_width_m=round((600-428)*PX,2),bath_width_change_m=round((600-580)*PX,2),
            hall_clearance_m=round((767-675)*PX,2),bath_door_width_m=round(84*PX,2),
            washer_dryer_footprint_m=[round(65*PX,2),round(71*PX,2)],
            kitchen_width_m=round(364*PX,2),kitchen_depth_m=round(153*PX,2),
            kitchen_opening_m=round(175*PX,2),bedrooms=3,bathrooms=2,
            preserved_exterior=D['outer']==json.loads((BASE/'plan_geometry.json').read_text())['outer'],
            status='Concept dimensions only; eight route/wall points checked')
(ROOT/'layout_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))

