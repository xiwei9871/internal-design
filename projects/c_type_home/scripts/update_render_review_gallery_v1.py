"""Continuous review artifacts with honest generation/QA counts, no style winner."""
import json,time,html,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];PARENT=ROOT/'renders/whole_house_final_study_v1';OUT=PARENT/'production_batch_v1';M=OUT/'00_MANIFEST';rooms=json.loads((PARENT/'00_MANIFEST/WHOLE_HOUSE_ROOM_MANIFEST_V1.json').read_text())['rooms'];levels=['01_faithful','02_designer','03_creative'];watch='--watch' in sys.argv
while True:
 notes=json.loads((M/'ROOM_VISUAL_NOTES.json').read_text()) if (M/'ROOM_VISUAL_NOTES.json').exists() else {}
 flags=json.loads((M/'VISUAL_REVIEW_FLAGS.json').read_text()) if (M/'VISUAL_REVIEW_FLAGS.json').exists() else []
 flag_index={(q['room_id'],q['view_id'],q['level']):q for q in flags}
 blocked=(M/'IMAGE2_PROVIDER_BLOCKER.json').exists()
 records=[];body='';counts={l:0 for l in levels};missing=[]
 for r in rooms:
  rid=r['room_id'];d=OUT/rid/'04_review';d.mkdir(exist_ok=True,parents=True);sheet=Image.new('RGB',(1700,640),'#f5f2e9');dr=ImageDraw.Draw(sheet);dr.text((8,5),rid+' | columns VIEW01–05 | rows FAITHFUL / DESIGNER / CREATIVE',fill='#333333');items=''
  for row,level in enumerate(levels):
   for i in range(1,6):
    vid=f'VIEW_{i:02d}';p=OUT/rid/level/(vid+'.png');x=(i-1)*340;y=28+row*202;exists=p.exists();status='MISSING'
    if exists:
     try:
      img=Image.open(p).convert('RGB');dimensions=list(img.size);img.thumbnail((334,188));sheet.paste(img,(x,y));counts[level]+=1;status='BLENDER_GEOMETRY_AUTHORITATIVE' if level=='01_faithful' else 'GENERATED_PENDING_VISUAL_QA';status=flag_index.get((rid,vid,level),{}).get('status',status);records.append({'room_id':rid,'view_id':vid,'level':level,'path':str(p),'dimensions':dimensions,'status':status})
     except Exception:exists=False
    if not exists:
     status='QUEUED_NOT_GENERATED';meta=p.with_suffix('.image2.json')
     if meta.exists():
      try:status=json.loads(meta.read_text()).get('status',status)
      except Exception:pass
     dr.rectangle((x,y,x+334,y+188),fill='#e6e2d8');dr.text((x+10,y+80),status,fill='#747166');missing.append({'room_id':rid,'view_id':vid,'level':level,'status':status})
    dr.text((x+8,y+188),level[:2]+' '+vid,fill='#333333')
    src=str(p.relative_to(PARENT));items+=f'<figure class="{level}"><figcaption>{level[3:]} · {vid}</figcaption>'+(f'<a href="/{src}" target="_blank"><img loading="lazy" src="/{src}?t={int(p.stat().st_mtime)}"></a>' if exists else f'<div class="missing">{html.escape(status)}</div>')+f'<small>{html.escape(status)}</small></figure>'
  sheet.save(d/(rid+'_3X5_COMPARISON.jpg'),quality=92)
  if rid not in notes:
   (d/'ROOM_REVIEW.md').write_text(f"# {r['display_name']}\n\nFAITHFUL is the accurate Blender base; AI visual acceptance is pending. No winner is selected.\n")
  body+=f'<section id="{rid}"><h2>{html.escape(r["display_name"])}</h2><p>{html.escape(notes.get(rid,''))}</p><div class="matrix">{items}</div></section>'
 summary={'rooms':len(rooms),'expected_images':len(rooms)*15,'actual_generated':sum(counts.values()),'counts':counts,'missing_count':len(missing),'visual_qa':'PARTIAL_REVIEW_WITH_FLAGS' if notes else 'PENDING','updated_unix':time.time()};(M/'RENDER_REGISTER.json').write_text(json.dumps({'summary':summary,'images':records,'missing':missing},ensure_ascii=False,indent=2));(M/'PROGRESS.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 notice='平台请求出现401/503，Image2已暂停；缺图按实际状态标出。已有图已保留。' if blocked else '队列正在生成。'
 nav=''.join(f'<a href="#{r["room_id"]}">{html.escape(r["display_name"])}</a>' for r in rooms)
 css='body{margin:0;font:15px system-ui;background:#f7f4ed;color:#2e332c}header,section{padding:25px 3vw}nav{position:sticky;top:0;display:flex;flex-wrap:wrap;gap:14px;background:#f7f4edfa;padding:16px 3vw;z-index:1}.matrix{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px}figure{margin:0;background:white;padding:6px;border-radius:6px}img{width:100%;display:block}small{font-size:10px;color:#888}figcaption{padding:7px 0}.missing{aspect-ratio:16/9;background:#e6e2d8;display:grid;place-content:center;color:#898579}section{scroll-margin-top:100px}a{color:#546d56}@media(max-width:850px){.matrix{grid-template-columns:repeat(2,1fr)}}'
 page=f'<!doctype html><html lang="zh"><meta charset="utf-8"><meta http-equiv="refresh" content="90"><title>全屋效果图批量评审</title><style>{css}</style><header><h1>全屋效果图批量评审</h1><p>已生成 {summary["actual_generated"]} / {summary["expected_images"]} 张。每房间五个视角 × 三种表现；点击图片看大图。</p><p>{notice}</p><p>三行依次为 FAITHFUL / DESIGNER / CREATIVE。AI 图仍待构图、门窗和家具漂移检查；不自动选定设计。</p></header><nav>{nav}</nav>{body}</html>'
 (OUT/'review_gallery.html').write_text(page)
 # One hero sheet per level; blank slots clearly remain blank.
 for level in levels:
  hero=Image.new('RGB',(1600,1060),'#f5f2e9');dr=ImageDraw.Draw(hero);dr.text((12,8),level.upper()+' WHOLE-HOUSE HEROES',fill='#333333')
  for i,r in enumerate(rooms):
   p=OUT/r['room_id']/level/'VIEW_01.png';x=(i%4)*400;y=35+(i//4)*255
   if p.exists():
    try:im=Image.open(p).convert('RGB');im.thumbnail((394,222));hero.paste(im,(x,y))
    except Exception:pass
   else:dr.rectangle((x,y,x+394,y+222),fill='#e6e2d8')
   dr.text((x+10,y+224),r['room_id'],fill='#333333')
  hero.save(OUT/('WHOLE_HOUSE_'+level[3:].upper()+'_HEROES.jpg'),quality=90)
 print('GALLERY_UPDATED',summary['actual_generated'],'/',summary['expected_images'],flush=True)
 if not watch or ((M/'IMAGE2_QUEUE_COMPLETE.json').exists() and (M/'BLENDER_QUEUE_COMPLETE.json').exists()):break
 time.sleep(60)
