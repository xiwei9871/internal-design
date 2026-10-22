#!/usr/bin/env python3
"""R2.1 completeness pass: add missing S1 functions without redesigning R2."""

from __future__ import annotations

from pathlib import Path
import json
import math

import ezdxf
from ezdxf import bbox as ez_bbox
from shapely.geometry import box as shape_box
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch, Rectangle, Arc


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
R2_MODEL = OUT / "S2_CURRENT_DESIGN_V1_R2_model.json"
R2_DXF = OUT / "S2_CURRENT_DESIGN_V1_R2.dxf"
GEOMETRY = BASE / "data/geometry.json"
CANONICAL = BASE / "current_existing/canonical_plan_v1.json"
WINDOWS = BASE / "current_existing/window_register.json"
KITCHEN = BASE / "current_existing/kitchen_cabinet_register.json"


def rect(x0, y0, w, d):
    return [float(x0), float(y0), float(x0 + w), float(y0 + d)]


def area(bbox):
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def add_item(item_id, label, semantic_id, zone, bbox, status, notes, room=None, color="#c00000", line_style="--"):
    return {
        "id": item_id,
        "source_label": label,
        "semantic_id": semantic_id,
        "functional_zone": zone,
        "historical_polygon_id": room,
        "bbox_task01_mm": bbox,
        "status": status,
        "notes": notes,
        "review_color": color,
        "line_style": line_style,
    }


def load():
    return (
        json.loads(R2_MODEL.read_text(encoding="utf-8")),
        json.loads(GEOMETRY.read_text(encoding="utf-8")),
        json.loads(CANONICAL.read_text(encoding="utf-8")),
        json.loads(WINDOWS.read_text(encoding="utf-8"))["windows"],
        json.loads(KITCHEN.read_text(encoding="utf-8"))["cabinets"],
    )


def additions():
    return [
        add_item("OWNER-ENSUITE-CANDIDATE", "owner ensuite candidate", "OWNER_ENSUITE_CANDIDATE", "owner_ensuite", [9050, 4650, 11300, 6300], "SCHEMATIC_CANDIDATE", ["uses existing cloakroom polygon as a candidate; 3.71m2 is below the 5-5.5m2 S1 target", "no walls are changed"], "R-CLOAK", "#a000a0"),
        add_item("OWNER-ENSUITE-SHOWER", "owner ensuite shower", "SHOWER_OWNER_ENSUITE", "owner_ensuite", rect(9100, 4800, 900, 1200), "SCHEMATIC_CANDIDATE", ["900x1200 target; final drainage and threshold TO_VERIFY"], "R-CLOAK", "#a000a0"),
        add_item("OWNER-ENSUITE-WC", "owner ensuite WC", "WC_OWNER_ENSUITE", "owner_ensuite", rect(10050, 4800, 450, 700), "SCHEMATIC_CANDIDATE", ["standard footprint; door swing/service routing TO_VERIFY"], "R-CLOAK", "#a000a0"),
        add_item("OWNER-ENSUITE-VANITY", "owner ensuite vanity", "VANITY_OWNER_ENSUITE", "owner_ensuite", rect(10600, 4800, 600, 500), "SCHEMATIC_CANDIDATE", ["standard footprint; no public bath deletion"], "R-CLOAK", "#a000a0"),
        add_item("GUEST-BATH-WASHER-CANDIDATE", "客卫3kg小洗衣机", "WASHER_SMALL_3KG", "guest_bath", rect(8650, 8100, 600, 650), "CONFLICT_REVIEW", ["required S1 function; candidate footprint shown without silently moving existing R2 fixtures", "SKU and wet-zone installation TO_VERIFY"], "R-BATH-P", "#d00000"),
        add_item("MAIN-LAUNDRY-WASHER", "main laundry washer", "WASHER_MAIN_10KG", "north_balcony", rect(8000, 11050, 600, 650), "TO_VERIFY", ["10kg target; north balcony is OPEN_NOT_ENCLOSED"], "R-BALC-N", "#e76f00"),
        add_item("MAIN-LAUNDRY-DRYER", "main laundry dryer", "DRYER_MAIN_10KG", "north_balcony", rect(8700, 11050, 600, 650), "TO_VERIFY", ["10kg target; stacking/SKU and ventilation TO_VERIFY"], "R-BALC-N", "#e76f00"),
        add_item("STUDY-WORKING-ZONE", "formal study workstation operating zone", "STUDY_WORKSTATION_OPERATION", "south_study", rect(12450, 8200, 1000, 1200), "CONFLICT_REVIEW", ["derived from locked desk guide; chair pull-back and dual-monitor use need human review"], "R-BED-N", "#7b2cbf"),
        add_item("STUDY-PRINTER-NAS", "printer / NAS provision", "STUDY_PRINTER_NAS", "south_study", rect(13200, 9800, 500, 500), "TO_VERIFY", ["equipment provision; no automatic furniture relocation"], "R-BED-N", "#7b2cbf"),
    ]


