from __future__ import annotations

import base64
import html
import json
from pathlib import Path


ROOT = Path(__file__).parent
V7 = ROOT.parent / "scheme_a_v7"
GEOMETRY_PATH = V7 / "scheme_a_geometry.json"
PLAN_PATH = V7 / "方案A7_功能平面.png"


VIEWS = [
    {
        "id": "L",
        "name": "餐客厅",
        "image": "living.png",
        "camera": (1080, 900),
        "target": (930, 1130),
        "direction": "从入户/餐区看向客厅南窗与沙发",
        "targets": "餐桌、沙发、电视柜、茶几、餐边柜",
    },
    {
        "id": "K",
        "name": "厨房与服务墙",
        "image": "kitchen.png",
        "camera": (735, 470),
        "target": (620, 225),
        "direction": "从走廊服务墙回看厨房操作台",
        "targets": "橱柜、薄型冰箱、微波/蒸箱、洗烘一体机",
    },
    {
        "id": "M",
        "name": "主卧",
        "image": "master.png",
        "camera": (730, 1240),
        "target": (570, 980),
        "direction": "从主卧窗边回看床与衣柜",
        "targets": "双人床、北侧/西侧衣柜、窗边弹性台",
    },
    {
        "id": "C",
        "name": "次卧二与儿童窗边区",
        "image": "child.png",
        "camera": (1168, 1080),
        "target": (1320, 1000),
        "direction": "从窗边学习区回看床与衣柜",
        "targets": "床、床头柜、衣柜、1800×600 学习桌、书柜",
    },
    {
        "id": "E",
        "name": "老人房",
        "image": "elder.png",
        "camera": (810, 620),
        "target": (980, 480),
        "direction": "从门侧看向床与整墙衣柜",
        "targets": "床、床头柜、整墙衣柜、通行净空",
    },
    {
        "id": "B",
        "name": "主卫",
        "image": "main_bath.png",
        "camera": (395, 835),
        "target": (310, 690),
        "direction": "从门侧看向淋浴、马桶、台盆",
        "targets": "淋浴、马桶、台盆、镜柜、干湿分区",
    },
    {
        "id": "S",
        "name": "次卫",
        "image": "secondary_bath.png",
        "camera": (570, 625),
        "target": (500, 470),
        "direction": "从过道侧看向淋浴与洁具",
        "targets": "内嵌推拉门、淋浴、马桶、台盆、过道净空",
    },
]


def points(points: list[list[float]]) -> str:
    return " ".join(f"{x},{y}" for x, y in points)


def rect(rect_values: list[float]) -> str:
    x, y, w, h = rect_values
    return f"<rect x='{x:g}' y='{y:g}' width='{w:g}' height='{h:g}' />"


