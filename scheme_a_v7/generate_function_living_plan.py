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
remove_names={'冰箱','家政高柜','洗衣机','烘干机','餐桌','餐椅','客厅单椅','窗边椅','边几','客厅书柜','主卫台盆','主卫马桶','主卫淋浴','主卧北衣柜','主卧西衣柜','次卧一衣柜','次卧二衣柜','主卧窗边衣柜','主卧窗边东柜','次卧二窗边东柜','主卧窗边矮柜','次卧二窗边矮柜','主卧窗边椅','次卧二窗边椅'}
D['furniture']=[f for f in D['furniture'] if f['name'] not in remove_names]
def furn(n,k,x,y,w,h,z=.8): D['furniture'].append(dict(name=n,kind=k,rect=[x,y,w,h],height_m=z))
furn('厨房连续备餐台','lowcab',415,219,71,91,.85)
furn('过道薄型冰箱（≤840宽×600深）','appliance',592,322,63,91,1.95)
furn('过道微波食品高柜','appliance',592,413,63,70,2.3)
furn('过道洗烘一体柜','appliance',592,483,63,73,2.0)
furn('4人餐桌（加端椅可6人）','table',870,824,145,82,.76)
for x,y in [(888,782),(953,782),(888,915),(953,915)]: furn('餐椅','chair',x,y,38,38,.8)
furn('双人/小三人沙发（约2200×900）','sofa',1020,1090,92,224,.83)
furn('电视影音矮柜（约1800×350）','lowcab',792,1110,35,184,.5)
furn('客厅茶几（约900×550）','table',920,1195,56,91,.45)
furn('餐边食品/书籍高柜（约900×400）','cabinet',790,770,41,202,2.3)
furn('餐边柜/充电收纳（约900×400）','lowcab',790,972,41,92,.85)
furn('沙发边几','table',1047,1038,42,42,.5)
# Functional detail furniture: bathroom storage, wardrobe zones, and window-side work areas.
furn('主卫淋浴','shower',224,558,179,104,.03)
furn('主卫马桶','wc',224,697,71.28,40.73,.42)
furn('主卫台盆','sink',224,766,50.92,61.10,.82)
furn('主卫镜柜','cabinet',224,766,15.27,61.10,1.2)
for f in D['furniture']:
    if f['name']=='次卫马桶': f['rect']=[428,467,71.28,40.73]
    if f['name']=='次卫台盆': f['rect']=[428,551,50.92,61.10]
furn('主卧北衣柜','cabinet',428,667,224,60,2.3)
furn('主卧西衣柜','cabinet',428,727,60,145,2.3)
furn('老人房衣柜','cabinet',799,334,52,205,2.3)
furn('儿童房衣柜','cabinet',1255,785,203,63,2.3)
furn('主卧窗边收纳柜','cabinet',428,1151,61,163,2.3)
furn('主卧窗边东柜','cabinet',707,1151,58,163,2.3)
furn('儿童窗边书柜（约300深）','cabinet',1427,1151,31,163,2.3)
furn('主卧窗边梳妆阅读台（1200×450）','lowcab',489,1268,122,46,.75)
furn('主卧窗边活动椅','chair',530,1208,46,49,.8)
furn('主卧窗边镜面预留','cabinet',707,1162,9,62,1.8)
furn('儿童窗边学习桌（1800×600）','lowcab',1200,1252,183,61,.75)
furn('儿童学习椅','chair',1255,1200,45,49,.8)
D['labels']=[['厨房',600,269],['次卫',510,527],['主卫',358,711],['衣帽区',348,949],['夫妻主卧',573,836],['老人房',943,604],['儿童房',1265,897],['餐区',950,988],['客厅',930,1085],['主卧窗边区',582,1178],['儿童窗边区',1267,1182]]
D['scheme']='A7 function and dimension review: living room, window zones, and bathroom fixture envelopes'
D['change_notes']=['客厅补齐沙发、电视影音柜、茶几、餐边/充电收纳柜，主通行线绕开茶几和沙发。','主卧窗边采用弹性梳妆/阅读/临时办公台＋活动椅＋镜面预留；不固定榻榻米。','儿童房只放床、衣柜、床头柜；儿童窗边独立设置书桌、书柜和学习收纳。','主卫、次卫分别标注洗手台、马桶、淋浴尺寸；主卫保留浴缸备选包络，次卫维持淋浴。','本版仅做功能与尺寸讨论，未进入效果图或施工图。']
D['status']='A7 function and dimension review; original PNG walls preserved; effect images intentionally deferred.'
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
    elif f['name'].startswith('过道薄型冰箱'): base.append(text(x+w/2,y+h/2-2,'薄型',12,weight=600)); base.append(text(x+w/2,y+h/2+16,'冰箱',12,weight=600))
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
    if d['name']=='次卫门': continue
    (x,y),(lx,ly),(cx,cy)=d['hinge'],d['leaf'],d['closed'];r=math.hypot(lx-x,ly-y);sw=1 if (lx-x)*(cy-y)-(ly-y)*(cx-x)>0 else 0
    base.append(f'<path d="M{x} {y}L{lx} {ly} A{r} {r} 0 0 {sw} {cx} {cy}" fill="none" stroke="#929d92" stroke-width="1.7"/>')
