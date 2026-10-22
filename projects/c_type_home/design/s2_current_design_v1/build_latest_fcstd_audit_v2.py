#!/usr/bin/env python3
"""Latest-FCStd-only baseline and geometry audit; no redesign."""

from __future__ import annotations

from pathlib import Path
import json
import math
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Arc, Patch, Rectangle
from shapely.geometry import box as shape_box


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
INGEST = OUT / "latest_fcstd_ingest_v2.json"
FCSTD = BASE / "cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd"
GEOMETRY = BASE / "data/geometry.json"
CANONICAL = BASE / "current_existing/canonical_plan_v1.json"
WINDOWS = BASE / "current_existing/window_register.json"
KITCHEN = BASE / "current_existing/kitchen_cabinet_register.json"
OX, OY = 1298172.0, -296458.0

AUX_LABELS = {"Rectangle", "Rectangle033", "Circle013", "Line517", "Line518", "Line519", "Text", "Text001", "Text002"}


def task_bbox(row):
    b = row.get("bbox_abs_mm")
    if not b:
        return None
    return [b[0] - OX, b[1] - OY, b[2] - OX, b[3] - OY]


def role(label):
    if any(k in label for k in ("沙发", "角几", "茶几", "lounge", "电视柜", "三人位")): return "living"
    if "餐" in label: return "dining"
    if "次主卧" in label: return "owner_bedroom"
    if "主卧" in label: return "mother_bedroom"
    if "次卧" in label: return "middle_guest_room"
    if any(k in label for k in ("书柜", "茶台", "主人椅", "条凳", "凳子", "床背板")): return "south_study"
    if "客卫" in label: return "guest_bath"
    if "次主卫" in label: return "owner_ensuite"
    if "主卫" in label: return "mother_bathroom"
    if any(k in label for k in ("冰柜", "洗衣机", "烘干机")): return "north_balcony"
    if any(k in label for k in ("橱柜", "厨房")): return "kitchen"
    if "斜坡" in label: return "transition"
    if "鞋柜" in label: return "entry"
    return "unknown"


def orientation(bbox):
    if not bbox: return "UNKNOWN"
    w, d = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if abs(w - d) <= 1: return "SQUARE_OR_RADIAL"
    return "LONG_AXIS_X" if w > d else "LONG_AXIS_Y"


def display_label(row):
    label = row.get("label", "")
    if all(ord(char) < 128 for char in label):
        return label
    return row.get("room_role", "guide").replace("_", " ").upper()


def load():
    return (json.loads(INGEST.read_text(encoding="utf-8")), json.loads(GEOMETRY.read_text(encoding="utf-8")), json.loads(CANONICAL.read_text(encoding="utf-8")), json.loads(WINDOWS.read_text(encoding="utf-8"))["windows"], json.loads(KITCHEN.read_text(encoding="utf-8"))["cabinets"])


def primary_objects(ingest):
    rows = []
    for row in ingest["objects"]:
        if row["label"] in AUX_LABELS: continue
        bbox = task_bbox(row)
        if not bbox: continue
        rows.append({
            "object_name": row["name"], "label": row["label"], "type": row["type"],
            "room_role": role(row["label"]), "bbox_task01_mm": bbox,
            "center_task01_mm": [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2],
            "orientation": orientation(bbox), "layout_intent": "LOCKED",
        })
    return rows


def room_boxes(geometry):
    return {row["id"]: shape_box(min(p[0] for p in row["polygon_mm"]), min(p[1] for p in row["polygon_mm"]), max(p[0] for p in row["polygon_mm"]), max(p[1] for p in row["polygon_mm"])) for row in geometry["spaces"]}


def find(rows, label):
    return next((row for row in rows if row["label"] == label), None)


