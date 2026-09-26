#!/usr/bin/env python3
"""Audit source entities that look like the former fan-shaped leisure platform."""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Rectangle
from ezdxf import bbox
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend


ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / "cad"
QC = ROOT / "qc"
SOURCE = CAD / "measured_working.dxf"
CURRENT = CAD / "structure_only_source_sync.dxf"
AUDIT_JSON = QC / "lounge_entity_audit.json"
AUDIT_PNG = QC / "lounge_entity_audit.png"
AX, AY = 1298172.0, -296458.0
AUDIT_REGION = [5000, 3800, 9000, 8300]

# These are source handles only; no source file is modified by this audit.
LOUNGE_PLATFORM_HANDLES = ["30830F", "308310", "308311"]
RETAINED_STAIR_HANDLES = ["308341", "308342", "308343", "308345"]
NESTED_FURNITURE_HANDLES = ["307F68"]


def _load_builder_helpers():
    path = ROOT / "scripts/build_structure_only_cad.py"
    spec = importlib.util.spec_from_file_location("structure_builder", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _record(entity, doc, classification, reason):
    builder = _load_builder_helpers()
    out = builder._entity_record(entity)
    out.update({"classification": classification, "reason": reason})
    if entity.dxftype() == "INSERT":
        block = doc.blocks.get(entity.dxf.name)
        out["block_name"] = entity.dxf.name
        out["nested_entity_count"] = sum(1 for _ in block)
        out["nested_layers"] = sorted(Counter(be.dxf.layer for be in block).keys())
        out["nested_furniture"] = any(be.dxf.layer == "F-FURN" for be in block)
    return out


def _task_bbox(entity):
    ext = bbox.extents([entity])
    if not ext.has_data:
        return None
    return [ext.extmin.x - AX, ext.extmin.y - AY, ext.extmax.x - AX, ext.extmax.y - AY]


def _intersects(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def _draw_candidate(ax, entity, color, label):
    typ = entity.dxftype()
    if typ == "LINE":
        ax.plot(
            [entity.dxf.start.x, entity.dxf.end.x],
            [entity.dxf.start.y, entity.dxf.end.y],
            color=color, linewidth=5, solid_capstyle="round", zorder=20,
        )
    elif typ == "ARC":
        center = entity.dxf.center
        ax.add_patch(Arc(
            (center.x, center.y), 2 * entity.dxf.radius, 2 * entity.dxf.radius,
            angle=0, theta1=entity.dxf.start_angle, theta2=entity.dxf.end_angle,
            color=color, linewidth=5, zorder=20,
        ))
    elif typ == "LWPOLYLINE":
        points = list(entity.get_points("xy"))
        if points:
            xs = [p[0] for p in points] + [points[0][0] if entity.closed else points[-1][0]]
            ys = [p[1] for p in points] + [points[0][1] if entity.closed else points[-1][1]]
            ax.plot(xs, ys, color=color, linewidth=5, zorder=20)
    elif typ == "INSERT":
        rect = _task_bbox(entity)
        if rect:
            ax.add_patch(Rectangle(
                (rect[0] + AX, rect[1] + AY), rect[2] - rect[0], rect[3] - rect[1],
                fill=False, edgecolor=color, linewidth=4, linestyle="--", zorder=20,
            ))
    rect = _task_bbox(entity)
    if rect:
        ax.text(
            (rect[0] + rect[2]) / 2 + AX,
            (rect[1] + rect[3]) / 2 + AY,
            label, color=color, fontsize=8, weight="bold", ha="center", va="center",
            bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": color}, zorder=30,
        )


def audit():
    source = ezdxf.readfile(str(SOURCE))
    current = ezdxf.readfile(str(CURRENT))
    by_handle = {e.dxf.get("handle"): e for e in source.modelspace() if e.dxf.get("handle")}
    candidate_specs = [
        (handle, "NON_STRUCTURAL_SOURCE_OVERLAY", "owner-confirmed fan-shaped lounge/platform geometry to remove")
        for handle in LOUNGE_PLATFORM_HANDLES
    ] + [
        (handle, "RETAINED_STAIR_CONTEXT", "straight two-riser stair geometry; retain pending visual review")
        for handle in RETAINED_STAIR_HANDLES
    ] + [
        (handle, "FURNITURE_NESTED_IN_SOURCE_BLOCK", "source INSERT contains nested F-FURN block geometry")
        for handle in NESTED_FURNITURE_HANDLES
    ]
    records = []
    missing_handles = []
    for handle, classification, reason in candidate_specs:
        entity = by_handle.get(handle)
        if entity is None:
            missing_handles.append(handle)
            continue
        records.append(_record(entity, source, classification, reason))

    region_inventory = []
    for entity in source.modelspace():
        try:
            rect = _task_bbox(entity)
        except Exception:
            continue
        if rect and _intersects(rect, AUDIT_REGION):
            region_inventory.append({
                "handle": entity.dxf.get("handle"),
                "layer": entity.dxf.layer,
                "type": entity.dxftype(),
                "bbox_task01": rect,
            })

    # Render current structure-only drawing as a light context, then highlight
    # only the candidate handles.  No geometry is written to either DXF.
    def keep(entity):
        return entity.dxf.layer != "RC-GRILL" and entity.dxftype() != "DIMENSION"

    ext_entities = []
    for entity in current.modelspace():
        if not keep(entity) or entity.dxftype() not in {"LINE", "LWPOLYLINE", "ARC", "CIRCLE", "TEXT", "MTEXT", "POLYLINE", "INSERT"}:
            continue
        try:
            ext = bbox.extents([entity])
        except Exception:
            continue
        if ext.has_data:
            ext_entities.append(entity)
    ext = bbox.extents(ext_entities)
    width = ext.extmax.x - ext.extmin.x
    height = ext.extmax.y - ext.extmin.y
    fig = plt.figure(figsize=(13, max(8, 13 * height / max(width, 1))), dpi=160)
    ax = fig.add_axes([0.04, 0.04, 0.92, 0.9])
    ax.set_facecolor("white")
    Frontend(RenderContext(current), MatplotlibBackend(ax, adjust_figure=False)).draw_layout(
        current.modelspace(), filter_func=keep, finalize=True
    )
    ax.set_xlim(ext.extmin.x - width * 0.02, ext.extmax.x + width * 0.02)
    ax.set_ylim(ext.extmin.y - height * 0.02, ext.extmax.y + height * 0.02)
    ax.set_aspect("equal")
    ax.set_title("Source Lounge/Platform Entity Audit — geometry candidates only", fontsize=14)
    colors = {
        "NON_STRUCTURAL_SOURCE_OVERLAY": "#e85d04",
        "RETAINED_STAIR_CONTEXT": "#2a9d8f",
        "FURNITURE_NESTED_IN_SOURCE_BLOCK": "#4361ee",
    }
    for record in records:
        entity = by_handle[record["handle"]]
        _draw_candidate(ax, entity, colors[record["classification"]], record["handle"])
    handles = [
        plt.Line2D([], [], color=colors["NON_STRUCTURAL_SOURCE_OVERLAY"], linewidth=5, label="remove candidate: fan-shaped lounge/platform"),
        plt.Line2D([], [], color=colors["RETAINED_STAIR_CONTEXT"], linewidth=5, label="retain context: straight two-riser stair"),
        plt.Line2D([], [], color=colors["FURNITURE_NESTED_IN_SOURCE_BLOCK"], linewidth=4, linestyle="--", label="remove candidate: nested furniture block"),
    ]
    ax.legend(handles=handles, loc="upper right", fontsize=8)
    fig.savefig(AUDIT_PNG, dpi=160, facecolor="white")
    plt.close(fig)

    report = {
        "source_dxf": str(SOURCE.relative_to(ROOT)),
        "source_dxf_sha256": __import__("hashlib").sha256(SOURCE.read_bytes()).hexdigest(),
        "audit_region_task01": AUDIT_REGION,
        "candidate_records": records,
        "missing_candidate_handles": missing_handles,
        "region_inventory": region_inventory,
        "approved_lounge_exclusion_handles": LOUNGE_PLATFORM_HANDLES,
        "retained_stair_context_handles": RETAINED_STAIR_HANDLES,
        "nested_furniture_handles": NESTED_FURNITURE_HANDLES,
        "layer_determination": {
            "lounge_platform": sorted({r["layer"] for r in records if r["classification"] == "NON_STRUCTURAL_SOURCE_OVERLAY"}),
            "retained_stair": sorted({r["layer"] for r in records if r["classification"] == "RETAINED_STAIR_CONTEXT"}),
            "nested_furniture": sorted({r["layer"] for r in records if r["classification"] == "FURNITURE_NESTED_IN_SOURCE_BLOCK"}),
        },
        "audit_png": str(AUDIT_PNG.relative_to(ROOT)),
    }
    AUDIT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "audit_png": str(AUDIT_PNG),
        "audit_json": str(AUDIT_JSON),
        "candidate_count": len(records),
        "missing": missing_handles,
        "lounge_handles": LOUNGE_PLATFORM_HANDLES,
        "nested_furniture_handles": NESTED_FURNITURE_HANDLES,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    audit()
