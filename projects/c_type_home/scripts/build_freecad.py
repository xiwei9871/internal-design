"""Build C型_原始户型数字化基准模型.FCStd from data/geometry.json.

Run under FreeCAD console:
    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd build_freecad.py

All objects are extruded with visualization_only_height_mm (2800) which is
NOT SOURCE DATA — the plan carries no storey height. Custom properties keep
provenance on every object: DesignID, SourceBasis, Confidence,
NeedsFieldVerification.
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import PROJECT_ROOT, load_geometry, wall_polygon_mm  # noqa: E402

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

OUT = PROJECT_ROOT / "cad" / "C型_原始户型数字化基准模型.FCStd"
VIS_H = 2800.0  # visualization_only_height_mm — NOT SOURCE DATA


def prism(rect, h):
    x1, y1, x2, y2 = rect
    pts = [App.Vector(x1, y1, 0), App.Vector(x2, y1, 0),
           App.Vector(x2, y2, 0), App.Vector(x1, y2, 0)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(
        App.Vector(0, 0, h))


def add_obj(doc, oid, label, rect, basis, conf, needs_fv):
    ob = doc.addObject("Part::Feature", oid.replace("-", "_"))
    ob.Label = label
    ob.Shape = prism(rect, VIS_H)
    ob.addProperty("App::PropertyString", "DesignID", "Design")
    ob.DesignID = oid
    ob.addProperty("App::PropertyString", "SourceBasis", "Design")
    ob.SourceBasis = basis
    ob.addProperty("App::PropertyString", "Confidence", "Design")
    ob.Confidence = conf
    ob.addProperty("App::PropertyBool", "NeedsFieldVerification", "Design")
    ob.NeedsFieldVerification = bool(needs_fv)
    return ob


def main():
    geo = load_geometry()
    doc = App.newDocument("CType_SourcePlanReconstruction")
    for w in geo["walls"]:
        add_obj(doc, w["id"], w.get("note", w["id"]), w["rect_mm"],
                w.get("provenance", "unknown"), w.get("confidence", "UNKNOWN"),
                w.get("needs_field_verification", True))
    for c in geo.get("columns", []):
        add_obj(doc, c["id"], c.get("note", c["id"]), c["rect_mm"],
                c.get("provenance", "pixel_scaled"),
                c.get("confidence", "LOW"), True)
    doc.recompute()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.saveAs(str(OUT))
    print("FCStd written:", OUT)


main()
