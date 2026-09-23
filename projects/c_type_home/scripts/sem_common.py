"""Shared helpers for Task 02 — space semantics & graph building.

Reads ONLY the frozen Task 01 contract (data/geometry.json). Task 02 adds
semantics; it never mutates geometry truth.
"""
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon, box

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import (  # noqa: E402
    PROJECT_ROOT, load_geometry, opening_world_rect, wall_axis)

SEMANTICS_DIR = PROJECT_ROOT / "semantics"
EXTERNAL_NODE = "EXTERNAL_COMMON_AREA"
# Interior zone bounded by walls but with no source label / no modeled
# polygon (corridor strip east of cloakroom). A graph node, NOT a space.
UNMODELED_ZONE = "UNMODELED_INTERIOR_ZONE"

# gap tolerance: space polygons stop ~50-300mm short of wall faces
TOL = 400.0
# probe distance beyond the host wall band into each side space
PROBE = 450.0

WET_CLASS_BY_LABEL = {
    "厨房": ("SERVICE", "source label 厨房 — cooking/wet service zone"),
    "主卫": ("WET", "source label 主卫 — bathroom"),
    "公卫": ("WET", "source label 公卫 — bathroom"),
    "生活阳台": ("SEMI_WET", "source label 生活阳台 — open balcony; "
                             "laundry/service use typical but unconfirmed"),
    "阳台": ("SEMI_WET", "source label 阳台 — open balcony"),
}
CANONICAL_ROLE = {
    "客厅": "living_room", "餐厅": "dining_room", "休闲厅": "family_hall",
    "厨房": "kitchen", "生活阳台": "service_balcony", "阳台": "balcony",
    "公卫": "bathroom", "主卫": "bathroom", "书房": "study",
    "卧室": "bedroom", "主卧": "master_bedroom", "衣帽间": "walk_in_closet",
}
WALL_LOCATION_CLASS = {
    "exterior": "EXTERIOR_ENVELOPE",
    "interior": "INTERIOR_PARTITION",
    "railing_parapet": "BALCONY_BOUNDARY",
    "shaft": "SERVICE_BOUNDARY",
}


def space_polys(geo):
    return {s["id"]: Polygon(s["polygon_mm"]) for s in geo["spaces"]}


def wall_box(wall):
    x1, y1, x2, y2 = wall["rect_mm"]
    return box(x1, y1, x2, y2)


def _crosses_wall(pt, poly, wboxes, host_id):
    """True if the segment pt -> nearest point on poly passes through a
    wall box other than the host wall (i.e. the space is on the far side
    of another wall and cannot be this opening's side space)."""
    from shapely.geometry import LineString
    near = poly.exterior.interpolate(
        poly.exterior.project(pt))
    seg = LineString([pt, near])
    for wid, b in wboxes:
        if wid == host_id:
            continue
        inter = seg.intersection(b)
        if not inter.is_empty and inter.length > 30:
            return True
    return False


def resolve_side_space(pt, polys, wboxes, host_id, tol=200.0):
    """Which modeled space is on this side of the opening.

    Strict containment wins; otherwise the nearest polygon within tol is
    accepted only if no other wall lies between the probe and it.
    Returns space_id or None."""
    for sid, poly in polys.items():
        if poly.covers(pt):
            return sid
    best, bd = None, tol
    for sid, poly in polys.items():
        d = poly.distance(pt)
        if d <= bd and not _crosses_wall(pt, poly, wboxes, host_id):
            best, bd = sid, d
    return best


def opening_side_spaces(op, host, polys, wboxes, n_samples=5):
    """Probe spaces on each side of an opening. Returns (a_hits, b_hits)
    as lists of space ids; empty list means no modeled space that side."""
    ox1, oy1, ox2, oy2 = opening_world_rect(op, host)
    a_hits, b_hits = [], []
    for i in range(n_samples):
        t = (i + 0.5) / n_samples
        if wall_axis(host) == "H":
            x = ox1 + (ox2 - ox1) * t
            pa = Point(x, oy1 - PROBE)   # plan-south side
            pb = Point(x, oy2 + PROBE)   # plan-north side
        else:
            y = oy1 + (oy2 - oy1) * t
            pa = Point(ox1 - PROBE, y)   # plan-west side
            pb = Point(ox2 + PROBE, y)   # plan-east side
        for pt, hits in ((pa, a_hits), (pb, b_hits)):
            # a probe landing inside another wall is an ambiguous sample
            if any(b.covers(pt) for wid, b in wboxes if wid != host["id"]):
                continue
            sid = resolve_side_space(pt, polys, wboxes, host["id"])
            if sid and sid not in hits:
                hits.append(sid)
    return a_hits, b_hits


def plan_orientation_of_wall(wall):
    """Image-relative outward direction for envelope walls, else None."""
    x1, y1, x2, y2 = wall["rect_mm"]
    if wall_axis(wall) == "V":
        return "PLAN_WEST" if (x1 + x2) / 2 < 9600 else "PLAN_EAST"
    return "PLAN_SOUTH" if (y1 + y2) / 2 < 6600 else "PLAN_NORTH"


def envelope_wall_ids(geo):
    return {w["id"] for w in geo["walls"]
            if w["type"] in ("exterior", "railing_parapet")}


def save(name, obj):
    SEMANTICS_DIR.mkdir(parents=True, exist_ok=True)
    import json
    p = SEMANTICS_DIR / name
    p.write_text(__import__("json").dumps(obj, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    print("wrote", p)
