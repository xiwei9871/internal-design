from base64 import b64encode
from pathlib import Path

r = Path(__file__).resolve().parent
def png(name):
    return 'data:image/png;base64,' + b64encode((r / name).read_bytes()).decode()
html = '''<!doctype html><meta charset="utf-8"><title>PNG 主布局重建</title>
<style>body{font-family:system-ui,-apple-system,"PingFang SC";background:#f7f5f0;color:#202124;margin:28px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.card{background:#fff;border:1px solid #ddd;border-radius:12px;padding:14px}img,svg{width:100%;height:auto;display:block}.note{background:#fff7df;padding:12px;margin:14px 0}</style>
<h1>按 PNG 重建｜V1</h1><div class="note"><b>依据：</b>CAD 为原始资料，PNG 为采用布局。所有黑色区域按可用空间保留；本页的墙线和 Blender 体块使用同一份 PNG 描摹几何。</div><div class="grid">
<div class="card"><h3>PNG 原图</h3><img src="PNG_REF"></div>
<div class="card"><h3>墙线＋房间＋家具描摹</h3>SVG_PLAN</div>
<div class="card"><h3>墙线叠加核对</h3><img src="OVERLAY"></div>
<div class="card"><h3>Blender 体块（连续可用空间）</h3><img src="BLENDER"></div>
<div class="card"><h3>Blender 正面投影墙线叠加核对</h3><img src="PROJECTION"></div></div>'''
html = html.replace('PNG_REF', png('reference.png')).replace('OVERLAY', png('wall_overlay.png')).replace('BLENDER', png('blockout_png_v1.png')).replace('PROJECTION', png('blender_projection_overlay.png')).replace('SVG_PLAN', (r/'floorplan.svg').read_text())
(r/'index.html').write_text(html)
print(r/'index.html')
