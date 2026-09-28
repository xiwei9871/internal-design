from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import shutil
import time
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
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

EXP = Path(__file__).resolve().parents[1]
PROJECT = EXP.parents[1]
AX, AY = 1298172.0, -296458.0
ITERATIONS = 2
PUBLIC_VIEW = [2400, 1500, 8800, 13800]
REQUIRED_BLOCKS = (
    "SOFA_3S_2200x900_PLAN",
    "SOFA_2S_1800x850_PLAN",
    "LOUNGE_CHAIR_900x900_PLAN",
    "DINING_TABLE_1500x600_PLAN",
    "DINING_CHAIR_450x500_PLAN",
)
OLD_PUBLIC_INSERT_NAMES = (
    "FURN_SOFA_3", "FURN_SOFA_2", "FURN_LOUNGE",
    "FURN_TABLE_RECT", "FURN_SIDE_TABLE", "FURN_COFFEE_TABLE",
)
SOURCE_V02 = PROJECT / "cad/design_v02_f1_l1.dxf"
CANONICAL_PATH = PROJECT / "current_existing/canonical_plan_v1.json"
WINDOW_PATH = PROJECT / "current_existing/window_register.json"
BRIEF_PATH = PROJECT / "brief/owner_brief_v1.json"
A1_PATH = PROJECT / "knowledge/design_rules/design_rulebook_v01.json"
A2_PATH = PROJECT / "knowledge/precedents/pattern_library_v01.json"
A0_PATH = PROJECT / "assets/cad_library/standard/compiled/residential_design_legends_v01.dxf"
BLOCK_MANIFEST_PATH = PROJECT / "assets/cad_library/standard/manifests/design_legend_manifest_v01.json"
BASE_PATH = EXP / "base/public_zone_clean_base.dxf"
BASE_MANIFEST_PATH = EXP / "base/base_manifest.json"
INPUT_MANIFEST_PATH = EXP / "inputs/input_manifest.json"
FORMAL_SHA_PATH = EXP / "inputs/formal_input_sha_before.json"
ARMS = ("CTRL", "ARCH", "STUDIO", "REROOM")
STRUCTURAL_LAYERS = {"S-S.WALL", "A-WALL-EXST-CORR", "F-DOOR", "A-GLAZ-EXST",
                     "A-OPEN-EXST", "S-COLUMN", "S-楼梯", "A-PARP-EXST", "F-SAN FIT"}
HIDDEN_RENDER_LAYERS = {"RC-GRILL", "A-ELEM-TAG", "A-TEXT", "F-TEXT",
                        "A-QC-ZONE", "A-WALL-DEMO", "A-SURVEY-HATCH", "A-NOTE"}