def dist_metrics(rows, geometry):
    rooms = room_boxes(geometry)
    metrics = []
    room_for = {"次卧小床1.2": "R-STUDY", "次主卧床": "R-BED-S", "主卧床": "R-MASTER"}
    for label, room in room_for.items():
        row = find(rows, label)
        if not row: continue
        b = row["bbox_task01_mm"]; rb = rooms[room].bounds
        metrics += [
            {"metric": label + " side clearance", "available_mm": round(min(b[0] - rb[0], rb[2] - b[2]), 1), "target_mm": 600, "status": "PASS" if min(b[0] - rb[0], rb[2] - b[2]) >= 600 else "CONFLICT", "source": "latest FCStd bbox to historical room polygon"},
            {"metric": label + " foot clearance", "available_mm": round(rb[3] - b[3], 1), "target_mm": 600, "status": "PASS" if rb[3] - b[3] >= 600 else "CONFLICT", "source": "latest FCStd bbox to historical room polygon"},
        ]
    for label, room, front_target in (("客卫马桶", "R-BATH-P", 800), ("主卫马桶", "R-BATH-M", 800), ("次主卫马桶", "R-CLOAK", 800)):
        row = find(rows, label)
        if not row: continue
        rb = rooms.get(room); b = row["bbox_task01_mm"]
        if not rb: continue
        metrics.append({"metric": label + " front clearance", "available_mm": round(rb.bounds[3] - b[3], 1), "target_mm": front_target, "status": "PASS" if rb.bounds[3] - b[3] >= front_target else "CONFLICT", "source": "latest FCStd fixture bbox / candidate room polygon"})
    # Individual dining chairs: do not collapse them into one shared result.
    table = find(rows, "餐桌")
    if table:
        tb = table["bbox_task01_mm"]
        for label in ("餐椅", "餐椅003", "餐椅004", "Circle013"):
            chair = find(rows, label)
            if not chair: continue
            cb = chair["bbox_task01_mm"]
            metrics.append({"metric": label + " table gap", "available_mm": round(min(abs(cb[0] - tb[2]), abs(tb[0] - cb[2]), abs(cb[1] - tb[3]), abs(tb[1] - cb[3])), 1), "target_mm": 150, "status": "PASS" if min(abs(cb[0] - tb[2]), abs(tb[0] - cb[2]), abs(cb[1] - tb[3]), abs(tb[1] - cb[3])) >= 150 else "CONFLICT", "source": "latest FCStd table/chair bboxes"})
    for label in ("次主卫湿区", "主卫湿区", "客卫（湿区）"):
        row = find(rows, label)
        if row:
            metrics.append({"metric": label + " internal footprint", "available_mm": round((row["bbox_task01_mm"][2] - row["bbox_task01_mm"][0]) * (row["bbox_task01_mm"][3] - row["bbox_task01_mm"][1]) / 1_000_000, 2), "target_mm": None, "status": "TO_VERIFY", "source": "latest named FCStd wet-zone guide", "notes": ["area is reference only; actual fixture usability is assessed separately"]})
    return metrics


def door_report(rows, openings):
    report = []
    for opening in openings:
        ob = opening["rect_mm"]; op = shape_box(*ob)
        for row in rows:
            b = row["bbox_task01_mm"]
            overlap = op.intersection(shape_box(*b)).area
            distance = op.distance(shape_box(*b))
            if overlap > 1.0 or distance < 100.0:
                report.append({"door_id": opening["id"], "room": opening.get("kind"), "object": row["label"], "swing_angle": "TO_VERIFY_90_DEG_SCHEMATIC", "minimum_distance_mm": round(distance, 1), "overlap_mm2": round(overlap, 1), "status": "CONFLICT" if overlap > 1 else "CLEARANCE_LOW"})
    return report


