"""PNG trace in source-image coordinates; all derived views use this geometry."""
from pathlib import Path
import json, html, shutil
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
def rect(x,y,w,h): return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
OUTER = [[403,145],[790,145],[790,310],[1184,310],[1184,674],[1160,674],[1160,760],[1485,760],[1485,1337],[403,1337],[403,1128],[200,1128],[200,534],[403,534]]
WALLS = [
 ('厨房西北墙',[[403,145],[515,145],[515,157],[415,157],[415,310],[403,310]]),
 ('厨房南墙',[[403,310],[592,310],[592,334],[428,334],[428,355],[403,355]]),
 ('次卧一西北墙',[[767,310],[904,310],[904,334],[790,334],[790,558],[767,558]]),
 ('次卧一东北墙',[[1047,310],[1184,310],[1184,674],[1160,674],[1160,334],[1047,334]]),
 ('次卧一南墙',rect(879,642,281,24)),
 ('次卧一门边',rect(767,637,23,29)),
 ('次卫西墙',[[403,418],[428,418],[428,643],[403,643],[403,558],[383,558],[383,534],[403,534]]),
 ('西翼外墙',[[200,534],[322,534],[322,558],[224,558],[224,1103],[240,1103],[240,1128],[200,1128]]),
 ('主卧北墙',rect(403,643,262,24)),
 ('主卧衣帽区东墙',rect(403,667,25,336)),
 ('主卧北墙转角',[[652,667],[665,667],[665,768],[675,768],[675,781],[652,781]]),
 ('主卧东墙',[[766,770],[790,770],[790,1314],[765,1314],[765,1151],[705,1151],[705,1128],[766,1128]]),
 ('主卧西南转角',[[403,1091],[428,1091],[428,1128],[489,1128],[489,1151],[428,1151],[428,1314],[403,1314]]),
 ('主卧西南端柱',rect(403,1314,25,23)),
 ('主卧客厅南端柱',rect(750,1314,58,23)),
 ('客厅次卧二南端柱',rect(1113,1314,47,23)),
 ('次卧二东北外墙',[[1128,760],[1485,760],[1485,1337],[1458,1337],[1458,785],[1152,785],[1152,797],[1128,797]]),
 ('次卧二西墙转角',[[1128,878],[1152,878],[1152,1128],[1235,1128],[1235,1151],[1128,1151],[1128,1088],[1088,1088],[1088,1064],[1128,1064]]),
 ('次卧二东南门边',rect(1378,1128,80,23)),
 ('主卫衣帽区隔墙西',rect(224,843,89,13)),
 ('主卫衣帽区隔墙东',rect(389,843,14,13)),
 ('次卫家政隔墙',rect(580,425,12,137)),
 ('西翼南窗门边',[[389,1103],[403,1103],[403,1091],[428,1091],[428,1128],[389,1128]]),
]
ZONES = [
 ('厨房',rect(415,157,364,153),'tile'),
 ('次卫',rect(428,334,152,309),'wet'),
 ('主卫',rect(224,558,179,285),'wet'),
 ('衣帽区',rect(224,856,179,247),'oak'),
 ('主卧',rect(428,667,338,647),'oak'),
 ('次卧一',rect(790,334,370,320),'oak'),
 ('次卧二',rect(1152,785,306,343),'oak'),
 ('次卧二窗边区',rect(1140,1151,318,163),'oak'),
]
WINDOWS = [
 ('厨房北窗',[515,151,790,151]),('厨房东窗',[784,157,784,310]),
 ('次卧一北窗',[904,322,1047,322]),('次卫西窗',[415,355,415,418]),
 ('主卫北窗',[322,546,383,546]),('衣帽区南窗',[224,1115,389,1115]),
 ('主卧南窗',[428,1325,750,1325]),('客厅南窗',[808,1325,1113,1325]),
 ('次卧二窗边南窗',[1160,1325,1458,1325]),
 ('次卧二窗边移门',[1235,1140,1378,1140]),('客厅窗边移门',[1134,1151,1134,1314]),
 ('厨房移门',[592,316,767,316]),
]
# x/y/w/h in PNG pixels, height in metres; geometry is furniture, never walls.
FURNITURE = []
def furn(name,kind,x,y,w,h,height=0.8):
    FURNITURE.append(dict(name=name,kind=kind,rect=[x,y,w,h],height_m=height))