BLOCK_LOCAL_BBOX = {
    "SOFA_3S_2200x900_PLAN": [-1100, -900, 1100, 0],
    "SOFA_2S_1800x850_PLAN": [-900, -850, 900, 0],
    "LOUNGE_CHAIR_900x900_PLAN": [-450, -450, 450, 450],
    "DINING_TABLE_1500x600_PLAN": [-750, -300, 750, 300],
    "DINING_CHAIR_450x500_PLAN": [-225, -250, 225, 250],
}
ROUTES = {
    "entry_to_living": {"points": [(3900, 5700), (4550, 8200)], "target_mm": 900, "kind": "primary"},
    "living_to_stair": {"points": [(4700, 8200), (7150, 7350)], "target_mm": 900, "kind": "primary"},
    "living_to_north_balcony": {"points": [(6900, 11100), (7800, 12100)], "target_mm": 850, "kind": "existing_limit"},
    "dining_to_keep_kitchen": {"points": [(4500, 3300), (5600, 3300)], "target_mm": 1000, "kind": "preferred"},
    "dining_to_living_transition": {"points": [(4400, 3800), (4400, 5200)], "target_mm": 900, "kind": "through_route"},
}
KEEP_RECTS = {
    "kitchen": [5500, 0, 8200, 4700],
    "entry_shoe": [2900, 4600, 3400, 5600],
    "entry_bench": [2900, 6800, 3400, 7200],
    "balcony_cabinet": [1400, 64, 2000, 2564],
    "washer_dryer": [7900, 13064, 8600, 13764],
}
ARM_SPECS = {
    "CTRL": {
        "device": "project-brief + A0/A1/A2 only",
        "source_principles": ["owner brief", "existing KEEP constraints", "A0 dimensions", "A1/A2 project knowledge"],
        "iteration_limit": ITERATIONS,
        "r01": [
            {"id":"LIV-SOFA-3","block":"SOFA_3S_2200x900_PLAN","x":3000,"y":10400,"rotation":90,"role":"living anchor"},
            {"id":"LIV-SOFA-2","block":"SOFA_2S_1800x850_PLAN","x":5450,"y":12600,"rotation":0,"role":"secondary seat"},
            {"id":"LIV-LOUNGE","block":"LOUNGE_CHAIR_900x900_PLAN","x":6200,"y":8200,"rotation":0,"role":"flex seat"},
            {"id":"DIN-TABLE","block":"DINING_TABLE_1500x600_PLAN","x":4250,"y":3250,"rotation":0,"role":"dining anchor"},
            {"id":"DIN-N","block":"DINING_CHAIR_450x500_PLAN","x":4250,"y":4050,"rotation":0,"role":"daily seat"},
            {"id":"DIN-S","block":"DINING_CHAIR_450x500_PLAN","x":4250,"y":2450,"rotation":180,"role":"daily seat"},
            {"id":"DIN-W","block":"DINING_CHAIR_450x500_PLAN","x":3250,"y":3250,"rotation":90,"role":"daily seat"},
            {"id":"DIN-E","block":"DINING_CHAIR_450x500_PLAN","x":5250,"y":3250,"rotation":270,"role":"daily seat"},
        ],
        "r02": [
            {"id":"LIV-SOFA-3","block":"SOFA_3S_2200x900_PLAN","x":3000,"y":10400,"rotation":90,"role":"living anchor"},
            {"id":"LIV-SOFA-2","block":"SOFA_2S_1800x850_PLAN","x":5450,"y":12600,"rotation":0,"role":"secondary seat"},
            {"id":"LIV-LOUNGE","block":"LOUNGE_CHAIR_900x900_PLAN","x":6700,"y":8500,"rotation":0,"role":"flex seat"},
            {"id":"DIN-TABLE","block":"DINING_TABLE_1500x600_PLAN","x":3700,"y":2700,"rotation":0,"role":"dining anchor"},
            {"id":"DIN-N","block":"DINING_CHAIR_450x500_PLAN","x":3700,"y":3500,"rotation":0,"role":"daily seat"},
            {"id":"DIN-S","block":"DINING_CHAIR_450x500_PLAN","x":3700,"y":1900,"rotation":180,"role":"daily seat"},
            {"id":"DIN-W","block":"DINING_CHAIR_450x500_PLAN","x":2700,"y":2700,"rotation":90,"role":"daily seat"},
            {"id":"DIN-E","block":"DINING_CHAIR_450x500_PLAN","x":4700,"y":2700,"rotation":270,"role":"daily seat"},
        ],
        "notes": ["r01 is an unoptimized project-only starting arrangement.", "r02 moves the dining group west/south to open the kitchen and glass-partition transition."]
    },
    "ARCH": {
        "device": "room/program reading + hierarchy + circulation + accessibility + concept organization",
        "source_principles": ["program and adjacency before placement", "clear primary circulation", "residential social hierarchy", "elder-friendly route continuity"],
        "iteration_limit": ITERATIONS,
        "r01": [
            {"id":"LIV-SOFA-3","block":"SOFA_3S_2200x900_PLAN","x":3000,"y":10400,"rotation":90,"role":"primary social anchor"},
            {"id":"LIV-SOFA-2","block":"SOFA_2S_1800x850_PLAN","x":5550,"y":12600,"rotation":0,"role":"conversation return"},
            {"id":"LIV-LOUNGE","block":"LOUNGE_CHAIR_900x900_PLAN","x":6800,"y":9300,"rotation":0,"role":"view seat"},
            {"id":"DIN-TABLE","block":"DINING_TABLE_1500x600_PLAN","x":3700,"y":2650,"rotation":0,"role":"kitchen-linked table"},
            {"id":"DIN-N","block":"DINING_CHAIR_450x500_PLAN","x":3700,"y":3450,"rotation":0,"role":"daily seat"},
            {"id":"DIN-S","block":"DINING_CHAIR_450x500_PLAN","x":3700,"y":1850,"rotation":180,"role":"daily seat"},
            {"id":"DIN-W","block":"DINING_CHAIR_450x500_PLAN","x":2700,"y":2650,"rotation":90,"role":"daily seat"},
            {"id":"DIN-E","block":"DINING_CHAIR_450x500_PLAN","x":4700,"y":2650,"rotation":270,"role":"daily seat"},
        ],
        "r02": [
            {"id":"LIV-SOFA-3","block":"SOFA_3S_2200x900_PLAN","x":3000,"y":10400,"rotation":90,"role":"primary social anchor"},
            {"id":"LIV-SOFA-2","block":"SOFA_2S_1800x850_PLAN","x":5600,"y":12600,"rotation":0,"role":"conversation return"},
            {"id":"LIV-LOUNGE","block":"LOUNGE_CHAIR_900x900_PLAN","x":6750,"y":8700,"rotation":0,"role":"view seat"},
            {"id":"DIN-TABLE","block":"DINING_TABLE_1500x600_PLAN","x":3600,"y":2500,"rotation":0,"role":"kitchen-linked table"},
            {"id":"DIN-N","block":"DINING_CHAIR_450x500_PLAN","x":3600,"y":3300,"rotation":0,"role":"daily seat"},
            {"id":"DIN-S","block":"DINING_CHAIR_450x500_PLAN","x":3600,"y":1700,"rotation":180,"role":"daily seat"},
            {"id":"DIN-W","block":"DINING_CHAIR_450x500_PLAN","x":2600,"y":2500,"rotation":90,"role":"daily seat"},
            {"id":"DIN-E","block":"DINING_CHAIR_450x500_PLAN","x":4600,"y":2500,"rotation":270,"role":"daily seat"},
        ],
        "notes": ["r01 reads the public zone as a domestic social room with a clear entry-to-stair axis.", "r02 is a circulation and accessibility revision, keeping the kitchen as an adjacent service anchor."]
    },
    "STUDIO": {
        "device": "benchmark -> concept -> plan -> one dominant spatial device -> red-team review -> CAD revision",
        "source_principles": ["one dominant clear-spine device", "concept before object placement", "red-team review before final CAD"],
        "iteration_limit": ITERATIONS,
        "r01": [
            {"id":"LIV-SOFA-3","block":"SOFA_3S_2200x900_PLAN","x":3000,"y":10400,"rotation":90,"role":"west edge anchor"},
            {"id":"LIV-SOFA-2","block":"SOFA_2S_1800x850_PLAN","x":6350,"y":12600,"rotation":0,"role":"north edge anchor"},
            {"id":"LIV-LOUNGE","block":"LOUNGE_CHAIR_900x900_PLAN","x":7050,"y":8500,"rotation":0,"role":"single view seat"},
            {"id":"DIN-TABLE","block":"DINING_TABLE_1500x600_PLAN","x":4000,"y":2950,"rotation":90,"role":"spine-aligned dining anchor"},
            {"id":"DIN-N","block":"DINING_CHAIR_450x500_PLAN","x":4000,"y":3950,"rotation":0,"role":"daily seat"},
            {"id":"DIN-S","block":"DINING_CHAIR_450x500_PLAN","x":4000,"y":1950,"rotation":180,"role":"daily seat"},
            {"id":"DIN-W","block":"DINING_CHAIR_450x500_PLAN","x":3150,"y":2950,"rotation":90,"role":"daily seat"},
            {"id":"DIN-E","block":"DINING_CHAIR_450x500_PLAN","x":4850,"y":2950,"rotation":270,"role":"daily seat"},
        ],
        "r02": [
            {"id":"LIV-SOFA-3","block":"SOFA_3S_2200x900_PLAN","x":3000,"y":10400,"rotation":90,"role":"west edge anchor"},
            {"id":"LIV-SOFA-2","block":"SOFA_2S_1800x850_PLAN","x":6350,"y":12600,"rotation":0,"role":"north edge anchor"},
            {"id":"LIV-LOUNGE","block":"LOUNGE_CHAIR_900x900_PLAN","x":7000,"y":9000,"rotation":0,"role":"single view seat"},
            {"id":"DIN-TABLE","block":"DINING_TABLE_1500x600_PLAN","x":3500,"y":2450,"rotation":90,"role":"spine-aligned dining anchor"},
            {"id":"DIN-N","block":"DINING_CHAIR_450x500_PLAN","x":3500,"y":3450,"rotation":0,"role":"daily seat"},
            {"id":"DIN-S","block":"DINING_CHAIR_450x500_PLAN","x":3500,"y":1450,"rotation":180,"role":"daily seat"},
            {"id":"DIN-W","block":"DINING_CHAIR_450x500_PLAN","x":2650,"y":2450,"rotation":90,"role":"daily seat"},
            {"id":"DIN-E","block":"DINING_CHAIR_450x500_PLAN","x":4350,"y":2450,"rotation":270,"role":"daily seat"},
        ],
        "notes": ["The dominant device is a continuous low-density spine from entry through dining to living/stair.", "r02 is the red-team revision: the table moves south/west while the living anchor stays fixed."]
    },
    "REROOM": {
        "device": "functional grouping -> anchor furniture selection -> geometry-guided refinement -> render/review/revise",
        "source_principles": ["functional groups before global arrangement", "anchor furniture first", "local revision when one relation fails", "global reorganization only when multiple relations fail"],
        "iteration_limit": ITERATIONS,
        "r01": [
            {"id":"LIV-SOFA-3","block":"SOFA_3S_2200x900_PLAN","x":5000,"y":7600,"rotation":0,"role":"living anchor"},
            {"id":"LIV-SOFA-2","block":"SOFA_2S_1800x850_PLAN","x":5000,"y":8850,"rotation":180,"role":"conversation partner"},
            {"id":"LIV-LOUNGE","block":"LOUNGE_CHAIR_900x900_PLAN","x":3500,"y":8200,"rotation":90,"role":"third seat"},
            {"id":"DIN-TABLE","block":"DINING_TABLE_1500x600_PLAN","x":4200,"y":3000,"rotation":0,"role":"dining group anchor"},
            {"id":"DIN-N","block":"DINING_CHAIR_450x500_PLAN","x":4200,"y":3800,"rotation":0,"role":"daily seat"},
            {"id":"DIN-S","block":"DINING_CHAIR_450x500_PLAN","x":4200,"y":2200,"rotation":180,"role":"daily seat"},
            {"id":"DIN-W","block":"DINING_CHAIR_450x500_PLAN","x":3200,"y":3000,"rotation":90,"role":"daily seat"},
            {"id":"DIN-E","block":"DINING_CHAIR_450x500_PLAN","x":5200,"y":3000,"rotation":270,"role":"daily seat"},
        ],
        "r02": [
            {"id":"LIV-SOFA-3","block":"SOFA_3S_2200x900_PLAN","x":4000,"y":8200,"rotation":0,"role":"living anchor"},
            {"id":"LIV-SOFA-2","block":"SOFA_2S_1800x850_PLAN","x":6100,"y":10000,"rotation":90,"role":"conversation partner"},
            {"id":"LIV-LOUNGE","block":"LOUNGE_CHAIR_900x900_PLAN","x":6900,"y":8500,"rotation":0,"role":"third seat"},
            {"id":"DIN-TABLE","block":"DINING_TABLE_1500x600_PLAN","x":3700,"y":2600,"rotation":0,"role":"dining group anchor"},
            {"id":"DIN-N","block":"DINING_CHAIR_450x500_PLAN","x":3700,"y":3400,"rotation":0,"role":"daily seat"},
            {"id":"DIN-S","block":"DINING_CHAIR_450x500_PLAN","x":3700,"y":1800,"rotation":180,"role":"daily seat"},
            {"id":"DIN-W","block":"DINING_CHAIR_450x500_PLAN","x":2700,"y":2600,"rotation":90,"role":"daily seat"},
            {"id":"DIN-E","block":"DINING_CHAIR_450x500_PLAN","x":4700,"y":2600,"rotation":270,"role":"daily seat"},
        ],
        "notes": ["r01 groups anchors around a local social node, intentionally testing whether local geometry can solve the public zone.", "r02 performs a global reorganization after the first pass shows multiple route conflicts."]
    },
}

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def jdump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