def bbox_map(r2_items):
    return {row["semantic_id"]: row["normalized_bbox_task01_mm"] for row in r2_items if row.get("normalized_bbox_task01_mm")}


def metric(metric_id, label, available, target, source, status=None, notes=None):
    shortfall = None if available is None or target is None else max(0.0, target - available)
    if status is None:
        status = "PASS" if shortfall == 0 else "CONFLICT"
    return {"id": metric_id, "label": label, "available_mm": available, "target_mm": target, "shortfall_mm": shortfall, "status": status, "source": source, "notes": notes or []}


def build_clearance_report(r2, geometry, canonical, extra):
    room_polygons = {row["id"]: shape_box(min(p[0] for p in row["polygon_mm"]), min(p[1] for p in row["polygon_mm"]), max(p[0] for p in row["polygon_mm"]), max(p[1] for p in row["polygon_mm"])) for row in geometry["spaces"]}
    boxes = bbox_map(r2["items"])
    metrics = []
    for semantic, room, side_target, end_target in (("BED_GUEST_1200", "R-STUDY", 600, 600), ("BED_OWNER", "R-BED-S", 600, 600), ("BED_MOTHER", "R-MASTER", 600, 600)):
        if semantic not in boxes or room not in room_polygons:
            continue
        b = boxes[semantic]; room_box = room_polygons[room].bounds
        side = min(b[0] - room_box[0], room_box[2] - b[2])
        end = room_box[3] - b[3]
        metrics += [metric(semantic + "-side", semantic + " side clearance", round(side, 1), side_target, "room boundary minus R2 bed bbox"), metric(semantic + "-end", semantic + " end clearance", round(end, 1), end_target, "room boundary minus R2 bed bbox")]
    # Guest bath boundary is locked and the four-function test is explicit.
    guest_room = room_polygons["R-BATH-P"].bounds
    metrics.extend([
        metric("GUEST-WC-FRONT", "guest WC front clearance", round(guest_room[3] - boxes["WC_GUEST"][3], 1), 800, "R2 WC bbox to locked guest-bath north boundary"),
        metric("GUEST-WC-SIDE", "guest WC side clearance", round(min(boxes["WC_GUEST"][0] - guest_room[0], guest_room[2] - boxes["WC_GUEST"][2]), 1), 600, "R2 WC bbox to locked guest-bath side boundary"),
        metric("GUEST-VANITY-OPERATING", "guest vanity operating clearance", round(guest_room[2] - boxes["VANITY_GUEST"][2], 1), 600, "locked guest-bath side clearance proxy"),
        metric("GUEST-WASHER-OPERATING", "3kg washer operating clearance", None, 600, "no approved anchor; candidate is intentionally unplaced", "TO_VERIFY", ["do not enlarge guest bath automatically"]),
    ])
    owner_candidate = next(x for x in extra if x["id"] == "OWNER-ENSUITE-CANDIDATE")
    candidate_area = area(owner_candidate["bbox_task01_mm"]) / 1_000_000.0
    metrics.append(metric("OWNER-ENSUITE-AREA", "owner ensuite candidate area", round(candidate_area, 2), 5.0, "existing R-CLOAK candidate polygon", "CONFLICT", ["candidate is below S1 target 5-5.5m2; no walls changed"]))
    study = next(x for x in extra if x["id"] == "STUDY-WORKING-ZONE")
    metrics.append(metric("STUDY-CHAIR-PULLBACK", "study chair pull-back clearance", None, 900, "formal workstation operating zone candidate", "TO_VERIFY", ["guide orientation locked; no automatic desk movement"]))
    dining = boxes.get("DINING_TABLE")
    if dining:
        dining_room = room_polygons["R-DINING"].bounds
        metrics.append(metric("DINING-CHAIR-PULLBACK", "dining chair pull-back clearance", round(min(dining[0] - dining_room[0], dining_room[2] - dining[2]), 1), 900, "R2 dining table bbox to dining room boundary", "CONFLICT"))
    metrics.append(metric("MOTHER-BATH-CRITICAL", "mother bath critical operating clearance", None, 900, "aging-in-place fixtures require human/SKU review", "TO_VERIFY"))
    metrics.append(metric("OWNER-ENSUITE-CRITICAL", "owner ensuite critical clearance", None, 900, "candidate bathroom boundary not yet confirmed", "TO_VERIFY"))
    metrics.append(metric("G-LIV-NBALC", "living to north balcony existing door clear width", 850, 850, "confirmed existing glass door", "PASS", ["NO_WORSENING; existing limitation"]))
    return metrics


