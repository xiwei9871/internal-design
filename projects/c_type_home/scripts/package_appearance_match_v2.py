"""Reference / rejected baseline / actual repaired render material comparison."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'design/appearance_match_v2';RENDERS=ROOT/'renders/whole_house_final_study_v1';OUT=RENDERS/'appearance_match_v2';OUT.mkdir(exist_ok=True)
manifest=json.loads((SRC/'review_renders/render-manifest.json').read_text())
labels={'CAM_living_VIEW_01':'V2 客厅同机位','AM2_CAM_SOFA_MATERIAL':'V2 沙发布艺与缝边近景','LD_CAM_dining_DETAIL':'V2 白蜡木餐桌近景','CAM_living_VIEW_02':'V2 客厅反向材质检查'}
for r in manifest['images']:
 im=Image.open(r['path']).convert('RGB');im.save(OUT/(r['camera']+'.jpg'),quality=94)
references=[('whole_house_modes_v3/living/A_faithful/VIEW_01.png','reference-living-A'),('whole_house_modes_v3/living/B_designer/VIEW_01.png','reference-living-B'),('whole_house_modes_v3/dining/C_creative/VIEW_01.png','reference-dining-C'),('living_dining_detail_v1/CAM_living_VIEW_01.jpg','rejected-V1'),('living_dining_detail_v1/LD_CAM_dining_DETAIL.jpg','rejected-dining-V1')]
for source,n in references:
 im=Image.open(RENDERS/source).convert('RGB');im.thumbnail((1600,1000));im.save(OUT/(n+'.jpg'),quality=90)
contact=Image.new('RGB',(1500,900),'#f7f3eb');d=ImageDraw.Draw(contact)
for i,(n,label) in enumerate([('reference-living-A','SELECTED FURNITURE APPEARANCE'),('rejected-V1','REJECTED V1'),('CAM_living_VIEW_01','V2 ACTUAL BLENDER RENDER'),('AM2_CAM_SOFA_MATERIAL','V2 OATMEAL LINEN'),('LD_CAM_dining_DETAIL','V2 ASH WOOD')]):
 im=Image.open(OUT/(n+'.jpg'));im.thumbnail((490,390));x=i%3*500;y=i//3*450;contact.paste(im,(x,y+28));d.text((x+8,y+8),label,fill='#252725')
contact.save(SRC/'MATERIAL_COMPARISON.jpg',quality=86)
def card(n,label):return f'<article><h2>{label}</h2><a href="{n}.jpg" target="_blank"><img src="{n}.jpg"></a></article>'
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type V2 白蜡木与布艺复现</title><style>body{font-family:system-ui,sans-serif;background:#f5f1e9;color:#242725;margin:0}main{max-width:1600px;margin:auto;padding:30px}h1{font-size:28px}h2{font-size:17px}p{line-height:1.7}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.pair{grid-template-columns:repeat(2,minmax(0,1fr))}article{padding:15px;background:white;border-radius:12px}img{width:100%;height:auto}table{border-collapse:collapse;width:100%;background:white;margin:20px 0}td,th{padding:13px;border-bottom:1px solid #e4ddcf;text-align:left}aside{background:#e9e0ce;padding:18px;border-radius:10px}@media(max-width:800px){.grid,.pair{grid-template-columns:1fr}}</style><main><h1>C-Type · V2 白蜡木与布艺外观复现</h1><p>1:1 的目标：忠实复现已选效果图的颜色、木纹、织纹、粗糙度、光泽和光影。真实模型继续决定尺寸。2026-10-10。</p><aside>本页展示实际 Blender Cycles 材质修正。V1 已被业主否定；V2 待逐项视觉验收，不以尺寸校验或贴图节点存在宣称达标。画作 / 地毯图案与窗外景观尚未完成逐项复现，本轮首先评审白蜡木和沙发布艺。</aside><h1>客厅：选定参考 / V1 / V2</h1><p>A 约束家具的木色和布艺；B 约束地毯、窗帘和画。比较材料时以对应表面为准。</p><div class="grid">'''
html+=card('reference-living-A','已选参考：A Faithful 家具')+card('rejected-V1','被否定的 V1')+card('CAM_living_VIEW_01','V2 同机位实际渲染')
html+='''</div><h1>布艺与白蜡木近景</h1><div class="grid pair">'''+card('AM2_CAM_SOFA_MATERIAL','V2 米白燕麦布：经纬织纹、缝边、边缘受压')+card('LD_CAM_dining_DETAIL','V2 白蜡木：浅蜂蜜木色、沿构造木纹、哑光反射')+'''</div><h1>餐厅材料对照</h1><div class="grid">'''+card('reference-dining-C','已选餐厅 C 外观参考')+card('rejected-dining-V1','被否定的餐厅 V1')+card('LD_CAM_dining_DETAIL','V2 餐桌木材实渲')+'''</div><h1>软装参考与反向检查</h1><div class="grid pair">'''+card('reference-living-B','已选 B：窗帘、地毯、挂画')+card('CAM_living_VIEW_02','V2 反向材质检查')+'''</div><table><tr><th>逐项验收</th><th>本轮已修正</th><th>当前状态</th></tr><tr><td>白蜡木</td><td>取消过亮重映射；保留扫描木纹与木孔，沿部件长轴映射，校准哑光反射</td><td>候选待业主对照</td></tr><tr><td>沙发布艺</td><td>从蓝色扫描保留织纹，校准米白燕麦色；修正 UV 压缩、增加细微缝边受压与鼓起</td><td>候选待业主对照</td></tr><tr><td>地板</td><td>修正错误材质槽，恢复真实尺度板缝</td><td>候选待业主对照</td></tr><tr><td>日光</td><td>射线核查窗头遮挡，调整到真实窗洞可通行的角度，修正薄窗玻璃阴影传输</td><td>主光已恢复；参考的丰富层次继续细化</td></tr></table><p>四张 1920×1080 实渲 · Cycles / Apple M4 Metal / 128 samples / OIDN High。原 V1、源模型和已有参考图保留，977 个登记源对象几何及位置不变；七个展示软包的局部包络不变。点击图片查看高分辨率 JPEG。</p></main></html>'''
(OUT/'review_gallery.html').write_text(html)
print(OUT/'review_gallery.html')
