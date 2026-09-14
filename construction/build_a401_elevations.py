"""A401 立面展开图：厨房/服务墙/衣柜/卫浴 9 个立面，常规划分第一版。

全部立面元素为 (x,y,w,h,label,虚线?) mm 矩形，原点在各框左下角。
柜体内部分隔、开门方向、设备型号均为常规假设，标注"待确认"。
"""
from __future__ import annotations

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

from cad_common import (BLACK, OUT, add_text, new_doc, render_preview)

CEIL = 2600  # 平吊顶完成面


def frame(msp, ox, oy, w, title, h=CEIL):
    """画一面墙的立面框：外轮廓 + 吊顶线 + 标题 + 总宽标注"""
    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)],
                       close=True, dxfattribs={"layer": "A-WALL", "lineweight": 50})
    msp.add_line((ox, oy + h - 100), (ox + w, oy + h - 100),
                 dxfattribs={"layer": "A-CEIL", "linetype": "DASHED"})
    add_text(msp, "吊顶完成面", 80, (ox + w - 60, oy + h - 70), TextEntityAlignment.RIGHT)
    add_text(msp, title, 160, (ox + w / 2, oy - 420), TextEntityAlignment.MIDDLE_CENTER)
    dim = msp.add_linear_dim(base=(ox, oy - 180), p1=(ox, oy), p2=(ox + w, oy),
                             dimstyle="ARCH",
                             dxfattribs={"layer": "A-DIMS", "true_color": colors.rgb2int(BLACK)})
    dim.render()


def elem(msp, ox, oy, x, y, w, h, label, dashed=False, lw=25, layer="A-FURN"):
    attribs = {"layer": layer, "lineweight": lw}
    if dashed:
        attribs["linetype"] = "DASHED"
    msp.add_lwpolyline([(ox + x, oy + y), (ox + x + w, oy + y),
                        (ox + x + w, oy + h), (ox + x, oy + h)],
                       close=True, dxfattribs=attribs)
    if label:
        add_text(msp, label, 90, (ox + x + w / 2, oy + y + h / 2),
                 TextEntityAlignment.MIDDLE_CENTER)


def wardrobe(msp, ox, oy, w, title, doors=4, note="内部格局待确认"):
    """通顶衣柜常规立面：顶柜线 + 均分门扇"""
    frame(msp, ox, oy, w, title)
    elem(msp, ox, oy, 0, 0, w, 2600, "", lw=35)
    msp.add_line((ox, oy + 2100), (ox + w, oy + 2100), dxfattribs={"layer": "A-FURN"})
    add_text(msp, "顶柜 H2100-2600", 90, (ox + w / 2, oy + 2350), TextEntityAlignment.MIDDLE_CENTER)
    dw = w / doors
    for i in range(1, doors):
        msp.add_line((ox + i * dw, oy), (ox + i * dw, oy + 2100), dxfattribs={"layer": "A-FURN"})
        add_text(msp, "挂/叠", 80, (ox + (i - 0.5) * dw, oy + 1050), TextEntityAlignment.MIDDLE_CENTER)
    add_text(msp, note, 90, (ox + w / 2, oy + 150), TextEntityAlignment.MIDDLE_CENTER)


