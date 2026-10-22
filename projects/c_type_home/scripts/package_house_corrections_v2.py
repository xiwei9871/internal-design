"""Owner-room correction review: preserve prior gallery, per-image source version."""
import json,html,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];D=R/'design/whole_house_model_v2';a=json.loads((D/'BUILD_AUDIT.json').read_text());V=json.loads((D/'VERIFICATION.json').read_text());O=R/'renders/whole_house_final_study_v1/whole_house_model_v2';O.mkdir(exist_ok=True);M=O/'media';M.mkdir(exist_ok=True)
if (O/'review_gallery.html').exists():raise SystemExit('Preserved gallery exists')
shots=[('reading','阅读架与书本'),('hallway','木门框走廊'),('vanity','母亲梳妆台'),('mother','母亲主卧床头柜2110'),('couple','夫妻次主卧床头柜2116和2016床'),('guest','客房1.2×2m床 · 门开启待决定'),('master_bath','主卫补充整体视角'),('secondary_bath','次主卫磨砂淋浴玻璃'),('north','北阳台软包及洗烘外观')]
remaining=json.loads((D/'review_remaining/manifest.json').read_text());imgs=[]
for rid,title in shots:imgs.append({'id':rid,'title':title,'path':str(D/'review'/(rid+'.png')),'source_sha256':a['pre_camera_review']['sha256']})
imgs+=remaining['images']
supported=json.loads((D/'north_supported/manifest.json').read_text());updates={r['id']:r for r in supported['images']};imgs=[updates.get(r['id'],r) for r in imgs]
assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==a['output_sha256']
def thumb(src,name):
 p=M/name
 if not p.exists():im=Image.open(src).convert('RGB');im.thumbnail((1280,900));im.save(p,quality=85)
 return 'media/'+name
notes={'reading':'保留已认可柜位和820×320mm尺寸，改善木边倒角、书皮、纸页和书脊；挂墙承重仍待施工确认。','hallway':'实木门框/套线，保留金属把手与合页。不是把所有五金改为木材。','vanity':'依据图册2206-0.8完整柜体/抽屉/腿与镜子构造，800×413×813mm主体；镜尺寸与隐藏接头由图片推定，非厂家精确资产。','mother':'按你选择2110的450×400×480mm两抽屉柜，母亲床本体保留。','couple':'2116的420×400×460mm一抽屉柜；2016-1.8整床2090×1930×980mm，床垫1800×2000。','guest':'你最新选择1200×2000标准款、床头朝东；当前候选能避开衣柜门，但房门开启仍碰床。建议向北约170mm微移并规定最南柜门北侧铰链；等人工选择，不能安装定版。','master_bath':'原洁具与木作保留，本轮补充台盆、镜柜、马桶关系；不是完整淋浴区/施工验收。','secondary_bath':'独立磨砂玻璃，传光但柔化反射；全屋窗户仍保持原透明材质。','north':'保持1800–2100开放350深、2100–2600闭合600深；完整木框软包重新制作，使用原生linen和V10静态形态；白机身黑舱门。','north_sofa':'坐芯与松填靠包分开，保留布艺织纹；这是一组1450×750定制结构候选，不是拉伸厂家整件。','living':'家具材质保持；采用灯光实验soft_fill，曝光+0.15和原AgX高对比不变。','dining':'已认可桌椅和吊灯保持，只比较照明。'}
old=R/'design/whole_house_model_v1/assembly';before={'reading':old/'review/reading_transition_VIEW_01.png','hallway':old/'review/hallway_VIEW_01.png','vanity':old/'review/mother_bedroom_VIEW_05.png','mother':old/'support_review/mother_bedroom_bed.png','couple':old/'support_review/couple_bedroom_VIEW_01.png','guest':old/'review/guest_bedroom_VIEW_01.png','master_bath':old/'review/master_bath_VIEW_01.png','secondary_bath':old/'review/secondary_bath_VIEW_01.png','north':old/'review/north_sunroom_VIEW_01.png','north_sofa':old/'review/north_sunroom_VIEW_01.png','living':old/'review/living_VIEW_01.png','dining':old/'review/dining_VIEW_01.png'}
cards=[];links=[]
for i,r in enumerate(imgs):
 rid=r['id'];path=Path(r['path']);assert path.exists();url=thumb(path,rid+'.jpg');prev=thumb(before[rid],'before_'+rid+'.jpg');r['preview']=url;links.append(f'<a href="#{rid}">{html.escape(r["title"])}</a>')
 flag='待人工外观评审。' if rid!='guest' else '功能未通过：房门碰撞，客房床位待选择，不可标为验收通过。'
 cards.append(f'<section id="{rid}"><h2>{html.escape(r["title"])}</h2><p>{html.escape(notes[rid])}</p><div class="pair"><figure><figcaption>新版实际Blender · 1280×720</figcaption><img src="{url}" loading="lazy"></figure><figure><figcaption>修改前（部分机位不同）</figcaption><img src="{prev}" loading="lazy"></figure></div><p class="flag">{flag}</p></section>')
