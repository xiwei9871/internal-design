"""Project geometry.json back onto the source raster for overlay QC.

Outputs qc/overlay_full.png, overlay_walls.png, overlay_openings.png and
qc/overlay_metrics.json.

Metrics (RC1): matched-source references only —
  * wall_edge_residuals: projected wall band vs the recorded source pixel
    band (px_evidence) of the SAME element — not nearest-dark-pixel.
  * opening_anchor_residuals: projected opening edges vs the recorded source
    pixel gap range of the SAME opening.
The old nearest-dark-pixel scan is kept as a secondary diagnostic only.
Neither metric replaces human visual inspection (hard gate).
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import (  # noqa: E402
    PROJECT_ROOT, SOURCE_IMG, load_geometry, mm_to_px, wall_polygon_mm,
    opening_world_rect, wall_axis, MM_PER_PX_X)

QC = PROJECT_ROOT / "qc"
COL = {"HIGH": (0, 220, 0), "MEDIUM": (255, 170, 0), "LOW": (255, 40, 40)}


def rect_to_px(rect):
    x1, y1, x2, y2 = rect
    p1 = mm_to_px(x1, y1)
    p2 = mm_to_px(x2, y2)
    return (min(p1[0], p2[0]), min(p1[1], p2[1]),
            max(p1[0], p2[0]), max(p1[1], p2[1]))


def draw_poly(draw, poly_px, color, width=2):
    draw.line(list(poly_px) + [poly_px[0]], fill=color, width=width)


def overlay(which):
    geo = load_geometry()
    img = Image.open(SOURCE_IMG).convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    wall_by_id = {w["id"]: w for w in geo["walls"]}

    if which in ("full", "walls"):
        for w in geo["walls"]:
            pts = [mm_to_px(x, y) for x, y in wall_polygon_mm(w)]
            draw_poly(d, pts, COL.get(w.get("confidence"), COL["LOW"]))
        for c in geo.get("columns", []):
            d.rectangle(rect_to_px(c["rect_mm"]),
                        outline=COL.get(c.get("confidence"), COL["LOW"]),
                        width=2)
    if which in ("full", "openings"):
        for kind, col in (("doors", (0, 120, 255)), ("windows", (0, 255, 255))):
            for op in geo.get(kind, []):
                host = wall_by_id.get(op.get("host_wall_id"))
                if host is None:
                    continue
                d.rectangle(rect_to_px(opening_world_rect(op, host)),
                            outline=col, width=2)
    if which == "full":
        for sp in geo.get("spaces", []):
            pts = [mm_to_px(x, y) for x, y in sp["polygon_mm"]]
            draw_poly(d, pts, (180, 0, 255, 200), width=1)
    return Image.alpha_composite(img, layer).convert("RGB")


def wall_edge_residuals(geo):
    """Projected wall band vs recorded source px band for the same wall."""
    res = []
    for w in geo["walls"]:
        ev = w.get("px_evidence")
        if not ev or ev.get("kind") != "band":
            continue
        pr = rect_to_px(w["rect_mm"])
        if ev["axis"] == "x":
            proj_lo, proj_hi = pr[0], pr[2]
        else:
            proj_lo, proj_hi = pr[1], pr[3]
        src_lo, src_hi = ev["range_px"]
        # disjoint gap between projected band and recorded source band (0 if overlapping)
        outside = max(0.0, proj_lo - src_hi, src_lo - proj_hi)
        # symmetric edge deltas
        d_lo = proj_lo - src_lo
        d_hi = proj_hi - src_hi
        res.append({
            "wall": w["id"], "conf": w.get("confidence"),
            "axis": ev["axis"],
            "src_band_px": [src_lo, src_hi],
            "proj_band_px": [round(proj_lo, 1), round(proj_hi, 1)],
            "edge_delta_px": [round(d_lo, 2), round(d_hi, 2)],
            "band_outside_px": round(outside, 2),
            "band_outside_mm": round(outside * MM_PER_PX_X, 1)})
    return res


def opening_anchor_residuals(geo):
    """Projected opening edges vs recorded source px gap of the same opening."""
    wall_by_id = {w["id"]: w for w in geo["walls"]}
    res = []
    for kind in ("doors", "windows"):
        for op in geo[kind]:
            ev = op.get("px_evidence")
            host = wall_by_id.get(op.get("host_wall_id"))
            if not ev or host is None:
                continue
            rect = opening_world_rect(op, host)
            pr = rect_to_px(rect)
            if ev["along_axis"] == "x":
                pa, pb = pr[0], pr[2]
            else:
                pa, pb = pr[1], pr[3]
            sa, sb = ev["range_px"]
            # source gap range along the wall axis; door gaps in raster are
            # often only in one wall face, so report absolute deltas
            res.append({
                "opening": op["id"], "kind": kind[:-1],
                "conf": op.get("confidence"),
                "src_gap_px": [sa, sb],
                "proj_span_px": [round(pa, 1), round(pb, 1)],
                "edge_delta_px": [round(pa - sa, 1), round(pb - sb, 1)],
                "span_src_px": round(sb - sa, 1),
                "span_proj_px": round(pb - pa, 1)})
    return res


def nearest_dark_diagnostic(geo, max_d=8):
    """LEGACY secondary diagnostic — nearest dark pixel distance can match
    text/dim lines/door arcs; NOT a gate metric."""
    gray = np.array(Image.open(SOURCE_IMG).convert("L"))
    dark = gray < 160
    h, w = dark.shape
    ys, xs = np.nonzero(dark)
    vals = []
    for wall in geo["walls"]:
        if wall.get("confidence") not in ("HIGH", "MEDIUM"):
            continue
        pr = rect_to_px(wall["rect_mm"])
        pts = [((pr[0] + pr[2]) / 2, pr[1]), ((pr[0] + pr[2]) / 2, pr[3]),
               (pr[0], (pr[1] + pr[3]) / 2), (pr[2], (pr[1] + pr[3]) / 2)]
        for ex, ey in pts:
            sel = ((xs >= ex - max_d) & (xs <= ex + max_d) &
                   (ys >= ey - max_d) & (ys <= ey + max_d))
            if sel.any():
                vals.append(float(np.hypot(xs[sel] - ex, ys[sel] - ey).min()))
    return round(sum(vals) / max(len(vals), 1), 2)


def main():
    geo = load_geometry()
    QC.mkdir(parents=True, exist_ok=True)
    overlay("full").save(QC / "overlay_full.png")
    overlay("walls").save(QC / "overlay_walls.png")
    overlay("openings").save(QC / "overlay_openings.png")

    wall_res = wall_edge_residuals(geo)
    op_res = opening_anchor_residuals(geo)
    metrics = {
        "note": "matched-source residuals are auxiliary; the overlay gate "
                "requires human visual inspection",
        "wall_edge_residuals": {
            "n": len(wall_res),
            "max_band_outside_px": max(
                (r["band_outside_px"] for r in wall_res), default=0),
            "mean_abs_edge_delta_px": round(
                sum(abs(d) for r in wall_res for d in r["edge_delta_px"])
                / max(2 * len(wall_res), 1), 2),
            "per_wall": wall_res},
        "opening_anchor_residuals": {
            "n": len(op_res),
            "per_opening": op_res},
        "secondary_diagnostic_nearest_dark_px":
            nearest_dark_diagnostic(geo),
    }
    (QC / "overlay_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print("overlays + metrics written to", QC)


if __name__ == "__main__":
    main()
