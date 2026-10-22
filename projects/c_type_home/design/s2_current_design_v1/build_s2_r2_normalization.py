#!/usr/bin/env python3
"""Incrementally normalize dimensions from the approved guide baseline.

No layout regeneration happens here. Every item begins at its exact guide bbox;
only explicitly listed footprint dimensions may change, with rotation locked to
zero. Conflicts remain visible for human review.
"""

from __future__ import annotations

from pathlib import Path
import json
import math
import sys

import ezdxf
from ezdxf import bbox as ez_bbox
from shapely.geometry import box as shape_box
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, Patch, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_s2_current_design_v1 import BLOCK_MAP, draw_block, load_block_library  # noqa: E402


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
BASELINE = OUT / "s2_guide_baseline_v1.json"
GUIDE = OUT / "human_guide_inventory.json"
GEOMETRY = BASE / "data/geometry.json"
CANONICAL = BASE / "current_existing/canonical_plan_v1.json"
WINDOWS = BASE / "current_existing/window_register.json"
KITCHEN = BASE / "current_existing/kitchen_cabinet_register.json"
WORKING_DXF = BASE / "cad/freecad_import/世纪欣园FF_freecad_WORKING.dxf"


def rect_from_anchor(bbox, width, depth, anchor="lower_left"):
    x0, y0, x1, y1 = bbox
    if anchor == "lower_left":
        return [x0, y0, x0 + width, y0 + depth]
    if anchor == "center":
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        return [cx - width / 2.0, cy - depth / 2.0, cx + width / 2.0, cy + depth / 2.0]
    if anchor == "right_lower":
        return [x1 - width, y0, x1, y0 + depth]
    raise ValueError(anchor)


def orientation_axis(bbox):
    if not bbox:
        return "UNKNOWN"
    width = bbox[2] - bbox[0]
    depth = bbox[3] - bbox[1]
    if abs(width - depth) <= 1.0:
        return "SQUARE"
    return "LONG_AXIS_X" if width > depth else "LONG_AXIS_Y"


# Footprints are expressed in the guide's existing axis orientation. No entry
# below changes rotation; a source guide that cannot safely be standardized is
# intentionally left unchanged and marked TO_VERIFY.
NORMALIZATION_SPECS = {
    "SOFA_3S": {"dims": (900, 2200), "anchor": "lower_left", "source_type": "STANDARD_REFERENCE", "reason": "standard 3-seat sofa footprint; preserve guide long axis Y"},
    "SOFA_2S": {"dims": (1800, 850), "anchor": "lower_left", "source_type": "STANDARD_REFERENCE", "reason": "standard 2-seat sofa footprint; preserve guide long axis X"},
    "DINING_TABLE": {"dims": (1500, 600), "anchor": "lower_left", "source_type": "USER_CONFIRMED", "reason": "brief nominal dining table; preserve guide long axis X"},
    "DINING_CHAIR_1": {"dims": (450, 500), "anchor": "center", "source_type": "STANDARD_REFERENCE", "reason": "standard dining chair footprint; preserve guide seat center"},
    "DINING_CHAIR_2": {"dims": (450, 500), "anchor": "center", "source_type": "STANDARD_REFERENCE", "reason": "standard dining chair footprint; preserve guide seat center"},
    "DINING_CHAIR_3": {"dims": (450, 500), "anchor": "center", "source_type": "STANDARD_REFERENCE", "reason": "standard dining chair footprint; preserve guide seat center"},
    "DINING_CHAIR_4": {"dims": (450, 500), "anchor": "center", "source_type": "STANDARD_REFERENCE", "reason": "standard dining chair footprint; preserve guide seat center"},
    # The original beds are horizontal in the Guide. Keep that axis; do not
    # turn a 2100x1500 guide into a 90-degree 1800x2100 placement.
    "BED_OWNER": {"dims": (2100, 1800), "anchor": "lower_left", "source_type": "STANDARD_REFERENCE", "reason": "standard 1800x2100 nominal bed mapped to locked guide axes; headboard side remains TO_VERIFY"},
    "BED_MOTHER": {"dims": (2100, 1800), "anchor": "lower_left", "source_type": "STANDARD_REFERENCE", "reason": "standard 1800x2100 nominal bed mapped to locked guide axes; headboard side remains TO_VERIFY"},
    "BED_GUEST_1200": {"dims": (2000, 1200), "anchor": "lower_left", "source_type": "USER_CONFIRMED", "reason": "nominal 1200mm guest bed width; preserve guide long axis X"},
    "STUDY_DESK_BACKBOARD": {"dims": (800, 1700), "anchor": "lower_left", "source_type": "STANDARD_REFERENCE", "reason": "standard desk footprint; preserve guide long axis Y and work zone"},
    "SHOWER_GUEST": {"dims": (900, 1200), "anchor": "lower_left", "source_type": "STANDARD_REFERENCE", "reason": "standard shower target within unchanged guest bath"},
    "WC_GUEST": {"dims": (450, 700), "anchor": "lower_left", "source_type": "STANDARD_REFERENCE", "reason": "standard WC footprint within unchanged guest bath"},
    "VANITY_GUEST": {"dims": (600, 500), "anchor": "lower_left", "source_type": "STANDARD_REFERENCE", "reason": "standard vanity footprint within unchanged guest bath"},
    "SHOWER_MOTHER": {"dims": (1000, 1200), "anchor": "lower_left", "source_type": "STANDARD_REFERENCE", "reason": "aging-in-place shower target; threshold/seat/clearance remain TO_VERIFY"},
    "WC_MOTHER": {"dims": (450, 700), "anchor": "lower_left", "source_type": "STANDARD_REFERENCE", "reason": "standard WC footprint within unchanged mother bath"},
    "VANITY_MOTHER": {"dims": (1200, 500), "anchor": "lower_left", "source_type": "USER_CONFIRMED", "reason": "guide cabinet width retained; depth standardized"},
}