def coverage(extra, metrics):
    return [
        {"requirement": "2 ensuites + 1 public bath", "status": "PARTIAL", "evidence": ["mother bath existing guide", "owner ensuite candidate R-CLOAK", "public guest bath retained"], "notes": ["owner ensuite candidate is undersized; human decision required"]},
        {"requirement": "guest bath shower + WC + vanity + 3kg washer", "status": "PARTIAL", "evidence": ["existing guest bath fixtures", "3kg washer candidate outline"], "notes": ["washer is unanchored; exact four-function fit is unresolved"]},
        {"requirement": "main 10kg washer + 10kg dryer", "status": "TO_VERIFY", "evidence": ["north balcony candidate footprints"], "notes": ["OPEN_NOT_ENCLOSED; SKU, stacking, ventilation and access remain TO_VERIFY"]},
        {"requirement": "formal high-frequency study", "status": "PARTIAL", "evidence": ["locked guide desk/bookcase/tea table", "study operating zone and printer/NAS provision"], "notes": ["chair pull-back and equipment placement need review"]},
        {"requirement": "middle guest room", "status": "IMPLEMENTED", "evidence": ["locked guide bed/wardrobe/stool role mapping"], "notes": []},
        {"requirement": "south study / backup sleeping", "status": "IMPLEMENTED", "evidence": ["locked guide desk/bookcase/tea-table topology"], "notes": []},
        {"requirement": "kitchen KEEP", "status": "IMPLEMENTED", "evidence": ["existing kitchen register and R2 geometry"], "notes": []},
    ]


