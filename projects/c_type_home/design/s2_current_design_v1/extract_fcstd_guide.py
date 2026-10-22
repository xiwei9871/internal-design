#!/usr/bin/env python3
"""Extract the latest human-named FreeCAD guide into task coordinates.

Run with FreeCAD's Python interpreter (freecadcmd). This is intentionally an
ingest-only step: it does not modify the FCStd or any formal CAD source.
"""

from __future__ import annotations

import json
from pathlib import Path

import FreeCAD as App


ROOT = Path("/Users/xiwei/interior_design")
FCSTD = ROOT / "projects/c_type_home/cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd"
OUT = ROOT / "projects/c_type_home/design/s2_current_design_v1/human_guide_inventory.json"

# cad_version_manifest.json records the conversion from absolute CAD to Task01
# coordinates as abs - (1298172, -296458).
ORIGIN_X = 1_298_172.0
ORIGIN_Y = -296_458.0


SEMANTIC_MAP = {
    "三人位沙发": ("SOFA_3S", "living", "PRIMARY_SOCIAL_ANCHOR"),
    "双人位沙发": ("SOFA_2S", "living", "CONVERSATION_SECONDARY_EDGE"),
    "角几": ("SIDE_TABLE", "living", "MOVABLE_OPTIONAL"),
    "茶几": ("COFFEE_TABLE_OPTIONAL", "living", "MOVABLE_OPTIONAL"),
    "lounge": ("LOUNGE_CHAIR", "living", "OPTIONAL_THIRD_SEAT"),
    "电视柜（或者悬浮电视墙）": ("MEDIA_EDGE", "living", "INTENT_AMBIGUOUS"),
    "斜坡（轮椅用": ("ACCESSIBILITY_RAMP", "transition", "ACCESSIBILITY_RAMP_GUIDE"),
    "客卫（湿区）": ("GUEST_BATH_WET_ZONE", "guest_bath", "ROOM_GUIDE"),
    "客卫马桶": ("WC_GUEST", "guest_bath", "FIXTURE_GUIDE"),
    "客卫洗手盆柜体": ("VANITY_GUEST", "guest_bath", "FIXTURE_GUIDE"),
    "主卫湿区": ("BATH_MOTHER_WET_ZONE", "mother_bathroom", "AGING_IN_PLACE_WET_ZONE"),
    "主卫马桶": ("WC_MOTHER", "mother_bathroom", "AGING_IN_PLACE_FIXTURE"),
    "主卫洗手盆和柜体": ("VANITY_MOTHER", "mother_bathroom", "AGING_IN_PLACE_FIXTURE"),
    "次卧小床1.2": ("BED_GUEST_1200", "guest_room", "NOMINAL_1200_WIDTH_GUIDE"),
    "床背板+窄书桌占位": ("STUDY_DESK_BACKBOARD", "study", "DESK_GUIDE"),
    "次卧衣柜": ("WARDROBE_GUEST", "guest_room", "STORAGE_GUIDE"),
    "书柜": ("BOOKCASE_STUDY_TALL", "study", "STORAGE_GUIDE"),
    "书柜001": ("BOOKCASE_STUDY_LOW", "study", "STORAGE_GUIDE"),
    "茶台": ("TEA_TABLE_STUDY", "study", "FLEXIBLE_SURFACE"),
    "主人椅": ("STUDY_CHAIR", "study", "WORK_SEAT_GUIDE"),
    "条凳": ("STUDY_BENCH", "study", "FLEXIBLE_SEAT"),
    "凳子": ("STUDY_STOOL", "study", "FLEXIBLE_SEAT"),
    "次卧凳子": ("GUEST_STOOL", "guest_room", "FLEXIBLE_SEAT"),
    "次主卧床": ("BED_OWNER", "owner_bedroom", "PRIMARY_BED_GUIDE"),
    "次主卧床头占位": ("NIGHTSTAND_OWNER", "owner_bedroom", "NIGHTSTAND_GUIDE"),
    "次主卧衣柜": ("WARDROBE_OWNER", "owner_bedroom", "STORAGE_GUIDE"),
    "次主卧电视柜": ("MEDIA_EDGE_OWNER", "owner_bedroom", "OPTIONAL_MEDIA"),
    "主卧床": ("BED_MOTHER", "mother_bedroom", "PRIMARY_BED_GUIDE"),
    "主卧床头柜占位": ("NIGHTSTAND_MOTHER", "mother_bedroom", "NIGHTSTAND_GUIDE"),
    "主卧衣柜": ("WARDROBE_MOTHER", "mother_bedroom", "STORAGE_GUIDE"),
    "主卧电视柜": ("MEDIA_EDGE_MOTHER", "mother_bedroom", "OPTIONAL_MEDIA"),
    "餐桌": ("DINING_TABLE", "dining", "FOUR_SEAT_DAILY"),
    "餐椅": ("DINING_CHAIR_1", "dining", "FOUR_SEAT_DAILY"),
    "餐椅003": ("DINING_CHAIR_2", "dining", "FOUR_SEAT_DAILY"),
    "餐椅004": ("DINING_CHAIR_4", "dining", "FOUR_SEAT_DAILY"),
    "Circle013": ("UNNAMED_AUXILIARY", "unknown", "UNNAMED_AUXILIARY"),
    "Rectangle033": ("UNNAMED_AUXILIARY", "unknown", "UNNAMED_AUXILIARY"),
    "Rectangle": ("SUPPORT_GEOMETRY", "unknown", "EXTRUSION_BASE"),
    "现有橱柜": ("KITCHEN_KEEP", "kitchen", "EXISTING_KEEP"),
    "鞋柜": ("ENTRY_SHOE_STORAGE", "entry", "STORAGE_GUIDE"),
    "橱柜": ("KITCHEN_AUX_STORAGE", "kitchen", "EXISTING_OR_GUIDE_TO_VERIFY"),
}


