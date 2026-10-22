"""Small JPEG evidence; models, textures and original renders remain local."""
import json, hashlib, html, shutil
from pathlib import Path
from PIL import Image, ImageDraw

R=Path(__file__).resolve().parents[1]
D=R/'design/pale_ash_review_v7'
A=json.loads((D/'BUILD_AUDIT.json').read_text())
V=json.loads((D/'VERIFICATION.json').read_text())
O=R/'renders/whole_house_final_study_v1/pale_ash_review_v7'
O.mkdir(exist_ok=True)
assert hashlib.sha256(Path(A['output']).read_bytes()).hexdigest()==V['output_sha256']
if (O/'review_gallery.html').exists():
    preserved=O/'review_gallery_initial.html'
    assert not preserved.exists(), 'Already finalized gallery'
    shutil.copyfile(O/'review_gallery.html',preserved)
names=['before_bed','after_bed','before_living','after_living','after_entry','after_hallway','before_ceiling','after_ceiling','after_open','after_slider','after_console']
for n in names:
    src=D/'review_final'/(n+'.png')
    assert src.exists(), str(src)
    im=Image.open(src).convert('RGB')
    im.thumbnail((1600,1000))
    im.save(O/(n+'.jpg'), quality=88)
shutil.copyfile(D/'references/CATALOG_PAGE17.jpg', O/'catalog_page17.jpg')
shutil.copyfile(D/'VERIFICATION.json', O/'verification.json')
sheet=Image.new('RGB',(1500,920),'#eee8dc')
draw=ImageDraw.Draw(sheet)
for i,(n,label) in enumerate([('before_bed','V5 before: bedroom'),('after_bed','V7 after: pale ash bedroom'),('before_living','V5 before: living room'),('after_living','V7 after: pale ash / ivory flax')]):
    im=Image.open(O/(n+'.jpg'))
    im.thumbnail((735,405))
    x=i%2*750
    y=i//2*460
    sheet.paste(im,(x,y+28))
    draw.text((x+8,y+7),label,fill='#302b25')
sheet.save(D/'APPEARANCE_COMPARE.jpg',quality=85)
sheet=Image.new('RGB',(1500,400),'#eee8dc')
draw=ImageDraw.Draw(sheet)
for i,(n,label) in enumerate([('before_ceiling','Before ceiling patches'),('after_ceiling','After planar union / 450mm step'),('after_open','Open ceiling review mode')]):
    im=Image.open(O/(n+'.jpg'))
    im.thumbnail((495,345))
    sheet.paste(im,(i*500,28))
    draw.text((i*500+8,8),label,fill='#302b25')
sheet.save(D/'CEILING_COMPARE.jpg',quality=85)
cards=[]
for title,ns in [('次主卧：同机位木色对照',['before_bed','after_bed']),('客厅：同机位木材与布艺对照',['before_living','after_living']),('门材质：玄关与卧室走廊',['after_entry','after_hallway']),('玻璃推拉门分件与电视柜细节',['after_slider','after_console']),('天花接缝与去顶查看',['before_ceiling','after_ceiling','after_open'])]:
    cards.append('<section><h2>'+title+'</h2><div class="grid">'+''.join('<figure><figcaption>'+n+'</figcaption><img src="'+n+'.jpg"></figure>' for n in ns)+'</div></section>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type 浅白蜡木与查看模式 V7</title>
<style>body{margin:0;background:#f3efe7;color:#302b25;font:16px/1.7 system-ui}main{max-width:1600px;margin:auto;padding:24px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}img{width:100%;border-radius:7px}figure{margin:0}section{border-top:1px solid #d8cabb;padding:18px 0}.note{padding:15px;background:#fff0d3}code{overflow-wrap:anywhere}@media(max-width:780px){.grid{grid-template-columns:1fr}}</style>
<main><h1>C-Type · 浅白蜡木 / 材质 / 查看模式 V7</h1>
<p>依据你指定的V5独立派生：统一浅白蜡木、米白布艺；入户双门哑光金属，内部平开门浅木，推拉门采用10mm薄玻璃＋细金属框，保持原40mm门扇外包；这一分件为表现候选，未选定采购型号。原床/沙发/电视柜/客房布局和外尺寸保持；没有使用Image2。</p>
<p class="note">模型默认视图层 <strong>OVERVIEW_CEILING_HIDDEN</strong>，天花在视口隐藏。切换右上角视图层到 <strong>INTERIOR_CLOSED_CEILING</strong>，可恢复闭合天花看室内光效。F12只渲染闭合天花层，保留遮光。默认材质预览是工作室灯光，下方Cycles图才是实际房间光效。</p>
<p>天花不是建筑屋顶；保留原有底标高2800 / 3250mm，高差450mm。将碎板及叠片做平面并集，补不超过202mm的拼接缝和小封闭缺口，新增高低交接立面。该修补为表现候选，墙/窗/门开口和冻结源未改；新增覆盖的制造构造不作为施工图。</p>
<p>8张实际Cycles 1600×900、128 samples、Metal GPU / OIDN High Accurate对照与门区图。模型保存的后续渲染配置为2560×1440、256 samples；不是说下方图片已达到那个尺寸。最终delivery补齐玻璃把手夹持件，玻璃门/电视柜近景来自delivery；客厅、卧室、门区及全屋图来自此前同材质framed候选，摄影证据按阶段保留。3张全屋图是Workbench几何证据，不作材质渲染。</p>'''
page+=''.join(cards)
page+='''<section><h2>真实图册参照</h2><p>桌面《木甲木乙—白蜡木系列》17页：2116床头柜、梳妆台及脚凳的浅天然木色。复用项目已验证的完整白蜡木PBR与麻布材质，保留纹理/粗糙度/法线。照片不是标准色卡，颜色仍需实物小样最终确认。</p><img src="catalog_page17.jpg"></section><section><h2>模型与核验</h2><p>'''
page+=html.escape(A['output'])+'<br>SHA256 <code>'+A['sha256']+'</code></p>'
page+='''<p>3461个原对象网格和位置保持，16保护源哈希保持；旧天花仍保留为隐藏对象。床外尺寸2130×1910×1070mm，电视柜成品2000×460×400mm、床尾净距657mm保持。客房布局/门扇问题保持原状态，此轮未修改。</p><p>原混元模型的隐藏接头与烘入明暗仍有生成限制。当前为HUMAN_REVIEW，外观待你评审。<a href="verification.json">核验记录</a> · <a href="../console1310_v5/review_gallery.html">返回V5</a></p></section></main></html>'''
(O/'review_gallery.html').write_text(page)
print('V7_GALLERY',str(O/'review_gallery.html'))
