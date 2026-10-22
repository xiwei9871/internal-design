import json,hashlib,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent;OLD=OUT.parent/'living_light_seating_v3';read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=read(OUT/'reports/IMAGES.json');g=read(OUT/'reports/GEOMETRY_LOCK.json');qa=read(OUT/'reports/VISUAL_REVIEW.json');cad=read(OUT/'reports/FREECAD_HASHES.json')
assert len(rows)==3 and all(r['status']=='GENERATED' for r in rows) and len(qa)==3
for r in rows:
 r.update(qa[r['camera']]);r['image_sha256']=sha(r['output']);r['prompt_sha256']=sha(r['prompt']);r['source_sha256']=g['source_sha256'];r['size']=list(Image.open(r['output']).size);assert r['size']==[1536,1024];Image.open(r['output']).verify();assert r['reference_sha256']==sha(r['reference']);assert r['visual_review']=='COMPLETE'
 for p,h in zip(r['inputs'],r['input_sha256']):assert sha(p)==h
 if r['mask']:assert Image.open(r['mask']).size==(1536,1024)
assert sha(g['source'])==g['source_sha256']
for p,h in cad.items():assert sha(p)==h
(OUT/'reports/IMAGES.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
font=lambda n:ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',n)
board=Image.new('RGB',(1800,1050),'#f5f3ee');dr=ImageDraw.Draw(board);dr.text((24,18),'客厅两版对比｜左：无柜＋单椅　右：有轻边柜＋单椅',font=font(32),fill='#30493e')
for j,cid in enumerate(['HERO','SPACE']):
 new=next(r for r in rows if r['camera']==cid)
 for k,p in enumerate([OLD/'images'/('LIVING_LIGHT_'+cid+'.png'),Path(new['output'])]):
  x=k*900+20;y=78+j*480;dr.text((x,y),('无柜' if k==0 else '有柜')+' · '+cid,font=font(26),fill='#30493e');im=Image.open(p);im.thumbnail((860,405));board.paste(im,(x,y+43))
board.save(OUT/'comparison/WITH_WITHOUT_SIDEBOARD_COMPARISON.png')
# Cabinet outline/callout from the visible projected cabinet footprint, saved separately from the clean image.
cams=read(OUT/'reports/CAMERA_REGISTER.json');hero=next(r for r in rows if r['camera']=='HERO');cam=next(c for c in cams if c['id']=='HERO');marked=Image.open(hero['output']).convert('RGB');md=ImageDraw.Draw(marked);box=cam['cabinet_projected_bbox_px'];md.rectangle([box[0]-8,box[1]-8,box[2]+4,box[3]+8],outline='#b58227',width=4);md.rounded_rectangle([890,390,1515,470],radius=10,fill='#fff9ed',outline='#b58227',width=2);md.text((907,403),'新增轻边柜｜1400×320×650 mm',font=font(29),fill='#7d5923');md.text((907,438),'按图3高亮带定位，柜脚落客厅下层平地',font=font(24),fill='#7d5923');md.line([(1260,470),(1320,box[1]-8)],fill='#b58227',width=4);marked.save(OUT/'comparison/WITH_SIDEBOARD_HERO_MARKED.png')
plain=Image.new('RGB',(1800,485),'#f5f3ee');pd=ImageDraw.Draw(plain)
for i,cid in enumerate(['HERO','SPACE','DETAIL']):
 r=next(r for r in rows if r['camera']==cid);pd.text((i*600+15,15),['有柜主视角','有柜整体视角','柜体细节'][i],font=font(25),fill='#30493e');im=Image.open(r['output']);im.thumbnail((570,380));plain.paste(im,(i*600+15,65))
plain.save(OUT/'comparison/WITH_SIDEBOARD_CONTACT_SHEET.png')
manifest=dict(status='HUMAN_REVIEW',source=g['source'],source_sha256=g['source_sha256'],source_unchanged=True,freecad_unchanged=True,no_model_writeback=True,new_images=3,schemes=dict(A='previous V3 no cabinet + chair/round table; preserved',B='new V4 cabinet + same chair/round table'),cabinet=g['sideboard'],geometry_lock=g,freecad_hashes=cad,baseline_no_cabinet_images=[str(OLD/'images'/('LIVING_LIGHT_'+c+'.png')) for c in ['HERO','SPACE']],baseline_sha256=[sha(OLD/'images'/('LIVING_LIGHT_'+c+'.png')) for c in ['HERO','SPACE']],image_api=dict(model='gpt-image-2',quality='high',size='1536x1024'),selected_scheme=None,images=rows)
(OUT/'LIVING_SIDEBOARD_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
text=['# 客厅有／无边柜对比','', '上一轮只出了无柜版，本轮补齐有柜版。两版的主沙发、窗边贵妃、单椅、圆边几、茶几、建筑和主要机位保持同一逻辑，不自动选择。','', '- 新柜按图3蓝色高亮带定位：主沙发南侧后方的客厅下层平地，中心X4450/Y7810mm；不是放在错层平台上。','- 候选尺寸1400×320×650mm，细腿200mm，浅白蜡木，两扇轻薄柜门；不照搬2200×400×700的大深柜。','- 图3高亮只用作位置带，按R4登记的2300×900沙发做局部像素标定；未从旧示意图重建墙体、斜门或平台。数字是候选参考，需正式阶段复尺。','- 无柜版：更开放，椅旁活动弹性更大。','- 有柜版：增加少量客厅收纳与台面，体量更大一些；浅进深和细腿减轻视觉负担，原东侧通道保持。','', '| 图像 | 观察 |','|---|---|']
for r in rows:text.append('| ['+r['camera']+']('+r['output']+') | '+r['notes']+' |')
text+=['','- [同机位两版对比]('+str(OUT/'comparison/WITH_WITHOUT_SIDEBOARD_COMPARISON.png')+')','- [有柜主视角位置标注]('+str(OUT/'comparison/WITH_SIDEBOARD_HERO_MARKED.png')+')','- [图3位置带与新柜占地]('+str(OUT/'reports/SIDEBOARD_LOCATION_PLAN.png')+')','','有柜图允许单椅/前景沙发自然遮住部分柜体，细节视角用于看清浅进深、柜门、细腿和落地位置。R4与8份记录的FreeCAD文件未改，未保存新.blend或.FCStd；等待人工比较。']
(OUT/'LIVING_SIDEBOARD_REVIEW.md').write_text('\n'.join(text)+'\n')
pack=['# 有柜版有效提示词','']
for r in rows:pack+=['## '+r['camera'],'','```text',Path(r['prompt']).read_text().strip(),'```','']
(OUT/'LIVING_SIDEBOARD_PROMPT_PACK.md').write_text('\n'.join(pack)+'\n')
checks=[]
for r in rows:
 for key in ['output','reference','prompt']:checks.append(Path(r[key]).exists())
for p in [OUT/'comparison/WITH_WITHOUT_SIDEBOARD_COMPARISON.png',OUT/'comparison/WITH_SIDEBOARD_HERO_MARKED.png',OUT/'comparison/WITH_SIDEBOARD_CONTACT_SHEET.png']:
 im=Image.open(p);im.load();checks.append(im.width<=1800 and im.height<=1100);im.close()
for p in re.findall(r'\]\(([^)]+)\)',(OUT/'LIVING_SIDEBOARD_REVIEW.md').read_text()):checks.append(Path(p).exists())
checks += [sha(g['source'])==g['source_sha256'],all(sha(p)==h for p,h in cad.items()),all(abs(h['z'])<.002 for h in g['floor_hits'][-5:]),not list(OUT.rglob('*.blend')),not list(OUT.rglob('*.FCStd'))]
assert all(checks)
report=dict(status='PASS',checks=len(checks),with_cabinet_images=3,comparison_schemes=2,cabinet_at_user_highlight=True,cabinet_on_lower_floor=True,source_unchanged=True,freecad_unchanged=True,no_model_writeback=True,delivery_status='HUMAN_REVIEW');(OUT/'reports/DELIVERY_INTEGRITY.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
