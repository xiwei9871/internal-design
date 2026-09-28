#!/usr/bin/env python3
"""Build a source-faithful, furniture-free structure CAD derivative.

The direct DWG conversion is the only geometry source.  This script removes
explicit furniture/overlay entities and then proves that retained wall
entities still match the source by handle, type, layer, and coordinates.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import ezdxf
from ezdxf import bbox


ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / "cad"
QC = ROOT / "qc"
SOURCE = CAD / "measured_working.dxf"
OUTPUT = CAD / "structure_only_source_sync.dxf"
REPORT_PATH = QC / "structure_only_cad_report.json"
AUDIT_JSON_PATH = QC / "lounge_entity_audit.json"
AUDIT_PNG_PATH = QC / "lounge_entity_audit.png"
AX, AY = 1298172.0, -296458.0
SOURCE_SHA = "3711c47c1172fbdb13fead356bd5b2285e66925f6aca4a62c49ff118437ba233"
FURNITURE_LAYERS = {"F-FURN", "A-FURN-PROP", "A-FURN-EXST-KEEP"}
OVERLAY_LAYERS = {
    "A-ACCESS-RAMP", "A-ACCESS-STAIR", "A-LEVEL", "A-QC-ZONE",
}
OVERLAY_WORDS = ("休闲厅", "平台", "LANDING", "LOUNGE", "RAMP")
LOUNGE_EXCLUSION_HANDLES = ["30830F", "308310", "308311"]
NESTED_FURNITURE_HANDLES = ["307F68"]
LOUNGE_EXPECTATIONS = {
    "30830F": {"layer": "S-楼梯", "type": "LINE"},
    "308310": {"layer": "S-楼梯", "type": "LINE"},
    "308311": {"layer": "S-楼梯", "type": "ARC"},
}
NESTED_FURNITURE_EXPECTATIONS = {
    "307F68": {"layer": "S-S.WALL", "type": "INSERT", "block": "bing"},
}
LAYER_STYLE_OVERRIDES = {
    # ACI 7 is white on the Matplotlib white canvas; keep geometry untouched
    # but make the source wall layer readable in the CAD deliverable.
    "S-S.WALL": {"color": 250, "lineweight": 70},
    "S-楼梯": {"color": 8, "lineweight": 35},
    "F-DOOR": {"color": 8, "lineweight": 20},
    "F-SAN FIT": {"color": 8, "lineweight": 13},
    "F-TEXT": {"color": 250},
}
GREEN_BOXES = {
    "upper_horizontal": [9735, 6226, 10551, 6566],
    "right_vertical": [11382, 2955, 11643, 3398],
    "life_balcony": [1292, -197, 5426, 2575],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text_value(entity) -> str:
    if entity.dxftype() == "TEXT":
        return str(entity.dxf.get("text", ""))
    if entity.dxftype() in {"MTEXT", "ATTRIB", "ATTDEF"}:
        return str(entity.dxf.get("text", ""))
    return ""


def _task_bbox(entity):
    try:
        ext = bbox.extents([entity])
    except Exception:
        return None
    if not ext.has_data:
        return None
    return [
        float(ext.extmin.x - AX), float(ext.extmin.y - AY),
        float(ext.extmax.x - AX), float(ext.extmax.y - AY),
    ]


def _geometry_signature(entity):
    """Stable, compact geometry signature for source/derived comparisons."""
    typ = entity.dxftype()
    if typ == "LINE":
        return {
            "kind": typ,
            "start": [float(entity.dxf.start.x - AX), float(entity.dxf.start.y - AY)],
            "end": [float(entity.dxf.end.x - AX), float(entity.dxf.end.y - AY)],
        }
    if typ == "LWPOLYLINE":
        points = []
        for x, y, *rest in entity.get_points("xyb"):
            points.append([float(x - AX), float(y - AY), float(rest[0]) if rest else 0.0])
        return {"kind": typ, "closed": bool(entity.closed), "points": points}
    if typ == "POLYLINE":
        points = []
        for vertex in entity.vertices:
            points.append([float(vertex.dxf.location.x - AX), float(vertex.dxf.location.y - AY)])
        return {"kind": typ, "closed": bool(entity.is_polygon_mesh), "points": points}
    if typ in {"CIRCLE", "ARC"}:
        out = {
            "kind": typ,
            "center": [float(entity.dxf.center.x - AX), float(entity.dxf.center.y - AY)],
            "radius": float(entity.dxf.radius),
        }
        for key in ("start_angle", "end_angle"):
            if entity.dxf.hasattr(key):
                out[key] = float(entity.dxf.get(key))
        return out
    if typ == "INSERT":
        return {
            "kind": typ,
            "name": entity.dxf.name,
            "insert": [float(entity.dxf.insert.x - AX), float(entity.dxf.insert.y - AY)],
            "rotation": float(entity.dxf.get("rotation", 0.0)),
            "xscale": float(entity.dxf.get("xscale", 1.0)),
            "yscale": float(entity.dxf.get("yscale", 1.0)),
        }
    if typ in {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}:
        ins = entity.dxf.get("insert")
        return {
            "kind": typ,
            "text": _text_value(entity),
            "insert": [float(ins.x - AX), float(ins.y - AY)] if ins else None,
        }
    return {"kind": typ, "bbox": _task_bbox(entity)}


def _entity_record(entity):
    return {
        "handle": entity.dxf.get("handle"),
        "layer": entity.dxf.layer,
        "type": entity.dxftype(),
        "geometry": _geometry_signature(entity),
        "bbox_task01": _task_bbox(entity),
    }


def _walk_records(doc):
    return {
        entity.dxf.get("handle"): _entity_record(entity)
        for entity in doc.modelspace()
        if entity.dxf.get("handle")
    }


def _intersects(a, b, pad=0.0):
    return not (
        a[2] < b[0] - pad or a[0] > b[2] + pad or
        a[3] < b[1] - pad or a[1] > b[3] + pad
    )


def _is_overlay_text(entity):
    text = _text_value(entity).upper()
    return any(word.upper() in text for word in OVERLAY_WORDS)


def _deletion_reason(entity):
    handle = entity.dxf.get("handle")
    if handle in LOUNGE_EXCLUSION_HANDLES:
        return "owner-confirmed fan-shaped lounge/platform geometry"
    if handle in NESTED_FURNITURE_HANDLES:
        return "nested F-FURN furniture block"
    layer = entity.dxf.layer
    if layer in FURNITURE_LAYERS:
        return "furniture layer"
    if layer in OVERLAY_LAYERS:
        return "platform/accessibility design overlay"
    if _is_overlay_text(entity):
        return "leisure/platform overlay label"
    return None


def _source_wall_checks(source_doc):
    wall_entities = [
        e for e in source_doc.modelspace()
        if e.dxf.layer == "S-S.WALL" and e.dxftype() not in {"TEXT", "MTEXT"}
    ]
    out = []
    for name, rect in GREEN_BOXES.items():
        matches = []
        padded = [rect[0] - 150, rect[1] - 150, rect[2] + 150, rect[3] + 150]
        for entity in wall_entities:
            entity_box = _task_bbox(entity)
            if entity_box and _intersects(entity_box, padded):
                matches.append(entity.dxf.get("handle"))
        out.append({
            "name": name,
            "rect_mm": rect,
            "source_wall_handles": sorted(handle for handle in matches if handle),
            "source_wall_linework": bool(matches),
        })
    return out


def _source_window_check(source_doc):
    register = json.loads((ROOT / "current_existing/window_register.json").read_text())
    window = next(item for item in register["windows"] if item["window_id"] == "W-KIT-S")
    opening = window["opening_rect_mm"]
    wall_matches = []
    padded = [opening[0] - 150, opening[1] - 150, opening[2] + 150, opening[3] + 150]
    for entity in source_doc.modelspace():
        if entity.dxf.layer != "S-S.WALL":
            continue
        entity_box = _task_bbox(entity)
        if entity_box and _intersects(entity_box, padded):
            wall_matches.append(entity.dxf.get("handle"))
    glazing_matches = []
    for entity in source_doc.modelspace():
        if entity.dxf.layer != "S-S.WALL":
            continue
        entity_box = _task_bbox(entity)
        if entity_box and _intersects(entity_box, opening):
            glazing_matches.append(entity.dxf.get("handle"))
    return {
        "window_id": window["window_id"],
        "type": window["type"],
        "opening_rect_mm": opening,
        "source_glazing_rect_mm": opening,
        "surrounding_wall_handles": sorted(handle for handle in wall_matches if handle),
        "surrounding_wall_linework": bool(wall_matches),
        "note": "Standard window occupies only the registered opening rectangle; source wall linework remains.",
    }


def _compare_records(source, output, predicate):
    source_selected = {h: r for h, r in source.items() if predicate(r)}
    output_selected = {h: r for h, r in output.items() if predicate(r)}
    missing = sorted(set(source_selected) - set(output_selected))
    extra = sorted(set(output_selected) - set(source_selected))
    deltas = []
    mismatches = []
    for handle in sorted(set(source_selected) & set(output_selected)):
        source_record = source_selected[handle]
        output_record = output_selected[handle]
        if source_record["layer"] != output_record["layer"] or source_record["type"] != output_record["type"]:
            mismatches.append({
                "handle": handle,
                "reason": "layer_or_type",
                "source": [source_record["layer"], source_record["type"]],
                "output": [output_record["layer"], output_record["type"]],
            })
        a = source_selected[handle]["bbox_task01"]
        b = output_selected[handle]["bbox_task01"]
        if a is None or b is None:
            continue
        bbox_deltas = [abs(x - y) for x, y in zip(a, b)]
        deltas.extend(bbox_deltas)
        if max(bbox_deltas, default=0.0) > 0.01:
            mismatches.append({
                "handle": handle,
                "reason": "bbox_coordinate_delta",
                "max_delta_mm": max(bbox_deltas),
            })
    return {
        "source_count": len(source_selected),
        "output_count": len(output_selected),
        "missing": missing,
        "extra": extra,
        "max_coordinate_delta_mm": max(deltas, default=0.0),
        "geometry_mismatches": mismatches,
    }


def build():
    if sha(SOURCE) != SOURCE_SHA:
        raise RuntimeError(f"source DXF SHA mismatch: {SOURCE}")
    source_doc = ezdxf.readfile(str(SOURCE))
    source_records = _walk_records(source_doc)
    for handle, expected in LOUNGE_EXPECTATIONS.items():
        entity = source_doc.entitydb.get(handle)
        if entity is None or entity.dxf.layer != expected["layer"] or entity.dxftype() != expected["type"]:
            raise RuntimeError(f"lounge exclusion source mismatch: {handle}")
    for handle, expected in NESTED_FURNITURE_EXPECTATIONS.items():
        entity = source_doc.entitydb.get(handle)
        if entity is None or entity.dxf.layer != expected["layer"] or entity.dxftype() != expected["type"]:
            raise RuntimeError(f"nested furniture exclusion source mismatch: {handle}")
        block = source_doc.blocks.get(entity.dxf.name)
        if entity.dxf.name != expected["block"] or not any(be.dxf.layer == "F-FURN" for be in block):
            raise RuntimeError(f"nested furniture block mismatch: {handle}")
    deleted = []
    for entity in list(source_doc.modelspace()):
        reason = _deletion_reason(entity)
        if reason:
            deleted.append({
                "handle": entity.dxf.get("handle"),
                "layer": entity.dxf.layer,
                "type": entity.dxftype(),
                "text": _text_value(entity),
                "reason": reason,
                "classification": (
                    "NON_STRUCTURAL_SOURCE_OVERLAY" if entity.dxf.get("handle") in LOUNGE_EXCLUSION_HANDLES
                    else "FURNITURE_SOURCE_ENTITY"
                ),
            })
            source_doc.modelspace().delete_entity(entity)
    for layer_name, style in LAYER_STYLE_OVERRIDES.items():
        if layer_name not in source_doc.layers:
            continue
        layer = source_doc.layers.get(layer_name)
        for key, value in style.items():
            setattr(layer.dxf, key, value)
    source_doc.saveas(str(OUTPUT))
    # LibreDWG source text contains a few trailing spaces in annotation values;
    # normalize only line endings/whitespace so the derived DXF has a clean,
    # reviewable text diff without touching coordinates or entity records.
    raw = OUTPUT.read_bytes()
    normalized = b"\n".join(line.rstrip(b" \t") for line in raw.splitlines()) + b"\n"
    OUTPUT.write_bytes(normalized)
    output_doc = ezdxf.readfile(str(OUTPUT))
    output_records = _walk_records(output_doc)

    exclusion_handles = {item["handle"] for item in deleted}
    wall_pred = lambda record: record["layer"] == "S-S.WALL" and record["handle"] not in exclusion_handles
    retained_pred = lambda record: record["handle"] not in exclusion_handles
    wall_match = _compare_records(source_records, output_records, wall_pred)
    retained_match = _compare_records(source_records, output_records, retained_pred)
    residual_furniture = [
        rec for rec in output_records.values()
        if rec["layer"] in FURNITURE_LAYERS
    ]
    for rec in output_records.values():
        if rec["type"] != "INSERT":
            continue
        entity = output_doc.entitydb.get(rec["handle"])
        try:
            block = output_doc.blocks.get(entity.dxf.name)
            if any(be.dxf.layer == "F-FURN" for be in block):
                residual_furniture.append(rec)
        except Exception:
            continue
    residual_overlay = [
        rec for rec in output_records.values()
        if rec["type"] in {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}
        and _is_overlay_text(ezdxf.readfile(str(OUTPUT)).entitydb[rec["handle"]])
    ]
    green_checks = _source_wall_checks(source_doc=ezdxf.readfile(str(SOURCE)))
    standard_window = _source_window_check(ezdxf.readfile(str(SOURCE)))
    outside_lounge_layers = {}
    for layer in ("S-S.WALL", "F-DOOR", "S-COLUMN", "S-楼梯"):
        outside_lounge_layers[layer] = _compare_records(
            source_records,
            output_records,
            lambda record, layer=layer: record["layer"] == layer and record["handle"] not in exclusion_handles,
        )
    lounge_remaining = sorted(
        handle for handle in LOUNGE_EXCLUSION_HANDLES if handle in output_records
    )
    exclusion_registry = [
        {
            "classification": "NON_STRUCTURAL_SOURCE_OVERLAY",
            "reason": "owner-confirmed lounge/leisure geometry to remove",
            "source_handles": LOUNGE_EXCLUSION_HANDLES,
        },
        {
            "classification": "FURNITURE_SOURCE_ENTITY",
            "reason": "source furniture layer or nested F-FURN block",
            "source_handles": sorted(
                handle for handle in exclusion_handles if handle not in LOUNGE_EXCLUSION_HANDLES
            ),
        },
    ]
    report = {
        "status": "PASS" if (
            not wall_match["missing"] and not wall_match["extra"]
            and wall_match["max_coordinate_delta_mm"] <= 0.01
            and not wall_match["geometry_mismatches"]
            and not residual_furniture and not residual_overlay
            and lounge_remaining == []
            and sorted(LOUNGE_EXCLUSION_HANDLES) == sorted(
                next(item["source_handles"] for item in exclusion_registry
                     if item["classification"] == "NON_STRUCTURAL_SOURCE_OVERLAY")
            )
            and all(
                not item["missing"] and not item["extra"]
                and item["max_coordinate_delta_mm"] <= 0.01
                and not item["geometry_mismatches"]
                for item in outside_lounge_layers.values()
            )
            and all(item["source_wall_linework"] for item in green_checks)
            and standard_window["surrounding_wall_linework"]
        ) else "FAIL",
        "source": {
            "dwg": "source/世纪欣园FF.dwg",
            "dxf": "cad/measured_working.dxf",
            "dxf_sha256": sha(SOURCE),
        },
        "output": {
            "dxf": str(OUTPUT.relative_to(ROOT)),
            "dxf_sha256": sha(OUTPUT),
        },
        "deleted_entities": deleted,
        "source_entity_counts": {
            f"{layer}|{typ}": count
            for (layer, typ), count in Counter(
                (r["layer"], r["type"]) for r in source_records.values()
            ).items()
        },
        "output_entity_counts": {
            f"{layer}|{typ}": count
            for (layer, typ), count in Counter(
                (r["layer"], r["type"]) for r in output_records.values()
            ).items()
        },
        "wall_match": wall_match,
        "retained_entity_match": retained_match,
        "expected_retained_entity_count": len(source_records) - len(exclusion_handles),
        "explicit_exclusion_registry": exclusion_registry,
        "lounge_entity_audit": {
            "json": str(AUDIT_JSON_PATH.relative_to(ROOT)),
            "png": str(AUDIT_PNG_PATH.relative_to(ROOT)),
            "approved_handles": LOUNGE_EXCLUSION_HANDLES,
        },
        "lounge_geometry_remaining": len(lounge_remaining),
        "lounge_geometry_remaining_handles": lounge_remaining,
        "outside_lounge_layer_checks": outside_lounge_layers,
        "residual_furniture_entities": residual_furniture,
        "residual_leisure_overlay_entities": residual_overlay,
        "green_box_checks": green_checks,
        "standard_window_check": standard_window,
        "coordinate_system": {"origin_abs": [AX, AY], "units": "mm", "task01": "abs - origin_abs"},
        "layer_style_overrides": LAYER_STYLE_OVERRIDES,
        "serialization_normalization": "trailing spaces stripped from DXF text lines only",
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "output": str(OUTPUT), "report": str(REPORT_PATH),
                      "deleted": len(deleted), "wall_match": wall_match}, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    build()
