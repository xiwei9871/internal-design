"""Small JPEG gallery: selected reference, V4 and V5 with honest defect ledger."""
import hashlib,html,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'design/lookdev_v5';RENDER=ROOT/'renders/whole_house_final_study_v1';OUT=RENDER/'lookdev_v5';OUT.mkdir(exist_ok=True)
m=json.loads((SRC/'review_renders/render-manifest.json').read_text());assert len(m['images'])==5
records=[]
def jpeg(source,name):
    with Image.open(source) as im:
        original=list(im.size);im=im.convert('RGB');im.thumbnail((1600,1600));p=OUT/(name+'.jpg');im.save(p,quality=92)
    records.append({'source':str(source),'sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),'original_size':original,'file':p.name,'bytes':p.stat().st_size})
for image in m['images']:jpeg(image['path'],image['camera'])
for p,name in [(RENDER/'whole_house_modes_v3/living/A_faithful/VIEW_01.png','ref-living'),(RENDER/'whole_house_modes_v3/dining/C_creative/VIEW_01.png','ref-dining'),(ROOT/'design/product_rebuild_v4/review_renders/V4_CAM_SOFA_COMPLETE.png','v4-sofa'),(ROOT/'design/product_rebuild_v4/review_renders/V4_CAM_DINING_DETAIL.png','v4-dining'),(ROOT/'design/product_rebuild_v4/review_renders/CAM_living_VIEW_01.png','v4-living')]:jpeg(p,name)
def card(name,label):return f'<article><h3>{html.escape(label)}</h3><a href="{name}.jpg" target="_blank"><img alt="{html.escape(label)}" src="{name}.jpg" loading="lazy"></a></article>'
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>C-Type 木色与布艺 · V5 对照测试</title><style>body{margin:0;background:#f4f0e8;color:#282823;font-family:system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:28px}h2{font-size:23px;margin-top:34px}h3{font-size:16px}p,li{line-height:1.8}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.pair{grid-template-columns:repeat(2,minmax(0,1fr))}article{padding:14px;background:white;border-radius:10px}img{width:100%;height:auto;display:block}aside{padding:18px;background:#e8dfcf;border-radius:10px}a{color:#635133}nav{display:flex;gap:22px;flex-wrap:wrap;margin:20px 0}@media(max-width:850px){.grid,.pair{grid-template-columns:1fr}main{padding:16px}}</style><main>
<h1>木色与布艺 · V5 对照测试</h1><p>2026-10-10 · 目标是参考图中的自然浅木色、木纹层次和松软米白布艺。</p>
<aside>上一版木材偏白、纹理过细。此版将客餐厅家具木材校准为更温暖的自然木色，使用白蜡木纹理候选，并重新处理布套松量与缝边。
相机、房间灯光和曝光都与 V4 相同，方便比较材质本身的变化。原版本保留，本版仍待人工外观评审。</aside>
<nav><a href="#wood">餐厅木色</a><a href="#soft">沙发软包</a><a href="#living">客厅整体</a><a href="#limits">剩余差距</a></nav>
<h2 id="wood">餐桌与餐椅 · 木色对照</h2><div class="grid">'''+card('ref-dining','已选效果图 · 自然浅木色')+card('v4-dining','V4 · 偏白、细密直纹')+card('V4_CAM_DINING_DETAIL','V5 · 木色与纹理校准')+'''</div><div class="grid pair" style="margin-top:16px">'''+card('V4_CAM_DINING_COMPLETE','V5 · 餐厅整体')+card('V5_MATERIAL_CONTROL','同一中性灯光 · 左 V4，右 V5')+'''</div>
<p>新纹理来源为 TextureCan 的公开白蜡木程序材质，授权 CC0。已在本项目 Blender 渲染中测试；它不是厂家实际木料的数字扫描。
去除用于地板的缝隙后，按家具板件排布木纹，并将深色底材校准到浅木色。第一轮纹理过重的候选已保留为失败对照，没有作为成品采用。</p>
<h2 id="soft">沙发 · 布套与缝边对照</h2><div class="grid pair">'''+card('v4-sofa','V4 · 薄平、规则的软包')+card('V4_CAM_SOFA_COMPLETE','V5 · 布套松量、边缘厚度与布艺')+'''</div>
<p>布艺继续使用完整亚麻材质。软包测试了有支撑的布套松量、内部填充约束和真实变形；5% 松量导致过多褶皱，最终收为 2%。
细分一度将缝扩大到 16–19 mm，已修正并验证恢复约 7.5 / 10 mm；底部与木承托接触。
这些是静态建模测试，不是实际填充物的力学认证。</p>
<h2 id="living">客厅整体 · 木色和布艺关系</h2><div class="grid">'''+card('ref-living','已选 A · 家具与布艺参考')+card('v4-living','V4 · 上一版')+card('CAM_living_VIEW_01','V5 · 当前测试版')+'''</div>
<h2 id="limits">仍需解决的差距</h2><p>木色已有明确变化，纹理仍是候选，需与实物木材及木蜡油样板核对。木作端面与实物接合尚未逐件认证。
软包表面与缝边有变化，但靠垫的丰满程度、轮廓和细小受压褶皱仍未达到参考图，不能称沙发外观已完全解决。
当前原型不纳入已批准的家具库，不自动传播到其他房间。</p>
<p>建筑、家具布局和原定最大尺寸保持；餐椅仍为前轮 560 mm 实物尺寸试点和外拉 180 mm 的候选摆位。
窗外仍为示意环境。本轮只调整客餐厅家具及软包，柜体、地板和其他房间未统一替换，避免把未认可材质扩散。</p>
<p>2162 个未改网格 / 世界矩阵保持，八项保护哈希通过，26 张贴图打包，无缺图。
四张房间正式图与一张中性材质对照：Cycles / Metal / 96 samples / OIDN GPU High Accurate。原 PNG 保留；网页使用缩略 JPEG。未调用 Image2，未开启全屋队列。</p>
<p>评审重点：木色是否更接近目标，木纹是否自然，软包是否有实质改善。软包若仍差距明显，下一步应以同款整件高精度资产或实物多角度资料建立家具本体，停止靠增加褶皱反复微调。</p></main></html>'''
(OUT/'review_gallery.html').write_text(page)
(OUT/'WEB_ARTIFACTS.json').write_text(json.dumps({'status':'HUMAN_REVIEW','records':records},indent=2)+'\n')
sheet=Image.new('RGB',(1500,840),'#f3eee5');draw=ImageDraw.Draw(sheet)
for i,name in enumerate(['ref-dining','v4-dining','V4_CAM_DINING_DETAIL','v4-sofa','V4_CAM_SOFA_COMPLETE','CAM_living_VIEW_01']):
    im=Image.open(OUT/(name+'.jpg'));im.thumbnail((490,375));x=i%3*500+(500-im.width)//2;y=i//3*420+30;sheet.paste(im,(x,y));draw.text((i%3*500+8,i//3*420+8),name,fill='#222222')
sheet.save(SRC/'V5_REVIEW_CONTACT.jpg',quality=84)
print(OUT/'review_gallery.html')