furn('主卧床','bed',551,906,214,187,.52)
furn('次卧一床','bed',945,390,215,185,.52)
furn('次卧二床','bed',1244,917,214,158,.52)
for n,r in [('主卧北衣柜',(428,667,224,60)),('主卧西衣柜',(428,727,60,145)),('次卧一衣柜',(799,334,52,205)),('次卧二衣柜',(1255,785,203,63)),('衣帽区长柜',(224,856,60,235)),('主卧窗边衣柜',(428,1151,61,163)),('主卧窗边东柜',(707,1151,58,163)),('次卧二窗边东柜',(1403,1151,55,163)),('客厅书柜',(790,770,41,294))]: furn(n,'cabinet',*r,2.3)
for n,r in [('厨房橱柜',(415,157,364,61)),('主卧窗边矮柜',(489,1273,218,41)),('次卧二窗边矮柜',(1140,1273,263,41)),('次卧一矮柜',(1006,627,134,27))]: furn(n,'lowcab',*r,.85)
furn('冰箱','appliance',415,219,71,91,1.8)
furn('家政高柜','appliance',592,322,63,101,2.3)
furn('洗衣机','appliance',592,425,63,64,.9)
furn('烘干机','appliance',592,489,63,67,.9)
furn('餐桌','table',922,789,92,245,.76)
for x,y in [(878,827),(878,955),(1020,821),(1020,891),(1020,961)]: furn('餐椅','chair',x,y,40,40,.8)
furn('主卧窗边椅','chair',651,1188,45,49,.8)
furn('次卧二窗边椅','chair',1348,1189,45,49,.8)
furn('客厅单椅','lounge',996,1221,70,72,.78)
furn('窗边椅','chair',841,1208,45,50,.8)
furn('边几','table',935,1224,45,68,.48)
furn('次卫台盆','sink',428,549,48,55,.82)
furn('主卫台盆','sink',224,773,54,52,.82)
furn('次卫马桶','wc',449,462,51,37,.42)
furn('主卫马桶','wc',246,677,64,47,.42)
furn('次卫淋浴','shower',428,334,152,103,.03)
furn('主卫淋浴','shower',224,558,179,104,.03)
LABELS = [('厨房',620,270),('次卫',535,540),('主卫',358,711),('衣帽区',347,950),('主卧',573,837),('次卧一',943,602),('次卧二',1255,896),('客餐厅',962,1116),('主卧窗边区',584,1177),('次卧二窗边区',1267,1183),('走道',708,589)]
DOORS = [dict(name='入户门',hinge=[1160,674],leaf=[1079,674],closed=[1160,755]),dict(name='次卧一门',hinge=[799,642],leaf=[799,561],closed=[880,642]),dict(name='次卧二门',hinge=[1152,797],leaf=[1235,797],closed=[1152,878]),dict(name='主卧门',hinge=[751,781],leaf=[751,864],closed=[675,781]),dict(name='衣帽区门',hinge=[428,1091],leaf=[428,1003],closed=[341,1091]),dict(name='主卫门',hinge=[389,843],leaf=[389,769],closed=[314,843]),dict(name='次卫门',hinge=[580,637],leaf=[504,637],closed=[580,561])]
data=dict(units='PNG pixels for xy, metres for z',reference_size=[1663,1485],metres_per_pixel=.00982,calibration='3320 mm / 338 px; approximate image calibration, not site survey',source='User-selected PNG layout; CAD is original structure reference',height_note='2.7 m assumed full walls; review render cuts walls to 1.05 m',outer=OUTER,walls=[dict(name=n,polygon=p) for n,p in WALLS],zones=[dict(name=n,polygon=p,material=m) for n,p,m in ZONES],windows=[dict(name=n,segment=s) for n,s in WINDOWS],furniture=FURNITURE,labels=LABELS,doors=DOORS)
(ROOT/'plan_geometry.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
Image.open(ROOT.parent/'dwg_import/source_plan.png').convert('RGB').resize((1663,1485)).save(ROOT/'reference.png')
colors=dict(oak='#edddbf',tile='#ece7de',wet='#dce9e8')
def polygon(points,**attrs):
    attr=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in attrs.items())
    return '<polygon points="'+' '.join(f'{x},{y}' for x,y in points)+'" '+attr+'/>'
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1663" height="1485" viewBox="0 0 1663 1485">','<rect width="1663" height="1485" fill="#fff"/>',polygon(OUTER,fill='#f4f0e6',stroke='#596367',stroke_width=2)]
for n,p,m in ZONES: parts.append(polygon(p,fill=colors[m]))
for f in FURNITURE:
    x,y,w,h=f['rect']; kind=f['kind']; col={'bed':'#faf7f0','cabinet':'#ba9c70','lowcab':'#cdb28a','table':'#b89a70','chair':'#bbbcb2','lounge':'#afb8b0','sink':'#fbfcfc','wc':'#fbfcfc','shower':'#d5e4e3','appliance':'#d7dad8'}[kind]
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{col}" stroke="#7d8079" stroke-width="1.5"/>')
    if kind=='bed':
        parts.append(f'<path d="M{x+w-50} {y+4}V{y+h-4}" stroke="#b8afa0" fill="none"/>')
        for yy in [y+14,y+h/2+5]: parts.append(f'<rect x="{x+w-42}" y="{yy}" width="32" height="{h/2-24}" rx="7" fill="#fffdf7" stroke="#c6beae"/>')
    if kind in ['cabinet','lowcab']:
        if w>h:
            for xx in range(int(x+50),int(x+w),50): parts.append(f'<path d="M{xx} {y}v{h}" stroke="#aa8e67"/>')
        else:
            for yy in range(int(y+50),int(y+h),50): parts.append(f'<path d="M{x} {yy}h{w}" stroke="#aa8e67"/>')
