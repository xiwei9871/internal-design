"""A303 给排水点位图：冷热水/排污/地漏/设备点位，坑距与选型待确认。

符号：▲给水点  ●排水/排污  ⊠地漏  ▭设备。
高度为距完成面 mm；墙排/地排、坑距（300/400）现场与选型确认。
"""
from __future__ import annotations

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

from cad_common import (OUT, add_text, draw_doors, draw_furniture,
                        draw_frame_and_title, draw_overall_dims,
                        draw_room_labels, draw_walls, draw_windows, m,
                        new_doc, render_preview)

# (px, py, 标注, 类型)  cold/hot 合并标注；type: sup=给水 drn=排水 floor=地漏 dev=设备
POINTS = [
    # 次卫
    (445, 578, "台盆 冷热H450 排水H300(墙排待确认)", "sup"),
    (447, 487, "马桶 给水H200", "sup"),
    (435, 500, "马桶排污 坑距300/400待确认", "drn"),
    (478, 368, "淋浴 冷热H1050", "sup"),
    (470, 420, "淋浴地漏 DN50", "floor"),
    (540, 600, "干区地漏 DN50", "floor"),
    # 主卫
    (250, 795, "台盆 冷热H450 排水H300(墙排待确认)", "sup"),
    (250, 715, "马桶 给水H200", "sup"),
    (238, 725, "马桶排污 坑距300/400待确认", "drn"),
    (265, 600, "淋浴 冷热H1050", "sup"),
    (240, 640, "淋浴地漏 DN50", "floor"),
    (360, 615, "浴缸 冷热H500+排水", "sup"),
    (375, 645, "浴缸地漏/排水", "drn"),
    # 厨房
    (448, 268, "水槽 冷热H450 排水H300", "sup"),
    (425, 300, "净水/洗碗机排水预留", "drn"),
    (608, 168, "燃气热水器位 冷热+排烟 待确认", "dev"),
    # 服务墙
    (628, 515, "洗衣机 冷H1100+排水；干衣排水待确认", "sup"),
    # 原阳台区
    (610, 1295, "原阳台地漏 存废待确认", "floor"),
    (1300, 1295, "原阳台地漏 存废待确认", "floor"),
]


def draw_point(msp, px, py, label, kind):
    x, y = m(px, py)
    if kind == "sup":
        msp.add_lwpolyline([(x, y + 75), (x + 65, y - 45), (x - 65, y - 45)], close=True,
                           dxfattribs={"layer": "A-PLUM", "lineweight": 35})
    elif kind == "drn":
        msp.add_circle((x, y), 60, dxfattribs={"layer": "A-PLUM", "lineweight": 35})
    elif kind == "floor":
        s = 65
        msp.add_lwpolyline([(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)],
                           close=True, dxfattribs={"layer": "A-PLUM", "lineweight": 35})
        msp.add_line((x - s, y - s), (x + s, y + s), dxfattribs={"layer": "A-PLUM"})
        msp.add_line((x - s, y + s), (x + s, y - s), dxfattribs={"layer": "A-PLUM"})
    else:
        msp.add_lwpolyline([(x - 80, y - 55), (x + 80, y - 55), (x + 80, y + 55), (x - 80, y + 55)],
                           close=True, dxfattribs={"layer": "A-PLUM", "lineweight": 35})
    if px > 1100:
        add_text(msp, label, 85, (x - 115, y - 40), TextEntityAlignment.RIGHT, layer="A-PLUM")
    else:
        add_text(msp, label, 85, (x + 115, y - 40), TextEntityAlignment.LEFT, layer="A-PLUM")


def main() -> None:
    doc = new_doc()
    msp = doc.modelspace()

    draw_walls(msp)
    draw_windows(msp)
    draw_doors(msp)
    draw_furniture(msp, labels=False)
    draw_room_labels(msp, height=170)
    for px, py, label, kind in POINTS:
        draw_point(msp, px, py, label, kind)
    draw_overall_dims(msp)
    draw_frame_and_title(msp, "给排水点位图", "A303",
                         notes=["· ▲给水（冷热同位标注） ●排水/排污 ⊠地漏 ▭设备",
                                "· 墙排/地排、马桶坑距300/400、浴缸排水方式：选型+现场确认",
                                "· 燃气热水器位置/品牌待确认（暂按厨房北墙）",
                                "· 原阳台地漏存废、物业立管包封范围待确认"])

    dxf_path = OUT / "A303_给排水点位图.dxf"
    doc.saveas(dxf_path)
    render_preview(doc, msp, OUT / "A303_给排水点位图_preview.png")
    print(dxf_path)
    print(OUT / "A303_给排水点位图_preview.png")


if __name__ == "__main__":
    main()