sheet=Image.new('RGB',(1500,1150),'#242b30');draw=ImageDraw.Draw(sheet)
for i,r in enumerate(imgs):
 im=Image.open(r['path']).convert('RGB');im.thumbnail((494,250));x=i%3*500;y=i//3*286;sheet.paste(im,(x,y+30));draw.text((x+6,y+6),r['id'],fill='white')
sheet.save(D/'REVIEW_CONTACT.jpg',quality=84)
lab=thumb(D/'light_lab/CONTACT.jpg','light_lab.jpg');catalog=R/'design/whole_house_model_v1/owner_review_2026_10_12'
refs=[thumb(catalog/'BED_REFERENCES.jpg','bed_reference.jpg'),thumb(D/'references/BEDSIDE_2110.png','bedside2110.jpg'),thumb(D/'references/BEDSIDE_2116.png','bedside2116.jpg'),thumb(catalog/'VANITY_BEDSIDE_REFERENCES.jpg','vanity_reference.jpg')]
page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type 房间修正 V2</title><style>body{{margin:0;background:#f4f1e9;color:#302b25;font:16px/1.7 system-ui}}main{{max-width:1500px;margin:auto;padding:24px}}nav{{display:flex;gap:15px;flex-wrap:wrap;padding:15px;background:#e7dfcf}}a{{color:#644929}}section{{padding:22px 0;border-bottom:1px solid #d5cbb8}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}figure{{margin:0}}figcaption{{padding:7px}}img{{width:100%;border-radius:7px}}.flag,.notice{{background:#fff4df;padding:12px;color:#735126}}code{{overflow-wrap:anywhere}}@media(max-width:800px){{.pair{{grid-template-columns:1fr}}}}</style><main><h1>C-Type · 房间修正 V2</h1><p>12张实际模型评审图。依据业主反馈与图册实物；0次Image2。保持已认可主体与冻结建筑。</p><p class="notice">客房尚未完成房门/柜门组合验收：1.2×2m床头朝东，衣柜门可避开床，但房门碰床。微调床位与柜门铰链方案等待人工选择。其他房间为已制作待外观评审。</p><p>本轮模型：<code>{html.escape(a['output'])}</code><br>SHA256：<code>{a['output_sha256']}</code>。原成果未覆盖。</p><p>16受保护源哈希保持，原有网格保持，75登记相机保持；修正材质分配与实际家具，附加镜头只作评审。图册隐藏结构/镜子尺寸仍有推定，不能称厂家精确模型。窗外景为示意。预览Cyces32 samples/Metal/GPU OIDN，非最终摄影验收。</p><nav>{''.join(links)}</nav>{''.join(cards)}<section><h2>照明隔离实验</h2><p>每行：原版／仅降低对比度／增加现有灯和日光。选择右列soft_fill，保留曝光和材质颜色，不使用全屋曝光抬高；未作现场照度认证。</p><img src="{lab}"></section><section><h2>已选实物依据</h2><p>2016床系，母亲2110、夫妻2116床头柜；梳妆台2206-0.8。</p>{''.join('<img loading="lazy" src="'+u+'">' for u in refs)}</section><p><a href="../whole_house_model_v1/review_gallery.html">V1完整图库</a> · <a href="media/verification.json">实际核验和未通过项</a> · <a href="media/delivery.json">来源清单</a></p></main></html>'''
(O/'review_gallery.html').write_text(page);(M/'verification.json').write_text(json.dumps(V,ensure_ascii=False,indent=2)+'\n');(M/'delivery.json').write_text(json.dumps({'model':a['output'],'sha256':a['output_sha256'],'images':imgs,'status':'HUMAN_REVIEW_GUEST_CLEARANCE_PENDING','image2_requests':0},ensure_ascii=False,indent=2)+'\n');print('GALLERY_V2',O/'review_gallery.html',len(imgs))
