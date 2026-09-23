"""Task 02 — QC renders on top of the source plan.

Outputs:
  qc/task02_space_semantics.png  space ids / labels / modeled areas
  qc/task02_connectivity.png     circulation graph over the plan
  qc/task02_constraint_map.png   elements colored by evidence category
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Polygon

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import (  # noqa: E402
    PROJECT_ROOT, SOURCE_IMG, load_geometry, mm_to_px, opening_world_rect,
    wall_polygon_mm)
from sem_common import SEMANTICS_DIR  # noqa: E402

QC = PROJECT_ROOT / "qc"
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
font = ImageFont.truetype(FONT_PATH, 22)
font_sm = ImageFont.truetype(FONT_PATH, 17)
font_xs = ImageFont.truetype(FONT_PATH, 14)

SPACE_COLORS = {
    "DRY": (80, 140, 255), "WET": (0, 180, 200), "SERVICE": (255, 150, 40),
    "SEMI_WET": (140, 200, 80), "UNKNOWN": (160, 160, 160)}
CONSTRAINT_COLORS = {
    "dimension_constrained": (0, 190, 90),
    "pixel": (255, 170, 0),
    "conflict": (220, 40, 200),
    "verify": (255, 60, 60),
}


def base_layer():
    img = Image.open(SOURCE_IMG).convert("RGBA")
    return img, Image.new("RGBA", img.size, (0, 0, 0, 0))


def centroid_px(poly):
    c = poly.centroid
    return mm_to_px(c.x, c.y)


def render_spaces(geo, sem):
    img, layer = base_layer()
    d = ImageDraw.Draw(layer)
    smap = {s["space_id"]: s for s in sem["spaces"]}
    for s in geo["spaces"]:
        pts = [mm_to_px(x, y) for x, y in s["polygon_mm"]]
        info = smap[s["id"]]
        col = SPACE_COLORS.get(info["wet_service_class"], (150,) * 3)
        d.polygon(pts, fill=col + (60,), outline=col + (255,))
        cx, cy = centroid_px(Polygon(s["polygon_mm"]))
        txt = f"{s['id']}\n{s['name_zh']} {info['area_m2']}m2\n{info['wet_service_class']}"
        d.multiline_text((cx, cy), txt, fill=(0, 0, 60), font=font_sm,
                         anchor="mm", align="center")
    d.text((30, 30), "Task02 space semantics — fill=WET/SERVICE class",
           fill=(0, 0, 0), font=font)
    return Image.alpha_composite(img, layer).convert("RGB")


def render_connectivity(geo, graph, cells):
    img, layer = base_layer()
    d = ImageDraw.Draw(layer)
    polys = {s["id"]: Polygon(s["polygon_mm"]) for s in geo["spaces"]}
    for z in cells.get("zones", []):
        polys[z["zone_id"]] = Polygon(z["polygon_mm"])
    cent = {sid: centroid_px(p) for sid, p in polys.items()}
    cent["EXTERNAL_COMMON_AREA"] = mm_to_px(1500, 6000)
    wall_by_id = {w["id"]: w for w in geo["walls"]}

    for e in graph["circulation_edges"]:
        a, b = e["space_a"], e["space_b"]
        if a not in cent or b not in cent:
            continue
        col = (0, 160, 0) if e.get("opening_id") else (40, 100, 255)
        if e["opening_type"] == "OPEN_PASSAGE":
            d.line([cent[a], cent[b]], fill=col, width=6)
        else:
            d.line([cent[a], cent[b]], fill=col, width=3)
            # mark the actual opening position
            op = next((o for o in geo["doors"] + geo["windows"]
                       if o["id"] == e["opening_id"]), None)
            if op:
                r = opening_world_rect(op, wall_by_id[op["host_wall_id"]])
                mx, my = mm_to_px((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
                d.ellipse([mx - 7, my - 7, mx + 7, my + 7],
                          fill=(255, 120, 0))
                d.text((mx + 10, my - 10), e["opening_id"],
                       fill=(200, 60, 0), font=font_xs)
    # unresolved openings get a hollow gray marker — visible but not
    # presented as a resolved connection
    for oid in graph.get("unresolved_edges", []):
        op = next((o for o in geo["doors"] if o["id"] == oid), None)
        if op:
            r = opening_world_rect(op, wall_by_id[op["host_wall_id"]])
            mx, my = mm_to_px((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
            d.ellipse([mx - 9, my - 9, mx + 9, my + 9],
                      outline=(120, 120, 120), width=3)
            d.text((mx + 12, my - 10), f"{oid} (UNRESOLVED)",
                   fill=(90, 90, 90), font=font_xs)
    for sid, (cx, cy) in cent.items():
        r = 16 if sid == "EXTERNAL_COMMON_AREA" else 22
        col = (255, 60, 60) if sid == "EXTERNAL_COMMON_AREA" else \
            (160, 60, 200) if sid.startswith("ZONE-") else \
            (0, 90, 200)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (220,))
        d.text((cx, cy - r - 12), sid.replace("R-", ""),
               fill=(0, 0, 80), font=font_xs, anchor="mm")
    d.text((30, 30), "Task02 connectivity — green=door edge, "
                     "blue=open passage, orange dot=opening",
           fill=(0, 0, 0), font=font)
    return Image.alpha_composite(img, layer).convert("RGB")


def render_constraints(geo):
    """Color-code walls/openings by evidence category."""
    img, layer = base_layer()
    d = ImageDraw.Draw(layer)
    wall_by_id = {w["id"]: w for w in geo["walls"]}
    conflict_ids = {"W-EXT-E1", "WIN-E1", "W-EXT-W", "WIN-W1", "D-13",
                    "W-BALC-N", "W-EXT-NE", "W-EXT-NE2", "D-10"}

    def col_for(o):
        prov = o.get("provenance", "")
        if o["id"] in conflict_ids:
            return CONSTRAINT_COLORS["conflict"]
        if o.get("confidence") == "LOW" or o.get(
                "needs_field_verification"):
            if "dimension" in prov:
                return CONSTRAINT_COLORS["dimension_constrained"]
            return CONSTRAINT_COLORS["verify"]
        if "dimension" in prov:
            return CONSTRAINT_COLORS["dimension_constrained"]
        return CONSTRAINT_COLORS["pixel"]

    for w in geo["walls"]:
        pts = [mm_to_px(x, y) for x, y in wall_polygon_mm(w)]
        d.line(pts + [pts[0]], fill=col_for(w), width=4)
    for kind in ("doors", "windows"):
        for op in geo[kind]:
            host = wall_by_id.get(op["host_wall_id"])
            if not host:
                continue
            x1, y1, x2, y2 = opening_world_rect(op, host)
            p1, p2 = mm_to_px(x1, y1), mm_to_px(x2, y2)
            d.rectangle([min(p1[0], p2[0]), min(p1[1], p2[1]),
                         max(p1[0], p2[0]), max(p1[1], p2[1])],
                        outline=col_for(op), width=3)
    legend = [("dimension-constrained", CONSTRAINT_COLORS["dimension_constrained"]),
              ("pixel-derived", CONSTRAINT_COLORS["pixel"]),
              ("source-conflict", CONSTRAINT_COLORS["conflict"]),
              ("field-verification-required", CONSTRAINT_COLORS["verify"])]
    y = 30
    d.text((30, y), "Task02 constraint map", fill=(0, 0, 0), font=font)
    for i, (txt, col) in enumerate(legend):
        d.rectangle([30, y + 40 + i * 30, 55, y + 62 + i * 30], fill=col)
        d.text((65, y + 42 + i * 30), txt, fill=(0, 0, 0), font=font_sm)
    return Image.alpha_composite(img, layer).convert("RGB")


def main():
    geo = load_geometry()
    sem = json.loads((SEMANTICS_DIR / "space_semantics.json")
                     .read_text(encoding="utf-8"))
    graph = json.loads((SEMANTICS_DIR / "adjacency_graph.json")
                       .read_text(encoding="utf-8"))
    cells = json.loads((SEMANTICS_DIR / "space_cells.json")
                       .read_text(encoding="utf-8"))
    QC.mkdir(exist_ok=True)
    render_spaces(geo, sem).save(QC / "task02_space_semantics.png")
    render_connectivity(geo, graph, cells).save(
        QC / "task02_connectivity.png")
    render_constraints(geo).save(QC / "task02_constraint_map.png")
    print("QC renders written to", QC)


if __name__ == "__main__":
    main()
