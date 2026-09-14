"""A101 平面布置图：从 A7 锁定几何生成 DXF + PNG 预览。"""
from __future__ import annotations

from cad_common import (OUT, draw_doors, draw_furniture, draw_frame_and_title,
                        draw_overall_dims, draw_room_labels, draw_walls,
                        draw_windows, new_doc, render_preview)


def main() -> None:
    doc = new_doc()
    msp = doc.modelspace()

    draw_walls(msp)
    draw_windows(msp)
    draw_doors(msp)
    draw_furniture(msp, labels=True)
    draw_room_labels(msp)
    draw_overall_dims(msp)
    draw_frame_and_title(msp, "平面布置图（家具/洁具/设备定位）", "A101",
                         notes=["未含：机电点位/天花/立面（另图）"])

    dxf_path = OUT / "A101_平面布置图.dxf"
    doc.saveas(dxf_path)
    render_preview(doc, msp, OUT / "A101_平面布置图_preview.png")
    print(dxf_path)
    print(OUT / "A101_平面布置图_preview.png")


if __name__ == "__main__":
    main()
