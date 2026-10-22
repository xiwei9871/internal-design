import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent;J=json.loads((OUT/'05_prompts/LIVING_JOBS.json').read_text());C=json.loads((OUT/'00_reference/R4_CAMERA_REGISTER.json').read_text())
F='/System/Library/Fonts/STHeiti Medium.ttc';font=lambda n:ImageFont.truetype(F,n);P=OUT/'06_reports/proxies';P.mkdir(exist_ok=True)
board=Image.new('RGB',(1800,2380),'#f5f3ee');d=ImageDraw.Draw(board);d.text((25,15),'R4 客厅探索｜FAITHFUL / DESIGNER / CREATIVE',font=font(32),fill='#304a3d')
for ci,c in enumerate(C):
 row=Image.new('RGB',(1800,460),'#f5f3ee');draw=ImageDraw.Draw(row)
 for vi,v in enumerate(['faithful','designer','creative']):
  j=next(j for j in J if j['camera_id']==c['id'] and j['variant']==v);x=15+vi*600;draw.text((x,15),c['id']+' '+v.upper(),font=font(25),fill='#304a3d');p=Path(j['output'])
  if p.exists():
   im=Image.open(p);im.load();im.thumbnail((570,380));row.paste(im,(x,62));im.save(P/(j['image_id']+'.png'))
  else:draw.text((x,210),'WAIT / API FAILURE',font=font(24),fill='#877c68')
 row.save(OUT/'04_contact_sheets'/(c['id']+'_3DIRECTIONS.png'));sm=row.copy();sm.thumbnail((1200,307));sm.save(P/(c['id']+'_3DIRECTIONS.png'));board.paste(row,(0,75+ci*460))
board.save(OUT/'04_contact_sheets/LIVING_ALL_15_CONTACT_SHEET.png')
for v in ['faithful','designer','creative']:
 sheet=Image.new('RGB',(1800,1410),'#f5f3ee');draw=ImageDraw.Draw(sheet);draw.text((25,15),'R4 '+v.upper()+'｜五个机位的候选灵感，尚不要求同家具一致',font=font(28),fill='#304a3d')
 for i,c in enumerate(C):
  j=next(j for j in J if j['camera_id']==c['id'] and j['variant']==v);x=i%3*600+15;y=i//3*460+80;draw.text((x,y),c['id'],font=font(26),fill='#304a3d')
  if Path(j['output']).exists():im=Image.open(j['output']);im.thumbnail((570,380));sheet.paste(im,(x,y+45))
 sheet.save(OUT/'04_contact_sheets'/('LIVING_'+v.upper()+'_5VIEW.png'))
ref=Image.new('RGB',(1800,1010),'#f5f3ee');d=ImageDraw.Draw(ref);d.text((25,15),'五个R4机位｜clay / geometry reference',font=font(30),fill='#304a3d')
for i,c in enumerate(C):
 x=i%3*600+15;y=i//3*460+70;d.text((x,y),c['id']+' '+c['name'],font=font(25),fill='#304a3d');im=Image.open(c['reference']);im.thumbnail((570,380));ref.paste(im,(x,y+45))
ref.save(OUT/'04_contact_sheets/LIVING_R4_CAMERA_REFERENCE_SHEET.png')
print(json.dumps(dict(available=sum(Path(j['output']).exists() for j in J),target=15,contact_sheets='FILESYSTEM_ONLY')))
