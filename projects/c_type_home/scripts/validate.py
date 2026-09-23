"""Automated validation for Task 01.

Produces qc/calibration.json, qc/dimension_chain_audit.json and
qc/geometry_audit.json, and prints a gate checklist.
"""
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import (  # noqa: E402
    PROJECT_ROOT, load_geometry, load_dimensions, all_objects)

QC = PROJECT_ROOT / "qc"


def calibration(dims):
    """Least-squares mm/px from chain tick anchors vs printed cumulatives."""
    def fit(xs_px, vals_mm):
        cum = [0.0]
        for v in vals_mm:
            cum.append(cum[-1] + (v or 0))
        pairs = [(p, c) for p, c in zip(xs_px, cum)]
        n = len(pairs)
        sx = sum(p * c for p, c in pairs)
        sxx = sum(p * p for p, _ in pairs)
        spx = sum(p for p, _ in pairs)
        scm = sum(c for _, c in pairs)
        m = (n * sx - spx * scm) / max(n * sxx - spx * spx, 1e-9)
        b = (scm - m * spx) / n
        res = [round(c - (m * p + b), 1) for p, c in pairs]
        return {"mm_per_px": round(m, 3), "offset_mm": round(b, 1),
                "residuals_mm": res,
                "max_abs_residual_mm": max(abs(r) for r in res)}

    out = {"source_image_size_px": [659, 1024], "fits": {}, "notes": []}
    top = next(c for c in dims["chains"] if c["id"] == "CHAIN-TOP-IN")
    bot = next(c for c in dims["chains"] if c["id"] == "CHAIN-BOTTOM-OUT")
    right = next(c for c in dims["chains"] if c["id"] == "CHAIN-RIGHT-IN")
    # fit each chain against cumulative dims relative to its own first tick
    out["fits"]["horizontal_top_inner"] = fit(
        [t - top["tick_px_x"][0] for t in top["tick_px_x"][:-1]],
        top["segment_values_mm"])
    out["fits"]["horizontal_bottom_outer"] = fit(
        [t - bot["tick_px_x"][0] for t in bot["tick_px_x"]],
        bot["segment_values_mm"])
    out["fits"]["vertical_right_inner"] = fit(
        [t - right["tick_px_y"][0] for t in right["tick_px_y"]],
        right["segment_values_mm"])
    sx = out["fits"]["horizontal_bottom_outer"]["mm_per_px"]
    sy = out["fits"]["vertical_right_inner"]["mm_per_px"]
    out["chosen_transform"] = {
        "X_mm": "(px-86.5)*37.045", "Y_mm": "(684.5-py)*36.49",
        "mm_per_px_x": 37.045, "mm_per_px_y": 36.49}
    out["anisotropy_pct"] = round(abs(sx - sy) / sy * 100, 2)
    out["notes"].append(
        f"sx={sx} vs sy={sy}: {out['anisotropy_pct']}% — consistent with "
        "JPEG/raster reading tolerance; independent X/Y calibration applied.")
    return out


def chain_audit(dims):
    audit = {"chains": {}, "source_conflicts": []}
    top_out = next(c for c in dims["chains"] if c["id"] == "CHAIN-TOP-OUT")
    top_in = next(c for c in dims["chains"] if c["id"] == "CHAIN-TOP-IN")
    tin = top_in["segment_values_mm"]
    groups = [sum(tin[0:3]), sum(tin[3:5]), sum(tin[5:8]), sum(tin[8:11])]
    audit["chains"]["TOP"] = {
        "outer": top_out["segment_values_mm"],
        "inner_group_sums": groups,
        "closes": groups == top_out["segment_values_mm"],
        "note": "trailing inner segment 100mm beyond outer end = wall edge sliver"}
    bot_out = next(c for c in dims["chains"] if c["id"] == "CHAIN-BOTTOM-OUT")
    audit["chains"]["BOTTOM"] = {
        "outer": bot_out["segment_values_mm"],
        "outer_total": sum(bot_out["segment_values_mm"]),
        "matches_top_total": sum(bot_out["segment_values_mm"]) == 16300,
        "inner_tail_status": "UNKNOWN — last two segments unreadable (ISSUE-002)"}
    rin = next(c for c in dims["chains"] if c["id"] == "CHAIN-RIGHT-IN")
    mid = sum(rin["segment_values_mm"][2:9])
    audit["chains"]["RIGHT"] = {
        "inner_segments": rin["segment_values_mm"],
        "mid_section_sum": mid,
        "outer_total": 12900,
        "closes": mid == 12900,
        "note": "leading 1000+700 and trailing 700 are jog offsets outside the 12900 envelope"}
    audit["source_conflicts"] = [
        {"id": "CONF-1", "desc": "bottom outer chain ends at px526.5 (X16300) while drawn east outer face is px528.5 (X16470); dim wins, difference treated as wall-thickness overshoot"},
        {"id": "CONF-2", "desc": "right chain 12900 north datum px331 has no wall face — lands on AC-bay top edge (ISSUE-006)"},
    ]
    return audit


def geometry_audit(geo):
    issues = []
    ids = [o["id"] for _, o in all_objects(geo)]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        issues.append(f"duplicate ids: {sorted(dup)}")

    walls = {w["id"]: w for w in geo["walls"]}
    orphan = [o["id"] for k in ("doors", "windows") for o in geo[k]
              if o.get("host_wall_id") not in walls]
    if orphan:
        issues.append(f"orphan openings: {orphan}")

    low = [o["id"] for _, o in all_objects(geo)
           if o.get("confidence") in ("LOW", "UNKNOWN")]
    bearing = [o["id"] for _, o in all_objects(geo)
               if o.get("structural_role") not in (None, "UNKNOWN")]
    if bearing:
        issues.append(f"structural claims without source: {bearing}")

    for w in geo["walls"]:
        x1, y1, x2, y2 = w["rect_mm"]
        if x2 <= x1 or y2 <= y1:
            issues.append(f"degenerate wall rect {w['id']}")

    audit = {
        "object_counts": {k: len(geo.get(k, [])) for k in
                          ("walls", "columns", "doors", "windows",
                           "spaces", "ac_bays")},
        "duplicate_ids": sorted(dup),
        "orphan_openings": orphan,
        "low_confidence_objects": low,
        "structural_claims": bearing,
        "issues": issues,
        "pass": not issues,
    }
    return audit


def main():
    geo = load_geometry()
    dims = load_dimensions()
    QC.mkdir(parents=True, exist_ok=True)
    (QC / "calibration.json").write_text(
        json.dumps(calibration(dims), ensure_ascii=False, indent=2),
        encoding="utf-8")
    (QC / "dimension_chain_audit.json").write_text(
        json.dumps(chain_audit(dims), ensure_ascii=False, indent=2),
        encoding="utf-8")
    audit = geometry_audit(geo)
    (QC / "geometry_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"geometry_audit_pass": audit["pass"],
                      "issues": audit["issues"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
