"""Review gallery with actual counts and explicit generation/visual states."""
import html, json, time
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'renders/whole_house_final_study_v1';OUT=PARENT/'photo_study_v2';M=OUT/'00_MANIFEST'
LEVELS=['A_faithful','B_designer','C_creative']
ROOMS=[r for r in json.loads((PARENT/'00_MANIFEST/WHOLE_HOUSE_ROOM_MANIFEST_V1.json').read_text())['rooms'] if r['room_id']!='kitchen']
def update():
    counts={l:0 for l in LEVELS};missing=[];records=[];body=''
    for room in ROOMS:
        rid=room['room_id'];directory=OUT/rid/'review';directory.mkdir(exist_ok=True,parents=True)
        canvas=Image.new('RGB',(1700,640),'#f5f2e9');draw=ImageDraw.Draw(canvas);draw.text((10,5),rid+' | A natural faithful / B designer / C creative',fill='#333333');figures=''
        for row,level in enumerate(LEVELS):
            for n in range(1,6):
                vid=f'VIEW_{n:02d}';p=OUT/rid/level/(vid+'.png');meta=p.with_suffix('.json');value=json.loads(meta.read_text()) if meta.exists() else {};status=value.get('visual_status',value.get('status','NOT_GENERATED'));exists=p.exists();x=(n-1)*340;y=28+row*202
                if exists:
                    try:
                        im=Image.open(p).convert('RGB');dims=list(im.size);im.thumbnail((334,188));canvas.paste(im,(x,y));counts[level]+=1;records.append({'room_id':rid,'view_id':vid,'level':level,'path':str(p),'native_size':dims,'status':status})
                    except Exception:exists=False;status='INVALID_IMAGE'
                if not exists:
                    draw.rectangle((x,y,x+334,y+188),fill='#e6e2d8');draw.text((x+8,y+75),status,fill='#777369');missing.append({'room_id':rid,'view_id':vid,'level':level,'status':status})
                draw.text((x+8,y+188),level+' '+vid,fill='#333333')
                rel=p.relative_to(PARENT);content=f'<a href="/{rel}" target="_blank"><img loading="lazy" src="/{rel}?t={int(p.stat().st_mtime)}"></a>' if exists else f'<div class="missing">{html.escape(status)}</div>'
                figures+=f'<figure><figcaption>{level} · {vid}</figcaption>{content}<small>{html.escape(status)}</small></figure>'
        canvas.save(directory/'ROOM_3X5.jpg',quality=95)
        heroqa=OUT/rid/'HERO_QA.json';notes=json.loads(heroqa.read_text()).get('notes',[]) if heroqa.exists() else ['主视角生成后需逐张视觉检查，才会进入另外四个机位。']
        body+=f'<section id="{rid}"><h2>{html.escape(room["display_name"])}</h2><p>{html.escape(" · ".join(notes))}</p><div class="matrix">{figures}</div></section>'
    summary={'expected_images':210,'generated':sum(counts.values()),'counts':counts,'missing_count':len(missing),'room_count':14,'status':'GENERATING_OR_REVIEW_PENDING','updated_unix':time.time()}
    (M/'PROGRESS.json').write_text(json.dumps(summary,indent=2));(M/'RENDER_REGISTER.json').write_text(json.dumps({'summary':summary,'images':records,'missing':missing},ensure_ascii=False,indent=2))
    nav=''.join(f'<a href="#{r["room_id"]}">{html.escape(r["display_name"])}</a>' for r in ROOMS)
    css='body{margin:0;font:15px system-ui;background:#f7f4ed;color:#2e332c}header,section{padding:25px 3vw}nav{position:sticky;top:0;display:flex;flex-wrap:wrap;gap:14px;background:#f7f4edfa;padding:16px 3vw;z-index:1}.matrix{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px}figure{margin:0;background:white;padding:6px;border-radius:6px}img{width:100%;display:block}small{font-size:10px;color:#888}figcaption{padding:7px 0}.missing{aspect-ratio:16/9;background:#e6e2d8;display:grid;place-content:center;color:#898579}section{scroll-margin-top:100px}a{color:#546d56}@media(max-width:850px){.matrix{grid-template-columns:repeat(2,1fr)}}'
    page=f'<!doctype html><html lang="zh"><meta charset="utf-8"><meta http-equiv="refresh" content="90"><title>全屋照片质感研究 V2</title><style>{css}</style><header><h1>全屋照片质感研究 V2</h1><p>其他14空间，5机位×3方向。已生成 {summary["generated"]}/210；厨房已认可样张单独保留。</p><p>使用最新已确认机位、真实家具参考、高质量Image2。A忠实浅木、B木石设计、C灰绿/藤编/柔和造型；只改变允许的表现层。每房三张主视角先核查，再传播到其他视角。数值尺度以Blender为准，不自动选方案。</p><p><a href="/kitchen_appliance_review_v3/review_gallery.html">厨房已认可设备修正版</a></p></header><nav>{nav}</nav>{body}</html>'
    (OUT/'review_gallery.html').write_text(page);return summary
if __name__=='__main__':print(json.dumps(update()))