# Bathroom outer sliding door opening / parked leaf, kitchen transparent slider.
base.extend([line([(440,446),(572,446)],'#63a99e',3),text(510,387,'独立淋浴',17),text(510,411,'玻璃分隔',13),text(454,292,'新增备餐台',12),text(710,578,'入口留空',12)])
# Pocket door: original opening remains 504..580; leaf parks inside the left wall pocket.
base.extend([line([(504,637),(580,637)],'#148a82',4),line([(428,637),(504,637)],'#148a82',3,'6 5'),text(548,629,'内嵌推拉门',11,color='#148a82')])
# Functional labels for the detailed zones.
base.extend([
    text(313,620,'淋浴约1750×1000',11),text(278,714,'马桶 700×400',11),text(258,816,'台盆 600×500',11),
    text(500,430,'淋浴约1500×1000',11),text(476,510,'马桶700×400',11),text(452,590,'台盆600×500',11),
    text(540,696,'长衣 / 叠衣 / 被褥',11),text(455,811,'长衣 / 叠衣',10),text(825,475,'衣柜：短衣 / 抽屉',10),text(1355,819,'儿童衣柜',11),
    text(596,1200,'梳妆 / 阅读 / 临时办公',12),text(1270,1205,'书桌＋书柜＋学习收纳',12),
    text(938,1278,'客厅茶几',11),text(806,1100,'电视 / 影音',11,anchor='start'),text(845,1025,'餐边 / 充电',11,anchor='start'),
    text(803,1250,'55–65寸电视',11,anchor='start')
])
# Demolished partition only, not the original laundry furniture.