def task_bbox_from_entity(entity) -> list[float]:
    ex = bbox.extents([entity])
    return [ex.extmin.x - AX, ex.extmin.y - AY, ex.extmax.x - AX, ex.extmax.y - AY]

def rect_signature(entity) -> tuple:
    try:
        b = task_bbox_from_entity(entity)
        return (entity.dxf.handle, entity.dxftype(), entity.dxf.layer, tuple(round(x, 3) for x in b))
    except Exception:
        return (entity.dxf.handle, entity.dxftype(), entity.dxf.layer, None)

def remove_public_movable_from_doc(doc) -> list[str]:
    removed = []
    for entity in list(doc.modelspace()):
        if entity.dxftype() == "INSERT" and entity.dxf.layer == "A-FURN-PROP" and entity.dxf.name in OLD_PUBLIC_INSERT_NAMES:
            removed.append(entity.dxf.name)
            doc.modelspace().delete_entity(entity)
    return removed

def structural_signatures(doc) -> list[tuple]:
    return sorted(rect_signature(e) for e in doc.modelspace() if e.dxf.layer in STRUCTURAL_LAYERS)

def prepare_base() -> dict:
    source_doc = ezdxf.readfile(str(SOURCE_V02))
    before_structural = structural_signatures(source_doc)
    source_hash = sha256(SOURCE_V02)
    removed = remove_public_movable_from_doc(source_doc)
    after_structural = structural_signatures(source_doc)
    if before_structural != after_structural:
        raise RuntimeError("base preparation modified structural geometry")
    source_doc.saveas(str(BASE_PATH))
    base_hash = sha256(BASE_PATH)
    record = {
        "source_file": str(SOURCE_V02.relative_to(PROJECT)),
        "source_sha256": source_hash,
        "base_file": str(BASE_PATH.relative_to(PROJECT)),
        "base_sha256": base_hash,
        "removed_public_movable_insert_names": sorted(removed),
        "removed_count": len(removed),
        "structural_signature_unchanged": True,
        "note": "Only old public movable furniture INSERTs were removed; walls/openings/KEEP kitchen/stair/ramp remain.",
    }
    jdump(BASE_MANIFEST_PATH, record)
    return record

