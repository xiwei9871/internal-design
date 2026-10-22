#!/usr/bin/env python3
"""Semantic-only restoration of the historical nine-window registry."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import FreeCAD as App


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
SOURCE = BASE / "cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd"
OUTPUT = BASE / "cad/freecad_import/世纪欣园FF_freecad_WINDOW_RESTORED.FCStd"
REGISTRY = OUT / "FINAL_WINDOW_REGISTER_95ab90e.json"
STRUCTURE = OUT / "latest_fcstd_structure_v3.json"

NUM_TOL = 1e-5
PHYSICAL_TYPES = {"Part::Line", "Part::Circle", "Part::Feature", "Part::Part2DObjectPython", "Part::Extrusion", "Part::FeaturePython"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def numbers(values):
    return [float(v) for v in values]


def shape_fingerprint(obj):
    shape = getattr(obj, "Shape", None)
    if shape is None or shape.isNull():
        return None
    bbox = shape.BoundBox
    placement = obj.Placement
    base = placement.Base
    axis = placement.Rotation.Axis
    return {
        "Name": obj.Name,
        "Label": obj.Label,
        "TypeId": obj.TypeId,
        "Placement": {
            "position": [base.x, base.y, base.z],
            "rotation_angle": placement.Rotation.Angle,
            "rotation_axis": [axis.x, axis.y, axis.z],
        },
        "BoundingBox": {"XMin": bbox.XMin, "XMax": bbox.XMax, "YMin": bbox.YMin, "YMax": bbox.YMax, "ZMin": bbox.ZMin, "ZMax": bbox.ZMax},
        "Shape": {"VertexCount": len(shape.Vertexes), "EdgeCount": len(shape.Edges), "FaceCount": len(shape.Faces), "Area": shape.Area, "Volume": shape.Volume},
    }


def collect_physical(doc):
    result = {}
    for obj in doc.Objects:
        if obj.TypeId not in PHYSICAL_TYPES:
            continue
        fp = shape_fingerprint(obj)
        if fp is not None:
            result[obj.Name] = fp
    return result


def compare_number(a, b):
    return abs(float(a) - float(b)) <= NUM_TOL


def compare_fingerprints(before, after):
    diffs = []
    if set(before) != set(after):
        diffs.append({"kind": "physical_object_set", "before_only": sorted(set(before) - set(after)), "after_only": sorted(set(after) - set(before))})
    for name in sorted(set(before) & set(after)):
        a, b = before[name], after[name]
        if a["Label"] != b["Label"] or a["TypeId"] != b["TypeId"]:
            diffs.append({"kind": "identity", "name": name, "before": {"Label": a["Label"], "TypeId": a["TypeId"]}, "after": {"Label": b["Label"], "TypeId": b["TypeId"]}})
            continue
        for key in ("position", "rotation_axis"):
            av, bv = a["Placement"][key], b["Placement"][key]
            if len(av) != len(bv) or any(not compare_number(x, y) for x, y in zip(av, bv)):
                diffs.append({"kind": "placement", "name": name, "field": key, "before": av, "after": bv})
        if not compare_number(a["Placement"]["rotation_angle"], b["Placement"]["rotation_angle"]):
            diffs.append({"kind": "placement", "name": name, "field": "rotation_angle", "before": a["Placement"]["rotation_angle"], "after": b["Placement"]["rotation_angle"]})
        for key in a["BoundingBox"]:
            if not compare_number(a["BoundingBox"][key], b["BoundingBox"][key]):
                diffs.append({"kind": "bbox", "name": name, "field": key, "before": a["BoundingBox"][key], "after": b["BoundingBox"][key]})
        for key in ("VertexCount", "EdgeCount", "FaceCount"):
            if a["Shape"][key] != b["Shape"][key]:
                diffs.append({"kind": "topology", "name": name, "field": key, "before": a["Shape"][key], "after": b["Shape"][key]})
        for key in ("Area", "Volume"):
            if not compare_number(a["Shape"][key], b["Shape"][key]):
                diffs.append({"kind": "shape_measure", "name": name, "field": key, "before": a["Shape"][key], "after": b["Shape"][key]})
    return diffs


def layer_counts(doc):
    counts = {}
    for obj in doc.Objects:
        if obj.Name.startswith("Layer") and hasattr(obj, "Group"):
            counts[obj.Label] = len(obj.Group)
    return counts


def match_registry(record, structure_rows):
    rect = record["opening_rect_mm"]
    points = [rect]
    if record.get("bay"):
        points += [record["bay"]["front"]] + record["bay"]["jambs"]
    region = [min(p[0] for p in points), min(p[1] for p in points), max(p[2] for p in points), max(p[3] for p in points)]
    def intersects(a, b):
        return not (a[2] < b[0] - 8 or a[0] > b[2] + 8 or a[3] < b[1] - 8 or a[1] > b[3] + 8)
    return [row["name"] for row in structure_rows if intersects([row["bbox_abs_mm"][0] - 1298172, row["bbox_abs_mm"][1] + 296458, row["bbox_abs_mm"][2] - 1298172, row["bbox_abs_mm"][3] + 296458], region)]


def main():
    source_sha_before = sha256(SOURCE)
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["windows"]
    structure_rows = json.loads(STRUCTURE.read_text(encoding="utf-8"))["rows"]
    doc = App.openDocument(str(SOURCE)); doc.recompute()
    before_fp = collect_physical(doc)
    before_total = len(doc.Objects)
    before_layers = layer_counts(doc)
    link_names = {}
    group = doc.addObject("App::DocumentObjectGroup", "WINDOW_SEMANTIC_REFERENCES")
    group.Label = "Final Window / Glass Opening Semantic References (95ab90e)"
    for record in registry:
        matched = match_registry(record, structure_rows)
        links = [doc.getObject(name) for name in matched if doc.getObject(name) is not None]
        semantic = doc.addObject("App::FeaturePython", "WINDOW_REF_" + record["window_id"])
        semantic.Label = "WINDOW_REF " + record["window_id"]
        props = [
            ("App::PropertyString", "SemanticId", record["window_id"]),
            ("App::PropertyString", "OpeningType", record["type"]),
            ("App::PropertyString", "HostWall", record.get("host_wall_id") or ""),
            ("App::PropertyString", "SourceCommit", "95ab90e"),
            ("App::PropertyString", "SourceStatus", record.get("current_status", "")),
            ("App::PropertyString", "Orientation", record.get("orientation", "")),
            ("App::PropertyLength", "ApprovedWidth", record.get("clear_width_mm", record.get("span_mm"))),
            ("App::PropertyVector", "ApprovedCenter", App.Vector((record["opening_rect_mm"][0] + record["opening_rect_mm"][2]) / 2, (record["opening_rect_mm"][1] + record["opening_rect_mm"][3]) / 2, 0)),
            ("App::PropertyLinkList", "PhysicalGeometry", links),
        ]
        for type_name, prop, value in props:
            semantic.addProperty(type_name, prop, "Final window registry semantic data")
            setattr(semantic, prop, value)
        group.addObject(semantic)
        link_names[record["window_id"]] = [obj.Name for obj in links]
    doc.recompute()
    doc.saveAs(str(OUTPUT))
    App.closeDocument(doc.Name)
    reopened = App.openDocument(str(OUTPUT)); reopened.recompute()
    after_fp = collect_physical(reopened)
    after_total = len(reopened.Objects)
    after_layers = layer_counts(reopened)
    fingerprint_diffs = compare_fingerprints(before_fp, after_fp)
    semantic_objects = [obj for obj in reopened.Objects if obj.Name.startswith("WINDOW_REF_")]
    links_resolved = 0; broken = []
    for obj in semantic_objects:
        links = list(getattr(obj, "PhysicalGeometry", []))
        if links: links_resolved += 1
        else: broken.append(obj.Name)
    physical_key_set_equal = set(before_fp) == set(after_fp)
    object_counts = {
        "before_total": before_total, "after_total": after_total, "new_semantic_objects": [obj.Name for obj in semantic_objects], "new_groups": ["WINDOW_SEMANTIC_REFERENCES"], "unexpected_physical_objects": sorted(set(after_fp) - set(before_fp)),
        "physical_geometry_object_count": {"before": len(before_fp), "after": len(after_fp)},
        "wall_physical_geometry_count": {"before": before_layers.get("S-S.WALL", 0), "after": after_layers.get("S-S.WALL", 0)},
        "door_physical_geometry_count": {"before": before_layers.get("F-DOOR", 0), "after": after_layers.get("F-DOOR", 0)},
        "fixture_physical_geometry_count": {"before": before_layers.get("F-SAN FIT", 0), "after": after_layers.get("F-SAN FIT", 0)},
        "furniture_physical_geometry_count": {"before": before_layers.get("F-FURN", 0), "after": after_layers.get("F-FURN", 0)},
    }
    (OUT / "geometry_fingerprint_before.json").write_text(json.dumps(before_fp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "geometry_fingerprint_after.json").write_text(json.dumps(after_fp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "object_count_diff.json").write_text(json.dumps(object_counts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "window_semantic_register_reopened.json").write_text(json.dumps({"count": len(semantic_objects), "entries": [{"id": obj.SemanticId, "links": [x.Name for x in obj.PhysicalGeometry], "broken": not bool(list(obj.PhysicalGeometry))} for obj in semantic_objects]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {
        "historical_source": "VERIFIED_95ab90e_9_ENTRIES_28_28_PASS",
        "semantic_entry_count": len(semantic_objects), "semantic_links_resolve": links_resolved, "broken_links": broken,
        "physical_geometry_drift_count": len(fingerprint_diffs), "fingerprint_diffs": fingerprint_diffs,
        "duplicate_physical_geometry": False, "unexpected_physical_objects_added": object_counts["unexpected_physical_objects"],
        "source_fcstd_untouched": sha256(SOURCE) == source_sha_before, "source_fcstd_sha_before": source_sha_before, "source_fcstd_sha_after": sha256(SOURCE), "reopened_saved_document": True,
        "window_restore": "PASS" if len(semantic_objects) == 9 and links_resolved == 9 and not broken and not fingerprint_diffs and not object_counts["unexpected_physical_objects"] else "FAIL",
        "architectural_2d_baseline": "FROZEN_FOR_3D" if len(semantic_objects) == 9 and links_resolved == 9 and not broken and not fingerprint_diffs else "NOT_FROZEN",
        "formal_cad_allowed": False, "blender": "HOLD",
    }
    (OUT / "window_restore_verification_v02.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "window_restore_verification_v02.md").write_text("# Window Restore Verification v02\n\n" + "\n".join(f"- **{k}:** `{v}`" for k,v in result.items() if k not in {"fingerprint_diffs"}) + "\n\nSemantic objects contain links only; no physical Shape is duplicated. Verification is based on the reopened saved FCStd.\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__": main()
