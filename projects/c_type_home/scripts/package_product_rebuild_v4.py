"""Adapt the existing V3 review gallery; retain full-resolution source renders."""
import hashlib
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'design/product_rebuild_v4'
RENDER = ROOT / 'renders/whole_house_final_study_v1'
OUT = RENDER / 'product_rebuild_v4'
OUT.mkdir(exist_ok=True)
manifest = json.loads((SRC / 'review_renders/render-manifest.json').read_text())
assert manifest['stage'] == 'review_renders' and len(manifest['images']) == 6
labels = {
    'CAM_living_VIEW_01': '客厅 · 整体外观',
    'V4_CAM_SOFA_COMPLETE': '沙发 · 整件木框与软包',
    'V4_CAM_DINING_COMPLETE': '餐厅 · 餐桌、四椅与吊灯',
    'V4_CAM_CHAIR_COMPLETE': '餐椅 · 藤编、扶手与坐垫',
    'V4_CAM_DINING_DETAIL': '餐桌 · 桌板与双柱支撑',
    'CAM_living_VIEW_02': '客厅 · 反向视角',
}
artifacts = []


def jpeg(source, name, edge=1600):
    source = Path(source)
    with Image.open(source) as im:
        original_size = list(im.size)
        im = im.convert('RGB')
        im.thumbnail((edge, edge))
        target = OUT / (name + '.jpg')
        im.save(target, quality=92)
    artifacts.append({'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                      'original_size': original_size, 'web_file': target.name, 'bytes': target.stat().st_size})


for record in manifest['images']:
    with Image.open(record['path']) as im:
        assert list(im.size) == record['size'], record['camera']
    jpeg(record['path'], record['camera'])
for source, name in [
    (RENDER / 'whole_house_modes_v3/living/A_faithful/VIEW_01.png', 'living-ref-A'),
    (RENDER / 'whole_house_modes_v3/living/B_designer/VIEW_01.png', 'living-ref-B'),
    (RENDER / 'whole_house_modes_v3/dining/C_creative/VIEW_01.png', 'dining-ref-C'),
    (RENDER / 'asset_model_v3/CAM_living_VIEW_01.jpg', 'living-V3-preserved'),
    (SRC / 'references/PAGE_28_FULL.jpg', 'catalog-chair'),
    (SRC / 'references/CATALOG_REBUILD_REFERENCES.jpg', 'catalog-construction'),
]:
    jpeg(source, name)

# Separate geometry evidence uses neutral Workbench shading, not the final materials.
product_manifest = json.loads((SRC / 'whole_product_views_v3/evidence.json').read_text())
sheet = Image.new('RGB', (1500, 824), '#ece8e0')
draw = ImageDraw.Draw(sheet)
for index, record in enumerate(product_manifest['views']):
    with Image.open(record['path']) as im:
        im = im.convert('RGB')
        im.thumbnail((480, 360))
        x = index % 3 * 500 + (500 - im.width) // 2
        y = index // 3 * 412 + 32
        sheet.paste(im, (x, y))
        draw.text((index % 3 * 500 + 12, index // 3 * 412 + 8),
                  record['product'] + ' / ' + record['view'], fill='#222222')
sheet.save(SRC / 'whole_product_views_v3/CONTACT.jpg', quality=83)
jpeg(SRC / 'whole_product_views_v3/CONTACT.jpg', 'whole-products')


def card(name, label):
    return (f'<article><h3>{html.escape(label)}</h3><a href="{name}.jpg" target="_blank" '
            f'aria-label="放大：{html.escape(label)}"><img src="{name}.jpg" '
            f'alt="{html.escape(label)}" loading="lazy"></a></article>')


page = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>C-Type 客厅与餐厅 · 整件家具重建 V4</title>
<style>body{margin:0;background:#f4f0e8;color:#282823;font-family:system-ui,sans-serif}
main{max-width:1500px;margin:auto;padding:28px}h1{font-size:28px}h2{font-size:23px;margin-top:36px}
h3{font-size:16px}p,li{line-height:1.8}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.pair{grid-template-columns:repeat(2,minmax(0,1fr))}article{padding:14px;background:white;border-radius:10px}
img{width:100%;height:auto;display:block}aside{padding:18px;background:#e8dfcf;border-radius:10px}
table{width:100%;border-collapse:collapse;background:white;margin:20px 0}th,td{text-align:left;padding:12px;border-bottom:1px solid #ded8cd}
nav{display:flex;gap:20px;flex-wrap:wrap;margin:20px 0}a{color:#635133}details{padding:16px;background:#eee7da;margin-top:20px}
@media(max-width:850px){.grid,.pair{grid-template-columns:1fr}main{padding:16px}table{font-size:13px}}</style></head>
<body><main><h1>客厅与餐厅 · 整件家具重建 V4</h1>
<p>2026-10-10 · 浅白蜡木、米白布艺、简洁。按选定效果图复现外观，真实模型决定尺寸。</p>
<aside>本版从整件构造重新制作沙发、躺椅、茶几、低柜、餐桌、四把餐椅和吊灯。沙发木框、承托和软包采用同一套构造，旧宽缝改为约 8–10 mm。
客厅采用 A 家具与 B 地毯、窗帘、东墙画；餐厅保留 1600×800 mm 跑道桌和浅色圆润吊灯，不挂画。
本版是可评审的测试候选，尚未认定外观 1:1 达标。</aside>
<nav><a href="#living">客厅对照</a><a href="#dining">餐厅对照</a><a href="#details">家具细节</a><a href="#fit">尺寸与使用</a></nav>
<h2 id="living">客厅 · 参考与新模型</h2><div class="grid">'''
page += card('living-ref-A', '已选 A · 家具造型、木色与布艺')
page += card('living-V3-preserved', '保留的 V3 · 上轮模型')
page += card('CAM_living_VIEW_01', labels['CAM_living_VIEW_01'])
page += '</div><div class="grid pair" style="margin-top:16px">'
page += card('living-ref-B', '已选 B · 仅采用地毯、窗帘与东墙画')
page += card('CAM_living_VIEW_02', labels['CAM_living_VIEW_02'])
page += '''</div><p>未加入 B 的落地灯、装饰抱枕、搭毯或额外花器。画作取自已选图的画面部分；地毯是同配色的近似重建，图案尚非完全相同。</p>
<h2 id="dining">餐厅 · 参考与新模型</h2><div class="grid pair">'''
page += card('dining-ref-C', '已选 C · 餐桌、浅色吊灯的外观方向')
page += card('V4_CAM_DINING_COMPLETE', labels['V4_CAM_DINING_COMPLETE'])
page += '''</div><p>餐桌坚持已确认的跑道形与实际尺寸。吊灯表面采用可擦洗的米白釉面，轮廓参考浅色圆润灯罩；原图的纸 / 布质感没有照搬。
藤编扶手椅按业主图册 6010A 的实际尺寸制作测试候选，仍待选型确认。</p>
<h2 id="details">家具整件与材质近景</h2><div class="grid">'''
for name in ['V4_CAM_SOFA_COMPLETE', 'V4_CAM_CHAIR_COMPLETE', 'V4_CAM_DINING_DETAIL']:
    page += card(name, labels[name])
page += '''</div><p>白蜡木与亚麻布复用 Poly Haven 原生 Blender 材质，按实际尺度排布纹理。软包采用闭合缝边与受支撑的鼓起形态；它是建模原型，不是填充物力学认证。</p>
<h2 id="fit">真实尺寸与使用差异</h2><table><thead><tr><th>对象</th><th>本版尺寸 / 标高</th><th>需关注</th></tr></thead><tbody>
<tr><td>L 型沙发</td><td>最大范围 1800×3300×700 mm</td><td>原占地保持；座包缝约 7.5 / 10 mm，背包缝约 8 mm</td></tr>
<tr><td>茶几 / 躺椅</td><td>茶几 1000×550×400 mm；躺椅在 1700×900×800 mm 范围内</td><td>造型按整件构造重建</td></tr>
<tr><td>餐桌</td><td>1600×800 mm；台面标高 750 mm</td><td>双柱与桌板支撑完整，保持原桌占地</td></tr>
<tr><td>四把餐椅</td><td>图册 560×560×850 mm；模型约 559×552×850 mm</td><td>比旧 400 mm 示意椅更大，每侧向外拉出 180 mm 以避开桌柱；不是已确认的采购或最终摆位</td></tr>
<tr><td>扶手 / 桌底</td><td>扶手顶部约 657.5 mm；桌底 712 mm，净距约 54.5 mm</td><td>当前静态椅桌无网格穿插；拉椅通行和人体膝脚空间仍待专项验证</td></tr>
</tbody></table>
<h2>这一版还存在的外观差距</h2><p>沙发靠垫仍比参考图规整，布艺的松软感和局部褶皱有差距；地毯织纹与图案只是近似。
完整家具来源为有依据的定制构造，并非原厂同款数字模型。吊灯型号尚未确定。窗外采用示意环境，不是住宅实际窗景。
光线通过现有窗户进入；已恢复原天花板集合的显示，未改天花板几何。</p>
<details><summary>查看实物构造参考与正 / 背 / 侧检查</summary><div class="grid pair">'''
page += card('catalog-construction', '业主图册 · 木框、软包与柜体构造参考')
page += card('catalog-chair', '业主图册 PDF 第 28 页 · 6010A 餐椅')
page += '</div>' + card('whole-products', '整件沙发与餐椅 · 中性几何检查（不显示最终材质）')
page += '''<p>沙发结合 PDF 第 4 页木框家族、第 8 页白蜡木软包材料与已选 A 外观做本户定制候选。
茶几、低柜、餐桌借鉴图册第 11 / 13 页整件结构，按本户尺寸重建，不将其写成原厂型号。</p></details>
<p>六张真实 Blender 渲染：五张 1920×1080、一张 1440×1920。网页使用缩略 JPEG，原始 PNG 保留。
Cycles / Metal / 128 samples；1946 个既有网格和世界矩阵保持，原有版本与建筑 Ground Truth 哈希保持。
本轮未调用 Image2，也未继续其他房间或全屋批量队列。</p>
<p>下一步：评审整件家具造型、白蜡木色、布艺质感和光照是否接近已选图，再决定此路线是否用于其他房间。</p>
</main></body></html>'''
(OUT / 'review_gallery.html').write_text(page)

contact = Image.new('RGB', (1500, 1000), '#f4f0e8')
draw = ImageDraw.Draw(contact)
names = ['living-ref-A', 'living-ref-B', 'CAM_living_VIEW_01',
         'dining-ref-C', 'V4_CAM_DINING_COMPLETE', 'V4_CAM_SOFA_COMPLETE']
for index, name in enumerate(names):
    with Image.open(OUT / (name + '.jpg')) as im:
        im.thumbnail((490, 455))
        x = index % 3 * 500 + (500 - im.width) // 2
        y = index // 3 * 500 + 30
        contact.paste(im, (x, y))
        draw.text((index % 3 * 500 + 8, index // 3 * 500 + 8), name, fill='#222222')
contact.save(SRC / 'V4_REVIEW_CONTACT.jpg', quality=83)
(OUT / 'WEB_ARTIFACTS.json').write_text(json.dumps({'status': 'HUMAN_REVIEW', 'artifacts': artifacts}, indent=2) + '\n')
print(OUT / 'review_gallery.html')