def load_data():
    return (
        json.loads(BASELINE.read_text(encoding="utf-8")),
        json.loads(GUIDE.read_text(encoding="utf-8")),
        json.loads(GEOMETRY.read_text(encoding="utf-8")),
        json.loads(CANONICAL.read_text(encoding="utf-8")),
        json.loads(WINDOWS.read_text(encoding="utf-8"))["windows"],
        json.loads(KITCHEN.read_text(encoding="utf-8"))["cabinets"],
    )


def make_change_rows(baseline, guide):
    by_semantic = {row["semantic_id"]: row for row in guide["primary_guides"]}
    rows = []
    for check in baseline["object_checks"]:
        semantic = check["semantic_id"]
        original = check["guide_bbox_task01_mm"]
        spec = NORMALIZATION_SPECS.get(semantic)
        guide_row = by_semantic.get(semantic, {})
        if not original:
            continue
        if spec:
            width, depth = spec["dims"]
            normalized = rect_from_anchor(original, width, depth, spec["anchor"])
            source_type = spec["source_type"]
            reason = spec["reason"]
            anchor_type = spec["anchor"]
            status = "DIMENSION_NORMALIZED"
        else:
            normalized = list(original)
            source_type = "USER_CONFIRMED" if guide_row.get("guide_status") not in {"INTENT_AMBIGUOUS", "ACCESSIBILITY_RAMP_GUIDE"} else "TO_VERIFY"
            reason = "preserve exact named guide; no safe automatic standardization without changing intent"
            anchor_type = "GUIDE_BBOX_LOCKED"
            status = "UNCHANGED_GUIDE" if source_type == "USER_CONFIRMED" else "TO_VERIFY"
        guide_center = [(original[0] + original[2]) / 2.0, (original[1] + original[3]) / 2.0]
        normalized_center = [(normalized[0] + normalized[2]) / 2.0, (normalized[1] + normalized[3]) / 2.0]
        center_delta = [normalized_center[0] - guide_center[0], normalized_center[1] - guide_center[1]]
        if spec and spec["anchor"] == "center":
            dx = 0.0
            dy = 0.0
        elif spec and spec["anchor"] == "right_lower":
            dx = 0.0
            dy = normalized[1] - original[1]
        else:
            dx = normalized[0] - original[0]
            dy = normalized[1] - original[1]
        rotation_delta = 0.0
        axis_change = orientation_axis(original) != orientation_axis(normalized)
        if orientation_axis(original) in {"SQUARE", "RADIAL"}:
            axis_change = False
        if axis_change and semantic in NORMALIZATION_SPECS:
            status = "HUMAN_REVIEW_REQUIRED"
            reason += "; proposed footprint axes would change semantic orientation; proposal not auto-applied"
            normalized = list(original)
            normalized_center = guide_center
            center_delta = [0.0, 0.0]
            dx = 0.0
            dy = 0.0
        rows.append({
            "source_object_name": check["source_object_name"],
            "source_label": check["source_label"],
            "semantic_id": semantic,
            "functional_zone": check["functional_zone"],
            "historical_polygon_id": check["historical_polygon_id"],
            "original_bbox_task01_mm": original,
            "normalized_bbox_task01_mm": normalized,
            "proposed_normalized_bbox_task01_mm": None,
            "original_size_mm": [original[2] - original[0], original[3] - original[1]],
            "normalized_size_mm": [normalized[2] - normalized[0], normalized[3] - normalized[1]],
            "anchor_type": anchor_type,
            "dx_mm": round(dx, 3),
            "dy_mm": round(dy, 3),
            "center_delta_mm": [round(center_delta[0], 3), round(center_delta[1], 3)],
            "rotation_delta_deg": rotation_delta,
            "original_orientation": orientation_axis(original),
            "normalized_orientation": orientation_axis(normalized),
            "orientation_axis_changed": axis_change,
            "reason": reason,
            "source_type": source_type,
            "normalization_status": status,
            "layout_intent": "LOCKED",
            "render_block_id": BLOCK_MAP.get(semantic),
            "proposed_normalized_size_mm": list(spec["dims"]) if spec and axis_change else None,
        })
    # The 3kg washer is a brief requirement without a named FCStd anchor.
    rows.append({
        "source_object_name": None,
        "source_label": "客卫3kg小洗衣机",
        "semantic_id": "WASHER_SMALL_3KG",
        "functional_zone": "guest_bath",
        "historical_polygon_id": "R-BATH-P",
        "original_bbox_task01_mm": None,
        "normalized_bbox_task01_mm": None,
        "proposed_normalized_bbox_task01_mm": None,
        "original_size_mm": None,
        "normalized_size_mm": [600, 650],
        "anchor_type": "NO_GUIDE_ANCHOR",
        "dx_mm": None,
        "dy_mm": None,
        "center_delta_mm": None,
        "rotation_delta_deg": 0.0,
        "original_orientation": "UNKNOWN",
        "normalized_orientation": "UNKNOWN",
        "orientation_axis_changed": False,
        "reason": "brief requirement exists but no named FCStd anchor; do not place automatically",
        "source_type": "TO_VERIFY",
        "normalization_status": "TO_VERIFY",
        "layout_intent": "LOCKED",
        "render_block_id": BLOCK_MAP.get("WASHER_SMALL_3KG"),
        "proposed_normalized_size_mm": [600, 650],
    })
    return rows


