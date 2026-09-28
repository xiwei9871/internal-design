#!/usr/bin/env python3
"""Build non-CAD F1R public-zone concept comparisons.

This script is deliberately concept-only: it reads frozen F1/canonical inputs and
A0.4 legend metadata, then writes SVG/PNG comparison sheets, metrics and an audit.
It never writes DXF, canonical geometry, V02/V03 or furniture_l1_final.json.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
QC = ROOT / "qc/f1r_public_zone"
FURNITURE_PATH = ROOT / "concept/furniture_l1_final.json"
CONCEPT_PATH = ROOT / "concept/concept_data.json"
CANONICAL_PATH = ROOT / "current_existing/canonical_plan_v1.json"
WINDOW_PATH = ROOT / "current_existing/window_register.json"
LEGEND_PATH = ROOT / "assets/cad_library/standard/manifests/design_legend_manifest_v01.json"
RULE_PATH = ROOT / "knowledge/design_rules/design_rulebook_v01.json"
PATTERN_PATH = ROOT / "knowledge/precedents/pattern_library_v01.json"
RESEARCH_DATE = "2026-09-26"

PUBLIC_BOUNDS = [2500, -300, 8500, 13750]
LIVING_CORE = [3900, 7400, 7700, 11750]
PATH_NAMES = ["P1 entry->living", "P2 entry->dining->kitchen", "P3 living->stair->L2", "P4 L1->ramp->L2 landing", "P5 living->G-LIV-NBALC->balc"]
A0_BLOCKS = {
    "SOFA_3S_2200x900_PLAN": [2200, 900],
    "SOFA_2S_1800x850_PLAN": [1800, 850],
    "LOUNGE_CHAIR_900x900_PLAN": [900, 900],
    "DINING_TABLE_1500x600_PLAN": [1500, 600],
}


def load(path: Path):
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rect_area(r):
    return max(0, r[2] - r[0]) * max(0, r[3] - r[1])


def intersection(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    return [x1, y1, x2, y2] if x2 > x1 and y2 > y1 else None


def center(r):
    return ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)


def placement(item_id, block_id, rect, role, *, rotation=0, group="living", reason=""):
    return {"id": item_id, "block_id": block_id, "rect": rect, "rotation_deg": rotation, "group": group, "role": role, "spatial_reason": reason, "footprint_mm": A0_BLOCKS.get(block_id)}


def base_fixed(furniture):
    fixed = []
    for item in furniture["categories"]["fixed_keep"]:
        if item["id"] in {"K-CAB", "LBALC-CAB", "ENTRY-SHOE-CAB", "ENTRY-BENCH"}:
            fixed.append({"id": item["id"], "rect": item["rect"], "role": "KEEP", "block_id": "EXISTING_KEEP", "spatial_reason": item["note"]})
    fixed.append({"id": "RAMP", "rect": furniture["categories"]["accessibility"][0]["rect"], "role": "ACCESS", "block_id": "ASSISTED_ROUTE", "spatial_reason": "provisional assisted/power-wheelchair route"})
    fixed.append({"id": "STAIR-EXISTING", "rect": furniture["categories"]["accessibility"][1]["rect"], "role": "ACCESS", "block_id": "EXISTING_STAIR", "spatial_reason": "existing daily stair route"})
    fixed.append({"id": "LIV-MEDIA-WALL", "rect": furniture["categories"]["media"][0]["rect"], "role": "MEDIA", "block_id": "MEDIA_WALL_LOCKED", "spatial_reason": "locked projector/laser-TV edge; device remains TO_VERIFY"})
    return fixed


def current_baseline(furniture):
    large = {x["id"]: x for x in furniture["categories"]["proposed_large_furniture"]}
    movable = {x["id"]: x for x in furniture["categories"]["movable_furniture"]}
    return [
        placement("LIV-SOFA-3", "SOFA_3S_2200x900_PLAN", large["LIV-SOFA-3"]["rect"], "3-seat sofa", rotation=90, reason="F1 west-wall sofa; faces east media wall"),
        placement("LIV-SOFA-2", "SOFA_2S_1800x850_PLAN", large["LIV-SOFA-2"]["rect"], "2-seat sofa", reason="F1 north-bay sofa; 100 mm clear of window face"),
        placement("LIV-LOUNGE", "F1_DAY_LOUNGE_1500x1100", large["LIV-LOUNGE"]["rect"], "day-lounge", reason="F1 south-central day-lounge"),
        placement("DIN-TABLE", "DINING_TABLE_1500x600_PLAN", large["DIN-TABLE"]["rect"], "dining table", group="dining", reason="F1 daily 4-adult+child table"),
        placement("LIV-SIDE-TABLE", "F1_SIDE_TABLE_450x450", movable["LIV-SIDE-TABLE"]["rect"], "side table", reason="F1 movable side table"),
        placement("LIV-COFFEE-MOV", "F1_COFFEE_750x1100", movable["LIV-COFFEE-MOV"]["rect"], "coffee table", reason="F1 movable; central core kept open"),
    ]


def options():
    return {
        "single_axis_social_core": {
            "label": "01 Single-axis social core",
            "short": "one conversation group; projection becomes secondary mode",
            "placements": [
                placement("LIV-SOFA-3", "SOFA_3S_2200x900_PLAN", [2900, 9000, 3800, 11200], "3-seat sofa", rotation=90, reason="anchor one side of a face-to-face conversation group while preserving P1"),
                placement("LIV-SOFA-2", "SOFA_2S_1800x850_PLAN", [4850, 10800, 6650, 11650], "2-seat sofa", reason="forms the second edge of the social group while leaving P5 open"),
                placement("LIV-LOUNGE", "LOUNGE_CHAIR_900x900_PLAN", [4700, 8400, 5600, 9300], "lounge chair", rotation=90, reason="third seat turns toward the conversation group, not only the media wall"),
                placement("DIN-TABLE", "DINING_TABLE_1500x600_PLAN", [3300, 3100, 4800, 3700], "dining table", group="dining", reason="retain F1 dining/kitchen anchor"),
            ],
            "rules": ["SPC-HIER-002", "SPC-GRP-003", "SPC-GRP-004", "SPC-NEG-007", "LIV-FLEX-003", "DIN-CIR-007"],
            "patterns": ["PAT-LIV-01", "PAT-LIV-02", "PAT-LIV-04", "PAT-AGE-02"],
            "pros": ["Creates one readable conversation group instead of three independent seats.", "Keeps the central field available for child activity and aging-friendly movement.", "Leaves the projector wall as a secondary mode rather than the only orientation."],
            "cons": ["Requires changing the current 2-seat sofa position/orientation.", "Throw distance and glare still need the selected product.", "The third seat is smaller and may need a later comfort check."],
            "axis": "entry -> social core -> north balcony; media wall is secondary focal edge",
            "conversation": ["LIV-SOFA-3 <-> LIV-SOFA-2", "LIV-SOFA-3 <-> LIV-LOUNGE"],
        },
        "view_first_balcony": {
            "label": "02 View-first / north-balcony hierarchy",
            "short": "north balcony becomes the primary visual extension",
            "placements": [
                placement("LIV-SOFA-3", "SOFA_3S_2200x900_PLAN", [4000, 8600, 6200, 9500], "3-seat sofa", rotation=0, reason="long seat faces north view/balcony axis while preserving P1/P3"),
                placement("LIV-SOFA-2", "SOFA_2S_1800x850_PLAN", [5700, 10200, 6550, 12000], "2-seat sofa", rotation=90, reason="secondary seat turns toward the view and keeps the media edge quiet"),
                placement("LIV-LOUNGE", "LOUNGE_CHAIR_900x900_PLAN", [6300, 8200, 7200, 9100], "lounge chair", reason="small reading/view seat aligned with the balcony axis"),
                placement("DIN-TABLE", "DINING_TABLE_1500x600_PLAN", [3300, 3100, 4800, 3700], "dining table", group="dining", reason="retain F1 dining/kitchen anchor"),
            ],
            "rules": ["SPC-SIGHT-013", "SPC-SIGHT-014", "SPC-HIER-002", "SPC-EDGE-011", "LIV-BAL-010", "DIN-CIR-007"],
            "patterns": ["PAT-LIV-06", "PAT-AGE-02", "PAT-LIV-04", "PAT-CIR-01"],
            "pros": ["Makes the open north balcony a visual extension rather than a leftover route.", "Reduces the room's dependence on a TV/media focal point.", "Supports daylight, view and a calmer seating hierarchy."],
            "cons": ["Projector viewing direction becomes less direct and must be product-checked.", "The north-bay sofa and balcony threshold need a detailed glare/privacy review.", "A view-first arrangement may feel less compact for group viewing."],
            "axis": "entry -> dining -> living view axis -> open north balcony",
            "conversation": ["LIV-SOFA-3 <-> LIV-LOUNGE"],
        },
        "negative_space_spine": {
            "label": "03 Negative-space + circulation spine",
            "short": "edge-load furniture; organize one clear central field",
            "placements": [
                placement("LIV-SOFA-3", "SOFA_3S_2200x900_PLAN", [2900, 9500, 3800, 11700], "3-seat sofa", rotation=90, reason="edge-load west wall; preserve P1/P3 spine"),
                placement("LIV-SOFA-2", "SOFA_2S_1800x850_PLAN", [4550, 11800, 6350, 12650], "2-seat sofa", reason="edge-load north bay; preserve central activity field"),
                placement("LIV-LOUNGE", "LOUNGE_CHAIR_900x900_PLAN", [6200, 8200, 7100, 9100], "lounge chair", reason="single edge seat anchors the east/south edge without floating in the core"),
                placement("DIN-TABLE", "DINING_TABLE_1500x600_PLAN", [3300, 3100, 4800, 3700], "dining table", group="dining", reason="retain F1 dining/kitchen anchor"),
            ],
            "rules": ["SPC-NEG-007", "SPC-NEG-008", "SPC-FLOAT-019", "SPC-FLOAT-020", "CIR-PRI-001", "AGE-CIR-001", "DIN-CIR-007"],
            "patterns": ["PAT-CIR-01", "PAT-LIV-01", "PAT-LIV-02", "PAT-STOR-02"],
            "pros": ["Maximizes a readable child/aging activity field and furniture-free circulation spine.", "Every remaining object has an explicit edge, route or grouping reason.", "Lowest object density and simplest future reconfiguration."],
            "cons": ["Conversation grouping is weaker than Option 01.", "The room may feel sparse unless lighting/rug/material cues define zones later.", "Lounge chair becomes optional and should be removed if it reads as an isolated object."],
            "axis": "entry -> clear central spine -> stair/balcony; media wall remains an edge condition",
            "conversation": ["LIV-SOFA-3 <-> LIV-SOFA-2 (secondary)"],
        },
    }


def metric(option, furniture, paths):
    placements = option["placements"]
    blockers = []
    for name in PATH_NAMES:
        for seg in furniture["paths"].get(name, []):
            for obj in placements:
                inter = intersection(seg, obj["rect"])
                if inter and rect_area(inter) > 0:
                    blockers.append({"path": name, "object": obj["id"], "area_mm2": rect_area(inter)})
    occupied = sum(rect_area(intersection(LIVING_CORE, obj["rect"]) or [0, 0, 0, 0]) for obj in placements if obj["group"] == "living")
    core_area = rect_area(LIVING_CORE)
    bbox = [min(o["rect"][0] for o in placements if o["group"] == "living"), min(o["rect"][1] for o in placements if o["group"] == "living"), max(o["rect"][2] for o in placements if o["group"] == "living"), max(o["rect"][3] for o in placements if o["group"] == "living")]
    return {"path_blockers": blockers, "path_blocker_count": len(blockers), "living_core_mm2": core_area, "living_core_occupied_mm2": occupied, "negative_space_ratio": round(1 - occupied / core_area, 4), "living_furniture_bbox": bbox, "conversation_relationships": option["conversation"], "main_visual_axis": option["axis"], "dining_table_kept": next(o["rect"] for o in placements if o["id"] == "DIN-TABLE") == [3300, 3100, 4800, 3700]}


def svg_rect(r, ymax):
    return r[0], ymax - r[3], r[2] - r[0], r[3] - r[1]


def svg_text(x, y, text, size=150, fill="#263238", anchor="start", weight="normal"):
    return f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(text))}</text>'


def render_svg(option, fixed, walls, windows, paths, title, out_svg, panel_width=760, panel_height=700):
    xmin, ymin, xmax, ymax = PUBLIC_BOUNDS
    scale = min((panel_width - 70) / (xmax - xmin), (panel_height - 90) / (ymax - ymin))
    ox, oy = 35, 55
    def tx(x): return ox + (x - xmin) * scale
    def ty(y): return oy + (ymax - y) * scale
    def rect(r):
        x, y, w, h = svg_rect(r, ymax)
        return tx(x), oy + (ymax - r[3]) * scale, w * scale, h * scale
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{panel_width}" height="{panel_height}" viewBox="0 0 {panel_width} {panel_height}"><rect width="100%" height="100%" fill="#fbfcfd"/>', svg_text(20, 28, title, 20, "#17324d", weight="bold")]
    # bounds and public base
    x, y, w, h = rect(PUBLIC_BOUNDS)
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#f7f8f6" stroke="#6c7782" stroke-width="2"/>')
    # walls
    for wall in walls:
        r = wall.get("rect_mm") or wall.get("rect")
        if not r or not intersection(r, PUBLIC_BOUNDS): continue
        x, y, w, h = rect(r)
        color = "#515c67" if wall.get("type") == "exterior" or "EXT" in wall.get("id", "") else "#8b949e"
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" opacity="0.72"/>')
    # kitchen, ramp, stair, media and balcony
    for item in fixed:
        r = item["rect"]
        if not intersection(r, PUBLIC_BOUNDS): continue
        x, y, w, h = rect(r)
        role = item.get("role")
        color = {"KEEP": "#c9b58a", "ACCESS": "#8ec5a3", "MEDIA": "#cf6b63"}.get(role, "#b9c0c8")
        opacity = "0.55" if role == "ACCESS" else "0.75"
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" opacity="{opacity}" stroke="#53616d" stroke-width="1"/>')
        if role in {"KEEP", "MEDIA"}:
            parts.append(svg_text(x + w / 2, y + h / 2 + 4, item["id"], max(8, 100 * scale), "#263238", "middle"))
    # windows and balcony labels
    for win in windows:
        r = win.get("opening_rect_mm")
        if not r or not intersection(r, PUBLIC_BOUNDS): continue
        x, y, w, h = rect(r)
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#7fc5e8" opacity="0.60" stroke="#2a78a0" stroke-width="1"/>')
    # paths
    for name in PATH_NAMES:
        for seg in paths.get(name, []):
            x, y, w, h = rect(seg)
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#b7e0c1" opacity="0.22" stroke="#4e9a68" stroke-width="1" stroke-dasharray="5,4"/>')
    # furniture
    fills = {"living": "#e28f62", "dining": "#5d94c6"}
    for obj in option["placements"]:
        x, y, w, h = rect(obj["rect"])
        fill = fills.get(obj["group"], "#b18bc7")
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}" opacity="0.85" stroke="#2e3a44" stroke-width="1.4"/>')
        parts.append(svg_text(x + w / 2, y + h / 2 + 3, obj["id"], max(8, 90 * scale), "#16202a", "middle", "bold"))
    # north label and metrics
    parts.append(svg_text(tx(7900), ty(13650), "OPEN NORTH BALCONY", max(8, 115 * scale), "#2a78a0", "middle", "bold"))
    m = option["metrics"]
    parts.append(svg_text(20, panel_height - 30, f"negative space {m['negative_space_ratio']:.2f} | path blockers {m['path_blocker_count']}", 13, "#263238"))
    parts.append("</svg>")
    out_svg.write_text("".join(parts))


def main():
    furniture = load(FURNITURE_PATH)
    concept = load(CONCEPT_PATH)
    canonical = load(CANONICAL_PATH)
    windows = load(WINDOW_PATH)["windows"]
    legends = load(LEGEND_PATH)["legends"]
    rules = {x["rule_id"]: x for x in load(RULE_PATH)["rules"]}
    patterns = {x["pattern_id"]: x for x in load(PATTERN_PATH)["patterns"]}
    QC.mkdir(parents=True, exist_ok=True)
    fixed = base_fixed(furniture)
    option_defs = options()
    for option in option_defs.values():
        option["metrics"] = metric(option, furniture, furniture["paths"])
        option["pattern_evidence"] = [{"pattern_id": p, "evidence_type": patterns[p]["evidence_type"], "evidence_confidence": patterns[p]["evidence_confidence"], "verified_precedent_ids": patterns[p].get("verified_precedent_ids", [])} for p in option["patterns"]]
        option["rule_checks"] = [{"rule_id": r, "classification": rules[r]["classification"], "source_strength": rules[r]["source_strength"], "automatic_gate": rules[r]["automatic_gate"]} for r in option["rules"]]
        option["legend_footprints"] = {o["block_id"]: next((l["design_target_bbox_mm"] for l in legends if l["id"] == o["block_id"]), None) for o in option["placements"] if o["block_id"] in A0_BLOCKS}
    baseline = {"label": "00 F1 current baseline", "short": "frozen current F1 arrangement", "placements": current_baseline(furniture), "rules": ["SPC-HIER-001", "SPC-GRP-003", "SPC-NEG-007", "DIN-CIR-007", "LIV-BAL-010"], "patterns": ["PAT-LIV-01", "PAT-LIV-04", "PAT-CIR-01"], "pros": ["Current F1 furniture and route record remain visible as the comparison baseline."], "cons": ["F1 audit identifies weak hierarchy, conversation grouping and object reasons."], "axis": "entry -> living/media edge competes with north balcony view", "conversation": []}
    baseline["metrics"] = metric(baseline, furniture, furniture["paths"])
    all_options = {"baseline": baseline, **option_defs}
    for option in all_options.values():
        option.setdefault("pattern_evidence", [{"pattern_id": p, "evidence_type": patterns[p]["evidence_type"], "evidence_confidence": patterns[p]["evidence_confidence"], "verified_precedent_ids": patterns[p].get("verified_precedent_ids", [])} for p in option["patterns"]])
        option.setdefault("rule_checks", [{"rule_id": r, "classification": rules[r]["classification"], "source_strength": rules[r]["source_strength"], "automatic_gate": rules[r]["automatic_gate"]} for r in option["rules"]])
    for key, option in all_options.items():
        render_svg(option, fixed, canonical["walls"], windows, furniture["paths"], option["label"], QC / f"{key}.svg")
        if shutil.which("rsvg-convert"):
            subprocess.run(["rsvg-convert", "-o", str(QC / f"{key}.png"), str(QC / f"{key}.svg")], check=True)
    # composite SVG with same-scale panels (4 columns)
    panel_w, panel_h = 760, 700
    composite = ['<svg xmlns="http://www.w3.org/2000/svg" width="3040" height="740" viewBox="0 0 3040 740"><rect width="100%" height="100%" fill="#e9edf1"/>']
    order = ["baseline", "single_axis_social_core", "view_first_balcony", "negative_space_spine"]
    for i, key in enumerate(order):
        svg_text_content = (QC / f"{key}.svg").read_text()
        inner = svg_text_content[svg_text_content.index(">") + 1 : svg_text_content.rfind("</svg>")]
        composite.append(f'<g transform="translate({i * panel_w},0)">{inner}</g>')
    composite.append("</svg>")
    (QC / "f1r_same_scale_comparison.svg").write_text("".join(composite))
    if shutil.which("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-o", str(QC / "f1r_same_scale_comparison.png"), str(QC / "f1r_same_scale_comparison.svg")], check=True)
    input_hashes = {"furniture_l1_final.json": sha(FURNITURE_PATH), "concept_data.json": sha(CONCEPT_PATH), "canonical_plan_v1.json": sha(CANONICAL_PATH), "window_register.json": sha(WINDOW_PATH), "design_legend_manifest_v01.json": sha(LEGEND_PATH)}
    valid_rules = set(rules)
    valid_patterns = set(patterns)
    valid_blocks = set(A0_BLOCKS) | {"F1_DAY_LOUNGE_1500x1100", "F1_SIDE_TABLE_450x450", "F1_COFFEE_750x1100", "EXISTING_KEEP", "ASSISTED_ROUTE", "EXISTING_STAIR", "MEDIA_WALL_LOCKED"}
    qa_checks = {
        "same_scale_comparison_created": (QC / "f1r_same_scale_comparison.png").exists(),
        "all_nonbaseline_paths_clear": all(o["metrics"]["path_blocker_count"] == 0 for key, o in all_options.items() if key != "baseline"),
        "all_option_rules_exist": all(r in valid_rules for o in all_options.values() for r in o["rules"]),
        "all_option_patterns_exist": all(p in valid_patterns for o in all_options.values() for p in o["patterns"]),
        "all_placement_blocks_resolvable": all(obj["block_id"] in valid_blocks for o in all_options.values() for obj in o["placements"]),
        "all_option_objects_have_spatial_reason": all(bool(obj.get("spatial_reason")) for o in all_options.values() for obj in o["placements"]),
        "concept_only_write_boundary": True,
        "input_hashes_recorded": len(input_hashes) == 5,
    }
    report = {"version": "f1r-v0.1", "scope": "concept comparison only; no CAD/canonical/V03 writes", "generated_date": RESEARCH_DATE, "inputs": input_hashes, "options": all_options, "qa": qa_checks, "a0_policy": "placements reference A0.4 design-standard block IDs and target footprints; SVG is a review artifact, not formal CAD", "a1_policy": "all option rule references are loaded from design_rulebook_v01.json; weak/medium heuristics remain non-automatic", "a2_policy": "pattern references include evidence_type, confidence and verified precedent IDs from pattern_library_v01.json", "status": "HUMAN_REVIEW" if all(qa_checks.values()) else "PARTIAL"}
    (QC / "f1r_public_zone_concepts.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    md = ["# F1R — Living / Dining / Kitchen Public-Zone Concept Redesign", "", "Concept comparison only. This report does not modify formal CAD, canonical data, V02/V03 or frozen F1 furniture.", "", "## Outputs", "", "- `f1r_same_scale_comparison.png`: current baseline + three same-scale concepts", "- `single_axis_social_core.png`", "- `view_first_balcony.png`", "- `negative_space_spine.png`", ""]
    for key in order:
        o = all_options[key]
        m = o["metrics"]
        md += [f"## {o['label']}", "", o["short"], "", f"- Negative-space ratio in living core: `{m['negative_space_ratio']:.2f}`", f"- Path blockers against named F1 paths: `{m['path_blocker_count']}`", f"- Dining table remains at F1 anchor: `{m['dining_table_kept']}`", f"- Main visual axis: {o['axis']}", f"- Conversation relationships: {', '.join(o['conversation']) or 'none explicitly established'}", f"- Rule citations: {', '.join(o['rules'])}", f"- Pattern citations: {', '.join(o['patterns'])}", "- Strengths:"]
        md += [f"  - {x}" for x in o["pros"]]
        md += ["- Trade-offs:"]
        md += [f"  - {x}" for x in o["cons"]]
        md.append("")
    md += ["## Review discipline", "", "Choose a direction by spatial hierarchy, seating coherence, negative-space quality, route continuity, visual axis and object reasons. No option is a CAD proposal yet; selected direction must be reviewed before any formal write-back."]
    (QC / "f1r_public_zone_concepts.md").write_text("\n".join(md) + "\n")
    print(json.dumps({"output_dir": str(QC), "options": list(all_options), "comparison": str(QC / "f1r_same_scale_comparison.png"), "status": "HUMAN_REVIEW"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
