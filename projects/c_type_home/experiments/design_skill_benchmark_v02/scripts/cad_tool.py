from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any

import ezdxf
from ezdxf import bbox
from ezdxf.addons import Importer
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

EXP = Path(__file__).resolve().parents[1]
PROJECT = EXP.parents[2]
AX, AY = 1298172.0, -296458.0
PUBLIC_VIEW = [2400, 1500, 8800, 13800]
A0_LIBRARY = PROJECT / "assets/cad_library/standard/compiled/residential_design_legends_v01.dxf"
CANONICAL_PATH = PROJECT / "current_existing/canonical_plan_v1.json"
WINDOW_PATH = PROJECT / "current_existing/window_register.json"
STRUCTURAL_LAYERS = {"S-S.WALL", "A-WALL-EXST-CORR", "F-DOOR", "A-GLAZ-EXST",
                     "A-OPEN-EXST", "S-COLUMN", "S-楼梯", "A-PARP-EXST", "F-SAN FIT"}
HIDDEN_RENDER_LAYERS = {"RC-GRILL", "A-ELEM-TAG", "A-TEXT", "F-TEXT",
                        "A-QC-ZONE", "A-WALL-DEMO", "A-SURVEY-HATCH", "A-NOTE"}
APPROVED_BLOCKS = {
    "SOFA_3S_2200x900_PLAN": [-1100, -900, 1100, 0],
    "SOFA_2S_1800x850_PLAN": [-900, -850, 900, 0],
    "LOUNGE_CHAIR_900x900_PLAN": [-450, -450, 450, 450],
    "DINING_TABLE_1500x600_PLAN": [-750, -300, 750, 300],
    "DINING_CHAIR_450x500_PLAN": [-225, -250, 225, 250],
}
# These are fixed architectural measurement anchors, not furniture placements.
ROUTE_ANCHORS = {
    "entry_to_living": ((3900, 5700), (4550, 8200), 900),
    "living_to_stair": ((4700, 8200), (7150, 7350), 900),
    "living_to_north_balcony": ((6900, 11100), (7800, 12100), 850),
    "dining_to_keep_kitchen": ((4500, 3300), (5600, 3300), 1000),
    "dining_to_living_transition": ((4400, 3800), (4400, 5200), 900),
}
KEEP_RECTS = {
    "kitchen": [5500, 0, 8200, 4700],
    "entry_shoe": [2900, 4600, 3400, 5600],
    "entry_bench": [2900, 6800, 3400, 7200],
    "balcony_cabinet": [1400, 64, 2000, 2564],
    "washer_dryer": [7900, 13064, 8600, 13764],
}

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

def append_event(log: Path, iteration: str, action: str, **data: Any) -> dict:
    event = {"timestamp": now(), "iteration": iteration, "action": action, "actor": "agent_session", **data}
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event

def read_events(log: Path) -> list[dict]:
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]

def validate_iteration_causality(events: list[dict]) -> dict:
    def first_time(iteration: str, actions: set[str]):
        vals = [x["timestamp"] for x in events if x.get("iteration") == iteration and x.get("action") in actions]
        return min(vals) if vals else None
    r01_feedback = first_time("r01", {"render", "geometry_report", "agent_review"})
    r02_action = first_time("r02", {"insert", "move", "rotate", "delete"})
    passed = bool(r01_feedback and r02_action and r02_action > r01_feedback)
    return {
        "pass": passed,
        "r01_feedback_first_timestamp": r01_feedback,
        "r02_edit_first_timestamp": r02_action,
        "reason": "r02 edits must occur after r01 render/geometry/review evidence",
    }

def task_bbox(entity) -> list[float]:
    ext = bbox.extents([entity])
    return [ext.extmin.x - AX, ext.extmin.y - AY, ext.extmax.x - AX, ext.extmax.y - AY]