def room_checks(rows, spaces):
    polygons = {row["id"]: shape_box(min(p[0] for p in row["polygon_mm"]), min(p[1] for p in row["polygon_mm"]), max(p[0] for p in row["polygon_mm"]), max(p[1] for p in row["polygon_mm"])) for row in spaces}
    checks = []
    for row in rows:
        bbox = row["normalized_bbox_task01_mm"]
        room = row["historical_polygon_id"]
        if not bbox or room not in polygons:
            continue
        footprint = shape_box(*bbox)
        ratio = footprint.intersection(polygons[room]).area / max(footprint.area, 1.0)
        original = row.get("original_bbox_task01_mm")
        original_ratio = ratio
        if original:
            original_shape = shape_box(*original)
            original_ratio = original_shape.intersection(polygons[room]).area / max(original_shape.area, 1.0)
        if ratio >= 0.98:
            status = "PASS"
        elif original_ratio < 0.98 and ratio >= original_ratio - 0.001:
            status = "EXISTING_GUIDE_OUTSIDE"
        else:
            status = "CONFLICT"
        checks.append({"semantic_id": row["semantic_id"], "room": room, "inside_ratio": round(ratio, 3), "original_inside_ratio": round(original_ratio, 3), "status": status})
    return checks


def collision_checks(rows, openings, kitchen):
    active = [row for row in rows if row["normalized_bbox_task01_mm"] and row["normalization_status"] not in {"TO_VERIFY", "OPTIONAL", "OPTIONAL_FLEXIBLE", "OPTIONAL_MOVABLE"} and not row["semantic_id"].endswith("_WET_ZONE")]
    baseline_active = [row for row in rows if row["original_bbox_task01_mm"] and row["normalization_status"] not in {"TO_VERIFY", "OPTIONAL", "OPTIONAL_FLEXIBLE", "OPTIONAL_MOVABLE"} and not row["semantic_id"].endswith("_WET_ZONE")]
    shapes = {row["semantic_id"] + ":" + row["source_object_name"] if row["source_object_name"] else row["semantic_id"]: shape_box(*row["normalized_bbox_task01_mm"]) for row in active}
    collisions = []
    for index, first in enumerate(active):
        first_key = first["semantic_id"] + ":" + first["source_object_name"] if first["source_object_name"] else first["semantic_id"]
        for second in active[index + 1:]:
            second_key = second["semantic_id"] + ":" + second["source_object_name"] if second["source_object_name"] else second["semantic_id"]
            overlap = shapes[first_key].intersection(shapes[second_key]).area
            if overlap > 10000.0:
                base_first = next((x for x in baseline_active if x["semantic_id"] == first["semantic_id"] and x["source_object_name"] == first["source_object_name"]), None)
                base_second = next((x for x in baseline_active if x["semantic_id"] == second["semantic_id"] and x["source_object_name"] == second["source_object_name"]), None)
                base_overlap = 0.0
                if base_first and base_second:
                    base_overlap = shape_box(*base_first["original_bbox_task01_mm"]).intersection(shape_box(*base_second["original_bbox_task01_mm"])).area
                collisions.append({"a": first_key, "b": second_key, "overlap_mm2": round(overlap, 1), "baseline_overlap_mm2": round(base_overlap, 1), "status": "EXISTING_GUIDE_COLLISION" if base_overlap > 10000.0 else "FURNITURE_COLLISION"})
    door_conflicts = []
    for opening in openings:
        opening_shape = shape_box(*opening["rect_mm"])
        for row in active:
            key = row["semantic_id"] + ":" + row["source_object_name"] if row["source_object_name"] else row["semantic_id"]
            overlap = shapes[key].intersection(opening_shape).area
            if overlap > 1.0:
                base_overlap = 0.0
                if row.get("original_bbox_task01_mm"):
                    base_overlap = shape_box(*row["original_bbox_task01_mm"]).intersection(opening_shape).area
                door_conflicts.append({"opening": opening["id"], "item": key, "overlap_mm2": round(overlap, 1), "baseline_overlap_mm2": round(base_overlap, 1), "status": "EXISTING_GUIDE_DOOR_CONFLICT" if base_overlap > 1.0 else "DOOR_SWING_CONFLICT"})
    kitchen_conflicts = []
    cabinet_shapes = [shape_box(*cabinet["rect_mm"]) for cabinet in kitchen]
    for row in active:
        if row["functional_zone"] != "kitchen" or row["semantic_id"] in {"KITCHEN_KEEP", "KITCHEN_AUX_STORAGE"}:
            continue
        current = shape_box(*row["normalized_bbox_task01_mm"])
        for index, cabinet in enumerate(cabinet_shapes):
            overlap = current.intersection(cabinet).area
            if overlap > 1.0:
                kitchen_conflicts.append({"item": row["semantic_id"], "cabinet_index": index, "overlap_mm2": round(overlap, 1), "status": "KEEP_GEOMETRY_CONFLICT"})
    return collisions, door_conflicts, kitchen_conflicts