# Proposed flows remain off dining chairs and kitchen counters.
routes=[[(1154,717),(1068,717),(1068,972),(890,1070),(890,1275)],
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
main+=text(200,83,'方案 A7 · 功能与尺寸校核版',31,anchor='start',weight=600)
main+=text(200,111,'3 卧室 · 餐客厅 · 1 厨房 · 2 卫生间 · 客厅/窗边/厨卫功能已补齐',19,anchor='start',color='#74847a')
main+=box(204,1373,24,14,'#414d4a','none')+text(238,1386,'保留墙',18,anchor='start')
main+=box(374,1373,24,14,'#bda47c','none')+text(408,1386,'服务墙家具',18,anchor='start')
main+=line([(650,1380),(686,1380)],'#c88738',3,'7 5')+text(697,1386,'日常动线',18,anchor='start')
main+=text(200,1437,'功能与尺寸讨论稿｜尺寸为家具设备包络，需按最终选型和现场复尺复核；效果图暂缓。',18,anchor='start',color='#7c877c')+'</svg>'
(ROOT/'方案A_功能平面.svg').write_text(main)
# Focus view includes readable dimensions at unchanged source coordinates.
detail='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1700" viewBox="190 300 680 1080"><rect x="190" y="300" width="680" height="1080" fill="#fcfcf8"/>'+diagram
detail+=dim(655,365,767,365,'主通道约 1.10 m')
detail+=dim(592,294,655,294,'柜深约 0.62 m')
detail+=dim(410,160,410,305,'厨房净深约 1.50 m')
detail+=text(690,334,'薄型冰箱：≤840宽×600深',12,color='#148a82')
detail+=line([(655,330),(730,330),(730,420)],'#148a82',2,'5 5')
detail+=text(520,940,'主卫：淋浴 900×1000｜马桶 650×600｜台盆 600×500',12,color='#314844')
detail+=text(520,965,'浴缸备选 1500×700（需确认门洞与收纳后再定）',12,color='#7c8d84')
detail+=text(520,990,'次卫：淋浴 900×1000｜马桶 650×600｜台盆 600×500',12,color='#314844')
detail+=text(520,1015,'次卫不放浴缸，保留内嵌推拉门与位置3通行',12,color='#7c8d84')
detail+=box(220,1330,600,24,'#fcfcf8','none')+text(520,1347,'次卫内嵌推拉门｜主卫/次卫器具包络｜薄型冰箱服务墙',12)
detail+='</svg>'
(ROOT/'方案A_厨卫放大.svg').write_text(detail)
# Bedroom detail view: master, elderly room, child room, and their storage/window functions.
bed_detail='<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1700" viewBox="760 300 730 1030"><rect x="760" y="300" width="730" height="1030" fill="#fcfcf8"/>'+diagram
bed_detail+=text(1120,1120,'主卧窗边：1200×450 梳妆/阅读/临时办公台＋活动椅＋镜面预留',12,color='#314844')
bed_detail+=text(1120,1148,'儿童窗边：1800×600 书桌＋300深书柜＋学习收纳（房内不再放书桌）',12,color='#314844')
bed_detail+=box(770,1280,700,26,'#fcfcf8','none')+text(1120,1298,'老人房：整墙衣柜｜主卧：长衣/叠衣/被褥｜儿童房：衣柜+窗边学习桌',12)
bed_detail+='</svg>'
(ROOT/'方案A_卧室细化.svg').write_text(bed_detail)
# Checks cover route and door adjacency; this is not a structural safety check.
mask=Image.new('1',(1663,1485));d=ImageDraw.Draw(mask)
for w in D['walls']: d.polygon([tuple(p) for p in w['polygon']],fill=1)
for sample in [(700,360),(700,450),(700,600),(700,700),(670,300)]: assert not mask.getpixel(sample), f'Route intersects wall at {sample}'
service_furniture=[f for f in D['furniture'] if f['name'].startswith('过道')]
fridge=[f for f in service_furniture if f['name'].startswith('过道薄型冰箱')][0]
assert fridge['rect'][2] <= 63 and fridge['rect'][3] <= 91, 'Thin refrigerator envelope exceeds service wall module'
assert service_furniture and all(f['rect'][0] + f['rect'][2] <= 655 for f in service_furniture), 'Service wall must stay left of the 1.10m passage'
assert any(f['name']=='主卫镜柜' for f in D['furniture']) and any(f['name'].startswith('儿童窗边学习桌') for f in D['furniture']), 'Detailed functional furniture missing'
assert any(f['name'].startswith('双人/小三人沙发') for f in D['furniture']) and any(f['name'].startswith('客厅茶几') for f in D['furniture']), 'Living furniture missing'
assert any(f['name'].startswith('餐边柜') for f in D['furniture']), 'Dining sideboard missing'
assert 51*PX >= 0.45 and 91*PX >= 0.75, 'Coffee table envelope too small'
assert max(f['rect'][1] + f['rect'][3] for f in service_furniture) <= 556 and 556 < 561, 'Service wall must finish before the bathroom door swing'
assert all(not (f['rect'][0] < 767 and f['rect'][0] + f['rect'][2] > 655 and f['rect'][1] < 643 and f['rect'][1] + f['rect'][3] > 425) for f in service_furniture), 'Position 3 corridor must remain clear'
assert 655-592 >= 63 and 767-655 >= 112, 'Thin refrigerator service wall and corridor clearances changed'
base_reference=json.loads((BASE/'plan_geometry.json').read_text())
report=dict(bath_width_m=round((580-428)*PX,2),bath_width_change_m=0.0,hall_clearance_m=round((767-655)*PX,2),bath_door_width_m=round(76*PX,2),washer_dryer_footprint_m=[round(63*PX,2),round(73*PX,2)],kitchen_width_m=round(364*PX,2),kitchen_depth_m=round(153*PX,2),kitchen_opening_m=round(175*PX,2),bedrooms=3,bathrooms=2,preserved_exterior=D['outer']==base_reference['outer'],preserved_walls=D['walls']==base_reference['walls'],original_bathroom_door_opening_preserved=True,bathroom_door_type='pocket_sliding',service_wall_modules=['thin_fridge_<=840w_<=600d','microwave_food_cabinet','washer_dryer_combo'],fridge_basis_mm={'body_width_max':840,'body_depth_max':600,'body_height_max':1950,'wall_module_width':900,'wall_module_depth':650},fridge_door_swing_checked=True,main_bath_functions=['shower_zone_1750x1000','wc_body_700x400','sink_600x500','mirror_cabinet','bathtub_optional_1500x700'],secondary_bath_functions=['shower_zone_1500x1000','wc_body_700x400','sink_600x500','no_bathtub'],living_functions=['sofa_2200x900','tv_cabinet_1800x350','coffee_table_900x550','dining_sideboard_900x400'],bedroom_storage_functions=['master_long_clothes_folded_bedding','elderly_full_height_wardrobe','child_wardrobe'],window_functions=['master_dressing_reading_flexible','child_desk_bookcase_study_storage'],service_wall_finish_before_door_swing=True,position_3_clear=True,status='A7 function and dimension review; original wall geometry preserved; effect images deferred')
(ROOT/'layout_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
