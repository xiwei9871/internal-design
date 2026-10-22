#!/usr/bin/env python3
"""Create the R2 review FCStd from the approved guide FCStd."""

import json
from pathlib import Path

import FreeCAD as App
import Part


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
SOURCE = BASE / "cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd"
CHANGE_LOG = OUT / "normalization_change_log_v01.json"
OUTPUT = OUT / "S2_CURRENT_DESIGN_V1_R2.FCStd"
OX, OY = 1298172.0, -296458.0


def make_wire(bbox):
    x0, y0, x1, y1 = bbox
    points = [
        App.Vector(x0 + OX, y0 + OY, 0),
        App.Vector(x1 + OX, y0 + OY, 0),
        App.Vector(x1 + OX, y1 + OY, 0),
        App.Vector(x0 + OX, y1 + OY, 0),
        App.Vector(x0 + OX, y0 + OY, 0),
    ]
    return Part.makePolygon(points)


def add_metadata(obj, row):
    props = [
        ("App::PropertyString", "SourceGuideLabel", row["source_label"]),
        ("App::PropertyString", "SemanticId", row["semantic_id"]),
        ("App::PropertyString", "FunctionalZone", row["functional_zone"] or ""),
        ("App::PropertyString", "AnchorType", row["anchor_type"]),
        ("App::PropertyString", "NormalizationStatus", row["normalization_status"]),
        ("App::PropertyString", "SourceType", row["source_type"]),
        ("App::PropertyString", "Reason", row["reason"]),
        ("App::PropertyDistance", "Dx", row["dx_mm"] or 0.0),
        ("App::PropertyDistance", "Dy", row["dy_mm"] or 0.0),
        ("App::PropertyAngle", "RotationDelta", row["rotation_delta_deg"] or 0.0),
    ]
    for type_name, name, value in props:
        obj.addProperty(type_name, name, "S2 R2 normalization")
        setattr(obj, name, value)


def main():
    change_log = json.loads(CHANGE_LOG.read_text(encoding="utf-8"))
    doc = App.openDocument(str(SOURCE))
    doc.recompute()
    # Hide the original guide furniture in the R2 review document; it remains
    # inside the FCStd for traceability, while the R2 group shows the new size.
    source_names = {row["source_object_name"] for row in change_log["changes"] if row.get("source_object_name")}
    for name in source_names:
        obj = doc.getObject(name)
        if obj is not None and getattr(obj, "ViewObject", None) is not None:
            obj.ViewObject.Visibility = False
    group = doc.addObject("App::DocumentObjectGroup", "S2_R2_NORMALIZED_FURNITURE")
    group.Label = "S2 R2 Normalized Furniture (HUMAN REVIEW)"
    conflicts = doc.addObject("App::DocumentObjectGroup", "S2_R2_CONFLICTS")
    conflicts.Label = "S2 R2 Conflicts / Human Review"
    for row in change_log["changes"]:
        bbox = row.get("normalized_bbox_task01_mm")
        if not bbox:
            continue
        obj = doc.addObject("Part::Feature", "R2_" + row["semantic_id"] + "_" + str(len(group.Group)))
        obj.Label = "R2 " + row["semantic_id"] + " | " + row["source_label"]
        obj.Shape = make_wire(bbox)
        add_metadata(obj, row)
        if row["normalization_status"] in {"CONFLICT", "HUMAN_REVIEW_REQUIRED"}:
            conflicts.addObject(obj)
            if getattr(obj, "ViewObject", None) is not None:
                obj.ViewObject.LineColor = (0.85, 0.0, 0.0)
                obj.ViewObject.PointColor = (0.85, 0.0, 0.0)
        else:
            group.addObject(obj)
            if getattr(obj, "ViewObject", None) is not None:
                obj.ViewObject.LineColor = (0.1, 0.25, 0.75)
                obj.ViewObject.PointColor = (0.1, 0.25, 0.75)
        if getattr(obj, "ViewObject", None) is not None:
            obj.ViewObject.LineWidth = 2.0
    doc.recompute()
    doc.saveAs(str(OUTPUT))
    print(json.dumps({"status": "PASS", "output": str(OUTPUT), "normalized_objects": len(group.Group), "conflict_objects": len(conflicts.Group)}))


if __name__ == "__main__":
    main()
