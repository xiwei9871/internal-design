from pathlib import Path
import base64, html, json
root=Path(__file__).parent
items=[('overview.png','整体鸟瞰与墙体体块'),('living.png','餐客厅·白蜡木家具'),('kitchen.png','厨房与走廊服务墙'),('master.png','主卧·定制柜体与窗边区'),('child.png','儿童房·窗边学习区'),('elder.png','老人房·整墙衣柜'),('main_bath.png','主卫·浴缸与 TOTO/科勒同级洁具'),('secondary_bath.png','次卫·淋浴与内嵌推拉门')]
body=[]
for fn,title in items:
    data=base64.b64encode((root/'renders'/fn).read_bytes()).decode()
    body.append(f'<div class="card"><h2>{html.escape(title)}</h2><img src="data:image/png;base64,{data}" alt="{html.escape(title)}"></div>')
notes=['原始 PNG 墙体和 A7 功能布局为本轮建模依据。','家具：采用木甲木乙白蜡木系列的造型语言，首轮对应 1030-2 双位沙发、3046 餐台、3125 餐椅、5015-TS 电视柜和 2019 床类。','定制衣柜、橱柜按 A7 包络位置建模，整体采用浅色白蜡木/原木色。','吊顶：平整白色；中央空调按低静压风管机概念布置送风口。','家电：冰箱、微波/蒸箱、洗烘柜用西门子/LG 风格占位，尚未锁定具体型号。','卫浴：按 TOTO/科勒同级洁具比例建模；主卫放入 1500×700 浴缸首轮效果，次卫保持淋浴。','本轮仅为效果图 V1，不代表最终施工图；墙体、设备品牌和机电尺寸需在下一轮确认。']
htmlout='''<!doctype html><meta charset="utf-8"><title>方案 A8 · 原木简约效果图 V1</title><style>body{font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f7f5f0;color:#263a35;margin:28px;line-height:1.6}h1{margin:0 0 4px}.sub{color:#65736b;margin-top:0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start}.card{background:#fff;border:1px solid #ddd;border-radius:12px;padding:14px;box-shadow:0 2px 10px #00000008}.card img{width:100%;height:auto;display:block;border-radius:6px}.notes{background:#fff8df;border-left:4px solid #cf9035;padding:13px 16px;margin:16px 0}.notes li{margin:6px 0}@media(max-width:900px){.grid{grid-template-columns:1fr}}</style><h1>方案 A8 · 原木简约效果图 V1</h1><p class="sub">A7 功能布局 → Blender 体块与材质首轮｜附件白蜡木家具参考｜效果图讨论稿</p><div class="notes"><b>本轮设计基准</b><ul>'''+''.join(f'<li>{html.escape(n)}</li>' for n in notes)+'''</ul></div><div class="grid">'''+''.join(body)+'''</div>'''
(root/'方案A8_网页预览.html').write_text(htmlout)