def route_checks(rows):
    active = [row for row in rows if row.get("normalized_bbox_task01_mm") and row["normalization_status"] not in {"TO_VERIFY"}]
    shapes = [shape_box(*row["normalized_bbox_task01_mm"]) for row in active]
    routes = [
        ("entry_to_living", 1100, [2900, 6500, 4200, 7900], "y"),
        ("living_to_stair", 1100, [5600, 6500, 7200, 7900], "x"),
        ("living_to_north_balcony", 850, [7200, 11400, 7900, 12750], "x"),
        ("dining_to_keep_kitchen", 1000, [5000, 2500, 5900, 4300], "x"),
        ("dining_to_glass_transition", 900, [2900, 4050, 5650, 4530], "y"),
        ("guest_room_to_balcony", 900, [12000, 10500, 13000, 10900], "x"),
    ]
    results = []
    for route_id, target, envelope, axis in routes:
        corridor = shape_box(*envelope)
        intersecting = [shape for shape in shapes if shape.intersection(corridor).area > 1.0]
        if axis == "x":
            nominal = envelope[3] - envelope[1]
            occupied = max((min(shape.bounds[3], envelope[3]) - max(shape.bounds[1], envelope[1]) for shape in intersecting), default=0.0)
        else:
            nominal = envelope[2] - envelope[0]
            occupied = max((min(shape.bounds[2], envelope[2]) - max(shape.bounds[0], envelope[0]) for shape in intersecting), default=0.0)
        measured = max(0.0, nominal - occupied)
        results.append({"id": route_id, "target_clear_width_mm": target, "proxy_measured_clear_width_mm": round(measured, 1), "status": "PASS" if measured >= target else "WARN", "method": "axis-aligned schematic screening", "existing_limit_note": "G-LIV-NBALC 850mm is an existing limitation" if route_id == "living_to_north_balcony" else None})
    return results


