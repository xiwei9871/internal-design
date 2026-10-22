import json,sys,math,hashlib,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageEnhance
from shapely.geometry import shape,Point,LineString,box,mapping
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[1];G=json.loads((OUT/'reports/OPTION_GEOMETRY.json').read_text());M=G['metrics'];font=lambda n:ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',n)
COL=dict(bg='#f6f4ed',ink='#30493e',sub='#687366',lower='#ebe5d7',upper='#c4ceb7',tread='#cfb28c',danger='#a74635')
def title(image,heading,note):
 im=image.convert('RGB');d=ImageDraw.Draw(im);d.rectangle((0,0,im.width,112),fill=COL['bg']);d.text((28,20),heading,font=font(34),fill=COL['ink']);d.text((28,69),note,font=font(23),fill=COL['sub']);return im
for k in ['A','B']:
 rs=json.loads((OUT/'reports'/('OPTION_'+k+'_RENDERS.json')).read_text())
 for r in rs:
  raw=Image.open(r['raw']);suffix=r['view'];heading='方案'+k+'｜'+({'PLAN':'总平面','AXON':'轴测与高差','VIEW_01':'客厅看错层','VIEW_02':'上层回看客厅','SECTION':'实模型剖切参考'}[suffix]);note='研究模型 · LOWER 0 / UPPER +450 · 建筑边界与门窗保持 · 家具仅R4示意'
  im=title(raw,heading,note)
  if suffix=='PLAN':
   d=ImageDraw.Draw(im);w,h=im.size;scale=h/13.5;cx,cy=5.4,7.45
   def p(x,y):return(w/2+(x-cx)*scale,h/2-(y-cy)*scale)
   labels=[(4.75,10.2,'客厅 LOWER 0'),(4.1,3.8,'餐厅 LOWER 0'),(8.45,6.9,'走廊 UPPER +450'),(6.9,5.8,'保留平台 +450' if k=='A' else '回收至 LOWER 0')]
   for x,y,t in labels:
    px,py=p(x,y);d.rounded_rectangle((px-7,py-7,px+max(len(t)*19,210),py+34),radius=5,fill='#faf8ef');d.text((px,py),t,font=font(23),fill=COL['ink'])
   # Actual R4 original footprint outline, a locator only, no traced architecture.
   for geo in [shape(G['fan'])]:
    pts=[p(x,y) for x,y in geo.exterior.coords];d.line(pts,fill='#a87935',width=3)
   d.text((35,h-75),'原弧形平台边界（定位）｜A 两道弧形踏步+顶平台；B 1200宽三阶直梯',font=font(24),fill=COL['ink'])
  im.save(OUT/('LEISURE_OPTION_'+k+'_'+suffix+'.png'))