for n,p in WALLS: parts.append(polygon(p,fill='#414b4d'))
for n,(x1,y1,x2,y2) in WINDOWS: parts.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="#91b8bd" stroke-width="6"/>')
for d in DOORS:
    (x,y),(lx,ly),(cx,cy)=d['hinge'],d['leaf'],d['closed']
    r=((lx-x)**2+(ly-y)**2)**.5
    cross=(lx-x)*(cy-y)-(ly-y)*(cx-x); sweep=1 if cross>0 else 0
    parts.append(f'<path d="M{x} {y}L{lx} {ly} A{r} {r} 0 0 {sweep} {cx} {cy}" fill="none" stroke="#747c77" stroke-width="2"/>')
for label,x,y in LABELS: parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="PingFang SC,Arial,sans-serif" font-size="23" fill="#344344">{html.escape(label)}</text>')
parts.extend(['<text x="200" y="83" font-family="PingFang SC,Arial" font-size="30" fill="#344344">按 PNG 重建 · 平面核对版</text>','<text x="200" y="1410" font-family="PingFang SC,Arial" font-size="19" fill="#727d79">房间布局以 PNG 为准；尺寸由图像标注校准，施工前仍需复尺。</text>','</svg>'])
(ROOT/'floorplan.svg').write_text('\n'.join(parts))
# Independent visibility check: every user-mentioned omitted area is inside slab and outside walls.
mask=Image.new('1',(1663,1485)); draw=ImageDraw.Draw(mask); draw.polygon(OUTER,fill=1)
wallmask=Image.new('1',(1663,1485)); wd=ImageDraw.Draw(wallmask)
for n,p in WALLS: wd.polygon(p,fill=1)
samples={'kitchen corridor':(709,456),'bath approach':(685,596),'central circulation':(954,712),'west wardrobe aisle':(341,952),'master bay':(600,1220),'living bay':(927,1190),'bedroom2 bay':(1300,1240)}
for name,p in samples.items(): assert mask.getpixel(p) and not wallmask.getpixel(p), (name,p)
for f in FURNITURE:
    x,y,w,h=f['rect']; assert mask.getpixel((int(x+w/2),int(y+h/2))),f['name']
report={'usable_points_verified':samples,'wall_polygons':len(WALLS),'windows_or_sliders':len(WINDOWS),'furniture_objects':len(FURNITURE),'pixel_scale_m':data['metres_per_pixel'],'dwg_used_for_layout':False}
(ROOT/'geometry_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
# Overlay lets the reviewer see every traced wall on the original, at identical pixels.
overlay=Image.open(ROOT/'reference.png').convert('RGBA'); ink=Image.new('RGBA',overlay.size); od=ImageDraw.Draw(ink)
for n,p in WALLS: od.polygon([tuple(q) for q in p],fill=(0,139,159,85),outline=(0,109,137,210),width=2)
Image.alpha_composite(overlay,ink).convert('RGB').save(ROOT/'wall_overlay.png')
print(json.dumps(report,ensure_ascii=False))
