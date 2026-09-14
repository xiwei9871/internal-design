from __future__ import annotations

import base64
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).parent
V7 = ROOT.parent / "scheme_a_v7"
PLAN = V7 / "方案A7_功能平面.png"
GEOMETRY = V7 / "scheme_a_geometry.json"

VIEWS = {
    "L": {"name": "餐客厅", "camera": (1080, 760), "target": (930, 1130), "crop": (730, 690, 1230, 1380)},
    "K": {"name": "厨房服务墙", "camera": (735, 650), "target": (620, 250), "crop": (360, 110, 850, 710)},
    "M": {"name": "主卧", "camera": (650, 1170), "target": (570, 980), "crop": (350, 610, 830, 1380)},
    "C": {"name": "儿童房与窗边区", "camera": (1168, 1080), "target": (1320, 1000), "crop": (1080, 740, 1500, 1380)},
    "E": {"name": "老人房", "camera": (810, 620), "target": (980, 480), "crop": (740, 280, 1210, 710)},
    "B": {"name": "主卫", "camera": (395, 835), "target": (310, 690), "crop": (185, 510, 445, 880)},
    "S": {"name": "次卫", "camera": (570, 625), "target": (500, 470), "crop": (380, 300, 640, 690)},
}

KEY_FURNITURE = {
    "主卧": {"主卧床", "主卧北衣柜", "主卧西衣柜", "主卧窗边收纳柜", "主卧窗边东柜", "主卧窗边镜面预留", "主卧窗边梳妆/阅读台", "主卧窗边活动椅"},
    "儿童房与窗边区": {"次卧二床", "儿童房衣柜", "儿童窗边低书柜", "儿童窗边学习桌", "儿童学习椅"},
    "老人房": {"次卧一床", "老人房衣柜"},
    "餐客厅": {"4人餐桌（加端椅可6人）", "餐椅", "双人/小三人沙发（约2200×900）", "电视影音矮柜（约1800×350）", "客厅茶几（约900×550）", "餐边食品/书籍高柜（约900×400）", "餐边柜/充电收纳（约900×400）", "沙发边几"},
    "厨房服务墙": {"厨房橱柜", "厨房连续备餐台", "过道薄型冰箱（≤840宽×600深）", "过道微波食品高柜", "过道洗烘一体柜"},
    "主卫": {"主卫淋浴", "主卫马桶", "主卫台盆", "主卫镜柜"},
    "次卫": {"次卫淋浴", "次卫马桶", "次卫台盆"},
}


def pts(values):
    return " ".join(f"{x:g},{y:g}" for x, y in values)


def cone(camera, target, length=270, fov=52):
    cx, cy = camera
    tx, ty = target
    dx, dy = tx - cx, ty - cy
    norm = math.hypot(dx, dy) or 1
    ux, uy = dx / norm, dy / norm
    half = math.radians(fov / 2)
    c, s = math.cos(half), math.sin(half)
    lx, ly = (ux * c - uy * s) * length, (ux * s + uy * c) * length
    rx, ry = (ux * c + uy * s) * length, (-ux * s + uy * c) * length
    return [(cx, cy), (cx + lx, cy + ly), (cx + rx, cy + ry)]


def build_svg(geometry, view_id=None):
    w, h = geometry["reference_size"]
    if view_id:
        view = VIEWS[view_id]
        x0, y0, x1, y1 = view["crop"]
        viewbox = f"{x0} {y0} {x1-x0} {y1-y0}"
        out_w, out_h = 820, round(820 * (y1-y0) / (x1-x0))
    else:
        viewbox = f"0 0 {w} {h}"
        out_w, out_h = w, h
    plan = base64.b64encode(PLAN.read_bytes()).decode("ascii")
    parts = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{out_w}' height='{out_h}' viewBox='{viewbox}'>",
             f"<image href='data:image/png;base64,{plan}' x='0' y='0' width='{w}' height='{h}'/>",
             "<g font-family='PingFang SC,Microsoft YaHei,Arial,sans-serif'>"]
    selected = KEY_FURNITURE.get(VIEWS[view_id]["name"], set()) if view_id else set().union(*KEY_FURNITURE.values())
    for item in geometry["furniture"]:
        if view_id and item["name"] not in selected:
            continue
        x, y, fw, fh = item["rect"]
        parts.append(f"<rect x='{x}' y='{y}' width='{fw}' height='{fh}' fill='#e85d4a' fill-opacity='.18' stroke='#b9362b' stroke-width='2'/>")
        if view_id and fw * fh > 900:
            parts.append(f"<text x='{x+fw/2}' y='{y+fh/2}' text-anchor='middle' dominant-baseline='middle' font-size='13' fill='#8e211c'>{html.escape(item['name'])}</text>")
    views = [VIEWS[view_id]] if view_id else list(VIEWS.values())
    ids = [view_id] if view_id else list(VIEWS)
    colors = {"L":"#1b8f89","K":"#1b8f89","M":"#1b8f89","C":"#1b8f89","E":"#1b8f89","B":"#c45c2e","S":"#c45c2e"}
    for key, view in zip(ids, views):
        cx, cy = view["camera"]; tx, ty = view["target"]
        col = colors[key]
        parts.append(f"<polygon points='{pts(cone((cx,cy),(tx,ty)))}' fill='{col}' fill-opacity='.12' stroke='{col}' stroke-width='3' stroke-dasharray='8 6'/>")
        parts.append(f"<line x1='{cx}' y1='{cy}' x2='{tx}' y2='{ty}' stroke='{col}' stroke-width='4' stroke-dasharray='12 8'/>")
        parts.append(f"<circle cx='{cx}' cy='{cy}' r='18' fill='{col}' stroke='white' stroke-width='4'/><text x='{cx}' y='{cy+7}' text-anchor='middle' font-size='18' font-weight='700' fill='white'>{key}</text>")
        if view_id:
            parts.append(f"<text x='{x0+16}' y='{y0+28}' font-size='20' font-weight='700' fill='{col}'>{key} · {html.escape(view['name'])}</text>")
            parts.append(f"<text x='{x0+16}' y='{y0+53}' font-size='14' fill='#36443d'>相机 ({cx},{cy}) → 目标 ({tx},{ty})；红框=家具包络，虚线扇形=视锥</text>")
    parts.append("</g></svg>")
    return "".join(parts)