# Measured sections: derive1mm-sampled elevation profile from authored option polygons atY5.55.
section_values={}
for k in ['A','B']:
 image=Image.new('RGB',(1800,1200),COL['bg']);d=ImageDraw.Draw(image);d.text((30,24),'方案'+k+'｜剖面 S—S（Y=5.55 m，向北）',font=font(36),fill=COL['ink']);d.text((30,76),'高程来自实际方案几何；示意纵向放大，横向按标注尺寸读取',font=font(24),fill=COL['sub'])
 raw=Image.open(OUT/'renders/raw'/('LEISURE_OPTION_'+k+'_SECTION.png')).convert('RGB');raw.thumbnail((850,440));image.paste(raw,(925,112));d.text((940,570),'Blender 实模型剖切（仅渲染时裁切，未回写模型）',font=font(22),fill=COL['sub'])
 polys=[(shape(G['A_full_upper']),.45),(shape(G['A_tier_300']),.30),(shape(G['A_tier_150']),.15)] if k=='A' else [(shape(G['B_retained_upper']),.45)]+[(shape(g),.15*(i+1)) for i,g in enumerate(G['B_steps'])]
 xs=[4.7+i*.002 for i in range(2001)];profile=[]
 for x in xs:
  z=round(max([zz for poly,zz in polys if poly.buffer(1e-7).covers(Point(x,5.55))]+[0]),4);profile.append((x,z))
 breaks=[]
 for j in range(1,len(profile)):
  if profile[j][1]!=profile[j-1][1]:breaks.append(dict(x=round(profile[j][0],3),z_from=profile[j-1][1],z_to=profile[j][1]))
 section_values[k]=dict(section_y=5.55,breaks=breaks,rise_mm=150,sampled_step_m=.002,known_going_mm=300)
 originx,originy=85,530;xscale=175;zscale=620
 def p(x,z):return(originx+(x-4.7)*xscale,originy-z*zscale)
 line=[p(x,z) for x,z in profile if x<=8.75];d.polygon([(originx,originy)]+line+[p(8.7,0)],fill='#d4c2a8');d.line(line,fill=COL['ink'],width=4);d.line([p(4.7,0),p(8.7,0)],fill='#71806b',width=2)
 for z,t in [(0,'LOWER = 0'),(.15,'+150'),(.30,'+300'),(.45,'UPPER = +450')]:
  yy=p(4.7,z)[1];d.line((72,yy,795,yy),fill='#c7cec0',width=1);d.text((90,yy-33),t,font=font(22),fill=COL['ink'])
 for r in breaks:
  x=r['x'];xx=p(x,0)[0];yy=p(x,max(r['z_from'],r['z_to']))[1];d.line((xx+8,p(x,min(r['z_from'],r['z_to']))[1],xx+8,yy),fill='#9a7546',width=2);d.text((xx+15,yy+13),'150',font=font(18),fill='#9a7546')
 if len(breaks)>=3:
  for a,b in zip(breaks[:2],breaks[1:3]):
   x0,x1=p(a['x'],0)[0],p(b['x'],0)[0];y=610;d.line((x0,y,x1,y),fill=COL['ink'],width=2);d.line((x0,y-8,x0,y+8),fill=COL['ink'],width=2);d.line((x1,y-8,x1,y+8),fill=COL['ink'],width=2);d.text(((x0+x1)/2-20,y+10),str(round((b['x']-a['x'])*1000)),font=font(20),fill=COL['ink'])
 d.text((48,686),'A：两道连续弧形踏步 + +450顶平台；步高150mm，弧边法向踏深300mm' if k=='A' else 'B：紧凑直梯，三级150mm，总高450mm；踏深300mm，宽1200mm',font=font(28),fill=COL['ink'])
 d.text((48,744),'坡道研究（未采用）：450mm / 1:12 → 坡段5400mm；两端各1525mm平台 → 8450mm',font=font(27),fill=COL['danger'])
 # Full correct ramp benchmark inset, labels preserve real lengths despite smaller drawing.
 rx,ry,sc=90,1060,.165
 def rp(x,z):return(rx+x*sc,ry-z*.25)
 total=8450;pts=[rp(0,0),rp(1525,0),rp(6925,450),rp(total,450)];d.line(pts,fill=COL['danger'],width=5);d.line([rp(0,0),rp(total,0)],fill='#c3b5a1',width=2)
 for a,b,t in [(0,1525,'1525 landing'),(1525,6925,'5400 run / 8.33%'),(6925,8450,'1525 landing')]:
  xa,xb=rp(a,0)[0],rp(b,0)[0];y=1100;d.line((xa,y,xb,y),fill=COL['danger'],width=2);d.text(((xa+xb)/2-len(t)*6,y+14),t,font=font(21),fill=COL['danger'])
 d.text((1035,943),'450 mm',font=font(23),fill=COL['danger']);d.text((65,826),'1900mm短坡 = 23.68%（1:4.22）｜该空间内完整安全坡道不可行，仅作研究示意',font=font(27),fill=COL['danger'])
 image.save(OUT/('LEISURE_OPTION_'+k+'_SECTION.png'))
(OUT/'reports/SECTION_MEASUREMENT.json').write_text(json.dumps(section_values,ensure_ascii=False,indent=2)+'\n')
# Diagram showing true-scale ramp vs available footprint and fixed wall conflicts.
plan=Image.new('RGB',(1500,950),COL['bg']);d=ImageDraw.Draw(plan);d.text((25,20),'B2 坡道尺度研究｜未纳入实施方案',font=font(34),fill=COL['ink']);d.text((25,72),'真实坡段 5400×1100mm，两端平台各1525mm；总长8450mm',font=font(25),fill=COL['sub'])
sec=json.loads((ROOT/'renders/r4_option_a/living_layout_exploration_v2/reports/R4_PLAN_SECTION_LINES.json').read_text());
def p(x,y):return(40+(x-.1)*140,820-(y-3.8)*140)
for l in sec['lines']:
 a,b=l['points']
 if all(.1<=v[0]<=8.9 and 3.8<=v[1]<=8.8 for v in [a,b]):d.line([p(*a),p(*b)],fill='#788278',width=2)
