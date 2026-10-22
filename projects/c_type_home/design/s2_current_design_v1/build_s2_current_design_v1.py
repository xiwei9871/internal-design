#!/usr/bin/env python3
"""Build S2 CURRENT DESIGN V1 from the named FreeCAD human guide.

This produces a review artifact only. It never edits the FCStd, canonical CAD,
V02/V03, or project-state approval gates.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Patch, Rectangle as MplRectangle
from matplotlib.backends.backend_pdf import PdfPages
from shapely.geometry import box as shape_box
import ezdxf
from ezdxf import bbox as ez_bbox


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
GUIDE_FILE = OUT / "human_guide_inventory.json"
GEOMETRY_FILE = BASE / "data/geometry.json"
CANONICAL_FILE = BASE / "current_existing/canonical_plan_v1.json"
WINDOW_FILE = BASE / "current_existing/window_register.json"
KITCHEN_FILE = BASE / "current_existing/kitchen_cabinet_register.json"
BLOCK_LIBRARY_FILE = BASE / "assets/cad_library/standard/compiled/residential_design_legends_v01.dxf"

BLOCK_MAP = {
    "SOFA_3S": "SOFA_3S_2200x900_PLAN",
    "SOFA_2S": "SOFA_2S_1800x850_PLAN",
    "LOUNGE_CHAIR": "LOUNGE_CHAIR_900x900_PLAN",
    "BED_OWNER": "BED_1800x2100_PLAN",
    "BED_MOTHER": "BED_1800x2100_PLAN",
    "BED_GUEST_1200": "BED_1500x2000_PLAN",
    "DINING_TABLE": "DINING_TABLE_1500x600_PLAN",
    "DINING_CHAIR_1": "DINING_CHAIR_450x500_PLAN",
    "DINING_CHAIR_2": "DINING_CHAIR_450x500_PLAN",
    "DINING_CHAIR_3": "DINING_CHAIR_450x500_PLAN",
    "DINING_CHAIR_4": "DINING_CHAIR_450x500_PLAN",
    "STUDY_DESK_BACKBOARD": "DESK_1700x800_PLAN",
    "GUEST-BATH-SHOWER": "SHOWER_900x1200_PLAN",
    "SHOWER_GUEST": "SHOWER_900x1200_PLAN",
    "SHOWER_MOTHER": "SHOWER_900x1200_PLAN",
    "WC_GUEST": "WC_STD_450x700_PLAN",
    "WC_MOTHER": "WC_STD_450x700_PLAN",
    "VANITY_GUEST": "VANITY_600x500_PLAN",
    "VANITY_MOTHER": "VANITY_900x500_PLAN",
    "WASHER_SMALL_3KG": "WASHER_600x650_PLAN",
    "WARDROBE_OWNER": "WARDROBE_D600_PLAN",
    "WARDROBE_MOTHER": "WARDROBE_D600_PLAN",
    "WARDROBE_GUEST": "WARDROBE_D600_PLAN",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rect(x0, y0, width, depth):
    return [float(x0), float(y0), float(x0 + width), float(y0 + depth)]


def center_from_bbox(bbox):
    return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)


def item(item_id, label, semantic_id, zone, bbox, nominal, source_label=None, status="ACTIVE", notes=None, room=None, orientation="axis_aligned"):
    return {
        "id": item_id,
        "source_label": source_label or label,
        "semantic_id": semantic_id,
        "label": label,
        "functional_zone": zone,
        "canonical_room": room,
        "target_bbox_task01_mm": [round(float(v), 3) for v in bbox],
        "target_footprint_mm": [round(bbox[2] - bbox[0], 3), round(bbox[3] - bbox[1], 3)],
        "nominal_product_geometry_mm": list(nominal) if nominal else None,
        "orientation": orientation,
        "design_status": status,
        "notes": notes or [],
    }


def build_target_items():
    """Normalized schematic footprints; guide positions inform topology only."""
    items = [
        item("LIV-SOFA-3S", "三人位沙发", "SOFA_3S", "living", rect(3310, 9000, 900, 2200), (2200, 900), room="R-LIVING", orientation="rotated_90deg", notes=["guide was a tall narrow bbox; normalized to standard 3-seat sofa footprint"]),
        item("LIV-SOFA-2S", "双人位沙发", "SOFA_2S", "living", rect(4350, 11800, 1800, 850), (1800, 850), room="R-LIVING", notes=["secondary conversation edge"]),
        item("LIV-LOUNGE", "lounge", "LOUNGE_CHAIR", "living", rect(4500, 8000, 900, 900), (900, 900), room="R-LIVING", notes=["one optional third seat; retain only if central spine remains clear"]),
        item("LIV-MEDIA", "电视柜（或者悬浮电视墙）", "MEDIA_EDGE", "living", rect(7450, 9000, 300, 2400), (300, 2400), room="R-LIVING", status="INTENT_AMBIGUOUS", notes=["secondary focal edge; projector/laser-TV compatible; do not assume conventional TV cabinet"]),
        item("LIV-SIDE-TABLE", "角几", "SIDE_TABLE", "living", rect(3450, 11750, 450, 450), (450, 450), room="R-LIVING", status="OPTIONAL_MOVABLE", notes=["not part of fixed circulation test"]),
        item("LIV-COFFEE-OPTIONAL", "茶几", "COFFEE_TABLE_OPTIONAL", "living", rect(5000, 10000, 600, 600), (600, 600), room="R-LIVING", status="OPTIONAL_MOVABLE", notes=["shown as optional dashed item; no fixed central coffee table is approved"]),
        item("DIN-TABLE", "餐桌", "DINING_TABLE", "dining", rect(3050, 3000, 1500, 600), (1500, 600), room="R-DINING", notes=["four-seat daily configuration"]),
        item("DIN-CHAIR-N", "餐椅", "DINING_CHAIR_1", "dining", rect(3575, 2550, 450, 450), (450, 500), room="R-DINING", notes=["north chair"]),
        item("DIN-CHAIR-S", "餐椅003", "DINING_CHAIR_2", "dining", rect(3575, 3600, 450, 450), (450, 500), room="R-DINING", notes=["south chair; dining-to-glass transition is explicitly checked"]),
        item("DIN-CHAIR-W", "Circle013", "DINING_CHAIR_3", "dining", rect(2600, 3075, 450, 450), (450, 500), room="R-DINING", status="AUXILIARY_SOURCE_REUSED", notes=["source circle was unnamed; interpreted only as a fourth dining-seat position from the surrounding guide"]),
        item("DIN-CHAIR-E", "餐椅004", "DINING_CHAIR_4", "dining", rect(4550, 3075, 450, 450), (450, 500), room="R-DINING", notes=["east chair"]),
        item("ENTRY-SHOE", "鞋柜", "ENTRY_SHOE_STORAGE", "entry", rect(3000, 4800, 300, 700), (300, 700), status="GUIDE_NORMALIZED", notes=["guide label now recognized; exact depth TO_VERIFY"]),
        item("RAMP-EXISTING", "斜坡（轮椅用", "ACCESSIBILITY_RAMP", "transition", rect(5780, 4750, 2067, 672), None, status="EXISTING_GUIDE_TO_VERIFY", notes=["ACCESSIBILITY_RAMP_GUIDE; preserve as assisted route input; slope and landings TO_VERIFY"]),
        item("OWNER-BED", "次主卧床", "BED_OWNER", "owner_bedroom", rect(9100, 1200, 1800, 2100), (1800, 2100), room="R-BED-S", orientation="headboard_to_west", notes=["standardized from guide; spouse periodic use"]),
        item("OWNER-WARDROBE", "次主卧衣柜", "WARDROBE_OWNER", "owner_bedroom", rect(9850, 3850, 2000, 600), (2000, 600), room="R-BED-S"),
        item("OWNER-NIGHTSTAND", "次主卧床头占位", "NIGHTSTAND_OWNER", "owner_bedroom", rect(10950, 2200, 450, 450), (450, 450), room="R-BED-S", status="GUIDE_NORMALIZED"),
        item("OWNER-MEDIA", "次主卧电视柜", "MEDIA_EDGE_OWNER", "owner_bedroom", rect(8050, 1300, 500, 2000), (500, 2000), room="R-BED-S", status="OPTIONAL", notes=["not required for public-zone decision"]),
        item("MOTHER-BED", "主卧床", "BED_MOTHER", "mother_bedroom", rect(12700, 1200, 1800, 2100), (1800, 2100), room="R-MASTER", orientation="headboard_to_west", notes=["mother long-term bedroom; assisted-side route must remain open"]),
        item("MOTHER-WARDROBE", "主卧衣柜", "WARDROBE_MOTHER", "mother_bedroom", rect(13150, 3850, 2000, 600), (2000, 600), room="R-MASTER"),
        item("MOTHER-NIGHTSTAND", "主卧床头柜占位", "NIGHTSTAND_MOTHER", "mother_bedroom", rect(14600, 2200, 450, 450), (450, 450), room="R-MASTER", status="GUIDE_NORMALIZED"),
        item("MOTHER-MEDIA", "主卧电视柜", "MEDIA_EDGE_MOTHER", "mother_bedroom", rect(11650, 1300, 500, 2000), (500, 2000), room="R-MASTER", status="OPTIONAL"),
        item("GUEST-BED", "次卧小床1.2", "BED_GUEST_1200", "middle_guest_room", rect(10450, 8400, 2000, 1200), (1200, 2000), room="R-STUDY", orientation="nominal_1200_width", notes=["1.2m is a nominal width guide; current source rectangle is not final product geometry"]),
        item("GUEST-WARDROBE", "次卧衣柜", "WARDROBE_GUEST", "middle_guest_room", rect(9850, 10000, 2000, 600), (2000, 600), room="R-STUDY"),
        item("GUEST-STOOL", "次卧凳子", "GUEST_STOOL", "middle_guest_room", rect(12000, 9800, 450, 450), (450, 450), room="R-STUDY", status="OPTIONAL"),
        item("STUDY-DESK", "床背板+窄书桌占位", "STUDY_DESK_BACKBOARD", "south_study", rect(13400, 10000, 1700, 800), (1700, 800), room="R-BED-N", notes=["formal work room first; backup sleep remains secondary"]),
        item("STUDY-BOOKCASE-TALL", "书柜", "BOOKCASE_STUDY_TALL", "south_study", rect(15800, 7000, 450, 4200), (450, 4200), room="R-BED-N"),
        item("STUDY-BOOKCASE-LOW", "书柜001", "BOOKCASE_STUDY_LOW", "south_study", rect(13900, 6700, 1600, 450), (1600, 450), room="R-BED-N"),
        item("STUDY-TEA", "茶台", "TEA_TABLE_STUDY", "south_study", rect(14500, 7600, 800, 800), (800, 800), room="R-BED-N", status="OPTIONAL_FLEXIBLE"),
        item("STUDY-CHAIR", "主人椅", "STUDY_CHAIR", "south_study", rect(15300, 8500, 900, 900), (900, 900), room="R-BED-N", status="OPTIONAL_FLEXIBLE"),
        item("STUDY-BENCH", "条凳", "STUDY_BENCH", "south_study", rect(13500, 7600, 300, 1600), (300, 1600), room="R-BED-N", status="OPTIONAL_FLEXIBLE"),
        item("STUDY-STOOL", "凳子", "STUDY_STOOL", "south_study", rect(14500, 9200, 450, 450), (450, 450), room="R-BED-N", status="OPTIONAL_FLEXIBLE"),
        item("GUEST-BATH-SHOWER", "客卫（湿区）", "SHOWER_GUEST", "guest_bath", rect(8000, 9500, 900, 1200), (900, 1200), room="R-BATH-P", notes=["guest bath remains within current boundary"]),
        item("GUEST-BATH-WC", "客卫马桶", "WC_GUEST", "guest_bath", rect(9000, 9000, 450, 700), (450, 700), room="R-BATH-P"),
        item("GUEST-BATH-VANITY", "客卫洗手盆柜体", "VANITY_GUEST", "guest_bath", rect(8000, 8100, 600, 500), (600, 500), room="R-BATH-P"),
        item("GUEST-BATH-WASHER", "客卫3kg小洗衣机", "WASHER_SMALL_3KG", "guest_bath", rect(8700, 8100, 600, 650), (600, 650), room="R-BATH-P", status="REQUIREMENT_SLOT", notes=["SKU and exact wet-zone arrangement TO_VERIFY"]),
        item("MOTHER-BATH-SHOWER", "主卫湿区", "SHOWER_MOTHER", "mother_bathroom", rect(15100, 4700, 1000, 1200), (1000, 1200), room="R-BATH-M", notes=["aging-in-place zero-threshold provision; dimensions remain design target"]),
        item("MOTHER-BATH-WC", "主卫马桶", "WC_MOTHER", "mother_bathroom", rect(14450, 5550, 450, 700), (450, 700), room="R-BATH-M"),
        item("MOTHER-BATH-VANITY", "主卫洗手盆和柜体", "VANITY_MOTHER", "mother_bathroom", rect(13150, 5750, 1200, 500), (1200, 500), room="R-BATH-M"),
        item("KITCHEN-KEEP", "现有橱柜", "KITCHEN_KEEP", "kitchen", rect(1520, 740, 500, 1500), (500, 1500), status="EXISTING_KEEP", notes=["source-named existing cabinet guide; preserve"]),
        item("KITCHEN-AUX", "橱柜", "KITCHEN_AUX_STORAGE", "kitchen", rect(4320, 715, 1200, 500), (1200, 500), status="EXISTING_OR_GUIDE_TO_VERIFY"),
    ]
    for current in items:
        current["render_block_id"] = BLOCK_MAP.get(current["semantic_id"])
    return items


def load_rooms():
    data = json.loads(GEOMETRY_FILE.read_text(encoding="utf-8"))
    return {row["id"]: row["polygon_mm"] for row in data["spaces"]}


def register_guides(guide, target_items):
    target_by_label = {}
    for current in target_items:
        target_by_label.setdefault(current["source_label"], []).append(current)
    rows = []
    for current in guide["primary_guides"] + guide["auxiliary_guides"]:
        matches = target_by_label.get(current["label"], [])
        rows.append({
            "source_object_name": current["name"],
            "source_label": current["label"],
            "semantic_id": current["semantic_id"],
            "guide_status": current["guide_status"],
            "guide_bbox_task01_mm": current.get("bbox_task01_mm"),
            "guide_footprint_mm": [current.get("guide_width_mm"), current.get("guide_depth_mm")],
            "design_targets": [
                {
                    "id": target["id"],
                    "target_bbox_task01_mm": target["target_bbox_task01_mm"],
                    "target_footprint_mm": target["target_footprint_mm"],
                    "nominal_product_geometry_mm": target["nominal_product_geometry_mm"],
                    "design_status": target["design_status"],
                }
                for target in matches
            ],
            "lineage": "FCStd named guide -> normalized schematic target",
            "geometry_scaled": bool(matches and current.get("bbox_task01_mm") != matches[0]["target_bbox_task01_mm"]),
            "notes": current.get("notes", []),
        })
    return rows


def build_report(target_items, rooms, openings, kitchen):
    active = [x for x in target_items if x["design_status"] not in {"OPTIONAL", "OPTIONAL_FLEXIBLE", "OPTIONAL_MOVABLE", "EXISTING_OR_GUIDE_TO_VERIFY", "EXISTING_GUIDE_TO_VERIFY"}]
    screening = [x for x in target_items if x["design_status"] not in {"OPTIONAL", "OPTIONAL_FLEXIBLE", "OPTIONAL_MOVABLE", "EXISTING_OR_GUIDE_TO_VERIFY", "EXISTING_GUIDE_TO_VERIFY"}]
    shapes = {x["id"]: shape_box(*x["target_bbox_task01_mm"]) for x in target_items}
    collisions = []
    for index, first in enumerate(screening):
        for second in screening[index + 1:]:
            overlap = shapes[first["id"]].intersection(shapes[second["id"]]).area
            if overlap > 1.0:
                collisions.append({"a": first["id"], "b": second["id"], "overlap_mm2": round(overlap, 1)})
    room_checks = []
    for current in target_items:
        room_id = current.get("canonical_room")
        if not room_id or room_id not in rooms:
            continue
        polygon = shape_box(
            min(p[0] for p in rooms[room_id]),
            min(p[1] for p in rooms[room_id]),
            max(p[0] for p in rooms[room_id]),
            max(p[1] for p in rooms[room_id]),
        )
        footprint = shapes[current["id"]]
        ratio = footprint.intersection(polygon).area / max(footprint.area, 1.0)
        room_checks.append({"id": current["id"], "room": room_id, "inside_ratio": round(ratio, 3), "status": "PASS" if ratio >= 0.98 else "WARN"})
    fixed_kitchen = []
    for cabinet in kitchen:
        fixed_kitchen.append(shape_box(*cabinet["rect_mm"]))
    kitchen_conflicts = []
    for current in screening:
        if current["functional_zone"] == "kitchen":
            for index, obstacle in enumerate(fixed_kitchen):
                overlap = shapes[current["id"]].intersection(obstacle).area
                if overlap > 1.0:
                    kitchen_conflicts.append({"item": current["id"], "cabinet_index": index, "overlap_mm2": round(overlap, 1)})
    door_conflicts = []
    for opening in openings:
        opening_shape = shape_box(*opening["rect_mm"])
        for current in screening:
            overlap = shapes[current["id"]].intersection(opening_shape).area
            if overlap > 1.0:
                door_conflicts.append({"opening": opening["id"], "item": current["id"], "overlap_mm2": round(overlap, 1)})

    routes = [
        {"id": "entry_to_living", "target_clear_width_mm": 1100, "envelope": [2900, 6500, 4200, 7900], "axis": "y"},
        {"id": "living_to_stair", "target_clear_width_mm": 1100, "envelope": [5600, 6500, 7200, 7900], "axis": "x"},
        {"id": "living_to_north_balcony", "target_clear_width_mm": 850, "envelope": [7200, 11400, 7900, 12750], "axis": "x", "existing_limitation": "G-LIV-NBALC confirmed clear width 850 mm; no-worsening rule"},
        {"id": "dining_to_keep_kitchen", "target_clear_width_mm": 1000, "envelope": [5000, 2500, 5900, 4300], "axis": "x"},
        {"id": "dining_to_glass_transition", "target_clear_width_mm": 900, "envelope": [2900, 4050, 5650, 4530], "axis": "y", "existing_limitation": "G-DIN-LIV confirmed sliding-glass transition"},
        {"id": "guest_room_to_balcony", "target_clear_width_mm": 900, "envelope": [12000, 10500, 13000, 10900], "axis": "x"},
    ]
    route_checks = []
    for route in routes:
        envelope = shape_box(*route["envelope"])
        intersecting = [current for current in active if shapes[current["id"]].intersection(envelope).area > 1.0]
        if route["axis"] == "x":
            occupied = max((min(shapes[x["id"]].bounds[3], route["envelope"][3]) - max(shapes[x["id"]].bounds[1], route["envelope"][1]) for x in intersecting), default=0)
            nominal_width = route["envelope"][3] - route["envelope"][1]
        else:
            occupied = max((min(shapes[x["id"]].bounds[2], route["envelope"][2]) - max(shapes[x["id"]].bounds[0], route["envelope"][0]) for x in intersecting), default=0)
            nominal_width = route["envelope"][2] - route["envelope"][0]
        measured = max(0.0, nominal_width - occupied)
        route_checks.append({
            "id": route["id"],
            "reference_target_mm": route["target_clear_width_mm"],
            "screening_envelope_mm": route["envelope"],
            "proxy_measured_clear_width_mm": round(measured, 1),
            "blocking_items": [x["id"] for x in intersecting],
            "status": "PASS" if measured >= route["target_clear_width_mm"] else "WARN",
            "measurement_method": "axis-aligned schematic envelope screening; not construction clearance verification",
            "existing_limitation": route.get("existing_limitation"),
        })

    bathroom_checks = []
    for room_id in ("R-BATH-P", "R-BATH-M"):
        fixture_ids = [x["id"] for x in target_items if x.get("canonical_room") == room_id and x["design_status"] not in {"OPTIONAL", "OPTIONAL_FLEXIBLE", "OPTIONAL_MOVABLE"}]
        bathroom_checks.append({
            "room": room_id,
            "fixture_ids": fixture_ids,
            "boundary_preserved": True,
            "fixture_collision_count": sum(1 for c in collisions if c["a"] in fixture_ids and c["b"] in fixture_ids),
            "aging_in_place": room_id == "R-BATH-M",
            "status": "WARN_REVIEW_REQUIRED",
            "notes": ["door swing, service routing, and final clearances require human review and field verification"],
        })
    return {
        "schema": "s2-current-design-v1-collision-circulation-report",
        "status": "DRAFT_HUMAN_REVIEW",
        "formal_cad_allowed": False,
        "collision_count": len(collisions),
        "collisions": collisions,
        "room_containment_checks": room_checks,
        "door_swing_conflicts": door_conflicts,
        "kitchen_keep_conflicts": kitchen_conflicts,
        "route_checks": route_checks,
        "bathroom_checks": bathroom_checks,
        "interpretation": [
            "These are schematic screening results, not construction or accessibility certification.",
            "A clearance warning is a design issue to review, not an automatic formal-CAD gate.",
            "The current guest bathroom boundary and kitchen keep geometry were not enlarged or redrawn.",
        ],
    }


def load_block_library():
    if not BLOCK_LIBRARY_FILE.is_file():
        return None
    return ezdxf.readfile(BLOCK_LIBRARY_FILE)


def draw_block(ax, block, target_bbox, orientation="axis_aligned", color="#1d3557", edge="#1d3557", alpha=0.82, linestyle="-"):
    """Render the actual standard block geometry into the target footprint."""
    entities = [entity for entity in block if entity.dxftype() in {"LINE", "LWPOLYLINE", "ARC", "CIRCLE"}]
    if not entities:
        return False
    ext = ez_bbox.extents(entities, fast=False)
    if not ext.has_data or ext.extmax.x == ext.extmin.x or ext.extmax.y == ext.extmin.y:
        return False
    x0, y0, x1, y1 = target_bbox
    sx = (x1 - x0) / (ext.extmax.x - ext.extmin.x)
    sy = (y1 - y0) / (ext.extmax.y - ext.extmin.y)

    def map_point(x, y):
        u = (x - ext.extmin.x) / (ext.extmax.x - ext.extmin.x)
        v = (y - ext.extmin.y) / (ext.extmax.y - ext.extmin.y)
        if orientation == "rotated_90deg":
            return x0 + v * (x1 - x0), y0 + (1.0 - u) * (y1 - y0)
        return x0 + u * (x1 - x0), y0 + v * (y1 - y0)

    for entity in entities:
        if entity.dxftype() == "LINE":
            start = map_point(entity.dxf.start.x, entity.dxf.start.y)
            end = map_point(entity.dxf.end.x, entity.dxf.end.y)
            ax.plot([start[0], end[0]], [start[1], end[1]], color=edge, linewidth=0.65, linestyle=linestyle, alpha=alpha)
        elif entity.dxftype() == "LWPOLYLINE":
            points = [map_point(row[0], row[1]) for row in entity.get_points("xy")]
            if entity.closed and points:
                points.append(points[0])
            if points:
                ax.plot([point[0] for point in points], [point[1] for point in points], color=edge, linewidth=0.65, linestyle=linestyle, alpha=alpha)
        elif entity.dxftype() in {"ARC", "CIRCLE"}:
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = entity.dxf.get("start_angle", 0.0)
            end_angle = entity.dxf.get("end_angle", 360.0)
            if entity.dxftype() == "CIRCLE":
                start_angle, end_angle = 0.0, 360.0
            points = []
            for step in range(33):
                angle = math.radians(start_angle + (end_angle - start_angle) * step / 32.0)
                points.append(map_point(center.x + radius * math.cos(angle), center.y + radius * math.sin(angle)))
            ax.plot([point[0] for point in points], [point[1] for point in points], color=edge, linewidth=0.65, linestyle=linestyle, alpha=alpha)
    return True


def render(model, report, rooms, windows, walls, kitchen):
    colors = {
        "living": "#8ecae6", "dining": "#ffb703", "owner_bedroom": "#bde0fe", "mother_bedroom": "#cdb4db",
        "middle_guest_room": "#caffbf", "south_study": "#ffc8dd", "guest_bath": "#90dbf4", "mother_bathroom": "#a8dadc",
        "entry": "#adb5bd", "kitchen": "#f4a261", "transition": "#e9c46a",
    }
    fig, ax = plt.subplots(figsize=(16, 12), dpi=180)
    for wall in walls:
        x0, y0, x1, y1 = wall["rect_mm"]
        ax.add_patch(MplRectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#6c757d", edgecolor="#343a40", linewidth=0.45, alpha=0.75))
    for opening in windows:
        x0, y0, x1, y1 = opening["opening_rect_mm"]
        ax.add_patch(MplRectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#52b6ca", edgecolor="#087f8c", linewidth=1.0, alpha=0.55))
    for cabinet in kitchen:
        x0, y0, x1, y1 = cabinet["rect_mm"]
        ax.add_patch(MplRectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#e76f51", edgecolor="#9d2b1f", linewidth=0.5, alpha=0.65))
    for room_id, polygon in rooms.items():
        xs = [p[0] for p in polygon] + [polygon[0][0]]
        ys = [p[1] for p in polygon] + [polygon[0][1]]
        ax.plot(xs, ys, color="#adb5bd", linewidth=0.5, alpha=0.65)
    block_library = load_block_library()
    for current in model["furniture"]:
        x0, y0, x1, y1 = current["target_bbox_task01_mm"]
        optional = current["design_status"] in {"OPTIONAL", "OPTIONAL_FLEXIBLE", "OPTIONAL_MOVABLE"}
        ambiguous = current["design_status"] in {"INTENT_AMBIGUOUS", "EXISTING_GUIDE_TO_VERIFY", "EXISTING_OR_GUIDE_TO_VERIFY"}
        edge = "#6c757d" if optional else ("#d00000" if ambiguous else "#1d3557")
        face = "none" if optional else colors.get(current["functional_zone"], "#ced4da")
        patch = MplRectangle((x0, y0), x1 - x0, y1 - y0, facecolor=face, edgecolor=edge, linewidth=1.1, linestyle="--" if optional or ambiguous else "-", alpha=0.18 if current.get("render_block_id") else 0.8)
        ax.add_patch(patch)
        rendered_block = False
        if block_library is not None and current.get("render_block_id") and current.get("render_block_id") in block_library.blocks:
            rendered_block = draw_block(ax, block_library.blocks.get(current["render_block_id"]), current["target_bbox_task01_mm"], current.get("orientation", "axis_aligned"), color=edge, edge=edge, alpha=0.95, linestyle="--" if optional or ambiguous else "-")
        if x1 - x0 > 220 or y1 - y0 > 220:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, current["id"].replace("-", "\n"), ha="center", va="center", fontsize=5.4, color="#1d3557")
    for route in report["route_checks"]:
        x0, y0, x1, y1 = route["screening_envelope_mm"]
        ax.add_patch(MplRectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor="#00a896", linewidth=0.8, linestyle=":"))
    # The role labels are driven by the user's named FreeCAD guide, not the
    # historical room labels in geometry.json.
    ax.text(11400, 10450, "MIDDLE GUEST ROOM\n(次卧小床1.2)", ha="center", va="center", fontsize=8, color="#2b6f3e", weight="bold")
    ax.text(14800, 10450, "STUDY / BACKUP SLEEP\n(bookcase · tea table · desk)", ha="center", va="center", fontsize=8, color="#8a3153", weight="bold")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(1000, 16600)
    ax.set_ylim(-1000, 14500)
    ax.set_xlabel("Task01 X (mm)")
    ax.set_ylabel("Task01 Y (mm)")
    ax.set_title("S2 CURRENT DESIGN V1 — schematic human review\nNamed FreeCAD guide normalized to target footprints; formal CAD HOLD")
    legend = [
        Patch(facecolor="#6c757d", edgecolor="#343a40", label="Existing structure / walls"),
        Patch(facecolor="#52b6ca", edgecolor="#087f8c", alpha=0.55, label="Existing windows / glass openings"),
        Patch(facecolor="#e76f51", edgecolor="#9d2b1f", label="KEEP kitchen cabinet geometry"),
        Patch(facecolor="#8ecae6", edgecolor="#1d3557", label="Normalized active furniture"),
        Patch(facecolor="none", edgecolor="#6c757d", linestyle="--", label="Optional / movable"),
        Patch(facecolor="none", edgecolor="#d00000", label="Intent ambiguous / TO_VERIFY"),
        Patch(facecolor="none", edgecolor="#00a896", linestyle=":", label="Circulation screening envelope"),
    ]
    ax.legend(handles=legend, loc="upper left", fontsize=7, framealpha=0.92)
    fig.tight_layout()
    png = OUT / "S2_CURRENT_DESIGN_V1.png"
    pdf = OUT / "S2_CURRENT_DESIGN_V1.pdf"
    fig.savefig(png, dpi=220)
    with PdfPages(pdf) as pages:
        pages.savefig(fig)
    plt.close(fig)
    return png, pdf


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    guide = json.loads(GUIDE_FILE.read_text(encoding="utf-8"))
    geometry = json.loads(GEOMETRY_FILE.read_text(encoding="utf-8"))
    canonical = json.loads(CANONICAL_FILE.read_text(encoding="utf-8"))
    windows = json.loads(WINDOW_FILE.read_text(encoding="utf-8"))["windows"]
    kitchen_data = json.loads(KITCHEN_FILE.read_text(encoding="utf-8"))
    kitchen = kitchen_data["cabinets"]
    rooms = {row["id"]: row["polygon_mm"] for row in geometry["spaces"]}
    target_items = build_target_items()
    register = {
        "schema": "s2-furniture-dimension-register-v01",
        "status": "DRAFT_HUMAN_REVIEW",
        "source_guide": str(GUIDE_FILE),
        "target_geometry_policy": "guide topology and intent; normalized real-size footprints",
        "items": register_guides(guide, target_items),
    }
    (OUT / "furniture_dimension_register_v01.json").write_text(json.dumps(register, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    model = {
        "schema": "s2-current-design-v1-schematic-model",
        "status": "DRAFT_HUMAN_REVIEW",
        "formal_cad_allowed": False,
        "source_fcstd_sha256": sha256(BASE / "cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd"),
        "coordinate_system": "Task01 mm; FCStd absolute coordinates transformed by x-1298172, y+296458",
        "brief_constraints": {
            "south_zone": "study / backup sleeping",
            "middle_zone": "guest room",
            "guest_bath_boundary": "KEEP_CURRENT_SIZE",
            "kitchen": "KEEP",
            "north_balcony": "OPEN_NOT_ENCLOSED",
            "no_formal_cad_writeback": True,
        },
        "guide_based_room_roles": {
            "middle_guest_room": {
                "source_labels": ["次卧小床1.2", "次卧衣柜", "次卧凳子"],
                "historical_polygon_id": "R-STUDY",
                "authority": "FreeCAD human guide naming/topology",
            },
            "south_study_backup_sleep": {
                "source_labels": ["床背板+窄书桌占位", "书柜", "书柜001", "茶台", "主人椅", "条凳", "凳子"],
                "historical_polygon_id": "R-BED-N",
                "authority": "FreeCAD human guide naming/topology",
            },
            "historical_room_labels_are_not_function_authority": True,
        },
        "rooms": geometry["spaces"],
        "windows": windows,
        "furniture": target_items,
        "existing_keep": {"walls": canonical["walls"], "openings": canonical["openings"], "kitchen_cabinets": kitchen},
        "guide_lineage": "human_guide_inventory.json -> furniture_dimension_register_v01.json -> normalized schematic furniture",
    }
    (OUT / "design_model_v01.json").write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = build_report(target_items, rooms, canonical["openings"], kitchen)
    (OUT / "s2_collision_circulation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    png, pdf = render(model, report, rooms, windows, canonical["walls"], kitchen)
    audit = f"""# S2 CURRENT DESIGN V1 — Design Audit\n\nStatus: `DRAFT_HUMAN_REVIEW`\n\n## Scope\n\nThis is a schematic design review generated from the latest named FreeCAD guide. It does not modify the FCStd, canonical plan, V02/V03, formal CAD, or project approval gates.\n\n## Guide ingestion\n\n- Primary named guide objects: {guide['primary_guide_count']}\n- Auxiliary / unnamed objects retained: {guide['auxiliary_count']}\n- All unnamed auxiliary geometry remains semantically unresolved.\n- `电视柜（或者悬浮电视墙）` remains `INTENT_AMBIGUOUS`.\n- `次卧小床1.2` is normalized as a nominal 1200 mm bed-width guide.\n- `斜坡（轮椅用` remains an assisted-route guide with slope and final length `TO_VERIFY`.\n- Room-role authority follows the named FreeCAD guide: `次卧小床1.2` + `次卧衣柜` = middle guest room; `书柜` + `茶台` + `床背板+窄书桌占位` = study / backup sleep. Historical `R-STUDY` / `R-BED-N` labels are retained only as polygon references.\n\n## Current schematic decisions\n\n- Living: 3-seat sofa anchor + 2-seat conversation edge + at most one lounge chair; media edge remains secondary.\n- Dining: four daily seats linked to KEEP kitchen; G-DIN-LIV transition is explicitly checked.\n- Middle guest room: nominal 1200 mm bed guide retained as a normalized target.\n- South study / backup sleep: desk and storage remain primary; flexible seating is optional.\n- Guest bathroom: boundary unchanged; WC, vanity, shower and 3 kg washer are shown as a feasibility study.\n- Mother bathroom: aging-in-place shower/WC/vanity intent shown; exact clearances and services remain field/SKU verification.\n\n## Geometry screening\n\n- Furniture collisions: {report['collision_count']}\n- Door-swing conflicts: {len(report['door_swing_conflicts'])}\n- KEEP kitchen conflicts: {len(report['kitchen_keep_conflicts'])}\n- Route warnings: {sum(x['status'] == 'WARN' for x in report['route_checks'])}\n\nThe route values are axis-aligned schematic screening envelopes. They are not construction clearances or accessibility certification. `G-LIV-NBALC` remains an existing 850 mm limitation under a no-worsening rule.\n\n## Human review focus\n\n1. Does the normalized 3+2+lounge living group preserve the intended central activity field?\n2. Does the middle guest room remain comfortable at a nominal 1200 mm bed width?\n3. Can the unchanged guest bath hold shower, WC, vanity and small washer without compromising door use?\n4. Does the study remain a real work room while retaining backup sleep/flexible seating?\n5. Does dining preserve the kitchen relationship and leave the G-DIN-LIV transition usable?\n\n## Outputs\n\n- `human_guide_inventory.json`\n- `furniture_dimension_register_v01.json`\n- `design_model_v01.json`\n- `s2_collision_circulation_report.json`\n- `S2_CURRENT_DESIGN_V1.png`\n- `S2_CURRENT_DESIGN_V1.pdf`\n\nNext gate: human review. No S2 approval or formal CAD write-back is implied.\n"""
    (OUT / "S2_CURRENT_DESIGN_V1_design_audit.md").write_text(audit, encoding="utf-8")
    print(json.dumps({"status": "DRAFT_HUMAN_REVIEW", "collision_count": report["collision_count"], "route_warnings": sum(x["status"] == "WARN" for x in report["route_checks"]), "png": str(png), "pdf": str(pdf)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
