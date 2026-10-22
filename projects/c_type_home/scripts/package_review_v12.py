"""Package actual Blender evidence as a bounded local review gallery."""
import json, shutil, html
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/"design/mother_hunyuan_v12";O=R/"renders/whole_house_final_study_v1/finishes_mother_v12";M=O/"media";M.mkdir(parents=True,exist_ok=True)
items=[("mother_bed","母亲主卧：完整Hunyuan3D床","整床2130×1910×1070mm，床头朝东；床头柜保持2110款。",D/"review/mother_bed.png"),("reading_grounded","阅读角：墙中居中、落地","820mm宽、320mm深；可用墙段两侧各约424mm。柜底与地板齐平，房门0至90度采样无碰撞。",R/"design/finishes_v11/review/reading_grounded.png"),("whole_house","全屋统一饰面","厨房、三个卫生间、北阳台铺瓷砖；其他区域同色浅木地板。普通墙暖白漆，厨卫内墙600×1200mm暗纹砖。",D/"review/whole_house.png")]
cards=[]
for n,title,note,p in items:
    assert p.exists(),p
    shutil.copyfile(p,M/(n+".png"))
    cards.append(f'<section id="{n}"><h2>{html.escape(title)}</h2><p>{html.escape(note)}</p><a href="media/{n}.png"><img src="media/{n}.png" alt="{html.escape(title)}"></a></section>')
page="""<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type V12 全屋修正检查</title><style>body{font:16px/1.65 system-ui,sans-serif;background:#f4f1eb;color:#282824;margin:0 auto;max-width:1440px;padding:24px}nav{display:flex;gap:18px;flex-wrap:wrap}a{color:#705936}section{background:white;margin:24px 0;padding:20px;border-radius:12px}img{width:100%;height:auto;border-radius:8px}</style><h1>C-Type V12 全屋修正检查</h1><p>2026-10-14 · HUMAN_REVIEW · Blender实际模型预览</p><nav><a href="#mother_bed">母亲主卧</a><a href="#reading_grounded">落地书柜</a><a href="#whole_house">全屋饰面</a><a href="http://127.0.0.1:5176/">Spatial Canvas</a></nav><p>保留原模型和Ground Truth。本页为EEVEE决策预览，材质在Blender源模型中实现。Spatial Canvas用于位置和对象选择。客房布局维持原决定；电视柜旁旧阅读长凳恢复隐藏。</p>"""+"".join(cards)+"</html>"
(O/"review_gallery.html").write_text(page)
a=json.loads((D/"BUILD_AUDIT.json").read_text());(O/"DELIVERY.json").write_text(json.dumps({"model":a["output"],"sha256":a["sha256"],"url":"http://127.0.0.1:5188/finishes_mother_v12/review_gallery.html","render_engine":"EEVEE","image2_requests":0},indent=2)+"\n")
print("REVIEW_V12",str(O/"review_gallery.html"))
