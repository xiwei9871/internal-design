#!/usr/bin/env python3
"""Create the completeness-pass FCStd without changing R2 source objects."""

from __future__ import annotations

from pathlib import Path
import json

import FreeCAD as App
import Part


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
SOURCE = OUT / "S2_CURRENT_DESIGN_V1_R2.FCStd"
CHANGE = OUT / "R2_1_change_log.json"
OUTPUT = OUT / "S2_CURRENT_DESIGN_V1_R2_1.FCStd"
OX, OY = 1298172.0, -296458.0


def wire(bbox):
    x0, y0, x1, y1 = bbox
    points = [App.Vector(x0 + OX, y0 + OY, 0), App.Vector(x1 + OX, y0 + OY, 0), App.Vector(x1 + OX, y1 + OY, 0), App.Vector(x0 + OX, y1 + OY, 0), App.Vector(x0 + OX, y0 + OY, 0)]
    return Part.makePolygon(points)


def main():
    change = json.loads(CHANGE.read_text(encoding="utf-8"))
    doc = App.openDocument(str(SOURCE))
    doc.recompute()
    group = doc.addObject("App::DocumentObjectGroup", "S2_R2_1_COMPLETENESS")
    group.Label = "S2 R2.1 Completeness Candidates (HUMAN REVIEW)"
    conflicts = doc.addObject("App::DocumentObjectGroup", "S2_R2_1_CONFLICTS")
    conflicts.Label = "S2 R2.1 Conflicts / TO_VERIFY"
    for row in change["changes"]:
        obj = doc.addObject("Part::Feature", "R2_1_" + row["id"])
        obj.Label = "R2.1 " + row["source_label"]
        obj.Shape = wire(row["bbox_task01_mm"])
        for type_name, prop, value in [
            ("App::PropertyString", "SemanticId", row["semantic_id"]),
            ("App::PropertyString", "FunctionalZone", row["functional_zone"]),
            ("App::PropertyString", "Status", row["status"]),
            ("App::PropertyString", "Notes", "; ".join(row["notes"])),
        ]:
            obj.addProperty(type_name, prop, "R2.1 completeness")
            setattr(obj, prop, value)
        if row["status"] in {"CONFLICT_REVIEW", "SCHEMATIC_CANDIDATE"}:
            conflicts.addObject(obj)
            if getattr(obj, "ViewObject", None) is not None:
                obj.ViewObject.LineColor = (0.85, 0.0, 0.0)
        else:
            group.addObject(obj)
            if getattr(obj, "ViewObject", None) is not None:
                obj.ViewObject.LineColor = (0.85, 0.45, 0.0)
        if getattr(obj, "ViewObject", None) is not None:
            obj.ViewObject.LineWidth = 2.0
    doc.recompute()
    doc.saveAs(str(OUTPUT))
    print(json.dumps({"status": "PASS", "output": str(OUTPUT), "candidate_objects": len(group.Group), "conflicts": len(conflicts.Group)}))


if __name__ == "__main__":
    main()
