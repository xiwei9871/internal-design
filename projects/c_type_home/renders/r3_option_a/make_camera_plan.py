import json,math,runpy
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
B=runpy.run_path(str(ROOT/'design/secondary_bath_options/r3/solid_backend.py'),run_name='slice_helpers')
geo=json.loads((OUT/'LIVING_PLAN_SOURCE_GEOMETRY.json').read_text());cam=json.loads((OUT/'R3_CAMERA_REGISTER.json').read_text());pref=json.loads((OUT/'TEST_PREFLIGHT.json').read_text())
assert geo['source_sha256']==pref['source_sha256']
polys=[]
for w in geo['walls']:
 zs=[v[2] for v in w['vertices']];w['minz']=min(zs);w['maxz']=max(zs);polys.append(B['cross_section'](w,1.55))
walls=unary_union(polys).intersection(box(2.6,7.4,8.2,14.2))
im=Image.new('RGB',(1100,1320),'#faf8f4');d=ImageDraw.Draw(im);ft=lambda n:ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',n)
def uv(p):return (120+(p[0]-2.6)*145,155+(14.2-p[1])*145)
def drawpoly(p,fill):
 if p.geom_type=='Polygon':
  d.polygon([uv(c) for c in p.exterior.coords],fill=fill)
  for hole in p.interiors:d.polygon([uv(c) for c in hole.coords],fill='#faf8f4')
 elif hasattr(p,'geoms'):
  for pp in p.geoms:drawpoly(pp,fill)
drawpoly(walls,'#a4aaa5')
for r in pref['active_living_area']:
 if r['name'].startswith(('B11_Rectangle046','B11_Rectangle047','B11_Rectangle048','B11_Rectangle049','B11_Circle_CATALOG','B11_Rectangle004')):
  drawpoly(box(r['lo'][0],r['lo'][1],r['hi'][0],r['hi'][1]),'#d3c4a7')
 if r['name'].startswith('LIVING_FIX_BAY') and 'GLASS' in r['name']:drawpoly(box(r['lo'][0],r['lo'][1],r['hi'][0],r['hi'][1]).buffer(.009),'#7bb9c5')
x,y=cam['position_m'][:2];tx,ty=cam['target_m'][:2];angle=math.atan2(ty-y,tx-x);half=math.atan(cam['sensor_width_mm']/2/cam['lens_mm']);range_=5.9
tri=Polygon([(x,y),(x+range_*math.cos(angle-half),y+range_*math.sin(angle-half)),(x+range_*math.cos(angle+half),y+range_*math.sin(angle+half))]).intersection(box(2.6,7.4,8.2,14.2))
overlay=Image.new('RGBA',im.size,(0,0,0,0));od=ImageDraw.Draw(overlay);od.polygon([uv(c) for c in tri.exterior.coords],fill=(48,125,160,45),outline=(48,125,160,220),width=3);im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB');d=ImageDraw.Draw(im)
p=uv((x,y));d.ellipse([p[0]-8,p[1]-8,p[0]+8,p[1]+8],fill='#245d79');d.line([p,uv((tx,ty))],fill='#245d79',width=3)
d.text((40,30),'客厅单张测试｜R3 A 相机及包络',font=ft(35),fill='#2e463c');d.text((40,90),'28mm · 视高1.55m · 朝西北看沙发与北侧飘窗',font=ft(24),fill='#536962')
d.text((40,1195),'蓝：实际飘窗玻璃与相机视锥　米色：原家具包络',font=ft(23),fill='#536962');d.text((40,1235),'休闲平台位于相机后方；本视角不得在画面里另造平台或楼梯。',font=ft(22),fill='#536962')
out=OUT/'living/diagnostics/LIVING_01_CAMERA_PLAN.png';out.parent.mkdir(parents=True,exist_ok=True);im.save(out)
print(str(out))