def main() -> None:
    doc = new_doc()
    msp = doc.modelspace()
    GX, GY = 5600, 4000  # 立面框网格间距

    # ---- E1 厨房北立面（宽3574，北墙窗占 982-3574）----
    ox, oy = 0, 0
    frame(msp, ox, oy, 3574, "E1 厨房北立面 1:50")
    elem(msp, ox, oy, 0, 0, 3574, 850, "地柜 H850")
    elem(msp, ox, oy, 0, 850, 3574, 50, "台面", lw=35)
    elem(msp, ox, oy, 982, 900, 2592, 1400, "原窗位（窗下为地柜）", layer="A-WINDOW")
    elem(msp, ox, oy, 350, 1500, 600, 500, "烟机位", dashed=True)
    elem(msp, ox, oy, 350, 850, 600, 60, "灶台600", layer="A-FIXT")
    elem(msp, ox, oy, 0, 1450, 300, 650, "吊柜")

    # ---- E2 厨房西立面（深1502，备餐台/水槽）----
    ox += GX
    frame(msp, ox, oy, 1502, "E2 厨房西立面 1:50")
    elem(msp, ox, oy, 0, 0, 893, 850, "水槽柜 H850")
    elem(msp, ox, oy, 0, 850, 893, 50, "台面")
    elem(msp, ox, oy, 150, 855, 590, 40, "水槽位", layer="A-FIXT")
    elem(msp, ox, oy, 0, 1450, 893, 650, "吊柜（待确认）")
    elem(msp, ox, oy, 950, 1600, 450, 550, "燃气热水器位 待确认", dashed=True, layer="A-FIXT")

    # ---- E3 服务墙立面（2298 = 冰箱894+蒸烤687+洗烘717）----
    ox += GX
    frame(msp, ox, oy, 2298, "E3 过道服务墙立面 1:50")
    elem(msp, ox, oy, 0, 0, 894, 1950, "冰箱位≤840")
    elem(msp, ox, oy, 0, 1950, 894, 650, "上柜")
    elem(msp, ox, oy, 894, 0, 687, 450, "下柜/抽屉")
    elem(msp, ox, oy, 894, 450, 687, 600, "蒸箱嵌机", layer="A-FIXT")
    elem(msp, ox, oy, 894, 1050, 687, 500, "烤箱嵌机", layer="A-FIXT")
    elem(msp, ox, oy, 894, 1550, 687, 1050, "上柜")
    elem(msp, ox, oy, 1581, 0, 717, 850, "洗衣机", layer="A-FIXT")
    elem(msp, ox, oy, 1581, 850, 717, 850, "干衣机", layer="A-FIXT")
    elem(msp, ox, oy, 1581, 1700, 717, 900, "上柜")

    # ---- 第二行：三个衣柜 ----
    ox, oy = 0, -GY
    wardrobe(msp, ox, oy, 2199, "E4 主卧北衣柜立面 1:50", doors=4)
    ox += GX
    wardrobe(msp, ox, oy, 2308, "E5 衣帽区长柜立面 1:50", doors=4)
    ox += GX
    wardrobe(msp, ox, oy, 2013, "E6 老人房衣柜立面 1:50", doors=4)

    # ---- 第三行：儿童房 + 两卫 ----
    ox, oy = 0, -2 * GY
    wardrobe(msp, ox, oy, 1993, "E7 儿童房衣柜立面 1:50", doors=3)
    ox += GX
    frame(msp, ox, oy, 2097, "E8 儿童窗边学习区立面 1:50")
    elem(msp, ox, oy, 0, 0, 1797, 750, "学习桌 H750")
    elem(msp, ox, oy, 1497, 0, 300, 2600, "通顶书柜300深")
    elem(msp, ox, oy, 0, 1750, 1497, 200, "吊柜/书架（待确认）", dashed=True)
    ox += 2700  # E8/E9 之间的空档放次卫
    frame(msp, ox, oy, 1493, "E10 次卫湿区立面 1:50", h=2400)
    elem(msp, ox, oy, 0, 0, 1493, 2400, "淋浴区+玻璃隔断", dashed=True, layer="A-FIXT")
    elem(msp, ox, oy, 200, 1600, 60, 300, "花洒", layer="A-FIXT")
    ox += 2900
    frame(msp, ox, oy, 2799, "E9 主卫湿区立面 1:50", h=2400)
    elem(msp, ox, oy, 0, 0, 1500, 550, "浴缸1500×700", layer="A-FIXT")
    elem(msp, ox, oy, 1500, 0, 1299, 2400, "淋浴区+玻璃隔断", dashed=True, layer="A-FIXT")
    elem(msp, ox, oy, 2400, 1600, 60, 300, "花洒", layer="A-FIXT")

    # ---- 图框（底部加 2700 高图签带，避开立面区）----
    x0, y0, x1, y1 = -1500, -2 * GY - 3900, 3 * GX - 800, 3200
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                       dxfattribs={"layer": "A-FRAME", "lineweight": 70,
                                   "true_color": colors.rgb2int(BLACK)})
    tx, ty = x1 - 6200, y0
    msp.add_lwpolyline([(tx, ty), (x1, ty), (x1, ty + 2400), (tx, ty + 2400)], close=True,
                       dxfattribs={"layer": "A-FRAME", "true_color": colors.rgb2int(BLACK)})
    for s, hgt, py_ in [
        ("学道街44号室内设计", 300, ty + 2050), ("立面展开图（柜体/厨卫）", 240, ty + 1650),
        ("图号 A401   建议比例 1:50   版本 v1", 180, ty + 1250),
        ("几何：A7 锁定平面 + 2700 墙高标定", 150, ty + 900),
        ("柜体分隔/开门方向/型号全部待确认", 150, ty + 550),
        ("宽度=平面锁定尺寸；高度为常规假设", 150, ty + 200)]:
        add_text(msp, s, hgt, (tx + 250, py_))
    for i, n in enumerate(["· 所有立面为常规划分第一版，内部格局待业主确认",
                            "· 卫浴立面仅示湿区；台盆/镜柜详图待洁具选型",
                            "· 橱柜详图待确认：门板、台面、拉篮、灯带、踢脚"]):
        add_text(msp, n, 150, (x0 + 250, y0 + 200 + i * 400))

    dxf_path = OUT / "A401_立面展开图.dxf"
    doc.saveas(dxf_path)
    render_preview(doc, msp, OUT / "A401_立面展开图_preview.png", figsize=(20, 14), dpi=150)
    print(dxf_path)
    print(OUT / "A401_立面展开图_preview.png")


if __name__ == "__main__":
    main()