def build_svg(
    geometry: dict,
    title: str = "A10 效果图视角定位（V1）",
    status_line: str = "校核状态：A10 图片由文字生成，尚未证明与这些镜头一一对齐。",
    status_detail: str = "下一轮将用同一套 CAD/3D 坐标渲染，再以本图核对墙线、门洞、窗位和家具包络。",
) -> str:
    width, height = geometry["reference_size"]
    plan_b64 = base64.b64encode(PLAN_PATH.read_bytes()).decode("ascii")
    room_fills = {
        "厨房": "#ead19e",
        "次卫": "#c6e7ea",
        "主卫": "#c6e7ea",
        "衣帽区": "#e8d9b8",
        "主卧": "#eadcc2",
        "次卧一": "#e8d9b8",
        "次卧二": "#e8d9b8",
        "次卧二窗边区": "#dce9dc",
    }

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}' role='img' aria-labelledby='title desc'>",
        "<title id='title'>A10 效果图视角定位图</title>",
        "<desc id='desc'>在已确认的 A7 平面图上标出每张效果图的拟定相机位置、视线方向和编号。</desc>",
        "<defs><marker id='arrow' markerWidth='12' markerHeight='12' refX='9' refY='4' orient='auto'><path d='M0,0 L10,4 L0,8 z' fill='#d06c2e'/></marker></defs>",
        f"<image href='data:image/png;base64,{plan_b64}' x='0' y='0' width='{width}' height='{height}' />",
        "<g opacity='0.28' stroke='#345c57' stroke-width='3'>",
    ]
    for zone in geometry["zones"]:
        name = zone["name"]
        fill = room_fills.get(name, "#dce9dc")
        parts.append(
            f"<polygon points='{points(zone['polygon'])}' fill='{fill}' stroke='#345c57' stroke-width='3' />"
        )
    parts.append("</g>")
    parts.append(
        "<g font-family='-apple-system,BlinkMacSystemFont,Segoe UI,PingFang SC,Microsoft YaHei,sans-serif'>"
    )
    for index, view in enumerate(VIEWS, start=1):
        cx, cy = view["camera"]
        tx, ty = view["target"]
        color = "#1b8f89" if view["id"] in {"L", "K", "M", "C"} else "#c45c2e"
        parts.append(
            f"<line x1='{cx}' y1='{cy}' x2='{tx}' y2='{ty}' stroke='#d06c2e' stroke-width='5' stroke-dasharray='14 9' marker-end='url(#arrow)' />"
        )
        parts.append(
            f"<circle cx='{cx}' cy='{cy}' r='25' fill='{color}' stroke='white' stroke-width='5' />"
            f"<text x='{cx}' y='{cy + 10}' text-anchor='middle' font-size='25' font-weight='700' fill='white'>{html.escape(view['id'])}</text>"
        )
        label_y = cy - 34 if cy > 90 else cy + 55
        parts.append(
            f"<rect x='{cx + 31}' y='{label_y - 24}' width='210' height='36' rx='8' fill='#fffdf8' fill-opacity='0.94' stroke='{color}' stroke-width='2' />"
            f"<text x='{cx + 42}' y='{label_y}' font-size='21' fill='#233831'>{index}. {html.escape(view['name'])}</text>"
        )
    parts.append(
        "<rect x='28' y='28' width='540' height='122' rx='12' fill='#fffdf8' fill-opacity='0.96' stroke='#345c57' stroke-width='3' />"
        f"<text x='52' y='67' font-size='28' font-weight='700' fill='#233831'>{html.escape(title)}</text>"
        "<text x='52' y='101' font-size='20' fill='#5a6f66'>编号 = 下一轮可复现的相机锚点；虚线箭头 = 看向方向</text>"
        "<text x='52' y='129' font-size='18' fill='#7c6b59'>1 源图像素 ≈ 9.82 mm；以 A7 几何为准，需复尺确认</text>"
    )
    parts.append(
        "<rect x='28' y='1370' width='850' height='82' rx='12' fill='#fff8df' fill-opacity='0.96' stroke='#c88a35' stroke-width='3' />"
        f"<text x='52' y='1403' font-size='19' fill='#684d2a'>{html.escape(status_line)}</text>"
        f"<text x='52' y='1431' font-size='18' fill='#684d2a'>{html.escape(status_detail)}</text>"
    )
    parts.append("</g></svg>")
    return "".join(parts)


