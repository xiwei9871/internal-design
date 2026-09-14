"""A302 电气点位图：插座/开关/网口/配电箱 常规布置第一版，待业主逐点确认。

点位以源像素坐标登记（同底模标定），标注高度为底边距完成面 mm。
常规依据：床头 H700、台面/书桌 H900、普通 H300、厨卫台面 H1200、
智能马桶/冰箱 H500、洗烘 H1300、开关/线控 H1300、强电箱 H1800。
"""
from __future__ import annotations

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

from cad_common import (BLACK, OUT, add_text, draw_doors, draw_furniture,
                        draw_frame_and_title, draw_overall_dims,
                        draw_room_labels, draw_walls, draw_windows, m,
                        new_doc, render_preview)

# (px, py, 标注, 类型)  类型: sock=插座方框 sw=开关圆 panel=配电箱
POINTS = [
    # 玄关/过道
    (1140, 668, "强电箱 H1800", "panel"),
    (1080, 668, "弱电箱 H300", "panel"),
    (980, 660, "过道备用 H300", "sock"),
    # 服务墙（过道侧，插座藏柜后）
    (640, 368, "冰箱16A H500", "sock"),
    (640, 448, "蒸烤16A×2 H500/1300", "sock"),
    (640, 518, "洗烘16A×2 H1300", "sock"),
    # 客厅
    (778, 1200, "TV位 插座×3+网口+TV H350", "sock"),
    (1060, 1030, "边几 H300", "sock"),
    (1125, 1290, "沙发侧 H300", "sock"),
    # 餐区
    (795, 1015, "餐边柜 台面×2 H1100", "sock"),
    (795, 860, "餐边高柜 H300", "sock"),
    # 厨房（台面沿北墙）
    (480, 163, "台面插座×3 H1200", "sock"),
    (640, 163, "台面插座×2 H1200", "sock"),
    (745, 163, "烟机 H2100", "sock"),
    (425, 295, "水槽下×2 H500(净水/洗碗预留)", "sock"),
    # 主卧
    (757, 940, "床头五孔×2+USB H700", "sock"),
    (757, 1070, "床头五孔×2+USB H700", "sock"),
    (545, 1260, "梳妆/阅读台 ×2 H900", "sock"),
    (700, 1168, "镜前 H900", "sock"),
    # 衣帽区
    (340, 1096, "挂烫/熨斗 H1100", "sock"),
    # 老人房
    (1150, 425, "床头五孔×2 H700", "sock"),
    (1150, 550, "床头五孔×2 H700", "sock"),
    (1050, 620, "矮柜 插座×2+网口 H350", "sock"),
    # 儿童房 + 窗边区
    (1448, 960, "床头五孔×2 H700", "sock"),
    (1448, 1045, "床头五孔×2 H700", "sock"),
    (1250, 1245, "书桌×3+网口 H900", "sock"),
    # 次卫（防水溅盒）
    (420, 525, "智能马桶16A H400", "sock"),
    (488, 578, "台盆防水 H1300", "sock"),
    # 主卫
    (300, 748, "智能马桶16A H400", "sock"),
    (285, 795, "台盆防水 H1300", "sock"),
    (395, 700, "电热毛巾架 H1300 待确认", "sock"),
    # 开关/线控（门内侧 H1300）
    (1130, 695, "玄关开关(客餐厅双控)", "sw"),
    (815, 645, "老人房开关+线控", "sw"),
    (1170, 805, "儿童房开关+线控", "sw"),
    (738, 795, "主卧开关+线控", "sw"),
    (415, 1072, "衣帽区开关", "sw"),
    (392, 830, "主卫开关", "sw"),
    (572, 648, "次卫开关", "sw"),
    (590, 318, "厨房开关", "sw"),
    (705, 795, "过道双控B", "sw"),
]


def draw_point(msp, px, py, label, kind):
    x, y = m(px, py)
    if kind == "panel":
        msp.add_lwpolyline([(x - 90, y - 120), (x + 90, y - 120),
                            (x + 90, y + 120), (x - 90, y + 120)], close=True,
                           dxfattribs={"layer": "A-ELEC", "lineweight": 35})
        msp.add_line((x - 90, y - 120), (x + 90, y + 120), dxfattribs={"layer": "A-ELEC"})
        msp.add_line((x - 90, y + 120), (x + 90, y - 120), dxfattribs={"layer": "A-ELEC"})
    elif kind == "sw":
        msp.add_circle((x, y), 70, dxfattribs={"layer": "A-ELEC", "lineweight": 35})
        add_text(msp, "S", 80, (x, y), TextEntityAlignment.MIDDLE_CENTER, layer="A-ELEC")
    else:
        s = 60
        msp.add_lwpolyline([(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)],
                           close=True, dxfattribs={"layer": "A-ELEC", "lineweight": 35})
        msp.add_line((x - s, y), (x + s, y), dxfattribs={"layer": "A-ELEC"})
    if px > 1100:  # 东墙点附近标注放左侧，避免溢出外墙
        add_text(msp, label, 85, (x - 110, y - 40), TextEntityAlignment.RIGHT, layer="A-ELEC")
    else:
        add_text(msp, label, 85, (x + 110, y - 40), TextEntityAlignment.LEFT, layer="A-ELEC")


def main() -> None:
    doc = new_doc()
    msp = doc.modelspace()

    draw_walls(msp)
    draw_windows(msp)
    draw_doors(msp)
    draw_furniture(msp, labels=False)  # 家具轮廓作定位参照，不写名字避免拥挤
    draw_room_labels(msp, height=170)
    for px, py, label, kind in POINTS:
        draw_point(msp, px, py, label, kind)
    draw_overall_dims(msp)
    draw_frame_and_title(msp, "电气点位图（插座/开关/配电箱）", "A302",
                         notes=["· 常规布置第一版，全部点位待业主逐点确认",
                                "· 高度=底边距完成面；厨卫插座均带防溅盒",
                                "· 16A：冰箱/蒸烤/洗烘/智能马桶；浴霸/暖风属天花回路见A301",
                                "· 网口建议全屋六类线汇聚弱电箱；具体回路划分待深化"])

    dxf_path = OUT / "A302_电气点位图.dxf"
    doc.saveas(dxf_path)
    render_preview(doc, msp, OUT / "A302_电气点位图_preview.png")
    print(dxf_path)
    print(OUT / "A302_电气点位图_preview.png")


if __name__ == "__main__":
    main()
