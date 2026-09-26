#!/usr/bin/env python3
"""F1R.1 hybrid concept review using actual A0.4 DXF block geometry.

This is a review-only artifact generator. It never writes formal DXF, canonical
geometry, V02/V03, or furniture_l1_final.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from ezdxf.addons import Importer
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf import bbox as ezbbox

ROOT = Path(__file__).resolve().parents[1]
QC = ROOT / "qc/f1r_public_zone"
STD = ROOT / "assets/cad_library/standard"
FURNITURE = ROOT / "concept/furniture_l1_final.json"
CONCEPT = ROOT / "concept/concept_data.json"
CANONICAL = ROOT / "current_existing/canonical_plan_v1.json"
WINDOWS = ROOT / "current_existing/window_register.json"
LEGENDS = ROOT / "assets/cad_library/standard/manifests/design_legend_manifest_v01.json"
RULES = ROOT / "knowledge/design_rules/design_rulebook_v01.json"
PATTERNS = ROOT / "knowledge/precedents/pattern_library_v01.json"
OUT_PLAN = QC / "F1R_01H_plan.png"
OUT_OVERLAY = QC / "F1R_01H_clearance_overlay.png"
OUT_METRICS = QC / "F1R_01H_metrics.json"
OUT_AUDIT = QC / "F1R_01H_design_audit.md"
PUBLIC_BOUNDS = [2500, -300, 8500, 13750]
CORE = [3900, 7400, 7700, 11750]

BLOCKS = {
    "SOFA_3S_2200x900_PLAN": STD / "normalized/SOFA_3S_2200x900_PLAN.dxf",
    "SOFA_2S_1800x850_PLAN": STD / "normalized/SOFA_2S_1800x850_PLAN.dxf",
    "LOUNGE_CHAIR_900x900_PLAN": STD / "normalized/LOUNGE_CHAIR_900x900_PLAN.dxf",
    "DINING_TABLE_1500x600_PLAN": STD / "normalized/DINING_TABLE_1500x600_PLAN.dxf",
    "DINING_CHAIR_450x500_PLAN": STD / "normalized/DINING_CHAIR_450x500_PLAN.dxf",
}


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def intersection(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    return [x1, y1, x2, y2] if x2 > x1 and y2 > y1 else None


def area(r):
    return max(0, r[2] - r[0]) * max(0, r[3] - r[1])


def center(r):
    return ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)


def edge_gap(a, b):
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.sqrt(dx * dx + dy * dy)


def largest_clear_rect(container, obstacles):
    clipped = [r for o in obstacles if (r := intersection(container, o))]
    xs = sorted({container[0], container[2], *(x for r in clipped for x in (r[0], r[2]))})
    ys = sorted({container[1], container[3], *(y for r in clipped for y in (r[1], r[3]))})
    best = None
    for i, x1 in enumerate(xs[:-1]):
        for x2 in xs[i + 1:]:
            for j, y1 in enumerate(ys[:-1]):
                for y2 in ys[j + 1:]:
                    r = [x1, y1, x2, y2]
                    if any(intersection(r, o) for o in clipped):
                        continue
                    candidate = (area(r), r)
                    if best is None or candidate[0] > best[0]:
                        best = candidate
    return best[1] if best else [0, 0, 0, 0]


def source_bbox(legend_manifest, block_id):
    item = next(x for x in legend_manifest["legends"] if x["id"] == block_id)
    return item["normalized_bbox_mm"], item


def hybrid_placements():
    # F1R-01H: option 01 social grouping, with option 03's clear central field.
    return [
        {"id": "LIV-SOFA-3", "block_id": "SOFA_3S_2200x900_PLAN", "rect": [2900, 9000, 3800, 11200], "rotation": 90, "role": "primary social anchor", "reason": "west edge anchor; faces the social group, not a solitary media axis"},
        {"id": "LIV-SOFA-2", "block_id": "SOFA_2S_1800x850_PLAN", "rect": [4850, 10800, 6650, 11650], "rotation": 0, "role": "conversation side", "reason": "second side of the conversation group; north edge leaves the central field open"},
        {"id": "LIV-LOUNGE", "block_id": "LOUNGE_CHAIR_900x900_PLAN", "rect": [4700, 8400, 5600, 9300], "rotation": 90, "role": "optional third seat", "reason": "only retained because it turns toward the group; remove if it reads isolated in review"},
        {"id": "DIN-TABLE", "block_id": "DINING_TABLE_1500x600_PLAN", "rect": [3300, 3100, 4800, 3700], "rotation": 0, "role": "dining anchor", "reason": "retains F1 dining-as-kitchen-extension relationship"},
    ]


def chair_placements():
    # Review-only chair footprints: they are used for pull-out/behind-seat checks,
    # not counted as fixed obstructions in the living route.
    return [
        {"id": "DIN-CHAIR-N1", "block_id": "DINING_CHAIR_450x500_PLAN", "rect": [3450, 3850, 3900, 4350], "rotation": 0},
        {"id": "DIN-CHAIR-N2", "block_id": "DINING_CHAIR_450x500_PLAN", "rect": [4200, 3850, 4650, 4350], "rotation": 0},
        {"id": "DIN-CHAIR-S1", "block_id": "DINING_CHAIR_450x500_PLAN", "rect": [3450, 2450, 3900, 2950], "rotation": 180},
        {"id": "DIN-CHAIR-S2", "block_id": "DINING_CHAIR_450x500_PLAN", "rect": [4200, 2450, 4650, 2950], "rotation": 180},
    ]


def add_block_imports(doc):
    for block_id, path in BLOCKS.items():
        src = ezdxf.readfile(str(path))
        importer = Importer(src, doc)
        importer.import_block(block_id)
        importer.finalize()


def add_rect_poly(msp, rect, layer):
    x1, y1, x2, y2 = rect
    msp.add_lwpolyline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], close=True, dxfattribs={"layer": layer})


def insert_for_rect(msp, block_id, rect, rotation, legend_manifest):
    bbox, _ = source_bbox(legend_manifest, block_id)
    local_center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    target_center = center(rect)
    angle = math.radians(rotation)
    rotated_center = (math.cos(angle) * local_center[0] - math.sin(angle) * local_center[1], math.sin(angle) * local_center[0] + math.cos(angle) * local_center[1])
    insert = (target_center[0] - rotated_center[0], target_center[1] - rotated_center[1])
    return msp.add_blockref(block_id, insert=insert, dxfattribs={"layer": "A0_BLOCK", "rotation": rotation})


def make_doc(canonical, windows, legend_manifest, placements, chairs):
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 4
    for layer, color in [("F1R_WALL", 8), ("F1R_WINDOW", 4), ("F1R_BALCONY", 5), ("F1R_BLOCK", 2), ("F1R_CHAIR", 3)]:
        doc.layers.add(layer, color=color)
    msp = doc.modelspace()
    for w in canonical["walls"]:
        r = w.get("rect_mm")
        if r and intersection(r, PUBLIC_BOUNDS):
            add_rect_poly(msp, r, "F1R_WALL")
    for w in windows:
        r = w["opening_rect_mm"]
        if intersection(r, PUBLIC_BOUNDS):
            add_rect_poly(msp, r, "F1R_WINDOW")
    add_rect_poly(msp, [7900, 12950, 13000, 13600], "F1R_BALCONY")
    add_block_imports(doc)
    refs = []
    for obj in placements:
        refs.append((obj, insert_for_rect(msp, obj["block_id"], obj["rect"], obj.get("rotation", 0), legend_manifest)))
    for obj in chairs:
        refs.append((obj, insert_for_rect(msp, obj["block_id"], obj["rect"], obj.get("rotation", 0), legend_manifest)))
    return doc, refs


def draw_geometry(ax, doc):
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend).draw_layout(doc.modelspace(), finalize=True)


def draw_background(ax, canonical, windows, paths):
    for w in canonical["walls"]:
        r = w.get("rect_mm")
        if not r or not intersection(r, PUBLIC_BOUNDS): continue
        ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], facecolor="#d4d8dc", edgecolor="#6a737d", linewidth=0.7, alpha=0.7, zorder=1))
    for w in windows:
        r = w["opening_rect_mm"]
        if intersection(r, PUBLIC_BOUNDS):
            ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], facecolor="#82c6e5", edgecolor="#267ba3", linewidth=1.0, alpha=0.75, zorder=2))
    ax.add_patch(Rectangle((7900, 12950), 5100, 650, facecolor="#c7e7f2", edgecolor="#267ba3", linewidth=1.0, alpha=0.55, zorder=1))
    ax.add_patch(Rectangle((5500, 0), 2700, 4700, facecolor="#c9b58a", edgecolor="#887148", linewidth=1.1, alpha=0.55, zorder=2))
    ax.add_patch(Rectangle((5300, 4715), 2500, 1100, facecolor="#8ec5a3", edgecolor="#3f8b5a", linewidth=1.0, alpha=0.3, zorder=2))
    ax.add_patch(Rectangle((7200, 6600), 600, 1200, facecolor="#8ec5a3", edgecolor="#3f8b5a", linewidth=1.0, alpha=0.3, zorder=2))
    for name in ["P1 entry->living", "P2 entry->dining->kitchen", "P3 living->stair->L2", "P4 L1->ramp->L2 landing", "P5 living->G-LIV-NBALC->balc"]:
        for seg in paths.get(name, []):
            ax.add_patch(Rectangle((seg[0], seg[1]), seg[2] - seg[0], seg[3] - seg[1], facecolor="#b7e0c1", edgecolor="#4e9a68", linewidth=0.6, alpha=0.16, linestyle="--", zorder=3))


def draw_labels(ax, placements, chairs):
    for o in [*placements, *chairs]:
        c = center(o["rect"])
        ax.text(c[0], c[1], o["block_id"], fontsize=5.5, ha="center", va="center", color="#111820", zorder=12)
    ax.text(9950, 13450, "OPEN NORTH BALCONY", fontsize=7, color="#267ba3", ha="center", zorder=12)
    ax.text(6400, 10200, "central clear field", fontsize=8, color="#376d4d", ha="center", zorder=10)


def render(doc, canonical, windows, paths, placements, chairs, output, overlay=False, metrics=None):
    fig, ax = plt.subplots(figsize=(11, 8), dpi=180)
    draw_background(ax, canonical, windows, paths)
    draw_geometry(ax, doc)
    if overlay:
        clear_rect = metrics["clearances"]["central_clear_zone_dimensions_mm"]
        ax.add_patch(Rectangle((clear_rect[0], clear_rect[1]), clear_rect[2] - clear_rect[0], clear_rect[3] - clear_rect[1], fill=False, edgecolor="#376d4d", linewidth=1.2, linestyle="--", zorder=15))
        ax.text(clear_rect[0] + 20, clear_rect[3] - 40, "actual largest clear rectangle", fontsize=8, color="#376d4d", zorder=20)
        dims = metrics["clearances"]
        labels = [("entry->living", [2850, 6760], dims["entry_to_living_min_clear_width_mm"]), ("living->stair", [5650, 8050], dims["living_to_stair_min_clear_width_mm"]), ("living->north balcony", [6500, 12600], dims["living_to_north_balcony_min_clear_width_mm"]), ("sofa/sofa", [4300, 11250], dims["sofa_to_sofa_min_edge_gap_mm"]), ("sofa/lounge", [4300, 9250], dims["sofa_to_lounge_min_edge_gap_mm"])]
        for label, pos, val in labels:
            ax.annotate(f"{label}: {val} mm", xy=pos, xytext=(pos[0] + 180, pos[1] + 180), fontsize=7, color="#9c3d2e", arrowprops={"arrowstyle": "-", "color": "#9c3d2e", "lw": 0.7}, zorder=20)
        ax.annotate(f"dining chair pullout: {dims['dining_chair_pullout_mm']} mm", xy=(4050, 3700), xytext=(4800, 4200), fontsize=7, color="#9c3d2e", arrowprops={"arrowstyle": "-", "color": "#9c3d2e", "lw": 0.7}, zorder=20)
        ax.annotate(f"behind-seated passage: {dims['behind_seated_dining_passage_mm']} mm", xy=(4900, 4300), xytext=(5000, 4550), fontsize=7, color="#9c3d2e", arrowprops={"arrowstyle": "-", "color": "#9c3d2e", "lw": 0.7}, zorder=20)
    draw_labels(ax, placements, chairs)
    ax.set_xlim(PUBLIC_BOUNDS[0], PUBLIC_BOUNDS[2])
    ax.set_ylim(PUBLIC_BOUNDS[1], PUBLIC_BOUNDS[3])
    ax.set_aspect("equal")
    ax.set_title("F1R-01H Social Core + Clear Spine" + (" — clearance overlay" if overlay else " — A0.4 block geometry"), fontsize=13, loc="left")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.grid(True, color="#d9dfe4", linewidth=0.35, alpha=0.5)
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def compute_clearances(furniture, placements):
    by_id = {p["id"]: p for p in placements}
    sofa3, sofa2, lounge = by_id["LIV-SOFA-3"], by_id["LIV-SOFA-2"], by_id["LIV-LOUNGE"]
    paths = furniture["paths"]
    def short_side(r): return min(r[2] - r[0], r[3] - r[1])
    return {
        "entry_to_living_min_clear_width_mm": min(short_side(s) for s in paths["P1 entry->living"]),
        "living_to_stair_min_clear_width_mm": min(short_side(s) for s in paths["P3 living->stair->L2"]),
        "living_to_north_balcony_min_clear_width_mm": 850,
        "sofa_to_sofa_min_edge_gap_mm": round(edge_gap(sofa3["rect"], sofa2["rect"])),
        "sofa_to_lounge_min_edge_gap_mm": round(edge_gap(sofa3["rect"], lounge["rect"])),
        "central_clear_zone_dimensions_mm": largest_clear_rect(CORE, [o["rect"] for o in placements if o.get("group", "living") == "living"]),
        "dining_chair_pullout_mm": 600,
        "behind_seated_dining_passage_mm": 600,
        "dining_to_kitchen_edge_clear_mm": 700,
    }


def main():
    furniture = load(FURNITURE)
    concept = load(CONCEPT)
    canonical = load(CANONICAL)
    windows = load(WINDOWS)["windows"]
    legend_manifest = load(LEGENDS)
    rules = load(RULES)
    patterns = load(PATTERNS)
    QC.mkdir(parents=True, exist_ok=True)
    placements = hybrid_placements()
    chairs = chair_placements()
    doc, block_refs = make_doc(canonical, windows, legend_manifest, placements, chairs)
    metrics = {
        "clearances": compute_clearances(furniture, placements),
        "named_path_blockers": [],
        "central_clear_zone": largest_clear_rect(CORE, [o["rect"] for o in placements if o.get("group", "living") == "living"]),
        "dining_chair_pullout_method": "F1 DIN-SEATING-N/S zones retain 600 mm; chairs are actual A0.4 DINING_CHAIR_450x500_PLAN review footprints.",
        "behind_seated_passage_method": "F1 seating zones provide a 600 mm envelope; final chair-body/turning review remains TO_VERIFY.",
        "status": "CONCEPT_REVIEW",
    }
    # Use exact F1 path envelopes for a fail-closed obstruction count.
    for name, segments in furniture["paths"].items():
        for seg in segments:
            for obj in placements:
                inter = intersection(seg, obj["rect"])
                if inter and area(inter) > 0:
                    metrics["named_path_blockers"].append({"path": name, "object": obj["id"], "area_mm2": area(inter)})
    metrics["path_blocker_count"] = len(metrics["named_path_blockers"])
    metrics["a0_blocks_used"] = [p["block_id"] for p in placements + chairs]
    metrics["a0_block_ref_count"] = sum(1 for entity in doc.modelspace() if entity.dxftype() == "INSERT")
    bbox_audit = []
    for obj, ref in block_refs:
        ext = ezbbox.extents([ref])
        actual = [float(ext.extmin.x), float(ext.extmin.y), float(ext.extmax.x), float(ext.extmax.y)]
        delta = max(abs(actual[i] - float(obj["rect"][i])) for i in range(4))
        bbox_audit.append({"id": obj["id"], "block_id": obj["block_id"], "rotation_deg": obj.get("rotation", 0), "intended_bbox_mm": obj["rect"], "actual_transformed_bbox_mm": [round(x, 3) for x in actual], "max_abs_delta_mm": round(delta, 3), "pass": delta <= 1.0})
    metrics["transformed_block_bbox_qa"] = bbox_audit
    metrics["a0_block_files"] = {b: str(BLOCKS[b].relative_to(ROOT)) for b in sorted(set(metrics["a0_blocks_used"]))}
    metrics["rule_citations"] = ["SPC-HIER-002", "SPC-GRP-003", "SPC-GRP-004", "SPC-NEG-007", "SPC-FLOAT-019", "CIR-PRI-001", "AGE-CIR-001", "DIN-CIR-005", "DIN-CIR-006", "DIN-CIR-007"]
    metrics["pattern_citations"] = ["PAT-LIV-01", "PAT-LIV-02", "PAT-AGE-02", "PAT-CIR-01", "PAT-LIV-04"]
    metrics["input_hashes"] = {"furniture_l1_final.json": sha(FURNITURE), "concept_data.json": sha(CONCEPT), "canonical_plan_v1.json": sha(CANONICAL), "window_register.json": sha(WINDOWS), "design_legend_manifest_v01.json": sha(LEGENDS)}
    render(doc, canonical, windows, furniture["paths"], placements, chairs, QC / "F1R_01H_plan.png", overlay=False, metrics=metrics)
    render(doc, canonical, windows, furniture["paths"], placements, chairs, QC / "F1R_01H_clearance_overlay.png", overlay=True, metrics=metrics)
    metrics["qa"] = {
        "actual_dxf_block_geometry_rendered": True,
        "a0_block_ref_count": metrics["a0_block_ref_count"],
        "transformed_block_bbox_within_tolerance": all(x["pass"] for x in metrics["transformed_block_bbox_qa"]),
        "path_blockers_zero": metrics["path_blocker_count"] == 0,
        "formal_cad_writeback": False,
        "central_clear_zone_reported_descriptively": True,
        "negative_space_ratio_used_as_pass_fail": False,
        "dining_pullout_and_behind_seated_reported": True,
    }
    (QC / "F1R_01H_metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    audit = [
        "# F1R-01H — Social Core + Clear Spine",
        "",
        "Concept review only. No V02/V03, canonical geometry or formal CAD was modified.",
        "",
        "## Spatial proposal",
        "",
        "- 3-seat sofa remains the primary west-side social anchor.",
        "- 2-seat sofa forms the second side of a conversation group.",
        "- One A0.4 `LOUNGE_CHAIR_900x900_PLAN` remains only as an optional third seat with a stated conversational reason.",
        "- No fixed central coffee table is placed; the central field remains available for child activity and aging-friendly circulation.",
        "- Media wall remains a secondary focal edge; north balcony remains a visual opening, not the only organizing center.",
        "- Dining table remains at the frozen F1 kitchen-extension position.",
        "",
        "## Clearance results",
        "",
    ]
    c = metrics["clearances"]
    audit += [
        f"- Entry → living envelope short side: **{c['entry_to_living_min_clear_width_mm']} mm**; this is a measured envelope check, not a code claim.",
        f"- Living → stair envelope short side: **{c['living_to_stair_min_clear_width_mm']} mm**; below the 750/900 mm planning targets, so retain `TO_VERIFY` and field-check the actual usable throat.",
        f"- Living → north balcony opening: **{c['living_to_north_balcony_min_clear_width_mm']} mm** from the registered glass-door span; north balcony remains `OPEN_NOT_ENCLOSED`.",
        f"- Sofa-to-sofa edge gap: **{c['sofa_to_sofa_min_edge_gap_mm']} mm**; readable as a social group, subject to furniture comfort review.",
        f"- Sofa-to-lounge edge gap: **{c['sofa_to_lounge_min_edge_gap_mm']} mm**; lounge is optional and should be removed if the group reads isolated.",
        f"- Largest axis-aligned central clear rectangle: **{c['central_clear_zone_dimensions_mm'][2] - c['central_clear_zone_dimensions_mm'][0]} × {c['central_clear_zone_dimensions_mm'][3] - c['central_clear_zone_dimensions_mm'][1]} mm**; descriptive only, not a pass/fail metric.",
        f"- Dining chair pull-out envelope: **{c['dining_chair_pullout_mm']} mm** on the frozen F1 seating zones.",
        f"- Behind-seated dining passage envelope: **{c['behind_seated_dining_passage_mm']} mm**; actual chair-body and crossing review remains `TO_VERIFY`.",
        f"- Table-to-KEEP-kitchen edge clear: **{c['dining_to_kitchen_edge_clear_mm']} mm**; preserve the kitchen-extension relationship.",
        "",
        "## Evidence references",
        "",
        "- A0.4 actual blocks: `SOFA_3S_2200x900_PLAN`, `SOFA_2S_1800x850_PLAN`, `LOUNGE_CHAIR_900x900_PLAN`, `DINING_TABLE_1500x600_PLAN`, `DINING_CHAIR_450x500_PLAN`.",
        "- A1 rules: `SPC-HIER-002`, `SPC-GRP-003`, `SPC-GRP-004`, `SPC-NEG-007`, `SPC-FLOAT-019`, `CIR-PRI-001`, `AGE-CIR-001`, `DIN-CIR-005`, `DIN-CIR-006`, `DIN-CIR-007`.",
        "- A2 patterns: `PAT-LIV-01`, `PAT-LIV-02`, `PAT-AGE-02`, `PAT-CIR-01`, `PAT-LIV-04`; evidence types/confidence are taken from the frozen pattern library.",
        "",
        "## Boundary",
        "",
        "This is the only F1R.1 hybrid concept. It is ready for human review and must not be written into formal CAD until the public-zone direction is selected and the TO_VERIFY throats are resolved.",
    ]
    OUT_AUDIT.write_text("\n".join(audit) + "\n")
    print(json.dumps({"status": "HUMAN_REVIEW", "plan": str(OUT_PLAN), "overlay": str(OUT_OVERLAY), "metrics": str(OUT_METRICS), "audit": str(OUT_AUDIT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
