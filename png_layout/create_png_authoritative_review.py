from base64 import b64encode
from pathlib import Path

root = Path(__file__).resolve().parent
art = root.parent
def uri(p): return 'data:image/png;base64,' + b64encode(p.read_bytes()).decode()
html = f'''<!doctype html><meta charset="utf-8"><title>PNG authoritative layout</title>
<style>body{{font-family:system-ui,-apple-system,"PingFang SC",sans-serif;background:#f7f5f0;color:#202124;margin:28px}}h1{{margin:0 0 6px}}p{{color:#5f6368}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}.card{{background:#fff;border:1px solid #ddd;border-radius:12px;padding:14px}}img{{width:100%;display:block}}.note{{background:#fff7df;border-left:4px solid #d99b2b;padding:12px 16px;margin:18px 0}}</style>
<h1>PNG 主布局核对版</h1><p>CAD 作为原始资料保留；本轮采用的户型布局、空间关系和后续 Blender 依据均以最初 PNG 为准。</p>
<div class="note"><b>建模规则：</b>PNG 中所有黑色区域都属于可用室内空间；不删除、不留白。DWG 只用于之后核对尺寸、结构墙、门窗和设备点位。</div>
<div class="grid"><div class="card"><h3>主依据｜原始平面图 PNG</h3><img src="{uri(art/'dwg_import/source_plan.png')}"></div><div class="card"><h3>当前验证｜Blender 连续空间体块</h3><img src="{uri(art/'v1/blockout_v2.png')}"></div></div>'''
(root/'index.html').write_text(html)
print(root/'index.html')
