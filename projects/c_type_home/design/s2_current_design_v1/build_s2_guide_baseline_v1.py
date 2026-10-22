#!/usr/bin/env python3
"""Replay the latest FreeCAD guide without normalization or layout drift."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, Patch, Rectangle


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
GUIDE = OUT / "human_guide_inventory.json"
GEOMETRY = BASE / "data/geometry.json"
CANONICAL = BASE / "current_existing/canonical_plan_v1.json"
WINDOWS = BASE / "current_existing/window_register.json"
KITCHEN = BASE / "current_existing/kitchen_cabinet_register.json"

ROLE_POLYGON = {
    "living": "R-LIVING",
    "dining": "R-DINING",
    "owner_bedroom": "R-BED-S",
    "mother_bedroom": "R-MASTER",
    "middle_guest_room": "R-STUDY",
    "south_study": "R-BED-N",
    "guest_bath": "R-BATH-P",
    "mother_bathroom": "R-BATH-M",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def orientation_for(row):
    width = row.get("guide_width_mm")
    depth = row.get("guide_depth_mm")
    if width is None or depth is None:
        return "UNKNOWN"
    if row.get("edge_count") == 1 and abs(width - depth) <= 1.0:
        return "RADIAL"
    if abs(width - depth) <= 1.0:
        return "SQUARE"
    if width > depth:
        return "LONG_AXIS_X"
    return "LONG_AXIS_Y"


def role_color(zone):
    return {
        "living": "#8ecae6",
        "dining": "#ffb703",
        "owner_bedroom": "#bde0fe",
        "mother_bedroom": "#cdb4db",
        "middle_guest_room": "#caffbf",
        "south_study": "#ffc8dd",
        "guest_bath": "#90dbf4",
        "mother_bathroom": "#a8dadc",
        "entry": "#adb5bd",
        "kitchen": "#f4a261",
        "transition": "#e9c46a",
    }.get(zone, "#ced4da")


def copy_rejected_outputs():
    """Keep the previous normalized run for audit; never overwrite it."""
    mapping = {
        "S2_CURRENT_DESIGN_V1.png": "S2_CURRENT_DESIGN_V1_REJECTED.png",
        "S2_CURRENT_DESIGN_V1.pdf": "S2_CURRENT_DESIGN_V1_REJECTED.pdf",
        "design_model_v01.json": "S2_CURRENT_DESIGN_V1_REJECTED.design_model.json",
        "furniture_dimension_register_v01.json": "S2_CURRENT_DESIGN_V1_REJECTED.dimension_register.json",
        "s2_collision_circulation_report.json": "S2_CURRENT_DESIGN_V1_REJECTED.circulation_report.json",
        "S2_CURRENT_DESIGN_V1_design_audit.md": "S2_CURRENT_DESIGN_V1_REJECTED_design_audit.md",
    }
    copied = []
    for source_name, target_name in mapping.items():
        source = OUT / source_name
        target = OUT / target_name
        if source.is_file():
            shutil.copy2(source, target)
            copied.append(target.name)
    (OUT / "S2_CURRENT_DESIGN_V1_REJECTED_reason.md").write_text(
        "# S2_CURRENT_DESIGN_V1 — HUMAN REVIEW FAIL\n\n"
        "Reason: `HUMAN_GUIDE_LAYOUT_DRIFT`. The previous run normalized and repositioned guide furniture instead of preserving locked human orientation/topology. It is retained for audit only.\n\n"
        "Do not use this rejected run as the source for S2 R2.\n",
        encoding="utf-8",
    )
    return copied


def build_baseline_rows(guide):
    rows = []
    for current in guide["primary_guides"]:
        bbox = current.get("bbox_task01_mm")
        if not bbox:
            status = "FAIL"
            center = None
        else:
            status = "PASS"
            center = [(bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0]
        rows.append({
            "source_object_name": current["name"],
            "source_label": current["label"],
            "semantic_id": current["semantic_id"],
            "functional_zone": current.get("zone"),
            "historical_polygon_id": ROLE_POLYGON.get(current.get("zone")),
            "guide_bbox_task01_mm": bbox,
            "reconstructed_bbox_task01_mm": bbox,
            "guide_center_task01_mm": center,
            "reconstructed_center_task01_mm": center,
            "displacement_mm": 0.0 if bbox else None,
            "guide_orientation": orientation_for(current),
            "reconstructed_orientation": orientation_for(current),
            "rotation_delta_deg": 0.0 if bbox else None,
            "wall_relationship": "PRESERVED_BY_EXACT_GUIDE_REPLAY" if bbox else "UNKNOWN",
            "layout_intent": "LOCKED",
            "status": status,
        })
    return rows


def render(guide, geometry, canonical, windows, kitchen):
    fig, ax = plt.subplots(figsize=(16, 12), dpi=180)
    for wall in canonical["walls"]:
        x0, y0, x1, y1 = wall["rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#6c757d", edgecolor="#343a40", linewidth=0.45, alpha=0.75))
    for opening in windows:
        x0, y0, x1, y1 = opening["opening_rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#52b6ca", edgecolor="#087f8c", linewidth=1.0, alpha=0.55))
    for cabinet in kitchen:
        x0, y0, x1, y1 = cabinet["rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#e76f51", edgecolor="#9d2b1f", linewidth=0.5, alpha=0.65))
    for space in geometry["spaces"]:
        polygon = space["polygon_mm"]
        xs = [p[0] for p in polygon] + [polygon[0][0]]
        ys = [p[1] for p in polygon] + [polygon[0][1]]
        ax.plot(xs, ys, color="#adb5bd", linewidth=0.5, alpha=0.65)
    for current in guide["primary_guides"]:
        bbox = current.get("bbox_task01_mm")
        if not bbox:
            continue
        x0, y0, x1, y1 = bbox
        width = x1 - x0
        depth = y1 - y0
        color = role_color(current.get("zone"))
        # User circles remain circles in the baseline; all other named objects
        # keep their exact guide bbox and long-axis orientation.
        if current.get("edge_count") == 1 and abs(width - depth) <= 1.0:
            ax.add_patch(Circle(((x0 + x1) / 2.0, (y0 + y1) / 2.0), width / 2.0, facecolor=color, edgecolor="#1d3557", linewidth=1.0, alpha=0.72))
        else:
            ax.add_patch(Rectangle((x0, y0), width, depth, facecolor=color, edgecolor="#1d3557", linewidth=1.0, alpha=0.62))
        if width > 260 or depth > 260:
            ax.text((x0 + x1) / 2.0, (y0 + y1) / 2.0, current["semantic_id"].replace("_", "\n"), ha="center", va="center", fontsize=5.2, color="#1d3557")
    ax.text(11400, 10450, "MIDDLE GUEST ROOM\n(guide: 次卧小床1.2)", ha="center", va="center", fontsize=8, color="#2b6f3e", weight="bold")
    ax.text(14800, 10450, "STUDY / BACKUP SLEEP\n(guide: 书柜 · 茶台 · 书桌)", ha="center", va="center", fontsize=8, color="#8a3153", weight="bold")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(1000, 16600)
    ax.set_ylim(-1000, 14500)
    ax.set_xlabel("Task01 X (mm)")
    ax.set_ylabel("Task01 Y (mm)")
    ax.set_title("S2 GUIDE BASELINE V1 — HUMAN_LAYOUT_INTENT LOCKED\nExact guide topology / orientation replay; no normalization")
    legend = [
        Patch(facecolor="#6c757d", edgecolor="#343a40", label="Existing structure / walls"),
        Patch(facecolor="#52b6ca", edgecolor="#087f8c", alpha=0.55, label="Existing windows / glass openings"),
        Patch(facecolor="#e76f51", edgecolor="#9d2b1f", label="KEEP kitchen geometry"),
        Patch(facecolor="#8ecae6", edgecolor="#1d3557", alpha=0.72, label="Exact named human guide bbox"),
    ]
    ax.legend(handles=legend, loc="upper left", fontsize=7, framealpha=0.92)
    fig.tight_layout()
    png = OUT / "S2_GUIDE_BASELINE_V1.png"
    pdf = OUT / "S2_GUIDE_BASELINE_V1.pdf"
    fig.savefig(png, dpi=220)
    with PdfPages(pdf) as pages:
        pages.savefig(fig)
    plt.close(fig)
    return png, pdf


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    guide = json.loads(GUIDE.read_text(encoding="utf-8"))
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    windows = json.loads(WINDOWS.read_text(encoding="utf-8"))["windows"]
    kitchen = json.loads(KITCHEN.read_text(encoding="utf-8"))["cabinets"]
    rejected = copy_rejected_outputs()
    rows = build_baseline_rows(guide)
    failures = [row for row in rows if row["status"] != "PASS" or row["rotation_delta_deg"] != 0.0 or row["displacement_mm"] != 0.0]
    png, pdf = render(guide, geometry, canonical, windows, kitchen)
    report = {
        "schema": "s2-guide-fidelity-report-v1",
        "status": "DRAFT_HUMAN_REVIEW",
        "fidelity_gate": "PASS" if not failures else "FAIL",
        "source_fcstd": str(BASE / "cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd"),
        "source_fcstd_sha256": sha256(BASE / "cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd"),
        "layout_policy": "HUMAN_LAYOUT_INTENT_LOCKED",
        "automatic_rotation_allowed": False,
        "automatic_large_relayout_allowed": False,
        "primary_guide_count": len(rows),
        "displacement_tolerance_mm": 0.0,
        "rotation_tolerance_deg": 0.0,
        "max_displacement_mm": max((row["displacement_mm"] or 0.0 for row in rows), default=0.0),
        "max_rotation_delta_deg": max((abs(row["rotation_delta_deg"] or 0.0) for row in rows), default=0.0),
        "object_checks": rows,
        "failures": failures,
        "outputs": {"png": str(png), "pdf": str(pdf)},
        "rejected_outputs_preserved": rejected,
        "stop_gate": "HUMAN_REVIEW_BEFORE_NORMALIZATION",
    }
    (OUT / "s2_guide_baseline_v1.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# S2 GUIDE BASELINE V1 — Fidelity Report",
        "",
        "Status: `DRAFT_HUMAN_REVIEW`",
        f"Fidelity gate: `{report['fidelity_gate']}`",
        "",
        "## Policy",
        "",
        "FCStd named guide objects are `HUMAN_LAYOUT_INTENT = LOCKED`. This baseline replays their exact task-coordinate bbox and orientation. It does not normalize dimensions, rotate objects, move furniture, or re-plan rooms.",
        "",
        "## Room-role authority",
        "",
        "- Middle guest room: `次卧小床1.2` + `次卧衣柜` + `次卧凳子`.",
        "- Study / backup sleep: `床背板+窄书桌占位` + `书柜` + `书柜001` + `茶台` + `主人椅` + `条凳` + `凳子`.",
        "- Historical geometry room labels are polygon references only; they do not override the named FreeCAD guide.",
        "",
        "## Gate checks",
        "",
        f"- Named guide objects checked: {len(rows)}",
        f"- Maximum displacement: {report['max_displacement_mm']:.1f} mm",
        f"- Maximum rotation delta: {report['max_rotation_delta_deg']:.1f}°",
        "- 90° orientation drift: none in the replay",
        "- Cross-room relayout: none in the replay",
        "- Wall relationship: preserved by exact guide bbox replay",
        "",
        "## Per-object checks",
        "",
        "| object | semantic | room role | guide orientation | reconstructed orientation | displacement | rotation delta | result |",
        "|---|---|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(f"| {row['source_label']} | `{row['semantic_id']}` | `{row['functional_zone']}` | `{row['guide_orientation']}` | `{row['reconstructed_orientation']}` | {row['displacement_mm'] or 0:.1f} | {row['rotation_delta_deg'] or 0:.1f}° | `{row['status']}` |")
    lines += [
        "",
        "## Stop gate",
        "",
        "This baseline stops for human review. Only after baseline approval may a copy be used for dimension normalization. Any nonzero rotation delta requires explicit human approval.",
        "",
        "The previous normalized run is preserved under `S2_CURRENT_DESIGN_V1_REJECTED*` because it failed `HUMAN_GUIDE_LAYOUT_DRIFT`.",
    ]
    (OUT / "guide_fidelity_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "S2_CURRENT_DESIGN_V1_REVIEW_FAIL.md").write_text(
        "# S2 CURRENT DESIGN V1 — HUMAN REVIEW FAIL\n\n"
        "Status: `FAIL`\n\n"
        "Reason: `HUMAN_GUIDE_LAYOUT_DRIFT`. The previous normalized output changed layout interpretation. It is retained as `S2_CURRENT_DESIGN_V1_REJECTED*`.\n\n"
        "Replacement workflow: exact guide baseline first, human review, then incremental normalization with rotation locked at 0° by default.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "fidelity_gate": report["fidelity_gate"], "checked": len(rows), "png": str(png), "pdf": str(pdf)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