def rollback_room_containment_conflicts(rows, containment):
    """Keep the locked guide footprint when a target size leaves its room."""
    for check in containment:
        if check["status"] != "CONFLICT":
            continue
        candidates = [row for row in rows if row["semantic_id"] == check["semantic_id"] and row.get("historical_polygon_id") == check["room"] and row.get("normalized_bbox_task01_mm")]
        for row in candidates:
            row["proposed_normalized_bbox_task01_mm"] = list(row["normalized_bbox_task01_mm"])
            row["normalized_bbox_task01_mm"] = list(row["original_bbox_task01_mm"])
            row["normalized_size_mm"] = [row["original_size_mm"][0], row["original_size_mm"][1]]
            row["dx_mm"] = 0.0
            row["dy_mm"] = 0.0
            row["center_delta_mm"] = [0.0, 0.0]
            row["normalization_status"] = "CONFLICT"
            row["reason"] += "; proposed standard footprint would leave the locked room boundary; proposal not applied"


def render_plan(rows, spaces, walls, windows, kitchen, path, diff=False):
    fig, ax = plt.subplots(figsize=(16, 12), dpi=180)
    for wall in walls:
        x0, y0, x1, y1 = wall["rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#6c757d", edgecolor="#343a40", linewidth=0.45, alpha=0.75))
    for opening in windows:
        x0, y0, x1, y1 = opening["opening_rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#52b6ca", edgecolor="#087f8c", linewidth=1.0, alpha=0.55))
    for cabinet in kitchen:
        x0, y0, x1, y1 = cabinet["rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#e76f51", edgecolor="#9d2b1f", linewidth=0.5, alpha=0.65))
    for row in rows:
        original = row["original_bbox_task01_mm"]
        normalized = row["normalized_bbox_task01_mm"]
        if original and diff:
            x0, y0, x1, y1 = original
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor="#777777", linewidth=0.8, linestyle="--", alpha=0.7))
        if not normalized:
            continue
        x0, y0, x1, y1 = normalized
        conflict = row["normalization_status"] in {"CONFLICT", "HUMAN_REVIEW_REQUIRED"}
        color = "#d00000" if conflict else "#1d3557"
        face = "none" if diff else ("#ffd6d6" if conflict else "#bde0fe")
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=face, edgecolor=color, linewidth=1.1, linestyle="-"))
        dx, dy = row["dx_mm"], row["dy_mm"]
        if diff and original and (abs(dx or 0) > 0.1 or abs(dy or 0) > 0.1):
            gcx = (original[0] + original[2]) / 2.0
            gcy = (original[1] + original[3]) / 2.0
            ncx = (normalized[0] + normalized[2]) / 2.0
            ncy = (normalized[1] + normalized[3]) / 2.0
            ax.annotate("", xy=(ncx, ncy), xytext=(gcx, gcy), arrowprops={"arrowstyle": "->", "color": color, "linewidth": 1.0})
            ax.text(ncx, ncy, f"dx={dx:.0f} dy={dy:.0f}", fontsize=5, color=color)
        if x1 - x0 > 350 or y1 - y0 > 350:
            ax.text((x0 + x1) / 2.0, (y0 + y1) / 2.0, row["semantic_id"].replace("_", "\n"), ha="center", va="center", fontsize=5.0, color=color)
    ax.text(11400, 10450, "MIDDLE GUEST ROOM\n(locked guide role)", ha="center", va="center", fontsize=8, color="#2b6f3e", weight="bold")
    ax.text(14800, 10450, "STUDY / BACKUP SLEEP\n(locked guide role)", ha="center", va="center", fontsize=8, color="#8a3153", weight="bold")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(1000, 16600)
    ax.set_ylim(-1000, 14500)
    ax.set_xlabel("Task01 X (mm)")
    ax.set_ylabel("Task01 Y (mm)")
    ax.set_title("S2 CURRENT DESIGN V1 R2 — anchor-preserving normalization" + ("\nDIFF: dashed gray = approved Guide; solid = R2" if diff else "\nHuman layout intent locked; formal CAD HOLD"))
    legend = [
        Patch(facecolor="#6c757d", edgecolor="#343a40", label="Existing structure / walls"),
        Patch(facecolor="#bde0fe", edgecolor="#1d3557", label="R2 normalized footprint"),
        Patch(facecolor="none", edgecolor="#777777", linestyle="--", label="Approved Guide baseline"),
        Patch(facecolor="#ffd6d6", edgecolor="#d00000", label="Conflict / human review required"),
    ]
    ax.legend(handles=legend, loc="upper left", fontsize=7, framealpha=0.92)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    return fig


