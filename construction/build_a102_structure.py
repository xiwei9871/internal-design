"""A102 原始结构暨拆改说明图：墙体/门/窗 + 完全无拆改声明。"""
from __future__ import annotations

from cad_common import (OUT, draw_doors, draw_frame_and_title, draw_overall_dims,
                        draw_room_labels, draw_walls, draw_windows, new_doc,
                        render_preview)


def main() -> None:
    doc = new_doc()
    msp = doc.modelspace()

    draw_walls(msp)
    draw_windows(msp)
    draw_doors(msp)
    draw_room_labels(msp)
    draw_overall_dims(msp)
    draw_frame_and_title(msp, "原始结构暨拆改说明图", "A102",
                         notes=["本设计完全无拆改：不拆除任何墙体，不新建墙体，",
                                "门洞/窗洞均维持原状。图示为原始结构确认。"])

    dxf_path = OUT / "A102_原始结构暨拆改说明图.dxf"
    doc.saveas(dxf_path)
    render_preview(doc, msp, OUT / "A102_原始结构暨拆改说明图_preview.png")
    print(dxf_path)
    print(OUT / "A102_原始结构暨拆改说明图_preview.png")


if __name__ == "__main__":
    main()
