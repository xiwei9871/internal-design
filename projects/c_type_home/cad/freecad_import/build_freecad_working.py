#!/usr/bin/env python3
"""Build a FreeCAD-friendly furniture-guide base from the audited R2000 DXF.

The source DWG and the full R2000 candidate are read-only inputs. This creates a
fresh R2000 document containing unchanged architectural geometry, while omitting
off-origin frozen title/revision graphics and text/dimension annotations that
the installed FreeCAD DXF importer cannot reliably decode.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json
import re
import math

import ezdxf
from ezdxf import bbox
from ezdxf.addons.importer import Importer
from ezdxf.math import Vec3


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DWG = REPO / "世纪欣园FF.dwg"
R12 = HERE / "世纪欣园FF_freecad_r12_ascii.dxf"
R2000 = HERE / "世纪欣园FF_freecad_2000_ascii.dxf"
WORKING = HERE / "世纪欣园FF_freecad_WORKING.dxf"
QA_JSON = HERE / "cad_conversion_qa.json"

ANNOTATION_TYPES = {"TEXT", "MTEXT", "DIMENSION", "ATTRIB", "ATTDEF"}
OFF_ORIGIN_FROZEN_LAYERS = {"RC-GRILL"}
GUIDE_LAYER = "USER_GUIDE_FURNITURE"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def box_for(entities):
    ext = bbox.extents(entities, fast=False)
    if not ext.has_data:
        return None
    return [ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y]


def round_box(box):
    return None if box is None else [round(float(value), 6) for value in box]


def decode_unicode_escapes(value):
    return re.sub(
        r"\\U\+([0-9A-Fa-f]{4})",
        lambda match: chr(int(match.group(1), 16)),
        value,
    )


def entity_signature(entity):
    """Geometry-only signature, excluding handles and ownership metadata."""
    kind = entity.dxftype()
    layer = decode_unicode_escapes(entity.dxf.get("layer", "0"))

    def point(value):
        return tuple(round(float(value[index]), 8) for index in range(3))

    if kind == "LINE":
        geometry = (point(entity.dxf.start), point(entity.dxf.end))
    elif kind in {"ARC", "CIRCLE"}:
        geometry = (
            point(entity.dxf.center),
            round(float(entity.dxf.radius), 8),
            round(float(entity.dxf.get("start_angle", 0.0)), 8),
            round(float(entity.dxf.get("end_angle", 0.0)), 8),
        )
    elif kind == "LWPOLYLINE":
        geometry = (
            bool(entity.closed),
            tuple(tuple(round(float(v), 8) for v in row) for row in entity.get_points("xyseb")),
        )
    elif kind == "INSERT":
        geometry = (
            decode_unicode_escapes(entity.dxf.name),
            point(entity.dxf.insert),
            round(float(entity.dxf.get("xscale", 1.0)), 8),
            round(float(entity.dxf.get("yscale", 1.0)), 8),
            round(float(entity.dxf.get("zscale", 1.0)), 8),
            round(float(entity.dxf.get("rotation", 0.0)), 8),
        )
    elif kind == "HATCH":
        hatch_box = round_box(box_for([entity]))
        geometry = (
            entity.dxf.get("solid_fill", 0),
            entity.dxf.get("pattern_name", ""),
            None if hatch_box is None else tuple(hatch_box),
        )
    else:
        raise ValueError(f"Unhandled retained entity type: {kind}")
    return kind, layer, geometry


def counter_by_type_and_layer(entities):
    return dict(sorted(Counter((e.dxftype(), e.dxf.get("layer", "0")) for e in entities).items()))


def printable_counts(counter):
    result = {}
    for (kind, layer), count in counter.items():
        result.setdefault(layer, {})[kind] = count
    return result


def transformed_insert_entities(source, insert):
    """Bake a mirrored INSERT into ordinary entities with WCS coordinates.

    FreeCAD's importer reads the raw negative coordinates of mirrored block
    members instead of applying the INSERT transform. Rebuilding the small
    door/fixture members here keeps their visible geometry at the source
    location while retaining their exact shape and scale.
    """
    matrix = insert.matrix44()
    block = source.blocks.get(insert.dxf.name)
    layer = insert.dxf.get("layer", "0")
    for original in block:
        clone = original.copy()
        if original.dxftype() == "LWPOLYLINE":
            points = []
            for x, y, start_width, end_width, bulge in original.get_points("xyseb"):
                point = matrix.transform((x, y, 0.0))
                points.append((point.x, point.y, start_width, end_width, bulge))
            clone.set_points(points, format="xyseb")
        elif original.dxftype() == "ARC":
            center = matrix.transform(original.dxf.center)
            start = math.radians(original.dxf.start_angle)
            end = math.radians(original.dxf.end_angle)
            start_point = matrix.transform(
                (
                    original.dxf.center.x + original.dxf.radius * math.cos(start),
                    original.dxf.center.y + original.dxf.radius * math.sin(start),
                    0.0,
                )
            )
            end_point = matrix.transform(
                (
                    original.dxf.center.x + original.dxf.radius * math.cos(end),
                    original.dxf.center.y + original.dxf.radius * math.sin(end),
                    0.0,
                )
            )
            start_angle = math.degrees(math.atan2(start_point.y - center.y, start_point.x - center.x)) % 360.0
            end_angle = math.degrees(math.atan2(end_point.y - center.y, end_point.x - center.x)) % 360.0
            if insert.dxf.get("xscale", 1.0) * insert.dxf.get("yscale", 1.0) < 0:
                start_angle, end_angle = end_angle, start_angle
            clone.dxf.center = center
            clone.dxf.start_angle = start_angle
            clone.dxf.end_angle = end_angle
        else:
            # The audited negative inserts contain only these two geometry types.
            # Do not silently approximate an unsupported member.
            raise ValueError(f"Unsupported mirrored block member: {original.dxftype()}")
        clone.dxf.layer = layer
        source.entitydb.add(clone)
        source.modelspace().add_entity(clone)
        yield clone


def main():
    for path in (DWG, R12, R2000):
        if not path.is_file():
            raise FileNotFoundError(path)

    source = ezdxf.readfile(R2000)
    source_msp = list(source.modelspace())
    if source.dxfversion != "AC1015":
        raise ValueError(f"Expected AC1015/R2000 candidate, got {source.dxfversion}")
    if source.header.get("$INSUNITS") != 4:
        raise ValueError(f"Expected millimeter INSUNITS=4, got {source.header.get('$INSUNITS')}")

    kept = []
    retained_source_entities = []
    exploded_block_insert = []
    for entity in source_msp:
        if entity.dxf.get("layer", "0") in OFF_ORIGIN_FROZEN_LAYERS:
            continue
        if entity.dxftype() in ANNOTATION_TYPES:
            continue
        retained_source_entities.append(entity)
        # The source kitchen/fixture block carries a far-off block base point.
        # Explode this one insert into its already transformed LINE/ARC geometry
        # so FreeCAD's hidden block-definition group cannot pull the view extents
        # to the unrelated source block origin.
        if entity.dxftype() == "INSERT" and (
            entity.dxf.name == "bing"
            or entity.dxf.get("xscale", 1.0) < 0
            or entity.dxf.get("yscale", 1.0) < 0
            or entity.dxf.get("zscale", 1.0) < 0
        ):
            expanded = list(transformed_insert_entities(source, entity))
            kept.extend(expanded)
            exploded_block_insert.append(
                {
                    "source_block": entity.dxf.name,
                    "source_layer": entity.dxf.get("layer", "0"),
                    "insert_point": list(entity.dxf.insert),
                    "rotation_deg": entity.dxf.get("rotation", 0.0),
                    "xscale": entity.dxf.get("xscale", 1.0),
                    "yscale": entity.dxf.get("yscale", 1.0),
                    "expanded_entity_count": len(expanded),
                    "reason": "eliminate far-off block-definition base point while preserving transformed geometry",
                }
            )
            continue
        kept.append(entity)
    excluded = [entity for entity in source_msp if entity not in retained_source_entities]
    if not kept:
        raise ValueError("No model-space entities remain after the documented exclusions")

    target = ezdxf.new("R2000")
    target.header["$INSUNITS"] = 4
    target.header["$DWGCODEPAGE"] = "ANSI_1252"
    target.header["$INSBASE"] = source.header.get("$INSBASE", (0.0, 0.0, 0.0))

    importer = Importer(source, target)
    importer.import_entities(kept)
    importer.finalize()

    if GUIDE_LAYER not in target.layers:
        target.layers.new(GUIDE_LAYER, dxfattribs={"color": 3, "linetype": "CONTINUOUS"})
    target.header["$CLAYER"] = GUIDE_LAYER
    target.saveas(WORKING)

    # Reopen the written file and verify it is a clean, ASCII-encoded R2000 DXF.
    result = ezdxf.readfile(WORKING)
    result_msp = list(result.modelspace())
    source_signatures = Counter(entity_signature(e) for e in kept)
    result_signatures = Counter(entity_signature(e) for e in result_msp)
    source_box = box_for(kept)
    result_box = box_for(result_msp)
    if source_signatures != result_signatures:
        raise AssertionError("Retained entity geometry signature differs after clean rebuild")
    if any(abs(a - b) > 1e-5 for a, b in zip(source_box, result_box)):
        raise AssertionError(f"Extents changed: {source_box} -> {result_box}")
    raw_bytes = WORKING.read_bytes()
    if not all(byte < 128 for byte in raw_bytes):
        raise AssertionError("Working DXF is not ASCII-encoded")

    layer_groups = {}
    for entity in source_msp:
        layer_groups.setdefault(entity.dxf.get("layer", "0"), []).append(entity)
    exclusions = {
        "source_modelspace_entities": len(source_msp),
        "excluded_modelspace_entities": len(excluded),
        "excluded_by_layer_and_type": printable_counts(counter_by_type_and_layer(excluded)),
        "excluded_off_origin_frozen_layer_bbox": round_box(
            box_for(layer_groups.get("RC-GRILL", []))
        ),
        "kept_modelspace_entities": len(retained_source_entities),
        "working_prepared_entity_count": len(kept),
        "exploded_block_inserts": exploded_block_insert,
        "kept_by_layer_and_type": printable_counts(counter_by_type_and_layer(retained_source_entities)),
    }

    def candidate_summary(path):
        doc = ezdxf.readfile(path)
        msp = list(doc.modelspace())
        ext = box_for(msp)
        return {
            "file": path.name,
            "sha256": sha256(path),
            "dxf_version": doc.dxfversion,
            "insunits": doc.header.get("$INSUNITS"),
            "codepage": doc.header.get("$DWGCODEPAGE"),
            "modelspace_entity_count": len(msp),
            "entity_counts": dict(sorted(Counter(e.dxftype() for e in msp).items())),
            "extents_xy": round_box(ext),
        }

    report = {
        "source_dwg": {
            "file": DWG.name,
            "sha256": sha256(DWG),
            "dwg_version": "AC1018 (AutoCAD 2004/2005/2006)",
            "units": "millimeters",
            "units_basis": "LibreDWG conversion header $INSUNITS=4",
            "converter": "LibreDWG dwg2dxf 0.14",
        },
        "candidates": {"r12": candidate_summary(R12), "r2000": candidate_summary(R2000)},
        "working_dxf": {
            "file": WORKING.name,
            "sha256": sha256(WORKING),
            "dxf_version": result.dxfversion,
            "codepage": result.header.get("$DWGCODEPAGE"),
            "all_bytes_ascii": all(byte < 128 for byte in raw_bytes),
            "insunits": result.header.get("$INSUNITS"),
            "units": "millimeters",
            "modelspace_entity_count": len(result_msp),
            "entity_counts": dict(sorted(Counter(e.dxftype() for e in result_msp).items())),
            "layer_entity_counts": printable_counts(counter_by_type_and_layer(result_msp)),
            "layer_names": sorted(layer.dxf.name for layer in result.layers),
            "block_count": len(result.blocks),
            "extents_xy": round_box(result_box),
            "width_mm": round(result_box[2] - result_box[0], 6),
            "height_mm": round(result_box[3] - result_box[1], 6),
            "geometry_delta_max_mm": 0.0,
            "retained_geometry_signatures_equal": True,
            "guide_layer": GUIDE_LAYER,
        },
        "exclusions": exclusions,
        "freecad_import": {"status": "PENDING"},
        "notes": [
            "Source DWG and full R2000 candidate are read-only and preserved.",
            "No retained geometry was translated, rotated, or scaled.",
            "The frozen RC-GRILL layer is off-origin title/revision content and was omitted from the furniture-guide working copy.",
            "TEXT, MTEXT, DIMENSION, ATTRIB, and ATTDEF annotation entities are omitted from the working copy; the full candidate retains them.",
            "The six wall HATCH entities are retained in the DXF; FreeCAD 1.1.3 reports HATCH as unsupported and does not display those fills.",
        ],
    }
    QA_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["working_dxf"], ensure_ascii=False, indent=2))
    print(f"Wrote {WORKING}")
    print(f"Wrote {QA_JSON}")


if __name__ == "__main__":
    main()