def draw_door_evidence(ax, openings):
    for opening in openings:
        x0, y0, x1, y1 = opening["rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor="#495057", linewidth=0.8))
        if (x1 - x0) >= (y1 - y0):
            center = (x0, y0)
            radius = max(x1 - x0, y1 - y0)
            ax.add_patch(Arc(center, 2 * radius, 2 * radius, angle=0, theta1=0, theta2=90, color="#495057", linewidth=0.55))
        else:
            center = (x0, y0)
            radius = max(x1 - x0, y1 - y0)
            ax.add_patch(Arc(center, 2 * radius, 2 * radius, angle=0, theta1=0, theta2=90, color="#495057", linewidth=0.55))


def render(extra, r2, geometry, canonical, windows, kitchen, metrics):
    fig, ax = plt.subplots(figsize=(16, 12), dpi=180)
    for wall in canonical["walls"]:
        x0, y0, x1, y1 = wall["rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#6c757d", edgecolor="#343a40", linewidth=0.45, alpha=0.75))
    for opening in windows:
        x0, y0, x1, y1 = opening["opening_rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#52b6ca", edgecolor="#087f8c", linewidth=1.0, alpha=0.55))
    draw_door_evidence(ax, canonical["openings"])
    for cabinet in kitchen:
        x0, y0, x1, y1 = cabinet["rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#e76f51", edgecolor="#9d2b1f", linewidth=0.5, alpha=0.65))
    for row in r2["items"]:
        bbox = row.get("normalized_bbox_task01_mm")
        if not bbox:
            continue
        x0, y0, x1, y1 = bbox
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#bde0fe", edgecolor="#1d3557", linewidth=0.85, alpha=0.45))
        if x1 - x0 > 350 or y1 - y0 > 350:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, row["semantic_id"].replace("_", "\n"), ha="center", va="center", fontsize=4.4, color="#1d3557")
    for row in extra:
        x0, y0, x1, y1 = row["bbox_task01_mm"]
        color = row["review_color"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor=color, linewidth=1.3, linestyle=row["line_style"]))
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, row["semantic_id"].replace("_", "\n"), ha="center", va="center", fontsize=4.5, color=color)
    ax.text(11400, 10450, "MIDDLE GUEST ROOM\n(lock preserved)", ha="center", va="center", fontsize=8, color="#2b6f3e", weight="bold")
    ax.text(14800, 10450, "STUDY / BACKUP SLEEP\n(formal workstation review)", ha="center", va="center", fontsize=8, color="#8a3153", weight="bold")
    for index, current in enumerate(metrics):
        if current["available_mm"] is None:
            continue
        # show only a few high-value dimensions on the plan; full table goes in PDF/report.
        if index >= 6:
            break
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(1000, 16600)
    ax.set_ylim(-1000, 14500)
    ax.set_xlabel("Task01 X (mm)")
    ax.set_ylabel("Task01 Y (mm)")
    ax.set_title("S2 CURRENT DESIGN V1 R2.1 — completeness pass\nR2 layout locked; doors and requirement candidates visible; formal CAD HOLD")
    legend = [
        Patch(facecolor="#6c757d", edgecolor="#343a40", label="Existing structure / walls"),
        Patch(facecolor="#bde0fe", edgecolor="#1d3557", alpha=0.45, label="R2 locked furniture"),
        Patch(facecolor="none", edgecolor="#a000a0", linestyle="--", label="Owner ensuite candidate"),
        Patch(facecolor="none", edgecolor="#d00000", linestyle="--", label="Conflict / human review"),
        Patch(facecolor="none", edgecolor="#e76f00", linestyle="--", label="Laundry / TO_VERIFY"),
        Patch(facecolor="none", edgecolor="#7b2cbf", linestyle="--", label="Study operation / equipment"),
        Patch(facecolor="none", edgecolor="#495057", label="Door openings / swing evidence"),
    ]
    ax.legend(handles=legend, loc="upper left", fontsize=7, framealpha=0.92)
    fig.tight_layout()
    png = OUT / "S2_CURRENT_DESIGN_V1_R2_1.png"
    pdf = OUT / "S2_CURRENT_DESIGN_V1_R2_1.pdf"
    fig.savefig(png, dpi=220)
    with PdfPages(pdf) as pages:
        pages.savefig(fig)
        fig2, table_ax = plt.subplots(figsize=(11, 8.5), dpi=180)
        table_ax.axis("off")
        table_ax.set_title("R2.1 Critical Clearance Review", fontsize=14, pad=15)
        rows = [[m["label"], "—" if m["available_mm"] is None else f"{m['available_mm']:.0f}", "—" if m["target_mm"] is None else f"{m['target_mm']:.0f}", "—" if m["shortfall_mm"] is None else f"{m['shortfall_mm']:.0f}", m["status"]] for m in metrics]
        table_ax.table(cellText=rows, colLabels=["Metric", "Available", "Target", "Shortfall", "Status"], loc="center", cellLoc="left", colLoc="left")
        pages.savefig(fig2, bbox_inches="tight")
        plt.close(fig2)
    plt.close(fig)
    return png, pdf


def write_dxf(extra):
    doc = ezdxf.readfile(R2_DXF)
    for name, color in (("S2_R2_1_OWNER_ENSUITE", 6), ("S2_R2_1_REQUIREMENT", 30), ("S2_R2_1_CONFLICT", 1), ("S2_R2_1_DOOR_EVIDENCE", 8)):
        if name not in doc.layers:
            doc.layers.new(name, dxfattribs={"color": color})
    msp = doc.modelspace()
    ox, oy = 1298172.0, -296458.0
    for row in extra:
        x0, y0, x1, y1 = row["bbox_task01_mm"]
        layer = "S2_R2_1_CONFLICT" if row["status"] in {"CONFLICT_REVIEW", "SCHEMATIC_CANDIDATE"} and row["semantic_id"] in {"WASHER_SMALL_3KG", "OWNER_ENSUITE_CANDIDATE"} else ("S2_R2_1_OWNER_ENSUITE" if row["functional_zone"] == "owner_ensuite" else "S2_R2_1_REQUIREMENT")
        msp.add_lwpolyline([(x0 + ox, y0 + oy), (x1 + ox, y0 + oy), (x1 + ox, y1 + oy), (x0 + ox, y1 + oy)], close=True, dxfattribs={"layer": layer})
    for opening in json.loads(CANONICAL.read_text(encoding="utf-8"))["openings"]:
        x0, y0, x1, y1 = opening["rect_mm"]
        msp.add_lwpolyline([(x0 + ox, y0 + oy), (x1 + ox, y0 + oy), (x1 + ox, y1 + oy), (x0 + ox, y1 + oy)], close=True, dxfattribs={"layer": "S2_R2_1_DOOR_EVIDENCE"})
    out = OUT / "S2_CURRENT_DESIGN_V1_R2_1.dxf"
    doc.saveas(out)
    return out


