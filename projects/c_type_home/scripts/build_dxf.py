"""Build C型_原始户型数字化基准图.dxf from data/geometry.json.

mm units, modelspace 1:1. Uncertain (LOW confidence) geometry is drawn on
A-UNCERTAIN so it is visually distinct from confirmed data.
"""
import ezdxf
from ezdxf import colors
from geo_common import (
    PROJECT_ROOT, load_geometry, load_dimensions, wall_polygon_mm,
    opening_world_rect, ORIGIN_PX, MM_PER_PX_X,
)

OUT = PROJECT_ROOT / "cad" / "C型_原始户型数字化基准图.dxf"

LAYER_CONF = {"HIGH": "normal", "MEDIUM": "normal", "LOW": "uncertain",
              "UNKNOWN": "uncertain"}


def rect_pts(r):
    x1, y1, x2, y2 = r
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def layer_for(entity_layer, conf):
    return "A-UNCERTAIN" if LAYER_CONF.get(conf) == "uncertain" else entity_layer


def add_rect(msp, rect, layer):
    msp.add_lwpolyline(rect_pts(rect), close=True, dxfattribs={"layer": layer})


def build():
    geo = load_geometry()
    dims = load_dimensions()
    doc = ezdxf.new("R2018")
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4  # millimetres
    doc.header["$LTSCALE"] = 200.0

    for name, col in [("A-WALL", 7), ("A-DOOR", 3), ("A-WINDOW", 4),
                      ("A-COLUMN", 8), ("A-SHAFT", 6), ("A-ROOM", 2),
                      ("A-DIMS", 1), ("A-TEXT", 7), ("A-UNCERTAIN", 9),
                      ("A-SOURCE-REF", 5)]:
        doc.layers.add(name, color=col)
    doc.layers.get("A-UNCERTAIN").dxf.linetype = "DASHED" if "DASHED" in doc.linetypes else "CONTINUOUS"

    msp = doc.modelspace()

    # walls: full rect on A-WALL, opening rects hatched-free on A-DOOR/A-WINDOW
    wall_by_id = {w["id"]: w for w in geo["walls"]}
    for w in geo["walls"]:
        add_rect(msp, w["rect_mm"], layer_for("A-WALL", w.get("confidence")))
        msp.add_text(
            w["id"], height=80, dxfattribs={"layer": "A-SOURCE-REF"}
        ).set_placement((w["rect_mm"][0], w["rect_mm"][1] - 120))

    for col in geo.get("columns", []):
        add_rect(msp, col["rect_mm"], layer_for("A-COLUMN", col.get("confidence")))

    for bay in geo.get("ac_bays", []):
        add_rect(msp, bay["rect_mm"], layer_for("A-SHAFT", bay.get("confidence")))

    for kind, layer in (("doors", "A-DOOR"), ("windows", "A-WINDOW")):
        for op in geo.get(kind, []):
            host = wall_by_id.get(op.get("host_wall_id"))
            if host is None:
                continue
            rect = opening_world_rect(op, host)
            add_rect(msp, rect, layer_for(layer, op.get("confidence")))
            cx = (rect[0] + rect[2]) / 2
            cy = (rect[1] + rect[3]) / 2
            msp.add_text(
                op["id"], height=90, dxfattribs={"layer": "A-SOURCE-REF"}
            ).set_placement((cx, cy))

    for sp in geo.get("spaces", []):
        layer = layer_for("A-ROOM", sp.get("confidence"))
        msp.add_lwpolyline(sp["polygon_mm"], close=True,
                           dxfattribs={"layer": layer})
        xs = [p[0] for p in sp["polygon_mm"]]
        ys = [p[1] for p in sp["polygon_mm"]]
        msp.add_text(
            sp["name_zh"], height=300, dxfattribs={"layer": "A-TEXT"}
        ).set_placement(((min(xs) + max(xs)) / 2 - 300, (min(ys) + max(ys)) / 2))

    # source dimension chains redrawn as simple dimension geometry (lines+text)
    for ch in dims["chains"]:
        if ch.get("orientation") != "horizontal" or "tick_px_x" not in ch:
            continue
        y_line = 15600 if ch["dimension_line_px_y"] < 500 else -2400
        ticks = [(86.5 + 0, None)]
        xs = []
        for t in ch["tick_px_x"]:
            xs.append((t - ORIGIN_PX[0]) * MM_PER_PX_X)
        for i, x in enumerate(xs):
            msp.add_line((x, y_line - 300), (x, y_line + 300),
                         dxfattribs={"layer": "A-DIMS"})
        for a, b in zip(xs, xs[1:]):
            msp.add_line((a, y_line), (b, y_line), dxfattribs={"layer": "A-DIMS"})
        for i, v in enumerate(ch["segment_values_mm"]):
            if v is None:
                continue
            msp.add_text(
                str(v), height=180, dxfattribs={"layer": "A-DIMS"}
            ).set_placement(((xs[i] + xs[i + 1]) / 2 - 200, y_line + 350))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(OUT)
    print(f"DXF written: {OUT}")


if __name__ == "__main__":
    build()
