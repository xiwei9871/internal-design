"""Build C型_原始户型数字化基准模型.FCStd from data/geometry.json.

Run under FreeCAD console:
    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd build_freecad.py

Walls are extruded with visualization_only_height_mm (2800) — NOT SOURCE
DATA, the plan carries no storey height. Door/window openings are cut out of
their host walls with real boolean ops, and each opening gets a leaf/panel
object preserving provenance properties:
DesignID, SourceBasis, Confidence, NeedsFieldVerification, HostWallID.
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import (  # noqa: E402
    PROJECT_ROOT, load_geometry, wall_axis, opening_world_rect)

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

OUT = PROJECT_ROOT / "cad" / "C型_原始户型数字化基准模型.FCStd"
VIS_H = 2800.0          # visualization_only_height_mm — NOT SOURCE DATA
DOOR_H = 2100.0         # visualization only — NOT SOURCE DATA
WIN_SILL = 900.0        # visualization only — NOT SOURCE DATA
WIN_H = 1500.0          # visualization only — NOT SOURCE DATA


def prism(rect, z0, h):
    x1, y1, x2, y2 = rect
    return Part.makeBox(x2 - x1, y2 - y1, h,
                        App.Vector(x1, y1, z0))


def set_props(ob, oid, basis, conf, needs_fv, host=None):
    ob.addProperty("App::PropertyString", "DesignID", "Design")
    ob.DesignID = oid
    ob.addProperty("App::PropertyString", "SourceBasis", "Design")
    ob.SourceBasis = basis
    ob.addProperty("App::PropertyString", "Confidence", "Design")
    ob.Confidence = conf
    ob.addProperty("App::PropertyBool", "NeedsFieldVerification", "Design")
    ob.NeedsFieldVerification = bool(needs_fv)
    if host is not None:
        ob.addProperty("App::PropertyString", "HostWallID", "Design")
        ob.HostWallID = host


def add_shape(doc, oid, label, shape, basis, conf, needs_fv, host=None):
    ob = doc.addObject("Part::Feature", oid.replace("-", "_"))
    ob.Label = label
    ob.Shape = shape
    set_props(ob, oid, basis, conf, needs_fv, host)
    return ob


def main():
    geo = load_geometry()
    doc = App.newDocument("CType_SourcePlanReconstruction")

    wall_by_id = {w["id"]: w for w in geo["walls"]}
    # openings grouped by host wall
    openings_by_host = {}
    for kind in ("doors", "windows"):
        for op in geo[kind]:
            openings_by_host.setdefault(op.get("host_wall_id"), []).append(
                (kind, op))

    for w in geo["walls"]:
        x1, y1, x2, y2 = w["rect_mm"]
        shape = prism(w["rect_mm"], 0, VIS_H)
        for kind, op in openings_by_host.get(w["id"], []):
            ox1, oy1, ox2, oy2 = opening_world_rect(op, w)
            # opening cut: full wall height; widen slightly so faces cut clean
            cut_h = DOOR_H if kind == "doors" else WIN_H
            z0 = 0.0 if kind == "doors" else WIN_SILL
            cutter = prism((ox1 - 1, oy1 - 1, ox2 + 1, oy2 + 1), z0, cut_h)
            try:
                shape = shape.cut(cutter)
            except Exception as e:
                print("cut failed", w["id"], op["id"], e)
        add_shape(doc, w["id"], w.get("note", w["id"])[:60], shape,
                  w.get("provenance", "unknown"),
                  w.get("confidence", "UNKNOWN"),
                  w.get("needs_field_verification", True))

    for c in geo.get("columns", []):
        add_shape(doc, c["id"], c.get("note", c["id"])[:60],
                  prism(c["rect_mm"], 0, VIS_H),
                  c.get("provenance", "pixel_scaled"),
                  c.get("confidence", "LOW"), True)

    # door leaf / window panel objects inside their openings
    for kind in ("doors", "windows"):
        leaf_t = 40.0
        for op in geo[kind]:
            host = wall_by_id.get(op.get("host_wall_id"))
            if host is None:
                continue
            rect = opening_world_rect(op, host)
            if wall_axis(host) == "H":
                cy = (rect[1] + rect[3]) / 2
                lrect = (rect[0], cy - leaf_t / 2, rect[2], cy + leaf_t / 2)
            else:
                cx = (rect[0] + rect[2]) / 2
                lrect = (cx - leaf_t / 2, rect[1], cx + leaf_t / 2, rect[3])
            h = DOOR_H if kind == "doors" else WIN_H
            z0 = 0.0 if kind == "doors" else WIN_SILL
            add_shape(doc, op["id"], op.get("label", op["id"]),
                      prism(lrect, z0, h),
                      op.get("provenance", "pixel_scaled"),
                      op.get("confidence", "UNKNOWN"),
                      op.get("needs_field_verification", True),
                      host=op.get("host_wall_id"))

    doc.recompute()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.saveAs(str(OUT))
    n = len(doc.Objects)
    print(f"FCStd written: {OUT} ({n} objects)")


main()
