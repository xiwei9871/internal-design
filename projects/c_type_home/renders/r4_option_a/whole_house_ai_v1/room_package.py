import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
def package(room):
 D=OUT/room['folder'];cams=json.loads((D/'reports/CAMERA_REGISTER.json').read_text());ip=D/'reports/IMAGES.json';imgs=json.loads(ip.read_text()) if ip.exists() else []
 f=lambda n:ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',n)
 board=Image.new('RGB',(1800,85+460*len(cams)),'#f5f3ee');dr=ImageDraw.Draw(board);dr.text((25,15),room['name']+'｜FAITHFUL / DESIGNER / CREATIVE',font=f(30),fill='#30493e')
 refboard=Image.new('RGB',(1800,75+450*((len(cams)+2)//3)),'#f5f3ee');rd=ImageDraw.Draw(refboard);rd.text((25,15),room['name']+'｜R4 geometry references',font=f(28),fill='#30493e')
 proxies=D/'reports/proxies';proxies.mkdir(exist_ok=True)
 for ci,c in enumerate(cams):
  row=Image.new('RGB',(1800,460),'#f5f3ee');r=ImageDraw.Draw(row)
  for vi,v in enumerate(['faithful','designer','creative']):
   x=vi*600+15;r.text((x,15),c['id']+' '+v.upper(),font=f(25),fill='#30493e');rec=next((i for i in imgs if i['camera']==c['id'] and i['variant']==v),None)
   if rec and Path(rec['output']).exists():
    qa='GEOM '+rec.get('geometry_preservation','WARNING')+' | DIV '+rec.get('divergence_gate','PENDING');color='#a33a29' if rec.get('geometry_preservation')=='FAIL' else '#886300' if rec.get('geometry_preservation')=='WARNING' or rec.get('divergence_gate','').startswith('WARNING') else '#30493e';r.text((x,43),qa,font=f(16),fill=color)
    im=Image.open(rec['output']);im.thumbnail((570,380));row.paste(im,(x,62));im.save(proxies/(rec['image_id']+'.png'))
   else:r.text((x,200),'WAIT / FAILED',font=f(25),fill='#857765')
  board.paste(row,(0,75+ci*460));row.save(D/'contact_sheet'/(c['id']+'_VERSIONS.png'));sm=row.copy();sm.thumbnail((1200,307));sm.save(proxies/(c['id']+'_VERSIONS.png'))
  x=ci%3*600+15;y=ci//3*450+70;rd.text((x,y),c['id'],font=f(25),fill='#30493e');im=Image.open(c['reference']);im.thumbnail((570,380));refboard.paste(im,(x,y+45));im.save(proxies/(c['id']+'_REFERENCE.png'))
 board.save(D/'contact_sheet/ROOM_CONTACT_SHEET.png');refboard.save(D/'contact_sheet/ROOM_REFERENCE_CONTACT_SHEET.png')
 index=['# '+room['name']+'图像索引','', '[候选contact sheet]('+str(D/'contact_sheet/ROOM_CONTACT_SHEET.png')+') · [R4参考contact sheet]('+str(D/'contact_sheet/ROOM_REFERENCE_CONTACT_SHEET.png')+')','','| 相机 | faithful | designer | creative |','|---|---|---|---|']
 for c in cams:
  row=[c['id']]
  for v in ['faithful','designer','creative']:
   rec=next((i for i in imgs if i['camera']==c['id'] and i['variant']==v),None);row.append('['+v+']('+rec['output']+')' if rec and Path(rec['output']).exists() else 'FAILED / WAIT')
  index.append('| '+' | '.join(row)+' |')
 index+=['','所有图是未选择候选。固定构造/净空以R4及reference为准；图上GEOM/DIV是轻量视觉核查，FAIL和WARNING须读取ROOM_REVIEW.md；不能当施工证明。']
 (D/'reports/IMAGE_INDEX.md').write_text('\n'.join(index)+'\n')
 return str(D/'contact_sheet/ROOM_CONTACT_SHEET.png')