def write_dxf(rows):
    doc = ezdxf.readfile(WORKING_DXF)
    for name, color in (("S2_R2_GUIDE_BASELINE", 8), ("S2_R2_FURNITURE", 3), ("S2_R2_CONFLICT", 1)):
        if name not in doc.layers:
            doc.layers.new(name, dxfattribs={"color": color})
    msp = doc.modelspace()
    ox, oy = 1298172.0, -296458.0
    for row in rows:
        original = row["original_bbox_task01_mm"]
        normalized = row["normalized_bbox_task01_mm"]
        if original:
            x0, y0, x1, y1 = original
            msp.add_lwpolyline([(x0 + ox, y0 + oy), (x1 + ox, y0 + oy), (x1 + ox, y1 + oy), (x0 + ox, y1 + oy)], close=True, dxfattribs={"layer": "S2_R2_GUIDE_BASELINE"})
        if normalized:
            x0, y0, x1, y1 = normalized
            layer = "S2_R2_CONFLICT" if row["normalization_status"] in {"CONFLICT", "HUMAN_REVIEW_REQUIRED"} else "S2_R2_FURNITURE"
            msp.add_lwpolyline([(x0 + ox, y0 + oy), (x1 + ox, y0 + oy), (x1 + ox, y1 + oy), (x0 + ox, y1 + oy)], close=True, dxfattribs={"layer": layer})
    output = OUT / "S2_CURRENT_DESIGN_V1_R2.dxf"
    doc.saveas(output)
    return output


