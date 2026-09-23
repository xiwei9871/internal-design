"""Automated validation for Task 01 (RC1).

Outputs:
  qc/calibration.json
  qc/dimension_chain_audit.json
  qc/geometry_audit.json          — Shapely-based validity/duplicate/overlap
  qc/dimension_model_measurements.json — model-measured distances vs source dims
"""
import json
import sys
from pathlib import Path

from shapely.geometry import Polygon, box
from shapely.validation import explain_validity

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import (  # noqa: E402
    PROJECT_ROOT, load_geometry, load_dimensions, all_objects)

QC = PROJECT_ROOT / "qc"
DIMMAP = PROJECT_ROOT / "data" / "dimension_map.json"


# ---------------------------------------------------------------- calibration
def calibration(dims):
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

    out = {"source_image_size_px": [1279, 1986], "fits": {}, "notes": []}
    top = next(c for c in dims["chains"] if c["id"] == "CHAIN-TOP-IN")
    bot = next(c for c in dims["chains"] if c["id"] == "CHAIN-BOTTOM-OUT")
    right = next(c for c in dims["chains"] if c["id"] == "CHAIN-RIGHT-IN")
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
        "X_mm": "(px-168.5)*19.131", "Y_mm": "(1328-py)*18.832",
        "mm_per_px_x": 19.131, "mm_per_px_y": 18.832}
    out["anisotropy_pct"] = round(abs(sx - sy) / sy * 100, 2)
    out["notes"].append(
        f"sx={sx} vs sy={sy}: {out['anisotropy_pct']}% anisotropy — "
        "independent X/Y calibration applied.")
    return out


# ------------------------------------------------------------- chain closure
def chain_audit(dims):
    audit = {"chains": {}, "source_conflicts": []}
    top_out = next(c for c in dims["chains"] if c["id"] == "CHAIN-TOP-OUT")
    top_in = next(c for c in dims["chains"] if c["id"] == "CHAIN-TOP-IN")
    tin = top_in["segment_values_mm"]
    groups = [sum(tin[0:3]), sum(tin[3:5]), sum(tin[5:8]), sum(tin[8:11])]
    audit["chains"]["TOP"] = {
        "outer": top_out["segment_values_mm"],
        "inner_group_sums": groups,
        "closes": groups == top_out["segment_values_mm"]}
    bot_out = next(c for c in dims["chains"] if c["id"] == "CHAIN-BOTTOM-OUT")
    audit["chains"]["BOTTOM"] = {
        "outer_total": sum(bot_out["segment_values_mm"]),
        "matches_top_total": sum(bot_out["segment_values_mm"]) == 16300,
        "inner_tail_status": "UNKNOWN — tail digits illegible on the "
                             "owner-accepted source (ISSUE-002)"}
    rin = next(c for c in dims["chains"] if c["id"] == "CHAIN-RIGHT-IN")
    audit["chains"]["RIGHT"] = {
        "mid_section_sum": sum(rin["segment_values_mm"][2:9]),
        "outer_total": 12900,
        "closes": sum(rin["segment_values_mm"][2:9]) == 12900}
    audit["source_conflicts"] = [
        {"id": "CONF-1", "desc": "bottom outer chain ends at px526.5 (X16300) while drawn east outer face is px528.5 (X16470); dim wins"},
        {"id": "CONF-2", "desc": "right chain 12900 north datum px331 has no wall face — lands on AC-bay top edge (ISSUE-006)"},
    ]
    return audit


# ------------------------------------------------------ model measurements
def resolve_ref(ref, geo, walls, bays, openings):
    kind = ref["kind"]
    if kind == "origin":
        return 0.0
    if kind == "anchor":
        return float(ref["value"])
    if kind == "face":
        obj = walls.get(ref["object"]) or bays.get(ref["object"])
        if obj is None:
            raise KeyError(f"unknown face object {ref['object']}")
        x1, y1, x2, y2 = obj["rect_mm"]
        return {"x_min": x1, "x_max": x2, "y_min": y1, "y_max": y2,
                "x_center": (x1 + x2) / 2, "y_center": (y1 + y2) / 2
                }[ref["face"]]
    if kind == "opening_edge":
        op = openings.get(ref["object"])
        if op is None:
            raise KeyError(f"unknown opening {ref['object']}")
        return float(op["opening_along_mm"][0 if ref["edge"] == "a" else 1])
    raise ValueError(kind)