def render(rows, extra_labels, geometry, canonical, windows, kitchen, output_png, output_pdf):
    fig, ax = plt.subplots(figsize=(16, 12), dpi=180)
    for wall in canonical["walls"]:
        x0, y0, x1, y1 = wall["rect_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#6c757d", edgecolor="#343a40", linewidth=0.45, alpha=0.75))
    for window in windows:
        x0, y0, x1, y1 = window["opening_rect_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#52b6ca", edgecolor="#087f8c", linewidth=1.0, alpha=0.55))
    for opening in canonical["openings"]:
        x0, y0, x1, y1 = opening["rect_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor="#495057", linewidth=0.8))
        radius = max(x1 - x0, y1 - y0); ax.add_patch(Arc((x0, y0), 2 * radius, 2 * radius, angle=0, theta1=0, theta2=90, color="#495057", linewidth=0.55))
    for cabinet in kitchen:
        x0, y0, x1, y1 = cabinet["rect_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#e76f51", edgecolor="#9d2b1f", linewidth=0.5, alpha=0.65))
    colors = {"living": "#bde0fe", "dining": "#ffb703", "owner_bedroom": "#bde0fe", "mother_bedroom": "#cdb4db", "middle_guest_room": "#caffbf", "south_study": "#ffc8dd", "guest_bath": "#90dbf4", "owner_ensuite": "#e0aaff", "mother_bathroom": "#a8dadc", "north_balcony": "#ffd6a5"}
    for row in rows:
        x0, y0, x1, y1 = row["bbox_task01_mm"]; color = colors.get(row["room_role"], "#ced4da"); ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=color, edgecolor="#1d3557", linewidth=0.8, alpha=0.58));
        if x1 - x0 > 350 or y1 - y0 > 350: ax.text((x0 + x1) / 2, (y0 + y1) / 2, display_label(row), ha="center", va="center", fontsize=4.4, color="#1d3557")
    for row in extra_labels:
        x0, y0, x1, y1 = row["bbox_task01_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor=row["color"], linewidth=1.3, linestyle="--")); ax.text((x0 + x1) / 2, (y0 + y1) / 2, row["label"], ha="center", va="center", fontsize=4.5, color=row["color"])
    ax.text(11400, 10450, "MIDDLE GUEST ROOM\n(latest FCStd guide)", ha="center", va="center", fontsize=8, color="#2b6f3e", weight="bold")
    ax.text(14800, 10450, "STUDY / BACKUP SLEEP\n(latest FCStd guide)", ha="center", va="center", fontsize=8, color="#8a3153", weight="bold")
    ax.set_aspect("equal", adjustable="box"); ax.set_xlim(1000, 16600); ax.set_ylim(-1000, 14500); ax.set_xlabel("Task01 X (mm)"); ax.set_ylabel("Task01 Y (mm)")
    ax.set_title("S2 GUIDE BASELINE V2 / R2.2 AUDIT — latest FCStd replay\nNo layout change; door evidence and latest ensuite/laundry objects visible")
    ax.legend(handles=[Patch(facecolor="#6c757d", edgecolor="#343a40", label="Existing walls"), Patch(facecolor="#bde0fe", edgecolor="#1d3557", alpha=0.58, label="Latest named FCStd objects"), Patch(facecolor="none", edgecolor="#a000a0", linestyle="--", label="Owner ensuite / laundry audit markers"), Patch(facecolor="none", edgecolor="#495057", label="Door openings / swing evidence")], loc="upper left", fontsize=7, framealpha=0.92)
    fig.tight_layout(); fig.savefig(output_png, dpi=220)
    with PdfPages(output_pdf) as pages:
        pages.savefig(fig)
        page, ax2 = plt.subplots(figsize=(11, 8.5), dpi=180); ax2.axis("off"); ax2.text(0.02, 0.98, "Latest FCStd geometry audit\nDoor evidence shown on plan; detailed metrics in R2_2_clearance_report.md", va="top", fontsize=14); pages.savefig(page); plt.close(page)
    plt.close(fig)


def main():
    ingest, geometry, canonical, windows, kitchen = load()
    rows = primary_objects(ingest)
    metrics = dist_metrics(rows, geometry)
    doors = door_report(rows, canonical["openings"])
    extra_labels = []
    # Only annotations: no extra geometry is inserted into the Guide baseline.
    for label, color in (("次主卫", "#a000a0"), ("洗衣机+烘干机（叠放）", "#e76f00")):
        row = next((x for x in rows if x["label"] == label), None)
        if row: extra_labels.append({"bbox_task01_mm": row["bbox_task01_mm"], "label": label + " latest", "color": color})
    baseline_objects = [{**row, "source_position": row["bbox_task01_mm"], "reconstructed_position": row["bbox_task01_mm"], "dx_mm": 0.0, "dy_mm": 0.0, "rotation_delta_deg": 0.0, "wall_anchor": "PRESERVED_LATEST_FCSTD", "status": "PASS"} for row in rows]
    baseline = {"schema": "s2-guide-baseline-v2", "status": "HUMAN_REVIEW", "source_fcstd": str(FCSTD), "source_mtime": ingest["source_mtime"], "source_sha256": ingest["source_sha256"], "freecad_object_count": ingest["object_count"], "named_guide_object_count": ingest["named_guide_object_count"], "human_layout_intent": "LOCKED", "room_reassignment": 0, "wall_reassignment": 0, "max_dx_mm": 0.0, "max_dy_mm": 0.0, "max_rotation_delta_deg": 0.0, "objects": baseline_objects}
    (OUT / "s2_guide_baseline_v2.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(FCSTD, OUT / "S2_GUIDE_BASELINE_V2.FCStd")
    render(rows, extra_labels, geometry, canonical, windows, kitchen, OUT / "S2_GUIDE_BASELINE_V2.png", OUT / "S2_GUIDE_BASELINE_V2.pdf")
    render(rows, extra_labels, geometry, canonical, windows, kitchen, OUT / "S2_CURRENT_DESIGN_V1_R2_2_AUDIT.png", OUT / "S2_CURRENT_DESIGN_V1_R2_2_AUDIT.pdf")
    audit = {"schema": "s2-r2-2-geometry-audit-v1", "status": "HUMAN_REVIEW", "source_fcstd_sha256": ingest["source_sha256"], "layout_fidelity_gate": "PASS", "measurement_only": True, "metrics": metrics, "door_collision_report": doors, "missing_or_to_verify": ["客卫3kg小洗衣机 named guide object missing in latest FCStd", "study printer/NAS named guide object missing", "owner ensuite door/opening named guide object not explicit; canonical candidate D-CLK remains TO_VERIFY", "main laundry service/drainage/power/SKU TO_VERIFY"], "no_layout_changes": True}
    (OUT / "R2_2_geometry_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    coverage = [
        ("2 ensuites + 1 public bath", "IMPLEMENTED_PARTIAL", "latest FCStd includes 主卫 and 次主卫 three fixture guides; guest bath retained", "owner ensuite door/partition usability TO_VERIFY"),
        ("guest bath shower + WC + vanity + 3kg washer", "PARTIAL", "latest FCStd has guest wet zone/WC/vanity", "3kg washer guide object is missing; no automatic placement"),
        ("main 10kg washer + 10kg dryer", "IMPLEMENTED_TO_VERIFY", "latest FCStd named 洗衣机+烘干机（叠放）", "SKU, service, stacking and balcony environment TO_VERIFY"),
        ("formal high-frequency study", "PARTIAL", "latest FCStd named desk/bookcase/tea table/chairs", "printer/NAS and operating zone are not named; measurement only"),
        ("middle guest room", "IMPLEMENTED", "latest FCStd named 次卧小床1.2/次卧衣柜/次卧凳子", "orientation locked"),
        ("kitchen KEEP", "IMPLEMENTED", "latest FCStd existing cabinet guide + kitchen register", "no change"),
    ]
    (OUT / "S1_REQUIREMENT_COVERAGE_R2_2.md").write_text("# S1 Requirement Coverage — R2.2\n\n| Requirement | Status | Evidence | Notes |\n|---|---|---|---|\n" + "\n".join(f"| {a} | `{b}` | {c} | {d} |" for a,b,c,d in coverage) + "\n", encoding="utf-8")
    clear_lines = ["# R2.2 Clearance Report", "", "Status: `HUMAN_REVIEW`", "", "All measurements come from the latest FCStd; no R2/R2.1 furniture coordinates are used.", "", "| Metric | Available | Target | Shortfall | Status | Source |", "|---|---:|---:|---:|---|---|"]
    for m in metrics:
        clear_lines.append(f"| {m['metric']} | {m['available_mm'] if m['available_mm'] is not None else '—'} | {m['target_mm'] if m['target_mm'] is not None else '—'} | {max(0,m['target_mm']-m['available_mm']) if m['available_mm'] is not None and m['target_mm'] is not None else '—'} | `{m['status']}` | {m['source']} |")
    clear_lines += ["", "## Owner ensuite", "", "Latest FCStd objects `次主卫湿区 / 次主卫台盆和柜体 / 次主卫马桶` are the source of truth. No fixture has been moved or rotated.", "", "## Balcony/laundry", "", "Latest FCStd `洗衣机+烘干机（叠放）` is preserved as stacked; SKU, service and environment remain TO_VERIFY."]
    (OUT / "R2_2_clearance_report.md").write_text("\n".join(clear_lines) + "\n", encoding="utf-8")
    door_lines = ["# Door Collision Report v02", "", "| Door ID | Room/kind | Object | Swing | Min distance mm | Overlap mm2 | Status |", "|---|---|---|---|---:|---:|---|"]
    for row in doors: door_lines.append(f"| {row['door_id']} | {row['room']} | {row['object']} | {row['swing_angle']} | {row['minimum_distance_mm']} | {row['overlap_mm2']} | `{row['status']}` |")
    if not doors: door_lines.append("| — | — | — | — | — | 0 | `PASS` |")
    (OUT / "door_collision_report_v02.md").write_text("\n".join(door_lines) + "\n", encoding="utf-8")
    (OUT / "R2_2_change_log.json").write_text(json.dumps({"schema": "r2-2-change-log-v1", "status": "MEASUREMENT_ONLY", "changes": [{"type": "MEASUREMENT_ADDED"}, {"type": "SEMANTIC_MAPPING_UPDATED"}, {"type": "ANNOTATION_ADDED"}], "object_moved": 0, "object_rotated": 0, "room_reassignment": 0, "wall_reassignment": 0}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "HUMAN_REVIEW", "source_sha": ingest["source_sha256"], "object_count": ingest["object_count"], "named_count": ingest["named_guide_object_count"], "door_conflicts": len(doors), "metrics": len(metrics)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