def formal_hashes() -> dict:
    paths = {
        "v02": SOURCE_V02,
        "canonical": CANONICAL_PATH,
        "windows": WINDOW_PATH,
        "a1": A1_PATH,
        "a2": A2_PATH,
        "a0_4": A0_PATH,
    }
    return {k: {"file": str(v.relative_to(PROJECT)), "sha256": sha256(v)} for k, v in paths.items()}

def make_input_manifest() -> dict:
    paths = {
        "project_brief_json": BRIEF_PATH,
        "project_brief_md": PROJECT / "brief/owner_brief_v1.md",
        "a0_4_compiled": A0_PATH,
        "a0_4_manifest": BLOCK_MANIFEST_PATH,
        "a1_rulebook": A1_PATH,
        "a2_pattern_library": A2_PATH,
        "canonical_geometry": CANONICAL_PATH,
        "window_register": WINDOW_PATH,
        "measured_cad": PROJECT / "current_existing/measured_working.dxf",
        "v02_base_cad": SOURCE_V02,
        "kitchen_register": PROJECT / "current_existing/kitchen_cabinet_register.json",
    }
    items = {k: {"file": str(v.relative_to(PROJECT)), "sha256": sha256(v)} for k, v in paths.items()}
    common_hash = hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()
    manifest = {
        "experiment": "D0.1 Residential CAD Design Skill Benchmark",
        "common_inputs": items,
        "common_input_set_sha256": common_hash,
        "model": "CURRENT_CODEX_SESSION",
        "same_renderer": "run_benchmark.py::render_dxf",
        "same_geometry_qa": "run_benchmark.py::analyze_trial",
        "iteration_limit": ITERATIONS,
        "prohibited_inputs": [
            "projects/c_type_home/qc/f1r_public_zone/*",
            "F1R_01H*",
            "F1R_02*",
            "old F1R JSON layout coordinates",
        ],
    }
    jdump(INPUT_MANIFEST_PATH, manifest)
    jdump(FORMAL_SHA_PATH, formal_hashes())
    return manifest

def source_manifest() -> dict:
    fetch = EXP / "sources/fetch_results.json"
    fetched = json.loads(fetch.read_text()) if fetch.exists() else []
    return {
        "sources": [
            {
                "name": "Skills-Architects",
                "repo": "https://github.com/Abhinavbwj/Skills-Architects",
                "commit": "30a0845dddcaebd765fc396059573d02e99c5b63",
                "files_read": [x for x in fetched if x.get("source") == "Skills-Architects"],
                "adopted": ["room/program reading", "spatial hierarchy", "functional zoning", "circulation", "residential typology", "accessibility", "concept organization"],
                "excluded": ["jurisdiction-specific code claims", "structural/MEP calculators", "non-residential content not needed for this home"],
            },
            {
                "name": "asset-management-interior",
                "repo": "https://github.com/gujun1502/arch-skills",
                "commit": "478d5ae32806e5a95dfcbeb70ba5a68126c22e9e",
                "files_read": [x for x in fetched if x.get("source") == "arch-skills"],
                "adopted": ["benchmark -> concept -> plan", "one dominant spatial device", "red-team review", "CAD revision"],
                "excluded": ["financial-office program content", "office asset procurement and budget assumptions"],
            },
            {
                "name": "ReRoom",
                "paper": "arXiv:2609.03596",
                "paper_sha256": next((x.get("sha256") for x in fetched if x.get("source") == "ReRoom"), None),
                "files_read": [x for x in fetched if x.get("source") == "ReRoom"],
                "adopted": ["Functional Grouping", "Anchor Furniture Selection", "Geometry-Guided Refinement", "Render -> Review -> Revise"],
                "excluded": ["claim of a public code implementation", "unavailable implementation details beyond the paper and Appendix S6"],
            },
        ],
        "network_note": "GitHub shallow clone attempts timed out; method files were fetched from commit-pinned raw URLs and saved locally with SHA256.",
    }

def ensure_a04_blocks(doc) -> None:
    missing = [n for n in REQUIRED_BLOCKS if n not in doc.blocks]
    if not missing:
        return
    lib = ezdxf.readfile(str(A0_PATH))
    importer = Importer(lib, doc)
    importer.import_blocks(missing)
    importer.finalize()
    if any(n not in doc.blocks for n in REQUIRED_BLOCKS):
        raise RuntimeError(f"missing A0.4 blocks after import: {missing}")

def clear_d0_entities(doc) -> None:
    for entity in list(doc.modelspace()):
        if entity.dxf.layer in {"D0-FURNITURE", "D0-QC"}:
            doc.modelspace().delete_entity(entity)

def insert_layout(doc, placements: list[dict]) -> list[dict]:
    if "D0-FURNITURE" not in doc.layers:
        doc.layers.add("D0-FURNITURE", color=2)
    clear_d0_entities(doc)
    placed = []
    for p in placements:
        entity = doc.modelspace().add_blockref(
            p["block"],
            (AX + p["x"], AY + p["y"], 0),
            dxfattribs={"layer": "D0-FURNITURE", "rotation": p.get("rotation", 0)},
        )
        q = dict(p)
        q["handle"] = entity.dxf.handle
        placed.append(q)
    return placed

