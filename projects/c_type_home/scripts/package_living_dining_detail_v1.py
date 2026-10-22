"""Small browser review package; images remain generated local artifacts."""
from pathlib import Path
import json, shutil
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'design/living_dining_detail_v1'
DEST=ROOT/'renders/whole_house_final_study_v1/living_dining_detail_v1'
DEST.mkdir(exist_ok=True)
manifest=json.loads((SOURCE/'final/render-manifest.json').read_text())
labels={'CAM_living_VIEW_01':'客厅主视角','CAM_living_VIEW_02':'客厅反向视角','CAM_dining_VIEW_01':'餐厅主视角','LD_CAM_living_DETAIL':'客厅软包与木框近景','LD_CAM_dining_DETAIL':'餐桌与椅子近景'}
cards=[]
for r in manifest['renders']:
 n=r['camera']; im=Image.open(r['path']).convert('RGB'); im.save(DEST/(n+'.jpg'),quality=92)
 cards.append(f'<article><h2>{labels[n]}</h2><a href="{n}.jpg" target="_blank"><img src="{n}.jpg" loading="lazy"></a><p>{r["size"][0]} × {r["size"][1]} · Cycles · 点击查看原图</p></article>')
refs=[('living/A_faithful/VIEW_01.png','ref-living-A.jpg','客厅家具：A Faithful'),('living/B_designer/VIEW_01.png','ref-living-B.jpg','客厅地毯、窗帘与画：B Designer'),('dining/C_creative/VIEW_01.png','ref-dining-C.jpg','餐厅桌面与吊灯方向：C Creative')]
refcards=[]
for path,n,label in refs:
 im=Image.open(DEST.parent/'whole_house_modes_v3'/path).convert('RGB'); im.thumbnail((1200,900)); im.save(DEST/n,quality=90)
 refcards.append(f'<article><h2>{label}</h2><img src="{n}" loading="lazy"></article>')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type 客厅餐厅精细模型 V1</title><style>body{margin:0;background:#f4f1eb;color:#252722;font-family:system-ui,sans-serif}main{max-width:1450px;margin:auto;padding:30px}h1{font-size:30px}p{line-height:1.7}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}article{padding:18px;background:white;border-radius:12px}img{width:100%;height:auto;display:block}h2{font-size:18px}.note{padding:18px;background:#e9e1d2;border-radius:10px}@media(max-width:800px){.grid{grid-template-columns:1fr}}</style><main><h1>C-Type 客厅 / 餐厅 · 精细 Blender 候选 V1</h1><p>浅原木、米白、简洁。实际 Blender 渲染，可编辑分件模型；2026-10-10。</p><p class="note">本轮用于评审构造、材料和视觉方向。餐桌 1600×800 mm，台面标高 750 mm；茶几 1000×550×400 mm。977 个登记源对象的网格与位置不变。画作和地毯为原创近似图案，吊灯商品型号未定。窗外 HDRI 仅作照明背景，不是实际现场景观。精细候选还不能称为参考图的逐项精确复刻。</p><div class="grid">'''+''.join(cards)+'''</div><h1>已选定的外观参考</h1><p>参考约束外观，真实模型约束尺寸。客厅不引入 Creative；餐厅不挂画。</p><div class="grid">'''+''.join(refcards)+'''</div></main></html>'''
(DEST/'review_gallery.html').write_text(html)
for n in ['BUILD_AUDIT.json','VERIFICATION.json']:shutil.copy2(SOURCE/n,DEST/n)
print(DEST/'review_gallery.html')
