from base64 import b64encode
from pathlib import Path

root = Path(__file__).resolve().parent
def data_uri(path):
    return 'data:image/png;base64,' + b64encode(path.read_bytes()).decode()

html = f'''<!doctype html><meta charset="utf-8"><title>CAD source review</title>
<style>body{{font-family:system-ui,-apple-system,"PingFang SC",sans-serif;background:#f7f5f0;color:#202124;margin:28px}}h1{{margin:0 0 6px}}p{{color:#5f6368}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}}.card{{background:white;border:1px solid #ddd;border-radius:12px;padding:14px;box-shadow:0 2px 8px #00000012}}img{{width:100%;height:auto;display:block;background:white}}.tag{{font-weight:650;margin:0 0 10px}}</style>
<h1>住宅平面 CAD 核对</h1><p><b>建模依据已确定：CAD 是原始资料，PNG 是本次采用的平面布局。</b> 右图是 DWG 中的墙线参考页，标注为“茶室、小孩房、老人房、书房、主卧室、厨房”，与 PNG 标签不一致，因此只用于原始资料留档，不直接套用其分隔布局。后续模型按左图 PNG 的外轮廓、房间关系和可用空间重建。</p><p><a href="/png_rebuild/">打开 PNG 主布局重建 V1 →</a></p>
<div class="grid"><div class="card"><div class="tag">原始平面图（PNG）</div><img src="{data_uri(root/'source_plan.png')}"></div><div class="card"><div class="tag">DWG 墙线（LibreDWG → SVG → PNG）</div><img src="{data_uri(root/'xuedaojie44_crop2.png')}"></div></div>'''
(root/'cad_review.html').write_text(html)
print(root/'cad_review.html')
