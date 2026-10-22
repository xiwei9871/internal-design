import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
JOBS=json.loads((OUT/'working/prompts/jobs.json').read_text());CAMS=json.loads((OUT/'working/cameras/LIVING_CAMERA_REGISTER.json').read_text())
FONT='/System/Library/Fonts/STHeiti Medium.ttc';ft=lambda n:ImageFont.truetype(FONT,n)
preview=OUT/'working/previews/ai_review';preview.mkdir(parents=True,exist_ok=True)
all_sheet=Image.new('RGB',(1800,5*460+100),'#f5f3ee');draw=ImageDraw.Draw(all_sheet);draw.text((25,20),'客厅 AI 候选｜5机位 × strict / design / explore',font=ft(32),fill='#304b3e')
for ci,cam in enumerate(CAMS):
 row=Image.new('RGB',(1800,470),'#f5f3ee');d=ImageDraw.Draw(row)
 for vi,mode in enumerate(['strict','design','explore']):
  job=next(j for j in JOBS if j['camera']==cam['id'] and j['version']==mode);p=Path(job['output']);x=vi*600+15
  d.text((x,15),cam['id']+' '+cam['name']+'｜'+mode,font=ft(24),fill='#304b3e')
  if p.exists():
   im=Image.open(p);im.load();im.thumbnail((570,380));row.paste(im,(x,65))
   small=im.copy();small.save(preview/(job['id']+'_proxy.png'))
  else:d.text((x,200),'待生成 / fallback',font=ft(25),fill='#777766')
 row.save(OUT/'exports/contact_sheets'/(cam['id']+'_VERSIONS.png'))
 sm=row.copy();sm.thumbnail((1200,313));sm.save(preview/(cam['id']+'_VERSIONS_PROXY.png'))
 all_sheet.paste(row.crop((0,0,1800,460)),(0,90+ci*460))
all_sheet.save(OUT/'exports/contact_sheets/LIVING_AI_CONTACT_SHEET_v1.png')
print(json.dumps(dict(contact_sheet='READY',existing_images=sum(Path(j['output']).exists() for j in JOBS),review_proxies=str(preview)),ensure_ascii=False))
