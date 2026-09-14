"""A301 天花布置图：平吊顶高度分区、多联机内机/风口/检修口、无主灯点位。

- 全屋平吊 2600（藏内机处局部 2400）；过道/玄关满吊 2400 藏主管；
  厨房卫浴铝扣板 2400。层高基准以底模墙高 2700 为准，现场复核。
- 多联机（中央空调）一拖多：客餐厅 1 台 + 三卧各 1 台，均靠门侧便于
  走管/冷凝排水/检修；外机 1 台（机位待现场确认）。品牌型号待确认。
- 无主灯：筒灯按 ~1150mm 网格布点；客餐厅与主卧沿吊顶边设灯带。
"""
from __future__ import annotations

import math

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from cad_common import (BLACK, DATA, OUT, add_text, draw_doors,
                        draw_frame_and_title, draw_overall_dims,
                        draw_room_labels, draw_walls, draw_windows, m,
                        new_doc, render_preview)

# 内机/风口/检修口（源像素 rect: x,y,w,h）
UNITS = [
    ("老人房内机", (800, 575, 95, 48), (805, 640, 71, 15), (905, 578, 46, 46)),
    ("儿童房内机", (1158, 790, 95, 48), (1165, 845, 71, 15), (1260, 792, 46, 46)),
    ("主卧内机",   (655, 672, 95, 48), (665, 728, 71, 15), (598, 672, 46, 46)),
    ("客餐厅内机", (840, 685, 115, 55), (855, 748, 71, 15), (968, 688, 46, 46)),
]

WET = {"次卫", "主卫"}
HEIGHTS = {"厨房": "H=2400 铝扣板", "次卫": "H=2400 铝扣板", "主卫": "H=2400 铝扣板",
           "衣帽区": "H=2600", "主卧": "H=2600", "次卧一": "H=2600", "次卧二": "H=2600",
           "次卧二窗边区": "H=2600"}


def px_rect(r):
    x, y, w, h = r
    return [m(x, y + h), m(x + w, y + h), m(x + w, y), m(x, y)]


def dashed_poly(msp, pts, layer="A-CEIL", lw=25):
    msp.add_lwpolyline(pts, close=True, dxfattribs={
        "layer": layer, "lineweight": lw, "linetype": "DASHED"})


def main() -> None:
    doc = new_doc()
    msp = doc.modelspace()

    draw_walls(msp)

    # --- 区域多边形 ---
    zone_polys = {}
    for z in DATA["zones"]:
        pts = [m(x, y) for x, y in z["polygon"]]
        zone_polys[z["name"]] = (Polygon(pts), pts)
    outer = Polygon([m(x, y) for x, y in DATA["outer"]])
    wall_u = unary_union([Polygon([m(x, y) for x, y in w["polygon"]]) for w in DATA["walls"]])
    remainder = outer.difference(unary_union(list(zone_polys.values())[0].__class__ and
                                             [p for p, _ in zone_polys.values()]).union(wall_u))
    rem_geoms = [g for g in (remainder.geoms if remainder.geom_type == "MultiPolygon" else [remainder])
                 if g.area > 1e5]

    # --- 吊顶高度标注；灯带仅客餐厅与主卧 ---
    for name, (poly, pts) in zone_polys.items():
        if name == "主卧":
            cove = poly.buffer(-300)
            for g in ([cove] if cove.geom_type == "Polygon" else
                      (list(cove.geoms) if hasattr(cove, "geoms") else [])):
                if g.area > 0:
                    dashed_poly(msp, list(g.exterior.coords[:-1]))
        c = poly.centroid
        add_text(msp, HEIGHTS[name], 120, (c.x, c.y - 250), TextEntityAlignment.MIDDLE_CENTER)
    for g in rem_geoms:
        cove = g.buffer(-350)
        for cg in ([cove] if cove.geom_type == "Polygon" else
                   (list(cove.geoms) if hasattr(cove, "geoms") else [])):
            if cg.area > 0:
                dashed_poly(msp, list(cg.exterior.coords[:-1]))
    # 过道满吊线（老人房南墙—儿童房西墙之间）
    msp.add_line(m(790, 780), m(1152, 780), dxfattribs={
        "layer": "A-CEIL", "linetype": "DASHED", "lineweight": 35})
    add_text(msp, "过道/玄关 满吊 H=2400（藏主管）", 130, m(965, 720), TextEntityAlignment.MIDDLE_CENTER)
    add_text(msp, "客餐厅 平吊 H=2600", 140, m(950, 1050), TextEntityAlignment.MIDDLE_CENTER)

    # --- 内机/风口/检修口 ---
    unit_boxes = []
    for name, ur, vr, ar in UNITS:
        up = px_rect(ur); vp = px_rect(vr); ap = px_rect(ar)
        unit_boxes.append(Polygon(up))
        dashed_poly(msp, up, lw=35)
        msp.add_lwpolyline(vp, close=True, dxfattribs={"layer": "A-CEIL", "lineweight": 25})
        msp.add_lwpolyline(ap, close=True, dxfattribs={"layer": "A-CEIL", "lineweight": 25})
        msp.add_line(ap[0], ap[2], dxfattribs={"layer": "A-CEIL"})
        msp.add_line(ap[1], ap[3], dxfattribs={"layer": "A-CEIL"})
        c = Polygon(up).centroid
        add_text(msp, name, 110, (c.x, c.y), TextEntityAlignment.MIDDLE_CENTER)

    # --- 无主灯筒灯：~1150mm 网格，湿区加密 ---
    unit_u = unary_union(unit_boxes)
    all_regions = [(p, n) for n, (p, _) in zone_polys.items()] + [(g, "客餐厅等") for g in rem_geoms]
    for poly, name in all_regions:
        spacing = 1000 if name in WET or name == "厨房" else 1150
        inner = poly.buffer(-250)  # 灯具符号整体收在吊顶范围内
        if inner.is_empty:
            continue
        minx, miny, maxx, maxy = inner.bounds
        x = minx + spacing / 2
        while x < maxx:
            y = miny + spacing / 2
            while y < maxy:
                p = Point(x, y)
                if inner.contains(p) and not unit_u.contains(p):
                    msp.add_circle((x, y), 45, dxfattribs={"layer": "A-CEIL"})
                    msp.add_line((x - 65, y), (x + 65, y), dxfattribs={"layer": "A-CEIL"})
                    msp.add_line((x, y - 65), (x, y + 65), dxfattribs={"layer": "A-CEIL"})
                y += spacing
            x += spacing

    draw_windows(msp)
    draw_doors(msp)
    draw_room_labels(msp, height=170)
    draw_overall_dims(msp)
    draw_frame_and_title(msp, "天花布置图（吊顶/空调内机/照明点位）", "A301",
                         notes=["· 图例：虚线框=风管式内机（藏吊顶）；细实线框=送风口；⌧=检修口450×450",
                                "· 多联机一拖多，外机1台机位待现场确认；内机品牌/型号待确认",
                                "· 筒灯 Ø90（厨卫防雾型），~1150mm网格，选型待确认",
                                "· 虚线=灯带/吊顶边界；层高基准以现场复尺为准"])

    dxf_path = OUT / "A301_天花布置图.dxf"
    doc.saveas(dxf_path)
    render_preview(doc, msp, OUT / "A301_天花布置图_preview.png")
    print(dxf_path)
    print(OUT / "A301_天花布置图_preview.png")


if __name__ == "__main__":
    main()