def bbox_task(shape):
    box = shape.BoundBox
    return [
        box.XMin - ORIGIN_X,
        box.YMin - ORIGIN_Y,
        box.XMax - ORIGIN_X,
        box.YMax - ORIGIN_Y,
    ]


def object_row(obj):
    label = str(obj.Label)
    semantic_id, zone, status = SEMANTIC_MAP.get(
        label,
        ("UNNAMED_AUXILIARY", "unknown", "UNNAMED_AUXILIARY"),
    )
    try:
        shape = obj.Shape
        box = bbox_task(shape) if not shape.isNull() else None
    except Exception:
        box = None
    dimensions = {}
    for prop in ("Length", "Height", "Radius", "LengthFwd", "LengthRev"):
        if prop in obj.PropertiesList:
            try:
                dimensions[prop] = float(getattr(obj, prop))
            except Exception:
                pass
    return {
        "name": obj.Name,
        "label": label,
        "type": obj.TypeId,
        "semantic_id": semantic_id,
        "zone": zone,
        "guide_status": status,
        "bbox_task01_mm": None if box is None else [round(v, 3) for v in box],
        "guide_width_mm": None if box is None else round(box[2] - box[0], 3),
        "guide_depth_mm": None if box is None else round(box[3] - box[1], 3),
        "dimensions": dimensions,
        "inlist_labels": [str(x.Label) for x in obj.InList if hasattr(x, "Label")],
    }


def main():
    if not FCSTD.is_file():
        raise FileNotFoundError(FCSTD)
    doc = App.openDocument(str(FCSTD))
    doc.recompute()
    objects = []
    for obj in doc.Objects:
        if obj.TypeId in {"Part::Part2DObjectPython", "Part::Extrusion", "Part::FeaturePython"}:
            objects.append(object_row(obj))
        elif obj.TypeId == "App::FeaturePython" and obj.Name.startswith("Text"):
            row = object_row(obj)
            row["semantic_id"] = "UNNAMED_AUXILIARY_TEXT"
            row["guide_status"] = "UNNAMED_AUXILIARY"
            objects.append(row)
    primary = [
        row
        for row in objects
        if row["semantic_id"] not in {"SUPPORT_GEOMETRY", "UNNAMED_AUXILIARY", "UNNAMED_AUXILIARY_TEXT"}
    ]
    auxiliary = [row for row in objects if row not in primary]
    report = {
        "schema": "s2-human-guide-inventory-v1",
        "source_fcstd": str(FCSTD),
        "source_document": doc.Name,
        "source_coordinate_transform": {
            "task01_x": "fcstd_x - 1298172",
            "task01_y": "fcstd_y + 296458",
            "source_coordinate_status": "absolute_fcstd_to_task01",
        },
        "ingest_status": "PASS",
        "primary_guide_count": len(primary),
        "auxiliary_count": len(auxiliary),
        "primary_guides": primary,
        "auxiliary_guides": auxiliary,
        "functional_constraints": {
            "south_zone": "study / backup sleeping",
            "middle_zone": "guest room",
            "kitchen": "KEEP",
            "guest_bath": "KEEP_CURRENT_SIZE",
            "north_balcony": "OPEN_NOT_ENCLOSED",
            "formal_cad": "HOLD",
        },
        "normalization_notes": [
            "television cabinet label is INTENT_AMBIGUOUS; do not force a conventional TV-only solution",
            "次卧小床1.2 is a nominal approximately 1200 mm bed-width guide; current rectangle is not a final product size",
            "斜坡（轮椅用 is parsed as ACCESSIBILITY_RAMP_GUIDE; slope and final length remain TO_VERIFY",
            "unnamed auxiliaries are retained without semantic guessing",
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["ingest_status"], "primary": len(primary), "auxiliary": len(auxiliary), "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
