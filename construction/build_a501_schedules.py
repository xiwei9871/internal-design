"""A501 门窗表 + 主要材料表：洞口尺寸由 A7 锁定几何换算，做法/型号待确认。"""
from __future__ import annotations

import math

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

from cad_common import (BLACK, DATA, MM, OUT, add_text, new_doc, render_preview)


def table(msp, ox, oy, col_ws, rows, row_h=330, text_h=105):
    """ox,oy 为表左上；rows[0] 为表头。"""
    w, h = sum(col_ws), row_h * len(rows)
    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy - h), (ox, oy - h)],
                       close=True, dxfattribs={"layer": "A-FRAME",
                                               "true_color": colors.rgb2int(BLACK)})
    for i in range(1, len(rows)):
        msp.add_line((ox, oy - i * row_h), (ox + w, oy - i * row_h),
                     dxfattribs={"layer": "A-FRAME"})
    x = ox
    for cw in col_ws[:-1]:
        x += cw
        msp.add_line((x, oy), (x, oy - h), dxfattribs={"layer": "A-FRAME"})
    for ri, row in enumerate(rows):
        cy = oy - ri * row_h - row_h / 2
        x = ox
        for ci, cell in enumerate(row):
            add_text(msp, str(cell), text_h if ri else text_h + 15,
                     (x + col_ws[ci] / 2, cy), TextEntityAlignment.MIDDLE_CENTER)
            x += col_ws[ci]
    return oy - h


def door_rows():
    rows = [["编号", "位置", "参考宽mm", "形式", "备注"]]
    for i,d in enumerate(DATA['doors'],1):
        sliding = d['type']=='pocket_sliding'
        rows.append([f'D{i}',d['name'],f"{d['opening_reference_mm']:.0f}",
            '暗藏推拉门' if sliding else '平开门',
            '洞口/暗藏侧待复核' if sliding else '结构洞口/门套待现场复尺'])
    return rows


def main() -> None:
    doc = new_doc()
    msp = doc.modelspace()
    add_text(msp, "门表（参考跨距非结构洞口；H2100假设待确认）", 180, (0, 600))
    y = table(msp, 0, 0, [700, 1600, 1100, 2200, 3400], door_rows())

    # ---- 窗表 ----
    win_rows = [["编号", "位置", "参考宽mm", "备注"]]
    for i, w in enumerate(DATA["windows"], 1):
        s = w["segment"]
        width = math.dist(s[:2], s[2:]) * MM
        win_rows.append([f"W{i}", w["name"], f"{width:.0f}", "原窗保留；高度/型材待确认"])
    add_text(msp, "窗表", 180, (0, y - 900))
    y = table(msp, 0, y - 1400, [700, 1600, 1100, 5000], win_rows)

    # ---- 材料表（右列）----
    mat_rows = [
        ["部位", "材料", "备注"],
        ["地面·干区", "橡木复合地板(白蜡木色系)", "规格/铺法待确认"],
        ["地面·厨房", "暖灰瓷砖", "规格/排版待确认"],
        ["地面·卫浴", "暖灰防滑砖+防水", "翻边高度待确认"],
        ["墙面", "乳胶漆", "色号待确认"],
        ["墙面·厨卫", "墙砖", "规格待确认"],
        ["天花·干区", "石膏板平吊+乳胶漆 H2600", "见A301"],
        ["天花·厨卫", "铝扣板 H2400", "规格待确认"],
        ["柜体/门", "哑光木饰面(白蜡木色系)", "门板形式待确认"],
        ["洁具", "智能马桶×2/台盆×2/浴缸1500×700", "品牌型号待确认"],
        ["设备", "多联机内机×4/洗烘/蒸烤/冰箱", "型号待确认"],
        ["五金", "门锁/合页/地漏/挂件", "待确认"],
    ]
    add_text(msp, "主要材料表", 180, (10500, 600))
    table(msp, 10500, 0, [1900, 4600, 3100], mat_rows)

    from cad_common import draw_frame_and_title
    draw_frame_and_title(msp, '门窗及材料表', 'A501', ['参考宽度来自A7线段，不代表结构洞口尺寸。', '门套/暗藏门口袋方向、窗高与全部产品选型待确认。'])

    dxf_path = OUT / "A501_门窗材料表.dxf"
    doc.saveas(dxf_path)
    render_preview(doc, msp, OUT / "A501_门窗材料表_preview.png", figsize=(18, 12), dpi=150)
    print(dxf_path)
    print(OUT / "A501_门窗材料表_preview.png")


if __name__ == "__main__":
    main()
