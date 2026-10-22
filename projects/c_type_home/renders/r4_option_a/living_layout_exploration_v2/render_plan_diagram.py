import json,math,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT))
from layout_spec import LAYOUTS
lines=json.loads((OUT/'reports/R4_PLAN_SECTION_LINES.json').read_text())['lines'];cams=json.loads((OUT/'reports/CAMERA_REGISTER.json').read_text())
board=Image.new('RGB',(1320,660),'#f7f4ee');font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',16)
# Clip derived mesh-section segments to each viewport. No raster trace or reconstructed wall geometry.
def clip(a,b):
 x0,y0=a;x1,y1=b;dx=x1-x0;dy=y1-y0;t0,t1=0.,1.
 for p,q in [(-dx,x0-2.9),(dx,7.8-x0),(-dy,y0-7.0),(dy,14.1-y0)]:
  if abs(p)<1e-12:
   if q<0:return None
   continue
  t=q/p
  if p<0:t0=max(t0,t)
  else:t1=min(t1,t)
  if t0>t1:return None
 return [(x0+t0*dx,y0+t0*dy),(x0+t1*dx,y0+t1*dy)]
for j,k in enumerate(['A','B','C']):
 tile=Image.new('RGB',(440,660),'#f7f4ee');dr=ImageDraw.Draw(tile)
 def pt(x,y):return(20+(x-2.9)*80,58+(14.1-y)*80)
 def rect(lo,hi,fill,outline='#698570'):dr.rectangle([*pt(lo[0],hi[1]),*pt(hi[0],lo[1])],fill=fill,outline=outline,width=2)
 dr.text((20,15),LAYOUTS[k]['name']+'｜包络/机位',font=font,fill='#30493e')
 rect([6.28,8.80],[7.398,11.50],'#e5ecd8');dr.text(pt(6.35,11.30),'≈1118mm',font=font,fill='#68734b')
 rect([3.65,12.95],[7.05,13.873],'#dbe9ed');dr.text(pt(4.10,13.60),'原飘窗+450',font=font,fill='#425f70');rect([7.398,8.635],[7.697,11.524],'#d8d1c2')
 for line in lines:
  seg=clip(*line['points'])
  if seg:dr.line([pt(*seg[0]),pt(*seg[1])],fill='#485354',width=2)
 rect([3.401,9.216],[4.301,11.516],'#e3d3b7');l=LAYOUTS[k]
 if k in ['A','B']:
  x,y=l['chaise_center'];rect([x-.85,y-.45],[x+.85,y+.45],'#e2c9b2');dr.text(pt(x-.6,y+.20),'贵妃椅',font=font,fill='#67492c')
 if k=='A':
  x,y=l['two_center'];rect([x-.95,y-.425],[x+.95,y+.425],'#dfd1be');dr.text(pt(x-.7,y+.1),'双人位↑',font=font,fill='#67492c')
 if k=='C':rect([3.46,10.616],[6.00,11.516],'#e3d3b7');dr.text(pt(4.55,11.10),'L回转段',font=font,fill='#67492c')
 if k in ['B','C']:
  x,y=l['chair_center'];ang=math.radians(l['chair_angle']);w,h=.835,.76;pts=[pt(x+u*math.cos(ang)-v*math.sin(ang),y+u*math.sin(ang)+v*math.cos(ang)) for u,v in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]];dr.polygon(pts,fill='#dfbfb3',outline='#816252');dr.text(pt(x-.3,y+.1),'单椅',font=font,fill='#67492c')
 x,y=l['table_center']
 for xx,yy,ww,hh in [(x,y,.98,.62),(x+.47,y+.22,.57,.52)]:dr.ellipse([*pt(xx-ww/2,yy+hh/2),*pt(xx+ww/2,yy-hh/2)],fill='#efeade',outline='#8a8172',width=2)
 for x,y in l['side_centers']:dr.ellipse([*pt(x-.21,y+.21),*pt(x+.21,y-.21)],fill='#d0b98e',outline='#876c41',width=2)
 for c in cams:
  if c['layout']!=k or c['camera'] not in ['L1','L2','L5']:continue
  x,y,_=c['pos'];tx,ty,_=c['target'];a=math.atan2(ty-y,tx-x);spread=math.atan(36/(2*c['lens']));cp=pt(x,y)
  for angle in [a-spread,a+spread]:dr.line([cp,pt(x+1.5*math.cos(angle),y+1.5*math.sin(angle))],fill='#9d8faf',width=1)
  dr.line([cp,pt(x+.8*math.cos(a),y+.8*math.sin(a))],fill='#705886',width=2);dr.ellipse([cp[0]-4,cp[1]-4,cp[0]+4,cp[1]+4],fill='#705886');dr.text((cp[0]+7,cp[1]+2),c['camera'],font=font,fill='#705886')
 dr.text((20,613),'建筑线=R4网格剖面；家具未选择',font=font,fill='#526451')
 dr.text((20,635),'C椅朝向在AI中有漂移，详见审阅' if k=='C' else '窗台前140mm不是通道',font=font,fill='#526451')
 board.paste(tile,(j*440,0))
board.save(OUT/'reports/LAYOUT_PLAN_CAMERA_ENVELOPES.png');print('current_layout_plan_saved')
