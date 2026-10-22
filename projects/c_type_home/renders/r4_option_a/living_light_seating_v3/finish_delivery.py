import json,hashlib,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent;read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=read(OUT/'reports/IMAGES.json');g=read(OUT/'reports/GEOMETRY_LOCK.json');cams=read(OUT/'reports/CAMERA_REGISTER.json');cad=read(OUT/'reports/FREECAD_READONLY_HASHES.json');qa=read(OUT/'reports/VISUAL_REVIEW.json')
assert len(rows)==3 and all(r['status']=='GENERATED' for r in rows);assert len(qa)==3
for row in rows:
 row.update(qa[row['camera']]);row['source_sha256']=g['source_sha256'];row['prompt_sha256']=sha(row['prompt']);row['image_sha256']=sha(row['output']);row['actual_size']=list(Image.open(row['output']).size)
 assert row['reference_sha256']==sha(row['reference']);assert row['visual_review']=='COMPLETE';Image.open(row['output']).verify();assert row['actual_size']==[1536,1024]
 if row.get('style_anchor'):assert sha(row['style_anchor'])==row['style_anchor_sha256']
assert sha(g['source'])==g['source_sha256']
for p,h in cad.items():assert sha(p)==h
manifest=dict(status='HUMAN_REVIEW',scope='One light-chair plus round-side-table direction, 3 views only',model='gpt-image-2',quality='high',size='1536x1024',geometry_lock=g,freecad_unchanged=True,freecad_hashes=cad,new_side_cabinet=None,no_model_writeback=True,excluded_wrong_elements=['previous AI heavy cabinet on raised split-level platform','2200x400x700 deep bulky sideboard','square drawer bedside-style side table'],images=rows)
(OUT/'LIVING_LIGHT_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(OUT/'reports/IMAGES.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
md=['# 客厅轻单椅＋小边几｜审阅','', '- 取消错误方案中的错层平台重柜、2200×400×700mm深边柜与封闭抽屉角几。本版不新增侧柜；R4原有低媒体柜仍在原平地位置。','- 新单椅：800×780×820mm，白蜡木开放框架、米白布艺，位于台阶西北侧客厅平地；候选中心X5150/Y8950mm，略朝会客中心旋转10°。','- 小边几：直径420、高510mm，开放三腿，放单椅东侧；候选中心X5950/Y8850mm。','- 主沙发原位；1700×900mm贵妃椅保持北窗前；平台上无新家具，东侧主要通行带参考净宽约1118mm。上述数字来自临时参考，不是AI像素测量或施工实测。','- 比大深柜更合适：开放框架和细腿更轻，可移动单椅保留会客弹性，墙面继续兼容艺术、壁画电视或投影。','', '| 图像 | 检查 |','|---|---|']
for cid in ['HERO','SPACE','WINDOW_LINK']:
 r=next(r for r in rows if r['camera']==cid);md.append('| ['+cid+']('+r['output']+') | '+r['notes']+' |')
md+=['','R4源文件和8份记录的FreeCAD文件哈希均未变。未保存新.blend或.FCStd；仅输出本轮AI候选，等待人工审核。']
(OUT/'LIVING_LIGHT_REVIEW.md').write_text('\n'.join(md)+'\n')
pack=['# 本轮有效提示词','']
for r in rows:pack+=['## '+r['camera'],'','reference: '+r['reference'],'style_anchor: '+str(r.get('style_anchor')),'','```text',Path(r['prompt']).read_text().strip(),'```','']
(OUT/'LIVING_LIGHT_PROMPT_PACK.md').write_text('\n'.join(pack))
# Optional compact filesystem sheet, never inline in chat.
b=Image.new('RGB',(1800,485),'#f5f3ee');d=ImageDraw.Draw(b);f=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',24)
for i,cid in enumerate(['HERO','SPACE','WINDOW_LINK']):
 r=next(r for r in rows if r['camera']==cid);d.text((i*600+15,15),['主视角','整体空间','窗边与单椅关系'][i],font=f,fill='#30493e');im=Image.open(r['output']);im.thumbnail((570,380));b.paste(im,(i*600+15,65))
b.save(OUT/'LIVING_LIGHT_CONTACT_SHEET.png')
checks=[]
for r in rows:
 for k in ['output','reference','prompt']:checks.append(Path(r[k]).exists())
for target in re.findall(r'\]\(([^)]+)\)',(OUT/'LIVING_LIGHT_REVIEW.md').read_text()):checks.append(Path(target).exists())
checks += [sha(g['source'])==g['source_sha256'],all(sha(p)==h for p,h in cad.items()),not list(OUT.rglob('*.blend')),not list(OUT.rglob('*.FCStd'))]
assert all(checks)
report=dict(status='PASS',formal_images=3,source_unchanged=True,freecad_files_unchanged=8,no_model_writeback=True,no_new_platform_furniture=True,new_side_cabinet=False,checks=len(checks),visual_review='COMPLETE',delivery_status='HUMAN_REVIEW')
(OUT/'reports/DELIVERY_INTEGRITY.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