def main():
    baseline, guide, geometry, canonical, windows, kitchen = load_data()
    if baseline["fidelity_gate"] != "PASS":
        raise RuntimeError("Guide fidelity baseline is not PASS; R2 is blocked")
    rows = make_change_rows(baseline, guide)
    spaces = geometry["spaces"]
    containment = room_checks(rows, spaces)
    rollback_room_containment_conflicts(rows, containment)
    containment = room_checks(rows, spaces)
    collisions, door_conflicts, kitchen_conflicts = collision_checks(rows, canonical["openings"], kitchen)
    route_results = route_checks(rows)
    nonzero_rotation = [row for row in rows if row["rotation_delta_deg"] not in (None, 0.0)]
    room_reassignments = [row for row in rows if row["historical_polygon_id"] != next((x["historical_polygon_id"] for x in baseline["object_checks"] if x["semantic_id"] == row["semantic_id"]), row["historical_polygon_id"])]
    normalized_model = {
        "schema": "s2-current-design-v1-r2-normalized-model",
        "status": "DRAFT_HUMAN_REVIEW",
        "formal_cad_allowed": False,
        "source_baseline": str(BASELINE),
        "human_layout_intent": "LOCKED",
        "rotation_policy": "rotation_delta_default_zero; nonzero requires human approval",
        "guide_based_room_roles": {
            "middle_guest_room": ["次卧小床1.2", "次卧衣柜", "次卧凳子"],
            "south_study_backup_sleep": ["床背板+窄书桌占位", "书柜", "书柜001", "茶台", "主人椅", "条凳", "凳子"],
        },
        "items": rows,
        "containment_checks": containment,
        "conflicts": {"furniture": collisions, "door_swing": door_conflicts, "kitchen_keep": kitchen_conflicts},
        "route_checks": route_results,
    }
    (OUT / "S2_CURRENT_DESIGN_V1_R2_model.json").write_text(json.dumps(normalized_model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "furniture_dimension_register_v02.json").write_text(json.dumps({"schema": "s2-furniture-dimension-register-v02", "status": "DRAFT_HUMAN_REVIEW", "items": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    change_log = {
        "schema": "normalization-change-log-v01",
        "status": "DRAFT_HUMAN_REVIEW",
        "source": "S2_GUIDE_BASELINE_V1",
        "rules": {"room_reassignment": 0, "wall_reassignment": 0, "rotation_delta_default_deg": 0, "large_relayout": "forbidden"},
        "changes": rows,
        "summary": {"dimension_changes": sum(row["normalization_status"] == "DIMENSION_NORMALIZED" for row in rows), "unchanged": sum(row["normalization_status"] == "UNCHANGED_GUIDE" for row in rows), "to_verify": sum(row["normalization_status"] == "TO_VERIFY" for row in rows), "conflicts": len(collisions) + len(door_conflicts) + len(kitchen_conflicts)},
    }
    (OUT / "normalization_change_log_v01.json").write_text(json.dumps(change_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    png = OUT / "S2_CURRENT_DESIGN_V1_R2.png"
    pdf = OUT / "S2_CURRENT_DESIGN_V1_R2.pdf"
    fig = render_plan(rows, spaces, canonical["walls"], windows, kitchen, png, diff=False)
    with PdfPages(pdf) as pages:
        pages.savefig(fig)
    plt.close(fig)
    diff_png = OUT / "S2_R2_DIFF_OVERLAY.png"
    fig = render_plan(rows, spaces, canonical["walls"], windows, kitchen, diff_png, diff=True)
    plt.close(fig)
    dxf = write_dxf(rows)
    review = f"""# S2 CURRENT DESIGN V1 R2 — Review\n\nStatus: `DRAFT_HUMAN_REVIEW`\n\n## Policy\n\nThis R2 is an incremental normalization from the approved Guide Baseline. Human layout intent is locked. No room reassignment, wall reassignment, automatic rotation, or furniture re-layout is performed.\n\n## Gate results\n\n- Guide fidelity baseline: `PASS`\n- Room reassignment: {len(room_reassignments)}\n- Nonzero rotations: {len(nonzero_rotation)}\n- Furniture collisions: {len(collisions)}\n- Door-swing conflicts: {len(door_conflicts)}\n- KEEP kitchen conflicts: {len(kitchen_conflicts)}\n- Route warnings: {sum(x['status'] == 'WARN' for x in route_results)}\n- Normalization proposals not applied because they would violate the locked room boundary: {sum(row['normalization_status'] == 'CONFLICT' for row in rows)}\n- Operation-space / room containment conflicts: {sum(x['status'] == 'CONFLICT' for x in containment)}\n\n## Anchor policy\n\nBeds, wardrobes, desks, sofas, dining table and wet fixtures keep their guide bbox anchor and axis. Dimension changes use the lower-left or center anchor recorded per object. No object is moved more than the recorded `dx_mm` / `dy_mm`; any conflict remains visible for human review.\n\n## Required human review\n\n- Bed headboard-side interpretation remains `TO_VERIFY` where the guide shape alone does not identify it.\n- The guest 3 kg washer has no named FCStd anchor and is not auto-placed.\n- Any item with `TO_VERIFY`, `HUMAN_REVIEW_REQUIRED`, or `CONFLICT` must be resolved by review before another revision.\n- The guest-room-to-balcony screening route remains below its 900 mm reference target in the schematic check; no furniture was rotated to hide this.\n\n## Outputs\n\n- `S2_CURRENT_DESIGN_V1_R2.FCStd`\n- `S2_CURRENT_DESIGN_V1_R2.dxf`\n- `S2_CURRENT_DESIGN_V1_R2.png`\n- `S2_CURRENT_DESIGN_V1_R2.pdf`\n- `S2_R2_DIFF_OVERLAY.png`\n- `furniture_dimension_register_v02.json`\n- `normalization_change_log_v01.json`\n\nBlender and formal CAD remain HOLD.\n"""
    (OUT / "S2_R2_review.md").write_text(review, encoding="utf-8")
    print(json.dumps({"status": "DRAFT_HUMAN_REVIEW", "nonzero_rotations": len(nonzero_rotation), "collisions": len(collisions), "door_conflicts": len(door_conflicts), "dxf": str(dxf), "png": str(png), "diff": str(diff_png)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
