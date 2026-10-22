"""Paths-only annotated plans and fixed-view A/B comparison sheets."""
import json,math,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import shape,box,Polygon
OUT=Path(__file__).resolve().parent;L=json.loads((OUT/'LAYOUT_CONTRACT.json').read_text());QA=json.loads((OUT/'CLEARANCE_QA.json').read_text());G=json.loads((OUT/'PLAN_GEOMETRY.json').read_text())
RD=OUT/'renders';PD=OUT/'proxies';PD.mkdir(exist_ok=True)
FONT='/System/Library/Fonts/STHeiti Medium.ttc'
def font(n):return ImageFont.truetype(FONT,n)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def draw_plan(opt):
 im=Image.new('RGB',(1400,1320),'#f6f5f1');d=ImageDraw.Draw(im)
 d.text((55,30),('A｜南侧推拉门' if opt=='A' else 'B｜南侧内开门'),font=font(42),fill='#233632')
 d.text((55,95),'最新 FreeCAD 布局 · 完整西墙 · 衣柜西侧入口 · 同一套洁具位置',font=font(24),fill='#50615d')
 scale=280;ox=300;oy=170;xbase=8.95;ytop=6.85
 def uv(p):return (ox+(p[0]-xbase)*scale,oy+(ytop-p[1])*scale)
 def geom(g,fill,outline=None,width=2):
  if g.is_empty:return
  if g.geom_type in ['MultiPolygon','GeometryCollection']:
   for p in g.geoms:
    if p.geom_type in ['Polygon','MultiPolygon']:geom(p,fill,outline,width)
  elif g.geom_type=='Polygon':
   d.polygon([uv(p) for p in g.exterior.coords],fill=fill)
   for ring in g.interiors:d.polygon([uv(p) for p in ring.coords],fill='#f6f5f1')
   if outline:d.line([uv(p) for p in g.exterior.coords],fill=outline,width=width,joint='curve')
 def rect(r,c,edge='#59625e'):geom(box(*r),c,edge)
 def label(pos,t,n=24,c='#273e36'):d.text(pos,t,font=font(n),fill=c)
 def leader(p,q,t,pos):d.line([uv(p),q],fill='#52635c',width=2);d.ellipse((q[0]-3,q[1]-3,q[0]+3,q[1]+3),fill='#52635c');label(pos,t,22)
 # Actual wall sections from fresh-open mesh data. Renovation additions are gold.
 geom(shape(G[opt]['walls']),'#969d99','#5c6660')
 geom(shape(G[opt]['new_walls']),'#ead398','#a99050')
 if opt=='B':geom(shape(G[opt]['sweep']),'#f1ddc2','#b08753',1)
 S=L['shared'];rect(S['vanity'],'#b5c6c8');rect(S['wardrobe'],'#c6b28e')
 vx=(S['vanity'][0]+S['vanity'][2])/2;vy=(S['vanity'][1]+S['vanity'][3])/2
 d.ellipse((*uv((vx-.20,vy+.14)),*uv((vx+.20,vy-.14))),fill='#e9eeec',outline='#72888a',width=2)
 for xx in [S['wardrobe'][0]+(S['wardrobe'][2]-S['wardrobe'][0])/3,S['wardrobe'][0]+2*(S['wardrobe'][2]-S['wardrobe'][0])/3]:d.line([uv((xx,S['wardrobe'][1])),uv((xx,S['wardrobe'][3]))],fill='#988260',width=2)
 geom(Polygon(S['shower']),'#d4e6e9','#6c8e93')
 pts=S['screen'];d.line([uv(p) for p in pts],fill='#3e747a',width=6)
 wc=S['wc'];rect(wc,'#ebeeeb','#8c9992');x0,y0,x1,y1=wc
 d.ellipse((*uv((x0+.03,y1-.055)),*uv((x1-.13,y0+.055))),fill='#f7f8f4',outline='#88958e',width=2)
 rect([x1-.15,y0,x1,y1],'#e2e8e2')
 # Door leaf states: dashed CLOSED, solid orange OPEN.
 closed=shape(G[opt]['closed']);coords=list(closed.exterior.coords)
 for a,b in zip(coords,coords[1:]):
  au,bu=uv(a),uv(b);length=math.dist(au,bu);steps=max(1,int(length/8))
  for j in range(0,steps,2):
   f=j/steps;h=min(1,(j+1)/steps);d.line([(au[0]+(bu[0]-au[0])*f,au[1]+(bu[1]-au[1])*f),(au[0]+(bu[0]-au[0])*h,au[1]+(bu[1]-au[1])*h)],fill='#4b7880',width=3)
 geom(shape(G[opt]['opened']),'#c87343','#744425',3)
 label(uv((9.39,6.70)),'北 ↑',26)
 label(uv((9.43,6.58)),'台盆柜 1200×500',22)
 label(uv((10.69,6.25)),'切角淋浴',22)
 label(uv((10.87,5.23)),'马桶',22)
 label(uv((10.29,4.18)),'衣柜 1400×600',22)
 leader((9.134,5.58),(260,475),'完整西墙 150 mm',(58,427))
 leader((10.53,4.60),(1150,800),'南侧补墙已闭合',(1140,828))
 if opt=='A':
  label(uv((10.10,4.99)),'门扇向东收入隐藏段 →',21,'#8b542f')
  label(uv((9.28,5.40)),'室内无开门回转区',21)
 else:
  label(uv((9.54,5.58)),'内开约 85°',21,'#8b542f')
  label(uv((9.66,5.43)),'含把手回转约 0.42 m²',19,'#8b542f')
 # Clear width dimension west of wardrobe; includes frame deductions.
 q0,q1=L['opening']['clear'];y=4.34;u0,u1=uv((q0,y)),uv((q1,y));d.line([u0,u1],fill='#25585b',width=2)
 for p in [u0,u1]:d.line([(p[0],p[1]-9),(p[0],p[1]+9)],fill='#25585b',width=2)
 label((u0[0]-10,u0[1]+16),'净通行约 729 mm',21,'#25585b')
 label((55,1190),'灰：基础墙体　黄：新增隔断　橙：开门状态　蓝虚线：关门状态',22)
 label((55,1234),'门框和构造为审阅尺寸；净入口、淋浴净开口及洁具排水仍需复尺。',21,'#7a6651')
 p=RD/f'{opt}_PLAN_DIMENSIONED.png';im.save(p)
 return p
