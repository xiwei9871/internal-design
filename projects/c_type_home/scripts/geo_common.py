"""Shared loader/helpers for c_type_home Task 01 geometry contract.

All outputs (DXF / FreeCAD / IFC / overlay) must be generated from the
single source file data/geometry.json loaded through this module.
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data" / "geometry.json"
DIMENSIONS = PROJECT_ROOT / "data" / "dimensions.json"
SOURCE_IMG = PROJECT_ROOT / "source" / "source_plan_original.jpg"

MM_PER_PX_X = 37.045
MM_PER_PX_Y = 36.49
ORIGIN_PX = (86.5, 684.5)


def load_geometry():
    return json.loads(DATA.read_text(encoding="utf-8"))


def load_dimensions():
    return json.loads(DIMENSIONS.read_text(encoding="utf-8"))


def wall_polygon_mm(wall):
    x1, y1, x2, y2 = wall["rect_mm"]
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def wall_axis(wall):
    x1, y1, x2, y2 = wall["rect_mm"]
    return "H" if (x2 - x1) >= (y2 - y1) else "V"


def opening_world_rect(opening, wall):
    """Return the rectangle a door/window opening cuts out of its host wall."""
    x1, y1, x2, y2 = wall["rect_mm"]
    a, b = opening["opening_along_mm"]
    if wall_axis(wall) == "H":
        return (a, y1, b, y2)
    return (x1, a, x2, b)


def px_to_mm(px, py):
    return ((px - ORIGIN_PX[0]) * MM_PER_PX_X,
            (ORIGIN_PX[1] - py) * MM_PER_PX_Y)


def mm_to_px(x_mm, y_mm):
    return (ORIGIN_PX[0] + x_mm / MM_PER_PX_X,
            ORIGIN_PX[1] - y_mm / MM_PER_PX_Y)


def all_objects(geo):
    objs = []
    for key in ("walls", "columns", "doors", "windows", "spaces", "ac_bays"):
        for o in geo.get(key, []):
            objs.append((key, o))
    return objs