def build_html(geometry: dict) -> str:
    plan_b64 = base64.b64encode(PLAN_PATH.read_bytes()).decode("ascii")
    rows = []
    for index, view in enumerate(VIEWS, start=1):
        cx, cy = view["camera"]
        tx, ty = view["target"]
        rows.append(
            "<tr>"
            f"<td>{index} · {html.escape(view['id'])}</td>"
            f"<td>{html.escape(view['name'])}<br><code>{html.escape(view['image'])}</code></td>"
            f"<td>({cx}, {cy})</td><td>({tx}, {ty})</td>"
            f"<td>{html.escape(view['direction'])}</td>"
            f"<td>{html.escape(view['targets'])}</td>"
            "<td><span class='status pending'>待同模渲染</span></td>"
            "</tr>"
        )

    dimension_rows = [
        ("图纸标尺", "1 源图像素", "≈ 9.82 mm", "A7 几何校准：3320 mm / 338 px；现场复尺后更新"),
        ("厨房包络", "364 × 153 px", "≈ 3574 × 1503 mm", "厨房区包络；橱柜深度目标 600 mm"),
        ("次卫包络", "152 × 309 px", "≈ 1493 × 3034 mm", "A7 次卫区包络，最终以墙线和洁具定位复核"),
        ("主卫包络", "179 × 285 px", "≈ 1758 × 2799 mm", "含淋浴、马桶、台盆的布置包络"),
        ("主卧包络", "338 × 647 px", "≈ 3320 × 6352 mm", "衣柜、床和窗边弹性台按此坐标布置"),
        ("次卧一包络", "370 × 320 px", "≈ 3633 × 3142 mm", "老人房；衣柜深度目标 600 mm"),
        ("次卧二包络", "306 × 343 px", "≈ 3005 × 3369 mm", "儿童房；床柜留出开门与通行区"),
        ("儿童窗边区", "318 × 163 px", "≈ 3123 × 1602 mm", "1800 × 600 mm 学习桌 + 约 300 mm 深书柜"),
        ("餐桌", "约 145 × 82 px", "约 1400 × 800 × 750 mm", "4 人日常，端部可加椅"),
        ("沙发", "约 92 × 224 px", "约 2200 × 900 × 830 mm", "效果图中应保持家具包络，不以透视比例量尺寸"),
        ("主卧窗边台", "约 122 × 46 px", "1200 × 450 × 750 mm", "梳妆/阅读弹性台；镜面为预留项"),
        ("冰箱", "约 63 × 91 px", "设计目标 ≤ 650 W × 600 D × 1900 H mm", "薄型型号；下单前按具体 SKU 外廓替换"),
        ("微波/蒸箱高柜", "约 600 mm 柜宽", "柜深约 600 mm；设备位按 SKU", "与冰箱、洗烘柜组成走廊服务墙"),
        ("洗烘一体柜", "约 600 mm 柜宽", "设备约 600 W × 600 D × 850 H mm", "可按叠放方案预留 2.0 m 高柜体"),
        ("主卫浴缸", "A7 设计目标", "1500 × 700 mm", "需确认墙边检修和开启净空"),
        ("主/次卫淋浴", "A7 设计目标", "主卫约 1750 × 1000；次卫约 1500 × 1000 mm", "以玻璃隔断和门扇开启校核"),
        ("台盆/坐便器", "设备外廓目标", "台盆约 600 × 500；坐便器约 700 × 400 mm", "具体品牌 SKU 后更新安装尺寸"),
    ]
    dim_rows = "".join(
        f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{html.escape(c)}</td><td>{html.escape(d)}</td></tr>"
        for a, b, c, d in dimension_rows
    )

    return f"""<!doctype html>
<html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>A10 · 效果图视角与尺寸校核</title>
<style>
body{{margin:0;background:#f5f2ec;color:#27352f;font-family:system-ui,-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;line-height:1.55}}
main{{max-width:1400px;margin:0 auto;padding:28px 24px 60px}}h1{{margin:0 0 6px;font-size:30px}}h2{{margin:28px 0 10px;font-size:22px}}.sub{{margin:0;color:#68786e}}.notice{{margin:18px 0;padding:14px 18px;background:#fff8df;border-left:4px solid #c88a35;border-radius:8px}}.notice strong{{color:#684d2a}}.map{{background:#fff;border:1px solid #dedbd3;border-radius:12px;padding:12px;overflow:auto}}.map img{{display:block;width:100%;height:auto;min-width:780px}}table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dedbd3;border-radius:10px;overflow:hidden;font-size:14px}}th,td{{padding:9px 10px;text-align:left;vertical-align:top;border-bottom:1px solid #e8e4dc}}th{{background:#eef2ed;color:#30483e;font-weight:600}}code{{font-size:12px;color:#6d5b43}}.status{{display:inline-block;padding:3px 8px;border-radius:999px;font-size:12px}}.pending{{background:#fff0d6;color:#865b1e}}.legend{{display:flex;gap:18px;flex-wrap:wrap;margin:10px 0;color:#586b61;font-size:13px}}.dot{{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:-1px;margin-right:5px}}.teal{{background:#1b8f89}}.orange{{background:#c45c2e}}.small{{font-size:13px;color:#68786e}}@media(max-width:800px){{main{{padding:20px 14px}}table{{font-size:12px}}th,td{{padding:7px}}}}
</style></head><body><main>
<h1>方案 A10 · 效果图视角与尺寸校核</h1>
<p class='sub'>把“风格效果图”和“真实空间依据”拆开核对，作为下一轮同模渲染的基准。 <a href='/files/index.html'>查看 A10 效果图页</a></p>
<div class='notice'><strong>先说结论：</strong>A10 当前 7 张图由 gpt-image-2 文字生成，能表达风格和家具内容，但没有从可验证的 CAD/3D 相机直接渲染，因此本页的编号和箭头是下一轮的相机锚点，不能反向证明 A10 已经按真实透视制作。尺寸以 A7 几何与下表的设计目标为准，现场复尺和具体产品 SKU 确认后才能进入施工图。</div>
<h2>1. 平面图上的相机位置</h2>
<div class='map'><img src='viewpoint-map.svg' alt='A7 平面图上的 A10 效果图相机位置、视线箭头和编号'></div>
<div class='legend'><span><i class='dot teal'></i>公共区/卧室镜头</span><span><i class='dot orange'></i>卫浴镜头</span><span>虚线箭头：相机看向点</span><span>坐标单位：原始 PNG 像素</span></div>
<h2>2. 效果图与镜头锚点</h2>
<div style='overflow:auto'><table><thead><tr><th>编号</th><th>效果图</th><th>相机位置<br>(x, y)</th><th>看向点<br>(x, y)</th><th>视角说明</th><th>应看到的内容</th><th>状态</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class='small'>相机位置和看向点是平面坐标锚点；下一轮会把它们转换成 CAD/Blender 的米制坐标、相机高度、镜头焦距和裁切范围，并以同一坐标系出图。</p>
<h2>3. 真实比例与尺寸基准</h2>
<div style='overflow:auto'><table><thead><tr><th>对象</th><th>A7 图上依据</th><th>换算/设计尺寸</th><th>使用说明</th></tr></thead><tbody>{dim_rows}</tbody></table></div>
<h2>4. 后续执行规则</h2>
<ol><li>先在 FreeCAD 的 BIM/Sketcher 中建立墙体、门洞、窗位、家具包络和设备外廓的参数化模型，全部以 mm 记录。</li><li>从同一模型导出功能平面、尺寸平面、立面和 Blender 渲染场景；相机编号沿用本页 L/K/M/C/E/B/S。</li><li>每张效果图同时交付本页视角编号、相机坐标、目标点、相机高度、焦距和画面裁切；家具尺寸从模型读取，不靠图片目测。</li><li>你确认布局、家具、材质和家电 SKU 后，再冻结施工图版本，避免先画完整施工节点后返工。</li></ol>
<p class='small'>源平面：A7 功能平面；源文件：scheme_a_geometry.json。比例说明为图纸校准值，不是现场测量结果。</p>
</main></body></html>"""


def main() -> None:
    geometry = json.loads(GEOMETRY_PATH.read_text(encoding="utf-8"))
    svg_path = ROOT / "方案A10_视角定位图.svg"
    html_path = ROOT / "方案A10_视角与尺寸校核.html"
    svg_path.write_text(build_svg(geometry), encoding="utf-8")
    html_path.write_text(build_html(geometry), encoding="utf-8")
    print(f"wrote {svg_path} ({svg_path.stat().st_size} bytes)")
    print(f"wrote {html_path} ({html_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
