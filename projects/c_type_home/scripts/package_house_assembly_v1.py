"""Package actual Blender images and room decisions, retaining prior artifacts."""
import json,html,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'design/whole_house_model_v1/assembly'
CONFIG=ROOT/'render_config/whole_house_model_v1'
OUT=ROOT/'renders/whole_house_final_study_v1/whole_house_model_v1'
OUT.mkdir(exist_ok=True);MEDIA=OUT/'actual_assembly';MEDIA.mkdir(exist_ok=True)
a=json.loads((RUN/'BUILD_AUDIT.json').read_text());v=json.loads((RUN/'VERIFICATION_FINAL.json').read_text())
manifest=json.loads((RUN/'review/render-manifest.json').read_text())
if (RUN/'support_review/render-manifest.json').exists():
 repaired=json.loads((RUN/'support_review/render-manifest.json').read_text())
 changes={i['path'].split('/')[-1]:i for i in repaired['images']}
 manifest['images']=[changes.get(Path(i['path']).name,i) for i in manifest['images']]
 manifest['support_repair']=repaired['source_sha256']
decisions=json.loads((CONFIG/'ROOM_DECISIONS.json').read_text())['rooms']
refs=json.loads((ROOT/'design/whole_house_model_v1/SELECTED_REFERENCES.json').read_text())
reference={r['room']:Path(r['path']) for r in refs}
old=ROOT/'renders/whole_house_final_study_v1/whole_house_modes_v3'
reference['living']=old/'living/A_faithful/VIEW_01.png';reference['dining']=old/'dining/C_creative/VIEW_01.png'
reference['kitchen']=ROOT/'design/whole_house_model_v1/references/kitchen_correct.png'
reference['mother_bedroom']=old/'mother_bedroom/C_creative/VIEW_05.png'
reference['study']=ROOT/'design/whole_house_model_v1/references/study_daybed.png'
def thumb(src,name):
 dest=MEDIA/name
 if not dest.exists():
  im=Image.open(src).convert('RGB');im.thumbnail((1280,900));im.save(dest,quality=85)
 return 'actual_assembly/'+name
cards=[];nav=[];images=[]
for i,r in enumerate(manifest['images']):
 rid=r['room_id'];name=r['display_name'];imagepath=thumb(Path(r['path']),Path(r['path']).stem+'.jpg');ref=reference.get(rid)
 refpath=thumb(ref,'ref_'+rid+'.jpg') if ref and ref.exists() else None
 if r['view']=='bed_supplement':refpath=thumb(old/'mother_bedroom/C_creative/VIEW_01_repair1.png','ref_mother_bed.jpg')
 eid=rid+'_'+str(i);nav.append(f'<a href="#{eid}">{html.escape(name)}</a>')
 mode=decisions[rid]['mode'];text=decisions[rid]['implementation_cn']
 visual=decisions[rid].get('review_flag_cn','候选外观等待逐房验收。')
 original_url='../'+str(Path(r['path']).relative_to(ROOT/'renders/whole_house_final_study_v1')) if Path(r['path']).is_relative_to(ROOT/'renders/whole_house_final_study_v1') else None
 pair=f'<figure><figcaption>选定外观参考（不用于测尺寸）</figcaption><img loading="lazy" src="{refpath}" alt="{name}参考"></figure>' if refpath else ''
 cards.append(f'<section id="{eid}"><h2>{html.escape(name)} <small>{html.escape(mode)}</small></h2><p>{html.escape(text)}</p><div class="pair"><figure><figcaption>实际 Blender · {html.escape(r["view"])} · 1280×720</figcaption><img loading="lazy" src="{imagepath}" alt="{name}实际模型"></figure>{pair}</div><p class="flag">{html.escape(visual)}</p></section>')
 images.append({**r,'web_preview':imagepath,'source_sha256':r.get('source_sha256',manifest.get('source_sha256')),'reference':str(ref) if ref else None})
sheet=Image.new('RGB',(1500,1580),'#1e252b');draw=ImageDraw.Draw(sheet)
for i,r in enumerate(manifest['images']):
 im=Image.open(r['path']).convert('RGB');im.thumbnail((490,276));x=(i%3)*500;y=(i//3)*263;im.thumbnail((490,232));sheet.paste(im,(x,y+25));draw.text((x+6,y+6),r['room_id']+' / '+r['view'],fill='white')
sheet.save(RUN/'REVIEW_CONTACT.jpg',quality=84)
sha=a['output_sha256'];model=Path(a['output']);assert hashlib.sha256(model.read_bytes()).hexdigest()==sha
doc=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type 全屋实际模型 V1</title>
<style>body{{margin:0;background:#f4f1ea;color:#292722;font:16px/1.7 system-ui,sans-serif}}main{{max-width:1480px;margin:auto;padding:24px}}nav{{display:flex;flex-wrap:wrap;gap:12px;background:#e4ddcf;padding:18px;border-radius:10px}}a{{color:#5c4934}}section{{padding:24px 0;border-bottom:1px solid #d7cebd}}h1{{font-size:30px}}h2{{font-size:24px}}small{{font-size:14px;font-weight:normal}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}figure{{margin:0}}img{{width:100%;display:block;border-radius:8px;cursor:zoom-in}}figcaption{{padding:8px 0;color:#5d574f}}.flag{{color:#73542e}}.note{{background:#fff9ed;padding:18px;border-left:4px solid #b68e5e}}code{{overflow-wrap:anywhere}}@media(max-width:800px){{.pair{{grid-template-columns:1fr}}}}</style>
<main><h1>C-Type 全屋实际 Blender 模型 · V1</h1><p>浅原木 / 米白 / 简洁。15 个空间、{len(images)} 张检查图。状态：HUMAN_REVIEW，模型候选已制作，外观未逐房验收。</p>
<p class="note">参考图只控制颜色、材质和造型；墙、门窗、标高、台阶和设备位置来自原模型。所有照片为实际 Blender Cycles 32 samples 的1280×720预览，未调用 Image2。窗外山景是照明环境示意，不代表现场。页面旧版已留档。</p>
<p>模型：<code>{html.escape(str(model))}</code><br>SHA256：<code>{sha}</code></p>
<p>核验：{v['protected_files']}源文件哈希保持，{v['original_geometry_unchanged']}原有网格保持，{v['registered_camera_count']}登记相机保持；阅读柜/矮柜及已查沙发坐靠包未检出穿插。新增家具为有参考的定制候选，承重、舒适度、人体动态安全与采购SKU仍需确认。</p>
<nav>{''.join(nav)}</nav>{''.join(cards)}<p>旧全屋三模式效果图：<a href="../whole_house_modes_v3/review_gallery.html">打开原图库</a>。技术证据：<a href="actual_assembly/verification.json">模型核验</a> / <a href="actual_assembly/delivery.json">预览与来源清单</a>。</p></main><script>document.querySelectorAll('img').forEach(i=>i.onclick=()=>window.open(i.src,'_blank'));</script></html>'''
page=OUT/'review_gallery.html'
if page.exists():
 snapshot=OUT/'review_gallery_contract_only_snapshot.html'
 if not snapshot.exists():shutil.copy2(page,snapshot)
page.write_text(doc)
(MEDIA/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
(MEDIA/'delivery.json').write_text(json.dumps({'model':str(model),'sha256':sha,'status':'HUMAN_REVIEW','images':images,'image2_requests':0},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'gallery':str(page),'images':len(images),'candidate':str(model),'sha256':sha},ensure_ascii=False))