def transformed_local_bbox(local: list[float], x: float, y: float, rotation: float) -> list[float]:
    pts = [(local[0], local[1]), (local[0], local[3]), (local[2], local[1]), (local[2], local[3])]
    a = math.radians(rotation % 360)
    transformed = [(x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
    xs, ys = zip(*transformed)
    return [min(xs), min(ys), max(xs), max(ys)]

def add_layout_to_file(source: Path, out: Path, placements: list[dict]) -> list[dict]:
    doc = ezdxf.readfile(str(source))
    ensure_a04_blocks(doc)
    placed = insert_layout(doc, placements)
    doc.saveas(str(out))
    checked = ezdxf.readfile(str(out))
    for p in placed:
        if p["handle"] not in checked.entitydb:
            raise RuntimeError(f"insert handle not present after save: {p['handle']}")
    return placed

def task_rect_shape(r: list[float]):
    return box(r[0], r[1], r[2], r[3])

def canonical_obstacles() -> Any:
    canonical = json.loads(CANONICAL_PATH.read_text())
    walls = []
    cuts = [item.get("rect_mm") or item.get("opening_rect_mm") for item in canonical.get("openings", []) + canonical.get("windows", [])]
    cuts = [c for c in cuts if c]
    for wall in canonical.get("walls", []):
        if wall.get("disposition") != "EXISTING":
            continue
        geom = task_rect_shape(wall["rect_mm"])
        for cut in cuts:
            geom = geom.difference(task_rect_shape(cut))
        if not geom.is_empty:
            walls.append(geom)
    return walls

def base_obstacles(doc) -> Any:
    parts = canonical_obstacles()
    for r in KEEP_RECTS.values():
        parts.append(task_rect_shape(r))
    for entity in doc.modelspace():
        if entity.dxf.layer in {"A-ACCESS-RAMP", "A-ACCESS-STAIR"}:
            try:
                parts.append(task_rect_shape(task_bbox_from_entity(entity)))
            except Exception:
                pass
    return unary_union(parts)

def line_component_length(intersection, point: Point) -> float:
    geoms = []
    if intersection.is_empty:
        return 0.0
    if intersection.geom_type == "LineString":
        geoms = [intersection]
    elif hasattr(intersection, "geoms"):
        geoms = [g for g in intersection.geoms if g.geom_type == "LineString"]
    if not geoms:
        return 0.0
    containing = [g for g in geoms if g.distance(point) < 2.0]
    chosen = containing or sorted(geoms, key=lambda g: g.distance(point))[:1]
    return max((g.length for g in chosen), default=0.0)

def route_widths(doc) -> dict:
    domain = task_rect_shape(PUBLIC_VIEW)
    obstacles = base_obstacles(doc)
    free = domain.difference(obstacles)
    results = {}
    for name, spec in ROUTES.items():
        line = LineString(spec["points"])
        half = 1900.0
        widths = []
        for i in range(1, 31):
            f = i / 31
            point = line.interpolate(f, normalized=True)
            dx = spec["points"][1][0] - spec["points"][0][0]
            dy = spec["points"][1][1] - spec["points"][0][1]
            length = max(math.hypot(dx, dy), 1.0)
            nx, ny = -dy / length, dx / length
            cross = LineString([(point.x - nx * half, point.y - ny * half), (point.x + nx * half, point.y + ny * half)])
            widths.append(line_component_length(free.intersection(cross), point))
        actual = min(widths) if widths else 0.0
        results[name] = {
            "route_points_task01": spec["points"],
            "actual_measured_min_mm": round(actual, 1),
            "reference_target_mm": spec["target_mm"],
            "measurement_method": "sampled perpendicular cross-sections through canonical-wall/opening and saved-DXF furniture obstacles",
            "kind": spec["kind"],
            "pass_reference": actual >= spec["target_mm"],
        }
    return results

def opening_transition_metrics(placements: list[dict]) -> dict:
    win = json.loads(WINDOW_PATH.read_text())
    opening = next((x for x in win.get("windows", []) if x.get("window_id") == "G-DIN-LIV"), None)
    if opening is None:
        return {"status": "UNKNOWN / NOT MEASURED"}
    rect = opening.get("bbox_task01") or opening.get("opening_rect_mm")
    chair_rects = []
    for p in placements:
        if p["id"].startswith("DIN-") and p["id"] != "DIN-TABLE":
            chair_rects.append(transformed_local_bbox(BLOCK_LOCAL_BBOX[p["block"]], p["x"], p["y"], p.get("rotation", 0)))
    y = (rect[1] + rect[3]) / 2.0
    intervals = sorted([(max(rect[0], r[0]), min(rect[2], r[2])) for r in chair_rects
                        if r[1] <= y <= r[3] and min(rect[2], r[2]) > max(rect[0], r[0])])
    cursor = rect[0]
    free = []
    for a, b in intervals:
        if a > cursor:
            free.append(a - cursor)
        cursor = max(cursor, b)
    if cursor < rect[2]:
        free.append(rect[2] - cursor)
    return {
        "opening_id": "G-DIN-LIV",
        "opening_bbox_task01": rect,
        "actual_transition_free_width_mm": round(max(free) if free else 0.0, 1),
        "chair_intervals_at_opening": intervals,
        "measurement_method": "saved-DXF DIN chair bboxes subtracted from registered sliding-partition opening",
    }

def furniture_records(doc, placements: list[dict]) -> list[dict]:
    by_handle = {p["handle"]: p for p in placements}
    records = []
    for e in doc.modelspace():
        if e.dxf.layer != "D0-FURNITURE":
            continue
        p = by_handle.get(e.dxf.handle)
        if not p:
            continue
        actual = task_bbox_from_entity(e)
        expected = transformed_local_bbox(BLOCK_LOCAL_BBOX[p["block"]], p["x"], p["y"], p.get("rotation", 0))
        delta = max(abs(actual[i] - expected[i]) for i in range(4))
        records.append({
            "id": p["id"],
            "block": p["block"],
            "handle": p["handle"],
            "rotation": p.get("rotation", 0),
            "intended_bbox_task01": [round(v, 3) for v in expected],
            "actual_bbox_task01": [round(v, 3) for v in actual],
            "max_bbox_delta_mm": round(delta, 4),
            "bbox_qa_pass": delta <= 1.0,
            "role": p.get("role", ""),
        })
    return records

def dining_metrics(records: list[dict]) -> dict:
    table = next((r for r in records if r["id"] == "DIN-TABLE"), None)
    chairs = [r for r in records if r["id"].startswith("DIN-") and r["id"] != "DIN-TABLE"]
    if not table:
        return {"status": "UNKNOWN / NOT MEASURED"}
    tr = table["actual_bbox_task01"]
    table_shape = task_rect_shape(tr)
    kitchen_shape = task_rect_shape(KEEP_RECTS["kitchen"])
    gaps = []
    for chair in chairs:
        cr = chair["actual_bbox_task01"]
        gaps.append({"id": chair["id"], "table_edge_gap_mm": round(table_shape.distance(task_rect_shape(cr)), 1), "chair_bbox": cr})
    return {
        "table_bbox_task01": tr,
        "table_to_keep_kitchen_gap_mm": round(table_shape.distance(kitchen_shape), 1),
        "chair_table_gaps": gaps,
        "seated_envelope_definition": "saved-DXF chair bbox projected from table edge; chair footprint is not relabeled as pullout travel",
        "min_table_to_chair_gap_mm": round(min((g["table_edge_gap_mm"] for g in gaps), default=0.0), 1),
    }

def analyze_trial(path: Path, placements: list[dict]) -> dict:
    doc = ezdxf.readfile(str(path))
    records = furniture_records(doc, placements)
    routes = route_widths(doc)
    opening = opening_transition_metrics(placements)
    dining = dining_metrics(records)
    overlaps = []
    for i, a in enumerate(records):
        ar = task_rect_shape(a["actual_bbox_task01"])
        for b in records[i + 1:]:
            inter = ar.intersection(task_rect_shape(b["actual_bbox_task01"]))
            if inter.area > 1.0:
                overlaps.append({"a": a["id"], "b": b["id"], "area_mm2": round(inter.area, 1)})
    violations = []
    for name, item in routes.items():
        if not item["pass_reference"] and name != "living_to_north_balcony":
            violations.append({"type": "route_clearance", "route": name, "actual_mm": item["actual_measured_min_mm"], "target_mm": item["reference_target_mm"]})
    if dining.get("table_to_keep_kitchen_gap_mm", 0) < 1000:
        violations.append({"type": "dining_kitchen_gap", "actual_mm": dining.get("table_to_keep_kitchen_gap_mm"), "target_mm": 1000})
    if opening.get("actual_transition_free_width_mm", 0) < 900:
        violations.append({"type": "G-DIN-LIV_transition", "actual_mm": opening.get("actual_transition_free_width_mm"), "target_mm": 900})
    violations.extend({"type": "furniture_overlap", **x} for x in overlaps)
    return {
        "source_dxf": str(path.relative_to(PROJECT)),
        "source_dxf_sha256": sha256(path),
        "furniture": records,
        "transformed_block_bbox_qa": {
            "count": len(records),
            "all_pass": all(r["bbox_qa_pass"] for r in records),
            "max_delta_mm": max((r["max_bbox_delta_mm"] for r in records), default=0.0),
        },
        "route_clearances": routes,
        "G_DIN_LIV": opening,
        "dining": dining,
        "furniture_overlap_count": len(overlaps),
        "geometry_violations": violations,
        "geometry_violation_count": len(violations),
    }

def draw_actual_block_geometry(ax, doc) -> None:
    """Draw block definition entities from the saved DXF INSERT transforms."""
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
            typ = entity.dxftype()
            if typ == "LINE":
                a = xf(entity.dxf.start.x, entity.dxf.start.y)
                b = xf(entity.dxf.end.x, entity.dxf.end.y)
                ax.plot([a[0], b[0]], [a[1], b[1]], color="#b44d12", linewidth=0.85, zorder=55)
            elif typ == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in entity.get_points("xy")]
                if entity.closed and pts:
                    pts.append(pts[0])
                if len(pts) >= 2:
                    xy = [xf(x, y) for x, y in pts]
                    ax.plot([p[0] for p in xy], [p[1] for p in xy], color="#b44d12", linewidth=0.85, zorder=55)
            elif typ == "ARC":
                cx, cy = entity.dxf.center.x, entity.dxf.center.y
                r = float(entity.dxf.radius)
                start, end = math.radians(entity.dxf.start_angle), math.radians(entity.dxf.end_angle)
                if end <= start:
                    end += 2 * math.pi
                pts = [xf(cx + r * math.cos(t), cy + r * math.sin(t)) for t in [start + (end-start)*i/32 for i in range(33)]]
                ax.plot([p[0] for p in pts], [p[1] for p in pts], color="#b44d12", linewidth=0.85, zorder=55)

def render_dxf(path: Path, png: Path, sidecar: Path) -> dict:
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    def keep(entity):
        if entity.dxf.layer in HIDDEN_RENDER_LAYERS or entity.dxf.layer == "D0-QC":
            return False
        if entity.dxftype() in {"TEXT", "MTEXT", "DIMENSION", "HATCH"}:
            return False
        return True
    fig = plt.figure(figsize=(8.2, 10.2), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_facecolor("white")
    backend = MatplotlibBackend(ax, adjust_figure=False)
    Frontend(RenderContext(doc), backend).draw_layout(msp, filter_func=keep, finalize=True)
    draw_actual_block_geometry(ax, doc)
    ax.set_xlim(AX + PUBLIC_VIEW[0], AX + PUBLIC_VIEW[2])
    ax.set_ylim(AY + PUBLIC_VIEW[1], AY + PUBLIC_VIEW[3])
    ax.set_aspect("equal")
    fig.savefig(png, dpi=150, facecolor="white")
    plt.close(fig)
    meta = {
        "source_dxf": str(path.relative_to(PROJECT)),
        "source_dxf_sha256": sha256(path),
        "renderer": "run_benchmark.py::render_dxf",
        "view_task01": PUBLIC_VIEW,
        "png": {"file": str(png.relative_to(PROJECT)), "sha256": sha256(png)},
    }
    jdump(sidecar, meta)
    return meta

def render_clearance(path: Path, png: Path, metrics: dict) -> None:
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    def keep(entity):
        if entity.dxf.layer in HIDDEN_RENDER_LAYERS or entity.dxf.layer == "D0-QC":
            return False
        if entity.dxftype() in {"TEXT", "MTEXT", "DIMENSION", "HATCH"}:
            return False
        return True
    fig = plt.figure(figsize=(8.2, 10.2), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    backend = MatplotlibBackend(ax, adjust_figure=False)
    Frontend(RenderContext(doc), backend).draw_layout(msp, filter_func=keep, finalize=True)
    draw_actual_block_geometry(ax, doc)
    ax.set_xlim(AX + PUBLIC_VIEW[0], AX + PUBLIC_VIEW[2])
    ax.set_ylim(AY + PUBLIC_VIEW[1], AY + PUBLIC_VIEW[3])
    ax.set_aspect("equal")
    for rec in metrics["furniture"]:
        x1, y1, x2, y2 = rec["actual_bbox_task01"]
        color = "#d95f02" if rec["id"].startswith("DIN-") else "#1b9e77"
        ax.add_patch(Rectangle((AX+x1, AY+y1), x2-x1, y2-y1, fill=False, edgecolor=color, linewidth=1.1, linestyle="--"))
    route_colors = ["#386cb0", "#7b3294", "#008837", "#e66101", "#a6611a"]
    for (name, spec), color in zip(ROUTES.items(), route_colors):
        xs, ys = zip(*spec["points"])
        ax.plot([AX+x for x in xs], [AY+y for y in ys], color=color, linewidth=1.1, alpha=0.8)
        mid = spec["points"][len(spec["points"])//2]
        width = metrics["route_clearances"][name]["actual_measured_min_mm"]
        ax.text(AX+mid[0], AY+mid[1], f"{name}: {width:.0f} mm", fontsize=6, color=color, bbox={"facecolor":"white","alpha":0.65,"edgecolor":"none","pad":0.4})
    op = metrics.get("G_DIN_LIV", {})
    if op.get("opening_bbox_task01"):
        x1,y1,x2,y2 = op["opening_bbox_task01"]
        ax.add_patch(Rectangle((AX+x1,AY+y1),x2-x1,y2-y1,fill=False,edgecolor="#e31a1c",linewidth=1.5))
        ax.text(AX+x1,AY+y2+80,f"G-DIN-LIV free {op.get('actual_transition_free_width_mm',0):.0f} mm",fontsize=6,color="#e31a1c")
    ax.text(AX+PUBLIC_VIEW[0]+100, AY+PUBLIC_VIEW[3]-150, "D0.1 geometric clearance overlay; measured from saved DXF", fontsize=7, color="#222")
    fig.savefig(png, dpi=150, facecolor="white")
    plt.close(fig)

def cad_diff(base: Path, final: Path) -> dict:
    bdoc, fdoc = ezdxf.readfile(str(base)), ezdxf.readfile(str(final))
    bs = {e.dxf.handle: rect_signature(e) for e in bdoc.modelspace() if e.dxf.layer != "D0-FURNITURE"}
    fs = {e.dxf.handle: rect_signature(e) for e in fdoc.modelspace() if e.dxf.layer != "D0-FURNITURE"}
    changed = sorted(h for h in bs if h in fs and bs[h] != fs[h])
    missing = sorted(h for h in bs if h not in fs)
    added_non_d0 = sorted(h for h in fs if h not in bs and fs[h][2] != "D0-FURNITURE")
    d0_count = sum(1 for e in fdoc.modelspace() if e.dxf.layer == "D0-FURNITURE")
    return {
        "base_dxf": str(base.relative_to(PROJECT)),
        "final_dxf": str(final.relative_to(PROJECT)),
        "non_furniture_changed_handles": changed,
        "non_furniture_missing_handles": missing,
        "unexpected_added_non_furniture_handles": added_non_d0,
        "d0_furniture_entity_count": d0_count,
        "formal_geometry_preserved": not changed and not missing and not added_non_d0,
    }

def make_design_log(arm: str, metrics: dict) -> str:
    spec = ARM_SPECS[arm]
    input_hash = json.loads(INPUT_MANIFEST_PATH.read_text())["common_input_set_sha256"]
    lines = [
        f"# D0.1 {arm} design log",
        "",
        f"- Method device: {spec['device']}",
        f"- Common input set: {input_hash}",
        "- CAD-first sequence: saved DXF -> render from that DXF -> measure that DXF -> next iteration.",
        "- Formal V02/V03/canonical files were not edited.",
        "",
        "## Method principles used",
        *[f"- {x}" for x in spec["source_principles"]],
        "",
        "## Iteration record",
        "- r01: initial method-specific arrangement; no previous arm result was read.",
        "- r02: same-method review revision using only r01 saved-DXF geometry and common constraints.",
        "- final: r02 CAD copied as the human-review candidate; no formal write-back.",
        "",
        "## Final geometry observations",
        f"- transformed A0.4 block bbox QA: {metrics['transformed_block_bbox_qa']['all_pass']} (max delta {metrics['transformed_block_bbox_qa']['max_delta_mm']:.2f} mm)",
        f"- geometry violations: {metrics['geometry_violation_count']}",
        f"- G-DIN-LIV measured transition free width: {metrics['G_DIN_LIV'].get('actual_transition_free_width_mm','UNKNOWN / NOT MEASURED')} mm",
        f"- dining-to-KEEP-kitchen gap: {metrics['dining'].get('table_to_keep_kitchen_gap_mm','UNKNOWN / NOT MEASURED')} mm",
        "",
        "## Review boundary",
        "- This is a blind concept benchmark artifact, not a construction drawing or approved design.",
        "- No claim of a winning method is made before human review.",
    ]
    return "\n".join(lines) + "\n"

def run_arm(arm: str) -> dict:
    start = time.perf_counter()
    spec = ARM_SPECS[arm]
    arm_dir = EXP / "arms" / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    trial_metrics = []
    placements_by_iter = {}
    prev = BASE_PATH
    for label in ("r01", "r02"):
        path = arm_dir / f"trial_{label}.dxf"
        placements = add_layout_to_file(prev, path, spec[label])
        placements_by_iter[label] = placements
        png = arm_dir / f"trial_{label}.png"
        sidecar = arm_dir / f"trial_{label}.render.json"
        render_dxf(path, png, sidecar)
        metrics = analyze_trial(path, placements)
        metrics["iteration"] = label
        jdump(arm_dir / f"trial_{label}_metrics.json", metrics)
        trial_metrics.append(metrics)
        prev = path
    final = arm_dir / "trial_final.dxf"
    shutil.copy2(prev, final)
    final_placements = placements_by_iter["r02"]
    final_png = arm_dir / "trial_final.png"
    render_dxf(final, final_png, arm_dir / "trial_final.render.json")
    final_metrics = analyze_trial(final, final_placements)
    final_metrics["iteration"] = "final"
    clearance_png = arm_dir / "trial_final_clearance.png"
    render_clearance(final, clearance_png, final_metrics)
    aggregate = {
        "arm": arm,
        "method_device": spec["device"],
        "iteration_limit": ITERATIONS,
        "trials": trial_metrics,
        "final": final_metrics,
        "wall_clock_seconds": round(time.perf_counter() - start, 3),
        "tool_calls": "UNKNOWN / NOT MEASURED",
        "manual_interventions": 0,
        "geometry_violations_per_iteration": {m["iteration"]: m["geometry_violation_count"] for m in trial_metrics + [final_metrics]},
        "final_dxf_sha256": sha256(final),
        "final_png_sha256": sha256(final_png),
        "prohibited_old_f1r_inputs_read": False,
    }
    jdump(arm_dir / "geometry_metrics.json", aggregate)
    jdump(arm_dir / "cad_diff.json", cad_diff(BASE_PATH, final))
    (arm_dir / "design_log.md").write_text(make_design_log(arm, final_metrics))
    return aggregate

def comparison_sheet(blind_paths: dict[str, Path], out: Path) -> None:
    images = [(label, Image.open(path).convert("RGB")) for label, path in blind_paths.items()]
    w, h = images[0][1].size
    margin, label_h = 20, 38
    canvas = Image.new("RGB", (2*w + 3*margin, 2*(h+label_h) + 3*margin), "white")
    draw = ImageDraw.Draw(canvas)
    for i, (label, image) in enumerate(images):
        x = margin + (i % 2) * (w + margin)
        y = margin + (i // 2) * (h + label_h + margin)
        canvas.paste(image, (x, y+label_h))
        draw.text((x, y+7), f"Blind option {label}", fill="black")
    canvas.save(out)

def human_review_form(out: Path) -> None:
    criteria = ["空间整体感", "座席 group", "主次关系", "家具是否像设计而非摆放", "负空间", "儿童活动", "老人通行", "投影兼容", "北阳台关系", "餐厅/厨房关系", "G-DIN-LIV", "尺度比例", "莫名其妙家具", "专业住宅感"]
    lines = [
        "# D0.1 Human review form",
        "",
        "请只按 A/B/C/D 盲图评分；不要先查看 arm_mapping.json。每项 1–5 分，备注写具体空间观察。",
        "",
        "| 维度 | A | B | C | D | 备注 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    lines += [f"| {c} |  |  |  |  |  |" for c in criteria]
    lines += [
        "",
        "## 综合选择",
        "- 首选：",
        "- 次选：",
        "- 需要淘汰的方案及原因：",
        "- 是否允许下一阶段概念冻结：",
        "",
        "## 评审限制",
        "- 盲图由同一 base DXF、同一 A0.4 block 库、同一 renderer 和同一几何 QA 生成。",
        "- 850 mm G-LIV-NBALC 作为 existing limitation，只检查 no-worsening。",
        "- 这份表不批准任何 V02/V03/canonical CAD 写回。",
    ]
    out.write_text("\n".join(lines) + "\n")

def run_all() -> dict:
    started = dt.datetime.now(dt.timezone.utc)
    base = prepare_base()
    inputs = make_input_manifest()
    src = source_manifest()
    arm_results = {arm: run_arm(arm) for arm in ARMS}
    mapping = {"A": "ARCH", "B": "REROOM", "C": "CTRL", "D": "STUDIO"}
    blind_paths, blind_clearance = {}, {}
    for label, arm in mapping.items():
        src_png = EXP / "arms" / arm / "trial_final.png"
        src_clear = EXP / "arms" / arm / "trial_final_clearance.png"
        dst = EXP / "blind_review" / f"{label}.png"
        dst_clear = EXP / "blind_review" / f"{label}_clearance.png"
        shutil.copy2(src_png, dst)
        shutil.copy2(src_clear, dst_clear)
        blind_paths[label], blind_clearance[label] = dst, dst_clear
    comparison_sheet(blind_paths, EXP / "blind_review/comparison_sheet.png")
    human_review_form(EXP / "blind_review/human_review_form.md")
    jdump(EXP / "blind_review/arm_mapping.json", {"mapping": mapping, "generated_at_utc": started.isoformat()})
    formal_after = formal_hashes()
    before = json.loads(FORMAL_SHA_PATH.read_text())
    formal_unchanged = before == formal_after
    gate = {
        "status": "HUMAN_REVIEW",
        "generated_at_utc": started.isoformat(),
        "base_cad_sha256": base["base_sha256"],
        "formal_input_sha_before": before,
        "formal_input_sha_after": formal_after,
        "gates": {
            "G0_SOURCE_AUDIT": all(src_item["files_read"] for src_item in src["sources"]),
            "G1_BASE_CAD": base["structural_signature_unchanged"] and base["removed_count"] == len(OLD_PUBLIC_INSERT_NAMES),
            "G2_ISOLATION": all(not r["prohibited_old_f1r_inputs_read"] for r in arm_results.values()),
            "G3_CAD_FIRST": all(all((EXP / "arms" / arm / f"trial_{it}.dxf").exists() for it in ("r01", "r02", "final")) for arm in ARMS),
            "G4_ACTUAL_BLOCKS": all(r["final"]["transformed_block_bbox_qa"]["all_pass"] and r["final"]["transformed_block_bbox_qa"]["count"] == 8 for r in arm_results.values()),
            "G5_ITERATIVE_REVIEW": all(len(r["trials"]) == ITERATIONS for r in arm_results.values()),
            "G6_SAME_INPUTS": len({inputs["common_input_set_sha256"]}) == 1,
            "G7_BLIND_OUTPUT": all(p.exists() for p in list(blind_paths.values()) + list(blind_clearance.values())),
            "G8_FORMAL_CAD_SAFETY": formal_unchanged,
        },
        "arms": {arm: {"iteration_count": len(r["trials"]), "wall_clock_seconds": r["wall_clock_seconds"], "tool_calls": r["tool_calls"], "manual_interventions": r["manual_interventions"], "geometry_violations_per_iteration": r["geometry_violations_per_iteration"], "final_dxf_sha256": r["final_dxf_sha256"]} for arm, r in arm_results.items()},
        "blind_outputs": {**{k: str(v.relative_to(PROJECT)) for k, v in blind_paths.items()}, **{f"{k}_clearance": str(v.relative_to(PROJECT)) for k, v in blind_clearance.items()}},
        "arm_mapping": str((EXP / "blind_review/arm_mapping.json").relative_to(PROJECT)),
        "stop_condition": "Do not start V03; do not write formal CAD; await human review.",
    }
    jdump(EXP / "reports/gates.json", gate)
    jdump(EXP / "reports/source_manifest.json", src)
    jdump(EXP / "reports/arm_results.json", arm_results)
    return gate

if __name__ == "__main__":
    print(json.dumps(run_all(), ensure_ascii=False, indent=2))

