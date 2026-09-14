"""A201 地面铺装图：分房间地面材质 + 面积 + 材料表。

zones 材质字段直接来自 A7 锁定几何；客餐厅/过道/窗边区为
外包轮廓减去已知分区与墙体的剩余区域（shapely 求差），按橡木计。
"""
from __future__ import annotations

import math

import ezdxf
from ezdxf import colors
from shapely.geometry import Polygon
from shapely.ops import unary_union

from cad_common import (BLACK, DATA, OUT, add_text, draw_doors,
                        draw_frame_and_title, draw_overall_dims,
                        draw_walls, draw_windows, m, new_doc, render_preview)
from ezdxf.enums import TextEntityAlignment

# 材质 → (填充图案, 图案比例, 中文做法说明)
MATERIALS = {
    "oak":  ("ANSI31", 400, "橡木复合地板（白蜡木色系，规格/铺法待确认）"),
    "tile": ("ANSI37", 200, "暖灰瓷砖（厨房，规格/排版待确认）"),
    "wet":  ("ANSI37", 180, "暖灰防滑砖 + 防水（卫浴，翻边高度/规格待确认）"),
}
REMAINDER_MAT = "oak"
REMAINDER_NOTE = "客餐厅/过道/主卧窗边区/儿童窗边区：橡木复合地板"
# 分区内部名 → 图面显示名（与 A101 房间标注一致）
DISPLAY = {"次卧一": "老人房", "次卧二": "儿童房", "次卧二窗边区": "儿童窗边区"}


def hatch_poly(msp, pts, pattern: str, scale: float, layer="A-FLOR"):
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer, "lineweight": 25})
    h = msp.add_hatch(color=8, dxfattribs={"layer": layer})
    h.set_pattern_fill(pattern, scale=scale)
    h.paths.add_polyline_path(pts, is_closed=True)


def area_m2(pts) -> float:
    return Polygon(pts).area / 1e6


def main() -> None:
    doc = new_doc()
    msp = doc.modelspace()

    draw_walls(msp)

    # --- 分区铺装 ---
    zone_polys = []
    for z in DATA["zones"]:
        pts = [m(x, y) for x, y in z["polygon"]]
        pattern, scale, _ = MATERIALS[z["material"]]
        hatch_poly(msp, pts, pattern, scale)
        zone_polys.append(Polygon(pts))

    # --- 剩余区域（客餐厅/过道/各窗边区）---
    outer = Polygon([m(x, y) for x, y in DATA["outer"]])
    wall_polys = [Polygon([m(x, y) for x, y in w["polygon"]]) for w in DATA["walls"]]
    remainder = outer.difference(unary_union(zone_polys + wall_polys))
    pattern, scale, _ = MATERIALS[REMAINDER_MAT]
    geoms = list(remainder.geoms) if remainder.geom_type == "MultiPolygon" else [remainder]
    for g in geoms:
        if g.area < 1e5:  # 忽略 <0.1㎡ 的碎缝
            continue
        pts = [(x, y) for x, y in g.exterior.coords[:-1]]
        hatch_poly(msp, pts, pattern, scale)

    # --- 分区名 + 面积 ---
    for z in DATA["zones"]:
        pts = [m(x, y) for x, y in z["polygon"]]
        c = Polygon(pts).centroid
        add_text(msp, DISPLAY.get(z["name"], z["name"]), 180, (c.x, c.y + 130), TextEntityAlignment.MIDDLE_CENTER)
        add_text(msp, f"{area_m2(pts):.1f}㎡", 140, (c.x, c.y - 130), TextEntityAlignment.MIDDLE_CENTER)
    rest_area = sum(g.area for g in geoms) / 1e6
    rc = remainder.representative_point() if remainder.geom_type == "Polygon" else max(geoms, key=lambda g: g.area).centroid
    add_text(msp, f"客餐厅/过道等 {rest_area:.1f}㎡", 160, (rc.x, rc.y), TextEntityAlignment.MIDDLE_CENTER)

    draw_windows(msp)
    draw_doors(msp)
    draw_overall_dims(msp)

    # --- 材料表（图框左下）---
    legend = [f"· {v[2]}" for v in MATERIALS.values()] + [f"· {REMAINDER_NOTE}"]
    draw_frame_and_title(msp, "地面铺装图", "A201",
                         notes=legend + ["门槛石/收边条做法待确认；卫浴防水翻边高度待确认",
                                          "面积为净面积估算（图像标定），结算以实测为准"])

    dxf_path = OUT / "A201_地面铺装图.dxf"
    doc.saveas(dxf_path)
    render_preview(doc, msp, OUT / "A201_地面铺装图_preview.png")
    print(dxf_path)
    print(OUT / "A201_地面铺装图_preview.png")


if __name__ == "__main__":
    main()
