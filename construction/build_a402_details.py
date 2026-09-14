"""A402 节点详图（示意）：5 个关键收口/防水节点剖面，常规做法第一版。

每个节点为分层条带剖面 + 引注；具体材料/型材/防水高度标"待确认"，
最终以深化设计与现场做法为准。
"""
from __future__ import annotations

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

from cad_common import (BLACK, OUT, add_text, new_doc, render_preview)


def band(msp, ox, oy, x, y, w, h, label, layer="A-FURN", dashed=False):
    attribs = {"layer": layer, "lineweight": 25}
    if dashed:
        attribs["linetype"] = "DASHED"
    msp.add_lwpolyline([(ox + x, oy + y), (ox + x + w, oy + y),
                        (ox + x + w, oy + h), (ox + x, oy + h)],
                       close=True, dxfattribs=attribs)
    if label:
        add_text(msp, label, 85, (ox + x + w / 2, oy + y + h / 2),
                 TextEntityAlignment.MIDDLE_CENTER)


def title(msp, ox, oy, w, s):
    add_text(msp, s, 150, (ox + w / 2, oy - 250), TextEntityAlignment.MIDDLE_CENTER)


def main() -> None:
    doc = new_doc()
    msp = doc.modelspace()
    G = 3200  # 节点间距

    # ---- D1 卫浴门槛防水节点（剖面）----
    ox, oy = 0, 0
    band(msp, ox, oy, 0, 0, 900, 100, "卫浴地砖")
    band(msp, ox, oy, 900, 0, 300, 130, "门槛石")
    band(msp, ox, oy, 1200, 0, 600, 80, "木地板")
    band(msp, ox, oy, 0, -60, 1800, 60, "结构楼板")
    band(msp, ox, oy, 0, 100, 900, 40, "防水层", layer="A-PLUM")
    band(msp, ox, oy, 0, 140, 60, 300, "防水翻边≥300", layer="A-PLUM", dashed=True)
    band(msp, ox, oy, 1170, 80, 60, 50, "扣条", layer="A-FIXT")
    add_text(msp, "卫浴侧防水层上翻≥300（湿区墙面1800，待确认）", 90,
             (ox + 900, oy + 520), TextEntityAlignment.MIDDLE_CENTER)
    title(msp, ox, oy, 1800, "D1 卫浴门槛防水节点")

    # ---- D2 淋浴玻璃隔断固定节点 ----
    ox += G
    band(msp, ox, oy, 0, 0, 1600, 100, "地砖+防水层(湿区)")
    band(msp, ox, oy, 750, 100, 100, 60, "U型槽/夹件")
    band(msp, ox, oy, 790, 160, 20, 900, "玻璃10mm(钢化)")
    band(msp, ox, oy, 700, 100, 40, 60, "密封胶")
    band(msp, ox, oy, 860, 100, 40, 60, "密封胶")
    add_text(msp, "玻璃固定方式（预埋槽/夹件/胶）待确认；建议贴防爆膜", 90,
             (ox + 800, oy + 1150), TextEntityAlignment.MIDDLE_CENTER)
    title(msp, ox, oy, 1600, "D2 淋浴玻璃隔断固定")

    # ---- D3 台面挡水节点 ----
    ox += G
    band(msp, ox, oy, 0, 0, 300, 800, "墙体/墙砖")
    band(msp, ox, oy, 300, 0, 1100, 40, "台面")
    band(msp, ox, oy, 300, 40, 40, 120, "后挡水条(一体/胶粘 待确认)")
    band(msp, ox, oy, 300, -500, 40, 500, "柜门")
    add_text(msp, "防霉胶收口；挡水高度/一体成型待确认", 90,
             (ox + 700, oy + 400), TextEntityAlignment.MIDDLE_CENTER)
    title(msp, ox, oy, 1400, "D3 台面挡水节点")

    # ---- D4 木地板-瓷砖收边节点 ----
    ox = 0
    oy = -2200
    band(msp, ox, oy, 0, 0, 900, 80, "橡木地板")
    band(msp, ox, oy, 900, 0, 200, 90, "收边条")
    band(msp, ox, oy, 1100, 0, 700, 100, "瓷砖")
    band(msp, ox, oy, 0, -60, 1800, 60, "找平层/楼板")
    add_text(msp, "T型扣条/极窄收口 待确认；两饰面完成面齐平", 90,
             (ox + 900, oy + 350), TextEntityAlignment.MIDDLE_CENTER)
    title(msp, ox, oy, 1800, "D4 木地板-瓷砖收边")

    # ---- D5 通顶衣柜收口节点 ----
    ox += G
    band(msp, ox, oy, 0, 0, 900, 1400, "吊顶(2600)")
    band(msp, ox, oy, 300, 0, 40, 1400, "", layer="A-WALL")
    band(msp, ox, oy, 340, -800, 400, 800, "衣柜顶封板")
    band(msp, ox, oy, 340, -1400, 400, 600, "衣柜柜体")
    add_text(msp, "顶封板与吊顶留缝/打胶 待确认；侧封板同", 90,
             (ox + 700, oy + 1600), TextEntityAlignment.MIDDLE_CENTER)
    title(msp, ox, oy, 1400, "D5 通顶衣柜顶部收口")

    # ---- 图框图签 ----
    x0, y0, x1, y1 = -1500, oy - 2500, 3 * G + 2200, 2200
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                       dxfattribs={"layer": "A-FRAME", "lineweight": 70,
                                   "true_color": colors.rgb2int(BLACK)})
    tx, ty = x1 - 6200, y0
    msp.add_lwpolyline([(tx, ty), (x1, ty), (x1, ty + 2400), (tx, ty + 2400)], close=True,
                       dxfattribs={"layer": "A-FRAME", "true_color": colors.rgb2int(BLACK)})
    for s, hgt, py_ in [
        ("学道街44号室内设计", 300, ty + 2050), ("节点详图（示意）", 240, ty + 1650),
        ("图号 A402   版本 v1", 180, ty + 1250),
        ("常规做法示意，最终以深化设计/现场为准", 150, ty + 900)]:
        add_text(msp, s, hgt, (tx + 250, py_))
    for i, n in enumerate(["· 防水高度、玻璃固定、挡水做法、收边形式、封板留缝全部待确认",
                            "· 详图比例为示意，不以图示量取尺寸"]):
        add_text(msp, n, 150, (x0 + 250, y0 + 200 + i * 400))

    dxf_path = OUT / "A402_节点详图.dxf"
    doc.saveas(dxf_path)
    render_preview(doc, msp, OUT / "A402_节点详图_preview.png", figsize=(16, 10), dpi=150)
    print(dxf_path)
    print(OUT / "A402_节点详图_preview.png")


if __name__ == "__main__":
    main()
