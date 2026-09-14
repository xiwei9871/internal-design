from pathlib import Path
import base64, html, json
root=Path(__file__).parent
items=[('方案A7_功能平面.png','总体功能平面'),('方案A7_客厅功能说明.png','客厅功能与动线'),('方案A7_厨卫尺寸说明.png','主卫/次卫器具尺寸'),('方案A7_卧室窗边说明.png','主卧/儿童窗边功能')]
notes=['本版先校核功能与尺寸，暂不进入效果图。','客厅：直排沙发、电视/影音柜、茶几、餐边/充电收纳柜。','儿童窗边单独承担书桌＋书柜＋学习收纳；儿童房内不再重复布置书桌。','主卧窗边采用梳妆/阅读/临时办公弹性台，保留活动椅与镜面预留。','主卫保留浴缸 1500×700 备选；次卫维持淋浴，不放浴缸。','所有尺寸是家具/器具包络，施工前按最终品牌和现场复尺确认。']
body=[]
for p,t in items:
    data=base64.b64encode((root/p).read_bytes()).decode()
    body.append(f'<div class="card"><h2>{html.escape(t)}</h2><img src="data:image/png;base64,{data}" alt="{html.escape(t)}"></div>')
status=json.loads((root/'layout_checks.json').read_text())
refs=[('宜家三人沙发参考','https://www.ikea.cn/cn/zh/p/slatorp-si-la-tuo-san-ren-sha-fa-tu-na-shen-hui-he-se-90552855/'),('宜家电视柜参考','https://www.ikea.cn/cn/zh/p/besta-bei-da-dai-chou-ti-dian-shi-gui-la-wei-ken-xin-wei-he-se-s09186447/'),('宜家餐边柜参考','https://www.ikea.cn/cn/zh/p/40565520/'),('宜家洗手台柜尺寸参考','https://file.app.ikea.cn/cms/u/20240509/5a354d85476942f5b44d100f83768ead.pdf'),('宜家淋浴尺寸参考','https://www.ikea.cn/cn/zh/cat/lin-yu-men-47358/'),('科勒1500×700浴缸参考','https://m.kohler.com.cn/product/K-1875T-0/'),('GB/T 11977-2025','https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=8FD01948EA761BE57D56129326444DE1')]
refhtml=''.join(f'<a href="{u}" target="_blank">{html.escape(n)}</a> ' for n,u in refs)
htmlout='''<!doctype html><meta charset="utf-8"><title>方案 A7 · 功能与尺寸校核版</title><style>body{font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f7f5f0;color:#263a35;margin:28px;line-height:1.6}h1{margin:0 0 4px}.sub{color:#65736b;margin-top:0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start}.card{background:#fff;border:1px solid #ddd;border-radius:12px;padding:14px;box-shadow:0 2px 10px #00000008}.card img{width:100%;height:auto;display:block;border-radius:6px}.notes{background:#fff8df;border-left:4px solid #cf9035;padding:13px 16px;margin:16px 0}.notes li{margin:6px 0}.refs{font-size:13px;color:#65736b;background:#fff;padding:12px 16px;border-radius:10px}.refs a{margin-right:10px}@media(max-width:900px){.grid{grid-template-columns:1fr}}</style><h1>方案 A7 · 功能与尺寸校核版</h1><p class="sub">原始 PNG 为唯一平面依据｜原墙体保留｜效果图暂缓</p><div class="notes"><b>本版检查重点</b><ul>'''+''.join(f'<li>{html.escape(n)}</li>' for n in notes)+'''</ul></div><div class="grid">'''+''.join(body)+'''</div><div class="refs"><b>尺寸参考来源：</b>'''+refhtml+'''</div>'''
(root/'方案A7_网页预览.html').write_text(htmlout)
