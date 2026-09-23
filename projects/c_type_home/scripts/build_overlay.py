"""Project geometry.json back onto the source raster for overlay QC.

Outputs qc/overlay_full.png, overlay_walls.png, overlay_openings.png and
qc/overlay_metrics.json. Automated metrics are auxiliary only — the overlay
gate requires human visual inspection (see TASK01_REPORT.md).
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
    opening_world_rect,
)

QC = PROJECT_ROOT / "qc"
COL = {"HIGH": (0, 220, 0), "MEDIUM": (255, 170, 0), "LOW": (255, 40, 40)}


def rect_to_px(rect):
    x1, y1, x2, y2 = rect
    p1 = mm_to_px(x1, y1)
    p2 = mm_to_px(x2, y2)
    return (min(p1[0], p2[0]), min(p1[1], p2[1]),
            max(p1[0], p2[0]), max(p1[1], p2[1]))


def base_image():
    return Image.open(SOURCE_IMG).convert("RGBA")


def draw_poly(draw, poly_px, color, width=2):
    draw.line(list(poly_px) + [poly_px[0]], fill=color, width=width)


def overlay(which):
    geo = load_geometry()
    img = base_image()
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


def edge_residuals_px(geo, max_d=8):
    """For MEDIUM/HIGH walls, sample edge midpoints and measure distance to
    the nearest dark source pixel (plan linework) — a raster-fit proxy."""
    gray = np.array(Image.open(SOURCE_IMG).convert("L"))
    dark = gray < 160
    h, w = dark.shape
    ys, xs = np.nonzero(dark)
    res = []
    for wall in geo["walls"]:
        if wall.get("confidence") not in ("HIGH", "MEDIUM"):
            continue
        px_rect = rect_to_px(wall["rect_mm"])
        edges = [
            ((px_rect[0] + px_rect[2]) / 2, px_rect[1]),
            ((px_rect[0] + px_rect[2]) / 2, px_rect[3]),
            (px_rect[0], (px_rect[1] + px_rect[3]) / 2),
            (px_rect[2], (px_rect[1] + px_rect[3]) / 2),
        ]
        ds = []
        for ex, ey in edges:
            x0, x1 = max(0, int(ex - max_d)), min(w, int(ex + max_d) + 1)
            y0, y1 = max(0, int(ey - max_d)), min(h, int(ey + max_d) + 1)
            sel = ((xs >= x0) & (xs <= x1) & (ys >= y0) & (ys <= y1))
            if not sel.any():
                ds.append(max_d)
                continue
            dd = np.hypot(xs[sel] - ex, ys[sel] - ey).min()
            ds.append(float(dd))
        res.append({"wall": wall["id"], "conf": wall["confidence"],
                    "edge_residual_px_mean": round(sum(ds) / len(ds), 2),
                    "edge_residual_px_max": round(max(ds), 2)})
    return res


def main():
    geo = load_geometry()
    QC.mkdir(parents=True, exist_ok=True)
    overlay("full").save(QC / "overlay_full.png")
    overlay("walls").save(QC / "overlay_walls.png")
    overlay("openings").save(QC / "overlay_openings.png")
    res = edge_residuals_px(geo)
    metrics = {
        "note": "auxiliary metric only — visual inspection is the gate",
        "n_walls_measured": len(res),
        "mean_edge_residual_px": round(
            sum(r["edge_residual_px_mean"] for r in res) / max(len(res), 1), 2),
        "mean_edge_residual_mm": round(
            sum(r["edge_residual_px_mean"] for r in res) / max(len(res), 1)
            * 37.045, 1),
        "per_wall": res,
    }
    (QC / "overlay_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print("overlays + metrics written to", QC)


if __name__ == "__main__":
    main()
