from __future__ import annotations

import base64
import html
import json
from pathlib import Path

ROOT = Path(__file__).parent
ITEMS = [
    ("living", "L · 餐客厅", "餐桌、沙发、电视柜和南向采光"),
    ("kitchen", "K · 厨房与走廊服务墙", "近处洗烘｜中段蒸烤｜远端靠厨房冰箱；左侧回形橱柜被服务墙遮挡"),
    ("master", "M · 主卧", "双人床、整墙衣柜和窗边弹性台"),
    ("child", "C · 儿童房", "床、衣柜和窗边学习区"),
    ("elder", "E · 老人房", "床、衣柜和清晰通行路径"),
    ("main_bath", "B · 主卫", "横向玻璃干湿分离、浴缸/淋浴、马桶和台盆"),
    ("secondary_bath", "S · 次卫", "横向玻璃干湿分离、淋浴、马桶和台盆"),
]


def uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> None:
    manifest = json.loads((ROOT.parent / "scheme_a_v11" / "scene_manifest.json").read_text(encoding="utf-8"))
    map_uri = uri(ROOT.parent / "scheme_a_v11" / "a11-viewpoint-map.svg", "image/svg+xml")
    cards = []
    for key, title, desc in ITEMS:
        image_uri = uri(ROOT / "renders" / f"{key}_image2_edit.png", "image/png")
        base_uri = uri(ROOT.parent / "scheme_a_v11" / "renders" / f"{key}.png", "image/png")
        cards.append(
            f"<article class='card'><h3>{html.escape(title)}</h3><p>{html.escape(desc)}</p>"
            f"<img src='{image_uri}' alt='{html.escape(title)} Image2 编辑效果图'>"
            f"<details><summary>查看 CAD/Blender 几何底图</summary><img class='base' src='{base_uri}' alt='{html.escape(title)} CAD 几何底图'></details></article>"
        )
    rows = []
    for key, info in manifest["camera_anchors"].items():
        rows.append(
            f"<tr><td>{html.escape(info['label'])}</td><td>{html.escape(key + '_image2_edit.png')}</td>"
            f"<td>{info['camera_px'][0]}, {info['camera_px'][1]}</td><td>{info['target_px'][0]}, {info['target_px'][1]}</td>"
            f"<td>{info['height_mm']} mm</td><td>{info['lens_mm']} mm</td></tr>"
        )
    page = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>方案 A12 · CAD 锁定视角 Image2 效果图</title><style>
body{{margin:0;background:#f3f1ec;color:#28372f;font-family:system-ui,-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;line-height:1.55}}main{{max-width:1450px;margin:auto;padding:28px 24px 64px}}h1{{font-size:30px;margin:0 0 4px}}h2{{font-size:22px;margin:30px 0 10px}}h3{{font-size:18px;margin:0 0 4px}}.sub{{margin:0;color:#66776c}}.notice{{margin:18px 0;padding:15px 18px;background:#fff8df;border-left:4px solid #c88a35;border-radius:8px}}.notice strong{{color:#684d2a}}.chain{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}}.chain span{{padding:6px 10px;border-radius:999px;background:#e1ece5;color:#35554a;font-size:13px}}.map{{background:#fff;border:1px solid #dedbd3;border-radius:12px;padding:12px;overflow:auto}}.map img{{display:block;width:100%;min-width:780px;height:auto}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.card{{background:#fff;border:1px solid #dedbd3;border-radius:12px;padding:13px;box-shadow:0 2px 12px #30251b12}}.card p{{font-size:13px;color:#68786f;margin:0 0 9px}}.card img{{width:100%;display:block;border-radius:7px}}.card .base{{margin-top:10px;border:1px solid #ddd}}details{{margin-top:10px;font-size:13px;color:#50665b}}table{{width:100%;border-collapse:collapse;background:#fff;font-size:13px}}th,td{{padding:8px 9px;border-bottom:1px solid #e8e4dc;text-align:left;vertical-align:top}}th{{background:#eef2ed;color:#30483e}}.small{{font-size:13px;color:#68786f}}@media(max-width:850px){{main{{padding:20px 14px}}.grid{{grid-template-columns:1fr}}}}
</style></head><body><main><h1>方案 A12 · CAD 锁定视角 Image2 效果图</h1><p class='sub'>A7 PNG 锁定平面 → FreeCAD 毫米底模 → Blender 固定相机 → Image2 材质与灯光效果层</p>
<div class='chain'><span>几何来源：A7 PNG</span><span>比例：9.82 mm/源像素</span><span>墙高：2700 mm</span><span>效果图：gpt-image-2</span><span>相机：7 个已锁定锚点</span></div>
<div class='notice'><strong>阅读方式：</strong>上方大图由 Image2 基于对应的 Blender 固定视角底图进行编辑，只改变材质、灯光和软装表达；展开每张图下方的“CAD/Blender 几何底图”，可直接对照源视角。Image2 可能对局部细节产生视觉重绘，因此施工尺寸、墙体、门窗和家具定位仍以 CAD/Blender 底模为准。任何布局变更都先改 CAD，再重新渲染。</div>
<h2>1. 平面图上的视角位置</h2><div class='map'><img src='{map_uri}' alt='A7 平面图上的七个固定视角'></div>
<h2>2. Image2 效果图（CAD 固定视角编辑）</h2><div class='grid'>{''.join(cards)}</div>
<h2>3. 视角与尺寸锚点</h2><div style='overflow:auto'><table><thead><tr><th>空间</th><th>效果图</th><th>相机位置（PNG px）</th><th>看向点（PNG px）</th><th>高度</th><th>焦距</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>4. 下一轮深化</h2><ul><li>先按底图逐张检查空间方向、门窗、家具比例和通行关系。</li><li>确认后再补充具体家电 SKU、洁具型号、柜门分格、五金、灯具和软装细节。</li><li>施工图继续从 FreeCAD/CAD 模型输出，Image2 图用于材质和氛围确认。</li></ul><p class='small'>源文件：方案A11_CAD底模.FCStd、方案A11_CAD同模渲染.blend、A12 image2_edit_manifest.json。</p>
</main></body></html>"""
    (ROOT / "方案A12_CAD锁定视角_Image2效果图.html").write_text(page, encoding="utf-8")
    (ROOT / "image2_render_preview.html").write_text(page, encoding="utf-8")
    print(f"wrote {ROOT / '方案A12_CAD锁定视角_Image2效果图.html'}")


if __name__ == "__main__":
    main()