for a,b,col in [(.275,1.8,'#dfb6a5'),(1.8,7.2,'#c88a74'),(7.2,8.725,'#dfb6a5')]:
 x0,y0=p(a,6.1);x1,y1=p(b,5.0);d.rectangle((x0,y0,x1,y1),fill=col,outline=COL['danger'],width=3)
F=shape(G['fan']);d.line([p(x,y) for x,y in F.exterior.coords],fill='#2b655c',width=4);d.text(p(5.55,6.57),'原弧形区仅1500×1900',font=font(24),fill='#2b655c');d.text((40,870),'红色完整坡道穿过原西侧墙/入户及下层交通，不可按此图实施；橙红坡段与现墙/门冲突',font=font(26),fill=COL['danger']);plan.save(OUT/'LEISURE_RAMP_FEASIBILITY.png')
# Two-column decision board, modest dimensions.
board=Image.new('RGB',(2200,1800),COL['bg']);bd=ImageDraw.Draw(board);bd.text((30,20),'错层过渡实验｜A 保留连续弧阶  vs  B 回收平台＋紧凑直梯',font=font(36),fill=COL['ink'])
for j,k in enumerate(['A','B']):
 x=j*1100+20;bd.text((x+12,85),'OPTION '+k+' '+('FAN RETAINED' if k=='A' else 'FAN REMOVED'),font=font(30),fill=COL['ink'])
 for i,suffix in enumerate(['PLAN','AXON','SECTION','VIEW_01']):
  y=135+(i//2)*545;xx=x+(i%2)*535;im=Image.open(OUT/('LEISURE_OPTION_'+k+'_'+suffix+'.png'));im.thumbnail((520,480));board.paste(im,(xx,y))
 notes=['保留原2.64㎡弧形上层区，定位为留白过渡','连续曲边更完整，无独立第二沙发组','额外占下层约2.60㎡；总过渡占地5.95㎡','弧阶仍有三级障碍，轮椅通行未解决','适合看重建筑曲线、愿意接受地面占用'] if k=='A' else ['新直梯1200宽，3×150高 / 300踏深','阶梯占地1.08㎡，下层净回收2.28㎡','主客厅边界简化，动线与布置弹性增加','仍非无障碍；完整安全坡道本区不可行','建议优先深化B，先核实平台结构能否拆除']
 for i,t in enumerate(notes):bd.text((x+22,1260+i*77),'• '+t,font=font(28),fill=COL['ink'] if i!=4 else '#825b31')
board.save(OUT/'LEISURE_OPTION_COMPARE_SHEET.png')
# Image index keeps all outputs readable without binary chat context.
idx=['# 错层A/B研究图像索引','', '[总对比]('+str(OUT/'LEISURE_OPTION_COMPARE_SHEET.png')+') · [报告]('+str(OUT/'LEISURE_COMPARE_REPORT.md')+')','','| 图类 | A | B |','|---|---|---|']
for s in ['PLAN','AXON','VIEW_01','VIEW_02','SECTION']:idx.append('| '+s+' | [A-'+s+']('+str(OUT/('LEISURE_OPTION_A_'+s+'.png'))+') | [B-'+s+']('+str(OUT/('LEISURE_OPTION_B_'+s+'.png'))+') |')
idx+=['','- [完整坡道不可行研究]('+str(OUT/'LEISURE_RAMP_FEASIBILITY.png')+')','- [A模型]('+str(OUT/'LEISURE_COMPARE_OPTION_A.blend')+')','- [B模型]('+str(OUT/'LEISURE_COMPARE_OPTION_B.blend')+')'];(OUT/'LEISURE_VIEW_INDEX.md').write_text('\n'.join(idx)+'\n')
print(json.dumps(dict(packaged_views=10,compare_sheet=True,ramp_study=True,metrics=M,section_values=section_values),ensure_ascii=False))
