import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/r3_option_a/living_batch_v2_door'
jobs=json.loads((OUT/'working/prompts/DOOR_CORRECTION_JOBS.json').read_text());results=json.loads((OUT/'logs/DOOR_CORRECTION_GENERATION_RESULTS.json').read_text())
P=OUT/'working/previews/ai';P.mkdir(exist_ok=True)
ft=lambda n:ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',n)
sheet=Image.new('RGB',(1800,1510),'#f6f4ef');d=ImageDraw.Draw(sheet);d.text((25,20),'直门与地坪修正后的AI候选｜A2 / A4 / D1',font=ft(32),fill='#344e41')
for ci,cam in enumerate(['A2','A4','D1']):
 row=Image.new('RGB',(1800,470),'#f6f4ef');draw=ImageDraw.Draw(row)
 for vi,mode in enumerate(['strict','design','explore']):
  j=next(j for j in jobs if j['camera']==cam and j['version']==mode);im=Image.open(j['output']);im.load();assert im.size==(1536,1024)
  im.thumbnail((570,380));row.paste(im,(15+vi*600,70));draw.text((15+vi*600,22),cam+'｜'+mode,font=ft(26),fill='#344e41');im.save(P/(j['id']+'_proxy.png'))
 row.save(OUT/'exports/contact_sheets'/(cam+'_CORRECTED_VERSIONS.png'));sm=row.copy();sm.thumbnail((1200,313));sm.save(P/(cam+'_CORRECTED_VERSIONS_PROXY.png'));sheet.paste(row,(0,85+ci*470))
sheet.save(OUT/'exports/contact_sheets/DOOR_CORRECTED_AI_CONTACT_SHEET.png')
index=['# 直门及地面修正后 AI 索引','', '[模型和地面修正说明]('+str(ROOT/'design/bedroom_door_r4/R4_REVIEW.md')+')','', '[9张候选总览]('+str(OUT/'exports/contact_sheets/DOOR_CORRECTED_AI_CONTACT_SHEET.png')+')','','| 相机 | strict | design | explore |','|---|---|---|---|']
for cam in ['A2','A4','D1']:
 row=[cam]
 for mode in ['strict','design','explore']:
  j=next(j for j in jobs if j['camera']==cam and j['version']==mode);row.append('['+mode+']('+j['output']+')')
 index.append('| '+' | '.join(row)+' |')
index.extend(['','A2是原反向视角，A4是原公共区联动视角，D1是新增门位核对视角；几何底图来自R4，门口地坪三角补面已在模型中实际修复。AI各图的饰面与装饰仍是候选，不作为施工尺寸证明。','', '## 逐图记录',''])
for j in jobs:
 r=next(r for r in results if r['id']==j['id']);index.append('- ['+j['id']+']('+j['output']+')：'+str(r['seconds'])+'秒；[prompt]('+j['prompt_file']+')。')
(OUT/'CORRECTED_IMAGE_INDEX.md').write_text('\n'.join(index)+'\n')
print(json.dumps(dict(generated=9,contact_sheet=str(OUT/'exports/contact_sheets/DOOR_CORRECTED_AI_CONTACT_SHEET.png'),index=str(OUT/'CORRECTED_IMAGE_INDEX.md')),ensure_ascii=False))
