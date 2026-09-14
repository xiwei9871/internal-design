from __future__ import annotations

import base64
import html
import json
from pathlib import Path


ROOT = Path(__file__).parent
items = [
    ("living.png", "L · 餐客厅", "餐桌、沙发、电视柜、茶几和通行关系"),
    ("kitchen.png", "K · 厨房与走廊服务墙", "橱柜、薄型冰箱、微波/蒸箱、洗烘柜"),
    ("master.png", "M · 主卧", "双人床、整墙衣柜和窗边弹性台"),
    ("child.png", "C · 儿童房与窗边学习区", "床、衣柜、1800×600 学习桌和书柜"),
    ("elder.png", "E · 老人房", "床、床头柜、衣柜和通行净空"),
    ("main_bath.png", "B · 主卫", "浴缸、淋浴、马桶、台盆和干湿分区"),
    ("secondary_bath.png", "S · 次卫", "内嵌推拉门、淋浴、马桶和台盆"),
]


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> None:
    manifest = json.loads((ROOT / "scene_manifest.json").read_text(encoding="utf-8"))
    map_uri = data_uri(ROOT / "a11-viewpoint-map.svg", "image/svg+xml")
    cards = []
    for filename, title, desc in items:
        uri = data_uri(ROOT / "renders" / filename, "image/png")
        cards.append(
            f"<article class='card'><h3>{html.escape(title)}</h3><p>{html.escape(desc)}</p><img src='{uri}' alt='{html.escape(title)}'></article>"
        )
    rows = []
    for key, info in manifest["camera_anchors"].items():
        rows.append(
            f"<tr><td>{html.escape(info['label'])}</td><td>{html.escape(key + '.png')}</td>"
            f"<td>{info['camera_px'][0]}, {info['camera_px'][1]}</td><td>{info['target_px'][0]}, {info['target_px'][1]}</td>"
            f"<td>{info['height_mm']} mm</td><td>{info['lens_mm']} mm</td><td>同模已渲染</td></tr>"
        )
    page = f"""<!doctype html>
<html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>方案 A11 · CAD 同模渲染校核</title>
<style>
body{{margin:0;background:#f3f1ec;color:#28372f;font-family:system-ui,-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;line-height:1.55}}main{{max-width:1450px;margin:auto;padding:28px 24px 64px}}h1{{font-size:30px;margin:0 0 4px}}h2{{font-size:22px;margin:30px 0 10px}}h3{{font-size:18px;margin:0 0 4px}}.sub{{margin:0;color:#66776c}}.notice{{margin:18px 0;padding:15px 18px;background:#fff8df;border-left:4px solid #c88a35;border-radius:8px}}.notice strong{{color:#684d2a}}.chain{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}}.chain span{{padding:6px 10px;border-radius:999px;background:#e1ece5;color:#35554a;font-size:13px}}.map{{background:#fff;border:1px solid #dedbd3;border-radius:12px;padding:12px;overflow:auto}}.map img{{display:block;width:100%;min-width:780px;height:auto}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.card{{background:#fff;border:1px solid #dedbd3;border-radius:12px;padding:13px;box-shadow:0 2px 12px #30251b12}}.card p{{font-size:13px;color:#68786f;margin:0 0 9px}}.card img{{width:100%;display:block;border-radius:7px}}table{{width:100%;border-collapse:collapse;background:#fff;font-size:13px}}th,td{{padding:8px 9px;border-bottom:1px solid #e8e4dc;text-align:left;vertical-align:top}}th{{background:#eef2ed;color:#30483e}}.small{{font-size:13px;color:#68786f}}code{{font-size:12px}}@media(max-width:850px){{main{{padding:20px 14px}}.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>方案 A11 · CAD 同模渲染校核</h1><p class='sub'>A7 PNG 锁定平面 → FreeCAD 毫米 CAD 底模 → OBJ → Blender 同坐标渲染</p>
<div class='chain'><span>墙线：A7 PNG</span><span>比例：9.82 mm/源像素</span><span>墙高：2700 mm</span><span>相机：PNG 坐标转换为米</span></div>
<div class='notice'><strong>本页的定位：</strong>这是几何与视角校核版。墙体、门窗、家具外廓和设备位置来自同一套 CAD/3D 坐标；材质、家电 SKU、洁具安装节点仍属于设计阶段。它已经比文字生成图可复核，但在现场复尺和产品型号确认前仍不等于施工图。后续改布局时，先改源几何再重导出，确保 CAD、Blender 和效果图继续使用同一版本。</div>
<h2>1. 平面图视角位置</h2><div class='map'><img src='{map_uri}' alt='A7 平面图上的七个 CAD 同模相机位置与视线方向'></div>
<h2>2. 同模测试渲染</h2><div class='grid'>{''.join(cards)}</div>
<h2>3. 相机参数</h2><div style='overflow:auto'><table><thead><tr><th>编号</th><th>图片</th><th>相机位置（PNG px）</th><th>看向点（PNG px）</th><th>相机高度</th><th>焦距</th><th>状态</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>4. 当前可确认内容</h2><ul><li>平面几何来自 A7 的墙体、分区、门窗和家具外廓，未调用 DWG 去替换用户确认的 PNG 布局。</li><li>FreeCAD 文件以毫米记录墙高、家具包络和设备外廓；OBJ 仅作为 Blender 的交换格式。</li><li>渲染画面可以检查相机是否在正确房间、视线是否穿过正确门洞以及家具是否遮挡通行。</li><li>最终效果图会在同一模型上继续补充真实柜门、五金、材质和具体家电/洁具型号。</li></ul>
<p class='small'>源文件：方案A11_CAD底模.FCStd、方案A11_CAD同模渲染.blend、cad_manifest.json、scene_manifest.json。</p>
</main></body></html>"""
    (ROOT / "方案A11_CAD同模渲染预览.html").write_text(page, encoding="utf-8")
    (ROOT / "cad_render_preview.html").write_text(page, encoding="utf-8")
    print(f"wrote {ROOT / '方案A11_CAD同模渲染预览.html'}")


if __name__ == "__main__":
    main()