plans=[draw_plan(o) for o in 'AB']
def sheet(name,pairs,title,note):
 width=2400;header=115;rowh=850
 im=Image.new('RGB',(width,header+rowh*len(pairs)+95),'#f6f5f1');d=ImageDraw.Draw(im)
 d.text((35,20),title,font=font(42),fill='#233632')
 d.text((35,72),note,font=font(23),fill='#59675f')
 for row,(a,b,tag) in enumerate(pairs):
  for j,p in enumerate([a,b]):
   img=Image.open(p);img.thumbnail((1160,785));x=j*1200+(1200-img.width)//2;y=header+row*rowh+50
   im.paste(img,(x,y));d.text((j*1200+35,header+row*rowh+5),('A 推拉门' if j==0 else 'B 内开门')+'｜'+tag,font=font(25),fill='#233632')
 d.text((35,im.height-55),'完整模型分别保存；图示剖切只用于查看内部，不写回模型。',font=font(22),fill='#6d725e')
 p=RD/name;im.save(p);return p
sheet('AB_PLAN_COMPARISON.png',[(plans[0],plans[1],'同尺度平面')],'次主卫 A/B｜最新布局对比','完整西墙采用最新 FreeCAD 墙线；两案入口和洁具布局完全一致。')
sheet('AB_MODEL_COMPARISON.png',[(RD/'A_ENTRY_100.png',RD/'B_ENTRY_100.png','完整入口'),(RD/'A_CUTAWAY_AXON_100.png',RD/'B_CUTAWAY_AXON_100.png','内部剖视')],'次主卫 A/B｜同角度模型对比','A 向东收入墙后；B 向内开约85°并设门挡。内部剖视切至约1140mm绝对标高。')
# Filesystem proxies for bounded inspection; never attached to final chat.
for p in RD.glob('*.png'):
 im=Image.open(p);im.thumbnail((600,600));im.save(PD/p.name)
manifest=dict(images=[dict(path=str(p),sha256=sha(p)) for p in sorted(RD.glob('*.png'))],proxies_directory=str(PD),context_policy='PATHS_ONLY')
(OUT/'REVIEW_IMAGE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(plans='PASS',review_sheets='PASS',images=len(manifest['images']),paths_only=True)))