def main():
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    out = ROOT / "viewpoint_audit"
    out.mkdir(exist_ok=True)
    overall = out / "A7_全部视角_相机视锥.svg"
    overall.write_text(build_svg(geometry), encoding="utf-8")
    cards = []
    for key in VIEWS:
        path = out / f"A7_{key}_视角核对.svg"
        path.write_text(build_svg(geometry, key), encoding="utf-8")
        cards.append((key, VIEWS[key]["name"], path.name))
    rows = "".join(f"<tr><td>{k}</td><td>{html.escape(n)}</td><td>({VIEWS[k]['camera'][0]},{VIEWS[k]['camera'][1]}) → ({VIEWS[k]['target'][0]},{VIEWS[k]['target'][1]})</td><td>红框为 A7 家具包络；扇形为平面视锥</td></tr>" for k,n,_ in cards)
    cards_html = "".join(f"<article><h3>{k} · {html.escape(n)}</h3><img src='viewpoint_audit/{fn}'><p>只核对方向、门窗遮挡、家具比例和通行关系；不以此图修改布局。</p></article>" for k,n,fn in cards)
    page = f"""<!doctype html><html lang='zh-CN'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>方案 A12 · 视角核对图</title><style>body{{margin:0;background:#f4f1eb;color:#27362f;font-family:system-ui,-apple-system,'PingFang SC','Microsoft YaHei',sans-serif}}main{{max-width:1450px;margin:auto;padding:24px}}h1{{margin:0 0 4px}}.notice{{background:#fff8df;border-left:4px solid #c88a35;padding:12px 16px;border-radius:8px;margin:15px 0}}.map{{background:#fff;padding:10px;border:1px solid #ddd;border-radius:10px}}.map img{{width:100%;display:block}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}}article{{background:#fff;border:1px solid #ddd;border-radius:10px;padding:10px}}article img{{width:100%;display:block}}article p{{font-size:13px;color:#67776d;margin:8px 2px 0}}table{{border-collapse:collapse;width:100%;background:#fff;margin:16px 0}}th,td{{border:1px solid #e1ddd4;padding:8px;text-align:left;font-size:13px}}th{{background:#edf1ec}}@media(max-width:850px){{.grid{{grid-template-columns:1fr}}main{{padding:14px}}}}</style><main><h1>方案 A12 · 平面图视角核对图</h1><p>原始 PNG + A7 家具包络 + Blender 相机锚点；用于进入下一轮渲染前的逐张审查。</p><div class='notice'><b>审查规则：</b>红框只能表示已锁定的家具/设备包络，虚线扇形表示镜头在平面上的取景方向。若效果图出现底图没有的墙、玻璃隔断、桌椅或柜体，视为渲染错误；先修正相机或提示词，不修改原始布局。</div><div class='map'><img src='viewpoint_audit/A7_全部视角_相机视锥.svg'></div><table><thead><tr><th>编号</th><th>空间</th><th>相机 → 目标</th><th>图例</th></tr></thead><tbody>{rows}</tbody></table><h2>逐张核对</h2><div class='grid'>{cards_html}</div></main></html>"""
    html_path = ROOT / "viewpoint_audit_v1.html"
    html_path.write_text(page, encoding="utf-8")
    print(html_path)
    print(overall)


if __name__ == "__main__":
    main()
