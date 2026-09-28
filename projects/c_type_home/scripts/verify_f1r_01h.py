#!/usr/bin/env python3
"""F1R.1R geometric clearance verification for the frozen F1R-01H concept.

The script reuses the same F1R-01H placements and actual A0.4 DXF block
references, but measures geometry from transformed extents and architectural
obstacles. It never writes formal CAD or changes the concept placement.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import ezdxf
from ezdxf import bbox as ezbbox
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import build_f1r_01h as base
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

ROOT = SCRIPT_DIR.parent
QC = ROOT / "qc/f1r_public_zone"
FURNITURE = ROOT / "concept/furniture_l1_final.json"
CONCEPT = ROOT / "concept/concept_data.json"
CANONICAL = ROOT / "current_existing/canonical_plan_v1.json"
WINDOWS = ROOT / "current_existing/window_register.json"
LEGENDS = ROOT / "assets/cad_library/standard/manifests/design_legend_manifest_v01.json"
RULES = ROOT / "knowledge/design_rules/design_rulebook_v01.json"
PATTERNS = ROOT / "knowledge/precedents/pattern_library_v01.json"
OUT_OVERLAY = QC / "F1R_01H_clearance_overlay_v2.png"
OUT_METRICS = QC / "F1R_01H_metrics_v2.json"
OUT_AUDIT = QC / "F1R_01H_design_audit_v2.md"
PUBLIC_BOUNDS = base.PUBLIC_BOUNDS
CORE = base.CORE


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


def largest_clear_rect(container, obstacles):
    clipped = [r for o in obstacles if (r := intersection(container, o))]
    xs = sorted({container[0], container[2], *(x for r in clipped for x in (r[0], r[2]))})
    ys = sorted({container[1], container[3], *(y for r in clipped for y in (r[1], r[3]))})
    best = (0, [0, 0, 0, 0])
    for i, x1 in enumerate(xs[:-1]):
        for x2 in xs[i + 1:]:
            for j, y1 in enumerate(ys[:-1]):
                for y2 in ys[j + 1:]:
                    r = [x1, y1, x2, y2]
                    if any(intersection(r, o) for o in clipped):
                        continue
                    if area(r) > best[0]: best = (area(r), r)
    return best[1]


def point_blocked(point, obstacles):
    x, y = point
    return any(r[0] < x < r[2] and r[1] < y < r[3] for r in obstacles)


def free_width_at(point, tangent, obstacles, half=2500, step=10):
    dx, dy = tangent
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    samples = []
    t = -half
    while t <= half:
        p = (point[0] + nx * t, point[1] + ny * t)
        inside_bounds = PUBLIC_BOUNDS[0] <= p[0] <= PUBLIC_BOUNDS[2] and PUBLIC_BOUNDS[1] <= p[1] <= PUBLIC_BOUNDS[3]
        samples.append(bool(inside_bounds and not point_blocked(p, obstacles)))
        t += step
    zero = int(round(half / step))
    if zero >= len(samples) or not samples[zero]: return 0.0
    left = right = zero
    while left > 0 and samples[left - 1]: left -= 1
    while right < len(samples) - 1 and samples[right + 1]: right += 1
    return (right - left) * step


def polyline_min_width(points, obstacles, step=100):
    values = []
    for a, b in zip(points[:-1], points[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1.0
        n = max(1, int(length / step))
        for i in range(n + 1):
            t = i / n
            point = (a[0] + dx * t, a[1] + dy * t)
            values.append(free_width_at(point, (dx, dy), obstacles))
    return min(values) if values else 0.0


def actual_block_bboxes(doc, refs):
    rows = []
    for obj, ref in refs:
        ext = ezbbox.extents([ref])
        actual = [float(ext.extmin.x), float(ext.extmin.y), float(ext.extmax.x), float(ext.extmax.y)]
        delta = max(abs(actual[i] - float(obj["rect"][i])) for i in range(4))
        rows.append({"id": obj["id"], "block_id": obj["block_id"], "rotation_deg": obj.get("rotation", 0), "intended_bbox_mm": obj["rect"], "actual_transformed_bbox_mm": [round(x, 3) for x in actual], "max_abs_delta_mm": round(delta, 3), "pass": delta <= 1.0})
    return rows


def existing_wall_obstacles(canonical):
    return [w["rect_mm"] for w in canonical["walls"] if w.get("disposition") == "EXISTING"]


def build_obstacles(canonical, furniture, block_bboxes):
    obs = existing_wall_obstacles(canonical)
    # Fixed geometry that affects the public-zone throats.
    obs.extend([[5500, 0, 8200, 4700], [5300, 4715, 7800, 5815], [7200, 6600, 7800, 7800], [2900, 6800, 3400, 7200]])
    obs.extend(row["actual_transformed_bbox_mm"] for row in block_bboxes if not row["id"].startswith("DIN-CHAIR"))
    return obs


def route_measurements(obstacles, canonical, windows):
    entry_path = [(2800, 5900), (3400, 6800), (4300, 7000), (4300, 8200)]
    stair_path = [(4500, 7000), (6000, 7000), (7100, 7000)]
    balcony_path = [(6000, 11800), (7000, 12000), (7750, 12225)]
    stair_rect = [7200, 6600, 7800, 7800]
    balcony_opening = next(x["opening_rect_mm"] for x in windows if x["window_id"] == "G-LIV-NBALC")
    return {
        "entry_to_living_actual_min_mm": round(polyline_min_width(entry_path, obstacles)),
        "living_to_stair_approach_actual_min_mm": round(polyline_min_width(stair_path, obstacles)),
        "living_to_stair_opening_actual_mm": stair_rect[3] - stair_rect[1],
        "living_to_north_balcony_approach_actual_min_mm": round(polyline_min_width(balcony_path, obstacles)),
        "living_to_north_balcony_opening_actual_mm": balcony_opening[3] - balcony_opening[1],
        "route_sampling": {"entry_to_living": entry_path, "living_to_stair": stair_path, "living_to_north_balcony": balcony_path, "cross_section_step_mm": 10, "polyline_sample_step_mm": 100},
    }


def dining_measurements(block_bboxes, canonical, furniture):
    by_id = {x["id"]: x["actual_transformed_bbox_mm"] for x in block_bboxes}
    table = by_id["DIN-TABLE"]
    north = [by_id["DIN-CHAIR-N1"], by_id["DIN-CHAIR-N2"]]
    south = [by_id["DIN-CHAIR-S1"], by_id["DIN-CHAIR-S2"]]
    pullouts = [min(abs(ch[1] - table[3]), abs(table[1] - ch[3])) for ch in [*north, *south]]
    # The opening behind the north chairs is the registered sliding glass door.
    opening = next(x["opening_rect_mm"] for x in load(WINDOWS)["windows"] if x["window_id"] == "G-DIN-LIV")
    north_gap = max(0, opening[1] - max(ch[3] for ch in north))
    south_gap = max(0, min(ch[1] for ch in south) - 0)
    behind = min(north_gap, south_gap)
    kitchen = [5500, 0, 8200, 4700]
    table_to_kitchen = max(0, kitchen[0] - table[2])
    return {"dining_table_actual_bbox_mm": table, "dining_chair_actual_bboxes_mm": [*north, *south], "dining_chair_pullout_actual_min_mm": min(pullouts), "behind_seated_passage_actual_min_mm": behind, "north_behind_seated_gap_mm": north_gap, "south_behind_seated_gap_mm": south_gap, "table_to_keep_kitchen_actual_min_mm": table_to_kitchen, "reference_targets": {"chair_pullout_mm": 600, "behind_seated_passage_mm": 900, "table_to_kitchen_mm": 1000}}


def render_overlay(doc, canonical, windows, furniture, refs, block_bboxes, metrics):
    fig, ax = plt.subplots(figsize=(11, 8), dpi=180)
    # Reuse the F1R background but do not treat the old path boxes as measurements.
    base.draw_background(ax, canonical, windows, furniture["paths"])
    base.draw_geometry(ax, doc)
    clear = metrics["actual_largest_clear_rectangle_mm"]
    ax.add_patch(Rectangle((clear[0], clear[1]), clear[2]-clear[0], clear[3]-clear[1], fill=False, edgecolor="#1c9c5b", linewidth=1.8, linestyle="--", zorder=18))
    ax.text(clear[0] + 20, clear[3] - 40, "ACTUAL largest clear rectangle", fontsize=8, color="#1c9c5b", zorder=20)
    c = metrics["clearances"]
    labels = [
        ("entry→living actual", c["entry_to_living_actual_min_mm"], (3000, 6900)),
        ("stair approach actual", c["living_to_stair_approach_actual_min_mm"], (5700, 7900)),
        ("stair opening actual", c["living_to_stair_opening_actual_mm"], (6800, 7200)),
        ("balcony approach actual", c["living_to_north_balcony_approach_actual_min_mm"], (6300, 12300)),
        ("balcony opening actual", c["living_to_north_balcony_opening_actual_mm"], (7000, 12600)),
        ("sofa→sofa actual", c["sofa_to_sofa_min_edge_gap_mm"], (4300, 11250)),
        ("sofa→lounge actual", c["sofa_to_lounge_min_edge_gap_mm"], (4300, 9250)),
        ("chair pullout actual", c["dining_chair_pullout_actual_min_mm"], (4100, 4100)),
        ("behind-seated actual", c["behind_seated_passage_actual_min_mm"], (5200, 4450)),
        ("table→KEEP kitchen actual", c["table_to_keep_kitchen_actual_min_mm"], (5000, 3300)),
    ]
    for label, value, xy in labels:
        ax.annotate(f"{label}: {value} mm", xy=xy, xytext=(xy[0]+170, xy[1]+170), fontsize=7, color="#a23d2d", arrowprops={"arrowstyle":"-", "color":"#a23d2d", "lw":0.7}, zorder=22)
    ax.set_xlim(PUBLIC_BOUNDS[0], PUBLIC_BOUNDS[2]); ax.set_ylim(PUBLIC_BOUNDS[1], PUBLIC_BOUNDS[3]); ax.set_aspect("equal")
    ax.set_title("F1R-01H — geometric clearance v2 (actual transformed geometry)", fontsize=13, loc="left")
    ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)"); ax.grid(True, color="#d9dfe4", linewidth=0.35, alpha=0.5)
    fig.tight_layout(); fig.savefig(OUT_OVERLAY, bbox_inches="tight"); plt.close(fig)


def main():
    furniture = load(FURNITURE); canonical = load(CANONICAL); windows = load(WINDOWS)["windows"]; legend = load(LEGENDS); rules = {x["rule_id"]:x for x in load(RULES)["rules"]}
    placements = base.hybrid_placements(); chairs = base.chair_placements(); doc, refs = base.make_doc(canonical, windows, legend, placements, chairs)
    block_bboxes = actual_block_bboxes(doc, refs)
    obstacles = build_obstacles(canonical, furniture, block_bboxes)
    routes = route_measurements(obstacles, canonical, windows)
    dining = dining_measurements(block_bboxes, canonical, furniture)
    actual_clear = largest_clear_rect(CORE, obstacles + [x["actual_transformed_bbox_mm"] for x in block_bboxes])
    # sofa relationships from actual transformed bboxes
    by_id = {x["id"]: x["actual_transformed_bbox_mm"] for x in block_bboxes}
    target = rules["LIV-CIRC-001"]
    clearances = {
        "entry_to_living_actual_min_mm": routes["entry_to_living_actual_min_mm"],
        "entry_to_living_reference_min_mm": target["recommended_min_mm"],
        "entry_to_living_reference_preferred_mm": target["preferred_mm"],
        "living_to_stair_actual_min_mm": min(routes["living_to_stair_approach_actual_min_mm"], routes["living_to_stair_opening_actual_mm"]),
        "living_to_stair_approach_actual_min_mm": routes["living_to_stair_approach_actual_min_mm"],
        "living_to_stair_opening_actual_mm": routes["living_to_stair_opening_actual_mm"],
        "living_to_stair_reference_secondary_min_mm": rules["CIR-SEC-003"]["recommended_min_mm"],
        "living_to_stair_reference_preferred_mm": rules["CIR-SEC-003"]["preferred_mm"],
        "living_to_north_balcony_actual_min_mm": min(routes["living_to_north_balcony_approach_actual_min_mm"], routes["living_to_north_balcony_opening_actual_mm"]),
        "living_to_north_balcony_approach_actual_min_mm": routes["living_to_north_balcony_approach_actual_min_mm"],
        "living_to_north_balcony_opening_actual_mm": routes["living_to_north_balcony_opening_actual_mm"],
        "living_to_north_balcony_reference_min_mm": rules["LIV-BAL-010"]["recommended_min_mm"],
        "living_to_north_balcony_reference_preferred_mm": rules["LIV-BAL-010"]["preferred_mm"],
        "sofa_to_sofa_min_edge_gap_mm": round(base.edge_gap(by_id["LIV-SOFA-3"], by_id["LIV-SOFA-2"])),
        "sofa_to_lounge_min_edge_gap_mm": round(base.edge_gap(by_id["LIV-SOFA-3"], by_id["LIV-LOUNGE"])),
        "dining_chair_pullout_actual_min_mm": dining["dining_chair_pullout_actual_min_mm"],
        "dining_chair_pullout_reference_min_mm": rules["DIN-CIR-005"]["recommended_min_mm"],
        "behind_seated_passage_actual_min_mm": dining["behind_seated_passage_actual_min_mm"],
        "behind_seated_passage_reference_min_mm": rules["DIN-CIR-006"]["recommended_min_mm"],
        "table_to_keep_kitchen_actual_min_mm": dining["table_to_keep_kitchen_actual_min_mm"],
        "table_to_keep_kitchen_reference_min_mm": rules["DIN-CIR-007"]["recommended_min_mm"],
        "sampling_method": "sampled cross-sections along architectural anchor polylines; route rectangle widths not used as measurements",
    }
    metrics = {"version":"f1r-01h-v2", "status":"HUMAN_REVIEW", "method":"geometric_free_space_v2", "clearances": clearances, "route_sampling": routes["route_sampling"], "reference_envelopes": {"entry_to_living": furniture["paths"]["P1 entry->living"], "living_to_stair": furniture["paths"]["P3 living->stair->L2"], "living_to_north_balcony": furniture["paths"]["P5 living->G-LIV-NBALC->balc"]}, "path_blocker_test": {"count": 0, "meaning":"no direct rectangle intersection in named path envelope; this is not a minimum-clearance result"}, "actual_largest_clear_rectangle_mm": actual_clear, "transformed_block_bbox_qa": block_bboxes, "dining": dining, "a0_block_ref_count": len(refs), "formal_cad_writeback": False, "input_hashes": {"furniture_l1_final.json":sha(FURNITURE),"concept_data.json":sha(CONCEPT),"canonical_plan_v1.json":sha(CANONICAL),"window_register.json":sha(WINDOWS),"design_legend_manifest_v01.json":sha(LEGENDS)}, "qa": {"actual_dxf_block_geometry_rendered": True, "transformed_bbox_all_within_1mm": all(x["pass"] for x in block_bboxes), "routes_measured_from_geometry": True, "reference_envelopes_kept_separate": True, "negative_space_ratio_used_as_pass_fail": False}}
    render_overlay(doc, canonical, windows, furniture, refs, block_bboxes, metrics)
    OUT_METRICS.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    c=clearances
    audit = ["# F1R-01H — Geometric Clearance Verification v2", "", "This report preserves the F1R-01H furniture layout. It does not modify V02/V03, canonical data or formal CAD.", "", "## Measurement method", "", "- A0.4 normalized DXF block references are inserted at the F1R-01H placements and their transformed extents are audited within 1 mm.", "- Existing canonical wall rectangles, KEEP kitchen, ramp, stair and registered openings are treated as geometry obstacles.", "- Route values use sampled cross-sections along architectural anchor polylines. The old F1 path rectangles are retained only as reference envelopes.", "- `path_blocker_count=0` remains a separate direct-intersection diagnostic; it is not a clearance pass.", "", "## Actual vs reference", "", f"- Entry → living: **{c['entry_to_living_actual_min_mm']} mm actual**; reference min {c['entry_to_living_reference_min_mm']} / preferred {c['entry_to_living_reference_preferred_mm']} mm.", f"- Living → stair: **{c['living_to_stair_actual_min_mm']} mm actual** = approach {c['living_to_stair_approach_actual_min_mm']} + stair opening {c['living_to_stair_opening_actual_mm']}; reference secondary min {c['living_to_stair_reference_secondary_min_mm']} / preferred {c['living_to_stair_reference_preferred_mm']} mm. `TO_VERIFY`.", f"- Living → north balcony: **{c['living_to_north_balcony_actual_min_mm']} mm actual** = approach {c['living_to_north_balcony_approach_actual_min_mm']} + registered opening {c['living_to_north_balcony_opening_actual_mm']}; reference min {c['living_to_north_balcony_reference_min_mm']} / preferred {c['living_to_north_balcony_reference_preferred_mm']} mm. `TO_VERIFY`.", f"- Sofa-to-sofa: **{c['sofa_to_sofa_min_edge_gap_mm']} mm actual transformed-bbox gap**.", f"- Sofa-to-lounge: **{c['sofa_to_lounge_min_edge_gap_mm']} mm actual transformed-bbox gap**.", f"- Actual largest clear rectangle: **{actual_clear[2]-actual_clear[0]} × {actual_clear[3]-actual_clear[1]} mm** at `{actual_clear}`; this is descriptive, not pass/fail.", f"- Dining chair pull-out: **{dining['dining_chair_pullout_actual_min_mm']} mm actual** vs reference {dining['reference_targets']['chair_pullout_mm']} mm.", f"- Behind-seated dining passage: **{dining['behind_seated_passage_actual_min_mm']} mm actual** (north side {dining['north_behind_seated_gap_mm']} mm; south side {dining['south_behind_seated_gap_mm']} mm) vs reference {dining['reference_targets']['behind_seated_passage_mm']} mm; `TO_VERIFY`.", f"- Table/chair to KEEP kitchen: **{dining['table_to_keep_kitchen_actual_min_mm']} mm actual table edge gap** vs reference {dining['reference_targets']['table_to_kitchen_mm']} mm.", "", "## Result", "", "Geometry method is corrected, but the measured living→stair, living→balcony, behind-seated passage and kitchen-edge numbers remain human-review items. Do not write the layout into formal CAD yet."]
    OUT_AUDIT.write_text("\n".join(audit) + "\n")
    print(json.dumps({"status":"HUMAN_REVIEW","overlay":str(OUT_OVERLAY),"metrics":str(OUT_METRICS),"audit":str(OUT_AUDIT)},ensure_ascii=False))


if __name__ == "__main__": main()
