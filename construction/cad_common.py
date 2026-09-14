"""施工图公共制图层：图层/文字/标注样式、墙门窗家具绘制、图框图签、PNG 预览。

坐标约定与 FreeCAD 底模一致：源 PNG 像素 × 9.82mm/px，
原点 (200,1337)px → 模型 (0,0)mm，Y 轴向上。
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "scheme_a_v7" / "scheme_a_geometry.json").read_text(encoding="utf-8"))
OUT = Path(__file__).resolve().parent
MM = 9.82
OX, OY = 200.0, 1337.0
BLACK = (18, 18, 18)  # ACI 7 在白色预览底上不可见，文字/图框用真彩色黑

LAYERS = {
    "A-WALL": 7, "A-WINDOW": 4, "A-DOOR": 3, "A-FURN": 30,
    "A-FIXT": 6, "A-DIMS": 1, "A-TEXT": 7, "A-HATCH": 8,
    "A-FRAME": 7, "A-FLOR": 2, "A-CEIL": 5, "A-ELEC": 1, "A-PLUM": 140,
}

# 洁具/家电/厨柜归 A-FIXT，其余家具归 A-FURN
FIXT_KEYS = ("马桶", "台盆", "淋浴", "镜柜", "冰箱", "洗烘", "微波", "橱柜", "备餐台", "蒸", "烤")


def m(px: float, py: float) -> tuple[float, float]:
    return ((px - OX) * MM, (OY - py) * MM)


def rect_pts(r):
    x, y, w, h = r
    return [m(x, y + h), m(x + w, y + h), m(x + w, y), m(x, y)]


def is_fixt(name: str) -> bool:
    return any(k in name for k in FIXT_KEYS)


def new_doc() -> ezdxf.EzDxf:
    doc = ezdxf.new("R2018")
    doc.units = 4  # mm
    for name, color in LAYERS.items():
        doc.layers.add(name, color=color)
    doc.styles.add("CN", font="PingFang SC")
    ds = doc.dimstyles.new("ARCH")
    ds.dxf.dimtxt = 200
    ds.dxf.dimasz = 140
    ds.dxf.dimexe = 120
    ds.dxf.dimexo = 60
    ds.dxf.dimgap = 60
    ds.dxf.dimtxsty = "CN"
    ds.dxf.dimblk = "ARCHTICK"
    ds.dxf.dimdec = 0  # 毫米整数
    return doc


def add_text(msp, s: str, height: float, pos, align=TextEntityAlignment.LEFT, layer="A-TEXT"):
    t = msp.add_text(s, height=height, dxfattribs={
        "layer": layer, "style": "CN", "true_color": colors.rgb2int(BLACK)})
    t.set_placement(pos, align=align)
    return t


def draw_walls(msp, fill: bool = True, lw: int = 50):
    for w in DATA["walls"]:
        pts = [m(x, y) for x, y in w["polygon"]]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-WALL", "lineweight": lw})
        if fill:
            h = msp.add_hatch(color=8, dxfattribs={"layer": "A-WALL"})
            h.paths.add_polyline_path(pts, is_closed=True)
    msp.add_lwpolyline([m(x, y) for x, y in DATA["outer"]], close=True,
                       dxfattribs={"layer": "A-WALL", "lineweight": 70})


def draw_windows(msp):
    for win in DATA["windows"]:
        (x1, y1), (x2, y2) = m(*win["segment"][:2]), m(*win["segment"][2:])
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "A-WINDOW", "lineweight": 25})
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L * 45, dx / L * 45  # 45mm 偏移框线
        msp.add_line((x1 + nx, y1 + ny), (x2 + nx, y2 + ny), dxfattribs={"layer": "A-WINDOW"})
        msp.add_line((x1 - nx, y1 - ny), (x2 - nx, y2 - ny), dxfattribs={"layer": "A-WINDOW"})


def draw_doors(msp):
    for d in DATA["doors"]:
        hp, lp, cp = m(*d["hinge"]), m(*d["leaf"]), m(*d["closed"])
        msp.add_line(hp, lp, dxfattribs={"layer": "A-DOOR", "lineweight": 35})
        r = math.hypot(lp[0] - hp[0], lp[1] - hp[1])
        a1 = math.degrees(math.atan2(lp[1] - hp[1], lp[0] - hp[0]))
        a2 = math.degrees(math.atan2(cp[1] - hp[1], cp[0] - hp[0]))
        if (a2 - a1) % 360 > 180:
            a1, a2 = a2, a1
        msp.add_arc(hp, r, a1, a2, dxfattribs={"layer": "A-DOOR"})


def draw_furniture(msp, labels: bool = True):
    for f in DATA["furniture"]:
        r = f["rect"]
        layer = "A-FIXT" if is_fixt(f["name"]) else "A-FURN"
        msp.add_lwpolyline(rect_pts(r), close=True, dxfattribs={"layer": layer, "lineweight": 25})
        if labels and r[2] * r[3] > 1500:  # 够大的包络才写名字，小件靠立面图
            cx, cy = m(r[0] + r[2] / 2, r[1] + r[3] / 2)
            add_text(msp, f["name"].split("（")[0], 110, (cx, cy), TextEntityAlignment.MIDDLE_CENTER)


def draw_room_labels(msp, height: float = 200):
    for name, px, py in DATA["labels"]:
        add_text(msp, name, height, m(px, py), TextEntityAlignment.MIDDLE_CENTER)


def outer_bounds():
    xs = [p[0] for p in (m(x, y) for x, y in DATA["outer"])]
    ys = [p[1] for p in (m(x, y) for x, y in DATA["outer"])]
    return min(xs), max(xs), min(ys), max(ys)


def draw_overall_dims(msp, off: float = 500):
    x0, x1, y0, y1 = outer_bounds()
    attribs = {"layer": "A-DIMS", "true_color": colors.rgb2int(BLACK)}
    dim = msp.add_linear_dim(base=(x0, y1 + off), p1=(x0, y1), p2=(x1, y1),
                             dimstyle="ARCH", dxfattribs=attribs)
    dim.render()
    dim = msp.add_linear_dim(base=(x0 - off, y0), p1=(x0, y0), p2=(x0, y1), angle=90,
                             dimstyle="ARCH", dxfattribs=attribs)
    dim.render()


def draw_frame_and_title(msp, title: str, sheet_no: str, notes: list[str]):
    x0, x1, y0, y1 = outer_bounds()
    bx0, by0, bx1, by1 = x0 - 1500, y0 - 5200, x1 + 1500, y1 + 1500
    msp.add_lwpolyline([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], close=True,
                       dxfattribs={"layer": "A-FRAME", "lineweight": 70, "true_color": colors.rgb2int(BLACK)})
    tx, ty = bx1 - 6200, by0
    msp.add_lwpolyline([(tx, ty), (bx1, ty), (bx1, ty + 2400), (tx, ty + 2400)], close=True,
                       dxfattribs={"layer": "A-FRAME", "true_color": colors.rgb2int(BLACK)})
    lines = [
        ("学道街44号室内设计", 300, ty + 2050),
        (title, 240, ty + 1650),
        (f"图号 {sheet_no}   建议比例 1:50   版本 v1", 180, ty + 1250),
        ("几何：A7 PNG 锁定平面，9.82mm/px 标定", 150, ty + 900),
        ("无拆改；尺寸为图像标定，施工前现场复尺", 150, ty + 550),
        (notes[-1] if notes else "", 150, ty + 200),
    ]
    for s, hgt, py_ in lines:
        if s:
            add_text(msp, s, hgt, (tx + 250, py_))
    for i, n in enumerate(notes[:-1]):
        add_text(msp, n, 150, (bx0 + 250, by0 + 200 + i * 400))


def render_preview(doc, msp, png_path: Path, figsize=(16, 12), dpi: int = 160):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    plt.rcParams["font.family"] = ["PingFang SC", "Arial Unicode MS", "sans-serif"]
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(msp, finalize=True)
    fig.savefig(png_path, dpi=dpi, facecolor="white")