def model_measurements(geo):
    dimmap = json.loads(DIMMAP.read_text(encoding="utf-8"))
    walls = {w["id"]: w for w in geo["walls"]}
    bays = {b["id"]: b for b in geo["ac_bays"]}
    openings = {o["id"]: o for k in ("doors", "windows") for o in geo[k]}

    records = []
    for m in dimmap["measurements"]:
        a = resolve_ref(m["from"], geo, walls, bays, openings)
        b = resolve_ref(m["to"], geo, walls, bays, openings)
        measured = abs(b - a)
        err = round(measured - m["value_mm"], 2)
        records.append({
            "dim_id": m["dim_id"], "source_value_mm": m["value_mm"],
            "confidence": m["confidence"],
            "geometry_refs": [m["from"], m["to"]],
            "measured_mm": measured, "error_mm": err,
            "result": "PASS" if abs(err) <= 1.0 or m["confidence"] != "HIGH"
                      else "FAIL",
            "note": m.get("note", "")})

    high = [r for r in records if r["confidence"] == "HIGH"]
    chains = {}
    for r in records:
        cid = r["dim_id"].split("#")[0]
        chains.setdefault(cid, []).append(r)
    chain_acc = {cid: round(sum(r["error_mm"] for r in rs), 2)
                 for cid, rs in chains.items()}
    gate = {
        "per_segment": all(r["result"] == "PASS" for r in high),
        "chain_accumulated_ok": all(
            abs(sum(r["error_mm"] for r in rs if r["confidence"] == "HIGH")) <= 2.0
            for rs in chains.values()),
        "n_high_segments": len(high),
        "n_failed_high": sum(1 for r in high if r["result"] == "FAIL"),
    }
    return {"gate_T01_3": gate, "chain_accumulated_error_mm": chain_acc,
            "records": records}


# -------------------------------------------------------- geometry audit
def polygon_of(obj):
    if "rect_mm" in obj:
        return box(*obj["rect_mm"])
    return Polygon(obj["polygon_mm"])


def geometry_audit(geo):
    problems = []
    infos = []
    ids = [o["id"] for _, o in all_objects(geo)]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        problems.append({"kind": "duplicate_ids", "ids": dup})

    polys = {}
    for kind, o in all_objects(geo):
        if "rect_mm" not in o and "polygon_mm" not in o:
            continue
        p = polygon_of(o)
        entry = {"valid": p.is_valid, "area_mm2": round(p.area, 1)}
        if not p.is_valid:
            entry["reason"] = explain_validity(p)
            problems.append({"kind": "invalid_polygon", "id": o["id"],
                             "reason": entry["reason"]})
        if p.area <= 0:
            problems.append({"kind": "non_positive_area", "id": o["id"]})
        polys[o["id"]] = p

    # duplicate geometry detection (identical polygons)
    seen = {}
    for oid, p in polys.items():
        key = p.wkb
        if key in seen:
            problems.append({"kind": "duplicate_geometry",
                             "ids": [seen[key], oid]})
        else:
            seen[key] = oid

    # unintended wall overlap detection: perpendicular junction overlaps are
    # expected (rect-based wall modelling); flag same-axis overlap or large
    # intersection area (>0.05 m²) between distinct walls.
    wall_items = [(w["id"], polys[w["id"]]) for w in geo["walls"]
                  if w["id"] in polys]
    overlaps = []
    for i, (ia, pa) in enumerate(wall_items):
        for ib, pb in wall_items[i + 1:]:
            inter = pa.intersection(pb)
            if inter.is_empty or inter.area == 0:
                continue
            wa = geo_wall_axis(geo, ia)
            wb = geo_wall_axis(geo, ib)
            flag = (wa == wb) or inter.area > 50_000
            rec = {"pair": [ia, ib], "overlap_area_mm2": round(inter.area, 0),
                   "same_axis": wa == wb, "suspect": flag}
            (problems if flag else infos).append(
                {"kind": "wall_overlap", **rec})
            overlaps.append(rec)

    walls = {w["id"]: w for w in geo["walls"]}
    orphan = [o["id"] for k in ("doors", "windows") for o in geo[k]
              if o.get("host_wall_id") not in walls]
    if orphan:
        problems.append({"kind": "orphan_openings", "ids": orphan})

    bearing = [o["id"] for _, o in all_objects(geo)
               if o.get("structural_role") not in (None, "UNKNOWN")]
    if bearing:
        problems.append({"kind": "unsupported_structural_claim",
                         "ids": bearing})

    low = [o["id"] for _, o in all_objects(geo)
           if o.get("confidence") in ("LOW", "UNKNOWN")]

    return {
        "library": "shapely",
        "object_counts": {k: len(geo.get(k, [])) for k in
                          ("walls", "columns", "doors", "windows",
                           "spaces", "ac_bays")},
        "polygons_checked": len(polys),
        "duplicate_ids": dup,
        "orphan_openings": orphan,
        "wall_overlaps": overlaps,
        "junction_overlaps_ok": [i for i in infos
                                 if i["kind"] == "wall_overlap"],
        "low_confidence_objects": low,
        "structural_claims": bearing,
        "problems": problems,
        "pass": not problems,
    }


def geo_wall_axis(geo, wid):
    w = next(w for w in geo["walls"] if w["id"] == wid)
    x1, y1, x2, y2 = w["rect_mm"]
    return "H" if (x2 - x1) >= (y2 - y1) else "V"


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
    meas = model_measurements(geo)
    (QC / "dimension_model_measurements.json").write_text(
        json.dumps(meas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "geometry_audit_pass": audit["pass"],
        "problems": audit["problems"],
        "measurement_gate": meas["gate_T01_3"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
