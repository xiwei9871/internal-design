from pathlib import Path
import base64
import html

root = Path(__file__).parent
items = [
    ("living.png", "餐客厅·白蜡木家具与中央空调"),
    ("kitchen.png", "厨房与走廊服务墙·原木定制柜"),
    ("master.png", "主卧·整墙衣柜与窗边弹性桌"),
    ("child.png", "儿童房·床柜与窗边学习区"),
    ("elder.png", "老人房·床与整墙衣柜"),
    ("main_bath.png", "主卫·浴缸、淋浴与台盆"),
    ("secondary_bath.png", "次卫·内嵌推拉门与淋浴"),
]

cards = []
for filename, title in items:
    image = base64.b64encode((root / "renders" / filename).read_bytes()).decode()
    cards.append(
        f'<section class="card"><h2>{html.escape(title)}</h2>'
        f'<img src="data:image/png;base64,{image}" alt="{html.escape(title)}"></section>'
    )

notes = [
    "空间布局、墙体、门洞和窗位沿用已确认的原始 PNG / A7 方案。",
    "本轮使用 gpt-image-2 生成写实效果图，重点表现家具形体、木纹、布艺、灯光、家电和卫浴细节。",
    "餐客厅采用附件白蜡木系列的浅原木家具语言；厨房、衣柜和服务墙按定制柜体表达。",
    "厨房服务墙保留薄型冰箱、微波/蒸箱和洗烘一体机的连续功能；中央空调以线性送风口表达。",
    "主卫使用约 1500×700 mm 浴缸，次卫使用淋浴和内嵌推拉门；具体 SKU 与施工节点后续复核。",
    "这些图片用于确认风格、材质和空间氛围，不替代平面尺寸图或施工图。",
]

page = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>方案 A10 · 写实效果图 V1</title>
<style>
body{margin:28px;background:#f5f2ec;color:#27352f;font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}
h1{margin:0 0 4px;font-size:30px}.sub{margin:0;color:#6f7c73}.notes{margin:18px 0;padding:14px 18px;background:#fff8df;border-left:4px solid #c88a35;border-radius:8px}.notes li{margin:5px 0}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.card{background:white;border:1px solid #dedbd3;border-radius:12px;padding:14px;box-shadow:0 2px 12px #30251b12}.card h2{font-size:20px;margin:0 0 10px}.card img{width:100%;display:block;border-radius:8px}@media(max-width:900px){body{margin:16px}.grid{grid-template-columns:1fr}}
</style></head><body>
<h1>方案 A10 · 写实效果图 V1</h1>
<p class="sub">已确认平面布局 → gpt-image-2 室内效果图｜简约风・原木色・白色平吊顶</p>
<div class="notes"><b>本轮设计基准</b><ul>'''
page += "".join(f"<li>{html.escape(note)}</li>" for note in notes)
page += '</ul></div><div class="grid">' + "".join(cards) + '</div></body></html>'
(root / "方案A10_网页预览.html").write_text(page, encoding="utf-8")
print(f"wrote {root / '方案A10_网页预览.html'} with {len(items)} images")