def main():
    r2, geometry, canonical, windows, kitchen = load()
    extra = additions()
    metrics = build_clearance_report(r2, geometry, canonical, extra)
    report = {
        "schema": "r2-1-clearance-report-v1",
        "status": "DRAFT_HUMAN_REVIEW",
        "layout_fidelity_gate": "PASS",
        "s1_requirement_completeness_gate": "FAIL",
        "design_usability_gate": "HOLD",
        "formal_cad_allowed": False,
        "metrics": metrics,
        "door_evidence": canonical["openings"],
        "extra_requirement_objects": extra,
        "notes": ["Existing R2 furniture is preserved; additions are schematic requirement candidates only.", "No owner ensuite walls are drawn as approved construction walls.", "No automatic relocation or rotation is performed."]
    }
    (OUT / "R2_1_clearance_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "S1_REQUIREMENT_COVERAGE.json").write_text(json.dumps({"schema": "s1-requirement-coverage-v1", "status": "S1_REQUIREMENT_COMPLETENESS_GATE_FAIL", "rows": coverage(extra, metrics)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "R2_1_change_log.json").write_text(json.dumps({"schema": "r2-1-change-log-v1", "status": "DRAFT_HUMAN_REVIEW", "policy": "R2_LAYOUT_LOCKED", "changes": extra, "automatic_relayout": False, "rotation_delta_deg": 0}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    png, pdf = render(extra, r2, geometry, canonical, windows, kitchen, metrics)
    dxf = write_dxf(extra)
    coverage_rows = coverage(extra, metrics)
    coverage_md = ["# S1 Requirement Coverage — R2.1", "", "Status: `S1_REQUIREMENT_COMPLETENESS_GATE = FAIL`", "", "| Requirement | Status | Evidence | Notes |", "|---|---|---|---|"]
    for row in coverage_rows:
        coverage_md.append(f"| {row['requirement']} | `{row['status']}` | {'; '.join(row['evidence'])} | {'; '.join(row['notes'])} |")
    (OUT / "S1_REQUIREMENT_COVERAGE.md").write_text("\n".join(coverage_md) + "\n", encoding="utf-8")
    clear_md = ["# R2.1 Clearance Report", "", "Status: `DRAFT_HUMAN_REVIEW`", "", "R2 layout is locked. Values below are schematic review values, not construction certification.", "", "| Metric | Available | Target | Shortfall | Status | Source |", "|---|---:|---:|---:|---|---|"]
    for m in metrics:
        available = "—" if m["available_mm"] is None else f"{m['available_mm']:.0f} mm"
        target = "—" if m["target_mm"] is None else f"{m['target_mm']:.0f} mm"
        shortfall = "—" if m["shortfall_mm"] is None else f"{m['shortfall_mm']:.0f} mm"
        clear_md.append(f"| {m['label']} | {available} | {target} | {shortfall} | `{m['status']}` | {m['source']} |")
    clear_md += ["", "## Conflict handling", "", "Conflicts remain marked and are not solved by rotating or moving locked R2 furniture. Each item requires a human decision or field/SKU verification.", "", "## Door evidence", "", "All canonical openings are drawn in R2.1 review outputs; the door rectangles and schematic swing arcs are visible for human review."]
    (OUT / "R2_1_clearance_report.md").write_text("\n".join(clear_md) + "\n", encoding="utf-8")
    # Build the R2.1 FCStd through the dedicated FreeCAD script after JSONs exist.
    print(json.dumps({"status": report["status"], "s1_requirement_completeness": report["s1_requirement_completeness_gate"], "png": str(png), "pdf": str(pdf), "dxf": str(dxf), "metrics": len(metrics)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