def transformed_bbox(local: list[float], x: float, y: float, rotation: float) -> list[float]:
    pts = [(local[0], local[1]), (local[0], local[3]), (local[2], local[1]), (local[2], local[3])]
    a = math.radians(rotation % 360)
    vals = [(x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
    xs, ys = zip(*vals)
    return [min(xs), min(ys), max(xs), max(ys)]

def ensure_blocks(doc) -> None:
    missing = [name for name in APPROVED_BLOCKS if name not in doc.blocks]
    if not missing:
        return
    source = ezdxf.readfile(str(A0_LIBRARY))
    importer = Importer(source, doc)
    importer.import_blocks(missing)
    importer.finalize()
    if any(name not in doc.blocks for name in APPROVED_BLOCKS):
        raise RuntimeError(f"missing approved A0.4 blocks: {missing}")

def clear_agent_furniture(doc) -> None:
    for entity in list(doc.modelspace()):
        if entity.dxf.layer == "D0-FURNITURE":
            doc.modelspace().delete_entity(entity)

def init_dxf(base: Path, out: Path, log: Path, iteration: str) -> None:
    shutil.copy2(base, out)
    doc = ezdxf.readfile(str(out))
    ensure_blocks(doc)
    if "D0-FURNITURE" not in doc.layers:
        doc.layers.add("D0-FURNITURE", color=2)
    clear_agent_furniture(doc)
    doc.saveas(str(out))
    append_event(log, iteration, "init", dxf=str(out), source_sha256=sha(base))

def insert_block(path: Path, log: Path, iteration: str, block: str, x: float, y: float, rotation: float = 0) -> str:
    if block not in APPROVED_BLOCKS:
        raise ValueError(f"block not approved for D0.2: {block}")
    doc = ezdxf.readfile(str(path))
    ensure_blocks(doc)
    if "D0-FURNITURE" not in doc.layers:
        doc.layers.add("D0-FURNITURE", color=2)
    entity = doc.modelspace().add_blockref(block, (AX + float(x), AY + float(y), 0),
                                           dxfattribs={"layer": "D0-FURNITURE", "rotation": float(rotation)})
    doc.saveas(str(path))
    append_event(log, iteration, "insert", dxf=str(path), handle=entity.dxf.handle,
                 block=block, x=float(x), y=float(y), rotation=float(rotation))
    return entity.dxf.handle

def find_entity(doc, handle: str):
    entity = doc.entitydb.get(handle)
    if entity is None or entity.dxf.layer != "D0-FURNITURE":
        raise ValueError(f"D0 furniture handle not found: {handle}")
    return entity

def move_block(path: Path, log: Path, iteration: str, handle: str, dx: float, dy: float) -> None:
    doc = ezdxf.readfile(str(path))
    entity = find_entity(doc, handle)
    entity.dxf.insert = (entity.dxf.insert.x + float(dx), entity.dxf.insert.y + float(dy), entity.dxf.insert.z)
    doc.saveas(str(path))
    append_event(log, iteration, "move", dxf=str(path), handle=handle, dx=float(dx), dy=float(dy))

def rotate_block(path: Path, log: Path, iteration: str, handle: str, angle: float) -> None:
    doc = ezdxf.readfile(str(path))
    entity = find_entity(doc, handle)
    entity.dxf.rotation = float(entity.dxf.rotation) + float(angle)
    doc.saveas(str(path))
    append_event(log, iteration, "rotate", dxf=str(path), handle=handle, angle=float(angle))

def delete_block(path: Path, log: Path, iteration: str, handle: str) -> None:
    doc = ezdxf.readfile(str(path))
    entity = find_entity(doc, handle)
    doc.modelspace().delete_entity(entity)
    doc.saveas(str(path))
    append_event(log, iteration, "delete", dxf=str(path), handle=handle)

def draw_actual_blocks(ax, doc) -> None:
    for insert in doc.modelspace():
        if insert.dxf.layer != "D0-FURNITURE":
            continue
        block = doc.blocks.get(insert.dxf.name)
        if block is None:
            continue
        sx = float(insert.dxf.get("xscale", 1.0))
        sy = float(insert.dxf.get("yscale", 1.0))
        angle = math.radians(float(insert.dxf.get("rotation", 0.0)))
        ca, sa = math.cos(angle), math.sin(angle)
        ox, oy = insert.dxf.insert.x, insert.dxf.insert.y
        def xf(x, y):
            x, y = x * sx, y * sy
            return ox + x * ca - y * sa, oy + x * sa + y * ca
        for entity in block:
            if entity.dxftype() == "LINE":
                a = xf(entity.dxf.start.x, entity.dxf.start.y)
                b = xf(entity.dxf.end.x, entity.dxf.end.y)
                ax.plot([a[0], b[0]], [a[1], b[1]], color="#b44d12", linewidth=0.85, zorder=55)
            elif entity.dxftype() == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in entity.get_points("xy")]
                if entity.closed and pts:
                    pts.append(pts[0])
                if len(pts) > 1:
                    xy = [xf(x, y) for x, y in pts]
                    ax.plot([p[0] for p in xy], [p[1] for p in xy], color="#b44d12", linewidth=0.85, zorder=55)

def render_dxf(path: Path, png: Path, log: Path | None = None, iteration: str = "render") -> dict:
    doc = ezdxf.readfile(str(path))
    def keep(entity):
        return entity.dxf.layer not in HIDDEN_RENDER_LAYERS and entity.dxftype() not in {"TEXT", "MTEXT", "DIMENSION", "HATCH"}
    fig = plt.figure(figsize=(8.2, 10.2), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    backend = MatplotlibBackend(ax, adjust_figure=False)
    Frontend(RenderContext(doc), backend).draw_layout(doc.modelspace(), filter_func=keep, finalize=True)
    draw_actual_blocks(ax, doc)
    ax.set_xlim(AX + PUBLIC_VIEW[0], AX + PUBLIC_VIEW[2])
    ax.set_ylim(AY + PUBLIC_VIEW[1], AY + PUBLIC_VIEW[3])
    ax.set_aspect("equal")
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=150, facecolor="white")
    plt.close(fig)
    result = {"source_dxf": str(path), "source_dxf_sha256": sha(path), "png": str(png), "png_sha256": sha(png), "view_task01": PUBLIC_VIEW}
    if log:
        append_event(log, iteration, "render", dxf=str(path), png=str(png), source_dxf_sha256=result["source_dxf_sha256"])
    return result

def canonical_obstacles() -> Any:
    canonical = json.loads(CANONICAL_PATH.read_text())
    cuts = [x.get("rect_mm") or x.get("opening_rect_mm") for x in canonical.get("openings", []) + canonical.get("windows", [])]
    cuts = [x for x in cuts if x]
    result = []
    for wall in canonical.get("walls", []):
        if wall.get("disposition") != "EXISTING":
            continue
        geom = box(*wall["rect_mm"])
        for cut in cuts:
            geom = geom.difference(box(*cut))
        if not geom.is_empty:
            result.append(geom)
    return result

def obstacle_union(doc):
    parts = canonical_obstacles() + [box(*r) for r in KEEP_RECTS.values()]
    for entity in doc.modelspace():
        if entity.dxf.layer in {"A-ACCESS-RAMP", "A-ACCESS-STAIR"}:
            try:
                parts.append(box(*task_bbox(entity)))
            except Exception:
                pass
    return unary_union(parts)

def route_widths(doc) -> dict:
    domain = box(*PUBLIC_VIEW)
    free = domain.difference(obstacle_union(doc))
    result = {}
    for name, (a, b, target) in ROUTE_ANCHORS.items():
        line = LineString([a, b])
        half = 1900.0
        widths = []
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = max(math.hypot(dx, dy), 1.0)
        nx, ny = -dy / length, dx / length
        for index in range(1, 31):
            point = line.interpolate(index / 31, normalized=True)
            cross = LineString([(point.x - nx * half, point.y - ny * half),
                                (point.x + nx * half, point.y + ny * half)])
            hit = free.intersection(cross)
            segments = [hit] if hit.geom_type == "LineString" else [x for x in getattr(hit, "geoms", []) if x.geom_type == "LineString"]
            nearby = [x for x in segments if x.distance(point) < 2]
            widths.append(max((x.length for x in (nearby or segments)), default=0.0))
        result[name] = {"actual_measured_min_mm": round(min(widths) if widths else 0.0, 1),
                        "reference_target_mm": target, "route_points_task01": [a, b],
                        "measurement_method": "saved-DXF furniture plus canonical wall/opening geometry cross-sections"}
    return result

def measure_dxf(path: Path, out: Path, log: Path | None = None, iteration: str = "measure") -> dict:
    doc = ezdxf.readfile(str(path))
    furniture = []
    for entity in doc.modelspace():
        if entity.dxf.layer != "D0-FURNITURE":
            continue
        local = APPROVED_BLOCKS.get(entity.dxf.name)
        if local is None:
            continue
        actual = task_bbox(entity)
        expected = transformed_bbox(local, entity.dxf.insert.x - AX, entity.dxf.insert.y - AY, entity.dxf.rotation)
        furniture.append({"handle": entity.dxf.handle, "block": entity.dxf.name,
                          "actual_bbox_task01": actual, "expected_bbox_task01": expected,
                          "bbox_delta_mm": max(abs(actual[i] - expected[i]) for i in range(4)),
                          "rotation": entity.dxf.rotation})
    overlaps = []
    for i, one in enumerate(furniture):
        for two in furniture[i + 1:]:
            area = box(*one["actual_bbox_task01"]).intersection(box(*two["actual_bbox_task01"])).area
            if area > 1:
                overlaps.append({"a": one["handle"], "b": two["handle"], "area_mm2": round(area, 1)})
    result = {
        "source_dxf": str(path),
        "source_dxf_sha256": sha(path),
        "furniture_count": len(furniture),
        "furniture": furniture,
        "transformed_bbox_all_pass": all(x["bbox_delta_mm"] <= 1 for x in furniture),
        "furniture_overlap_count": len(overlaps),
        "furniture_overlaps": overlaps,
        "route_clearances": route_widths(doc),
        "measurement_anchors": "ROUTE_ANCHORS are immutable architectural measurement anchors; no arm furniture coordinates are stored in this tool",
    }
    dump(out, result)
    if log:
        append_event(log, iteration, "geometry_report", dxf=str(path), geometry=str(out), source_dxf_sha256=result["source_dxf_sha256"])
    return result

def record_review(log: Path, iteration: str, review_file: Path) -> None:
    if not review_file.exists():
        raise FileNotFoundError(review_file)
    append_event(log, iteration, "agent_review", review_file=str(review_file), review_sha256=sha(review_file))

def cli() -> None:
    parser = argparse.ArgumentParser(description="D0.2 agent-driven CAD tool; no design layout constants.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init"); p.add_argument("--base", type=Path, required=True); p.add_argument("--out", type=Path, required=True); p.add_argument("--log", type=Path, required=True); p.add_argument("--iteration", default="r01")
    p = sub.add_parser("insert"); p.add_argument("--dxf", type=Path, required=True); p.add_argument("--log", type=Path, required=True); p.add_argument("--iteration", required=True); p.add_argument("--block", required=True); p.add_argument("--x", type=float, required=True); p.add_argument("--y", type=float, required=True); p.add_argument("--rotation", type=float, default=0)
    p = sub.add_parser("move"); p.add_argument("--dxf", type=Path, required=True); p.add_argument("--log", type=Path, required=True); p.add_argument("--iteration", required=True); p.add_argument("--handle", required=True); p.add_argument("--dx", type=float, required=True); p.add_argument("--dy", type=float, required=True)
    p = sub.add_parser("rotate"); p.add_argument("--dxf", type=Path, required=True); p.add_argument("--log", type=Path, required=True); p.add_argument("--iteration", required=True); p.add_argument("--handle", required=True); p.add_argument("--angle", type=float, required=True)
    p = sub.add_parser("delete"); p.add_argument("--dxf", type=Path, required=True); p.add_argument("--log", type=Path, required=True); p.add_argument("--iteration", required=True); p.add_argument("--handle", required=True)
    p = sub.add_parser("render"); p.add_argument("--dxf", type=Path, required=True); p.add_argument("--png", type=Path, required=True); p.add_argument("--log", type=Path); p.add_argument("--iteration", default="r01")
    p = sub.add_parser("measure"); p.add_argument("--dxf", type=Path, required=True); p.add_argument("--out", type=Path, required=True); p.add_argument("--log", type=Path); p.add_argument("--iteration", default="r01")
    p = sub.add_parser("review"); p.add_argument("--log", type=Path, required=True); p.add_argument("--iteration", required=True); p.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "init": init_dxf(args.base, args.out, args.log, args.iteration)
    elif args.command == "insert": print(insert_block(args.dxf, args.log, args.iteration, args.block, args.x, args.y, args.rotation))
    elif args.command == "move": move_block(args.dxf, args.log, args.iteration, args.handle, args.dx, args.dy)
    elif args.command == "rotate": rotate_block(args.dxf, args.log, args.iteration, args.handle, args.angle)
    elif args.command == "delete": delete_block(args.dxf, args.log, args.iteration, args.handle)
    elif args.command == "render": print(json.dumps(render_dxf(args.dxf, args.png, args.log, args.iteration), ensure_ascii=False))
    elif args.command == "measure": print(json.dumps(measure_dxf(args.dxf, args.out, args.log, args.iteration), ensure_ascii=False))
    elif args.command == "review": record_review(args.log, args.iteration, args.file)

if __name__ == "__main__":
    cli()

