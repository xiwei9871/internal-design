#!/usr/bin/env python3
"""Build the A0.3 normalized source block library.

This is source normalization only: units, origin, layers, block wrapping, and
QA. It never applies design-standard resizing such as 1800x2100 beds.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Ellipse
from ezdxf import bbox
from ezdxf.math import Matrix44


ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "assets/cad_library"
RAW = LIB / "raw"
NORMALIZED = LIB / "normalized"
PREVIEWS = LIB / "previews"
MANIFESTS = LIB / "manifests"
COMPILED = LIB / "compiled"
SELECTION = MANIFESTS / "selection_v01.json"
A02_REPORT = ROOT / "qc/a0_2_cad_sample_report.json"
BLOCK_MANIFEST = MANIFESTS / "block_manifest.json"
QA_REPORT = MANIFESTS / "qa_report.json"
COMPILED_FILE = COMPILED / "residential_plan_blocks_v01.dxf"
DWG2DXF = "/opt/homebrew/bin/dwg2dxf"

LAYERS = {
    "LIB-PLAN": 7,
    "LIB-ANNOTATION": 8,
}
KEEP_TYPES = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE", "TEXT", "MTEXT"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten_entities(doc):
    """Yield modelspace geometry with INSERTs expanded to virtual entities."""
    def walk(entity):
        if entity.dxftype() == "INSERT":
            try:
                for virtual in entity.virtual_entities():
                    yield from walk(virtual)
            except Exception:
                return
        else:
            yield entity
    for entity in doc.modelspace():
        yield from walk(entity)


def source_doc(item):
    raw_path = ROOT / item["raw_file"]
    if raw_path.suffix.lower() == ".dxf":
        return ezdxf.readfile(str(raw_path))
    tmp = Path(tempfile.mkdtemp(prefix="a03_dwg_")) / (raw_path.stem + ".dxf")
    result = subprocess.run([DWG2DXF, "-y", "-o", str(tmp), str(raw_path)], capture_output=True, text=True, timeout=60)
    if result.returncode != 0 or not tmp.exists():
        raise RuntimeError(f"DWG conversion failed for {raw_path}: {result.stderr[-500:]}")
    return ezdxf.readfile(str(tmp))


def _bbox(entities):
    entities = list(entities)
    if not entities:
        raise ValueError("no drawable entities")
    ext = bbox.extents(entities)
    if not ext.has_data:
        raise ValueError("drawable entities have no extents")
    return [float(ext.extmin.x), float(ext.extmin.y), float(ext.extmax.x), float(ext.extmax.y)]


def _base_point(category, rect):
    x1, y1, x2, y2 = rect
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    if category == "bed":
        return [cx, y2], "head-center"
    if category == "sofa":
        return [cx, y2], "back-center"
    if category in {"desk", "dining_table", "dining_chair", "office_chair", "shower", "vanity"}:
        return [cx, cy], "center"
    if category == "wc":
        return [cx, y2], "rear-center / wall-connection side"
    if category in {"wardrobe", "washer", "fridge"}:
        return [x1, y2], "back-left"
    return [cx, cy], "center"


def _add_layers(doc):
    for name, color in LAYERS.items():
        if name not in doc.layers:
            doc.layers.add(name, color=color)


def _copy_transform(entity, factor, base):
    out = entity.copy()
    out.transform(Matrix44.scale(factor, factor, factor))
    out.translate(-base[0], -base[1], 0.0)
    if out.dxftype() in {"TEXT", "MTEXT"}:
        out.dxf.layer = "LIB-ANNOTATION"
    else:
        out.dxf.layer = "LIB-PLAN"
    out.dxf.color = 256
    return out


def _entity_signature(entity):
    return {
        "type": entity.dxftype(),
        "layer": entity.dxf.layer,
    }


def _draw(ax, entity, scale, ox, oy):
    def tx(x): return x * scale + ox
    def ty(y): return y * scale + oy
    typ = entity.dxftype()
    try:
        if typ == "LINE":
            ax.plot([tx(entity.dxf.start.x), tx(entity.dxf.end.x)], [ty(entity.dxf.start.y), ty(entity.dxf.end.y)], color="#222", lw=0.75)
        elif typ == "LWPOLYLINE":
            pts = list(entity.get_points("xy"))
            if pts:
                if entity.closed: pts.append(pts[0])
                ax.plot([tx(p[0]) for p in pts], [ty(p[1]) for p in pts], color="#222", lw=0.75)
        elif typ == "POLYLINE":
            pts = list(entity.vertices)
            if pts: ax.plot([tx(p.dxf.location.x) for p in pts], [ty(p.dxf.location.y) for p in pts], color="#222", lw=0.75)
        elif typ == "ARC":
            c = entity.dxf.center
            ax.add_patch(Arc((tx(c.x), ty(c.y)), 2 * entity.dxf.radius * scale, 2 * entity.dxf.radius * scale, angle=0, theta1=entity.dxf.start_angle, theta2=entity.dxf.end_angle, color="#222", lw=0.75))
        elif typ == "CIRCLE":
            c = entity.dxf.center
            ax.add_patch(Circle((tx(c.x), ty(c.y)), entity.dxf.radius * scale, fill=False, color="#222", lw=0.75))
        elif typ == "ELLIPSE":
            c = entity.dxf.center; major = entity.dxf.major_axis
            w = 2 * math.hypot(major.x, major.y) * scale
            h = w * math.sqrt(max(0.0, 1.0 - entity.dxf.ratio ** 2))
            angle = math.degrees(math.atan2(major.y, major.x))
            ax.add_patch(Ellipse((tx(c.x), ty(c.y)), w, h, angle=angle, fill=False, color="#222", lw=0.75))
        elif typ == "SPLINE":
            pts = list(entity.flattening(0.5))
            if pts: ax.plot([tx(p.x) for p in pts], [ty(p.y) for p in pts], color="#222", lw=0.75)
    except Exception:
        pass


def _render_preview(item, normalized_path, metric):
    doc = ezdxf.readfile(str(normalized_path))
    block = doc.blocks.get(item["id"])
    entities = list(block)
    rect = metric["normalized_bbox_mm"]
    width, depth = rect[2] - rect[0], rect[3] - rect[1]
    pad = 100.0
    fig = plt.figure(figsize=(5, 5), dpi=160)
    ax = fig.add_axes([0.08, 0.08, 0.84, 0.78])
    ax.set_xlim(rect[0] - pad, rect[2] + pad)
    ax.set_ylim(rect[1] - pad, rect[3] + pad)
    ax.set_aspect("equal")
    ax.set_axis_off()
    for entity in entities:
        _draw(ax, entity, 1.0, 0.0, 0.0)
    ax.set_title(f"{item['id']}\n{width:.0f} × {depth:.0f} mm", fontsize=8)
    out = PREVIEWS / f"{item['id']}.png"
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)
    return out


def _contact_sheet(entries):
    cols, rows = 5, math.ceil(len(entries) / 5)
    fig, axes = plt.subplots(rows, cols, figsize=(20, rows * 4), dpi=160)
    axes = list(axes.flat)
    cell_w, cell_h = 2800.0, 2800.0
    for idx, (item, metric, path) in enumerate(entries):
        ax = axes[idx]
        ax.set_xlim(0, cell_w); ax.set_ylim(0, cell_h); ax.set_aspect("equal"); ax.axis("off")
        rect = metric["normalized_bbox_mm"]
        width, depth = rect[2] - rect[0], rect[3] - rect[1]
        scale = min((cell_w - 220) / max(width, 1), (cell_h - 220) / max(depth, 1))
        ox = (cell_w - width * scale) / 2 - rect[0] * scale
        oy = (cell_h - depth * scale) / 2 - rect[1] * scale
        doc = ezdxf.readfile(str(path)); block = doc.blocks.get(item["id"])
        for entity in block:
            _draw(ax, entity, scale, ox, oy)
        ax.set_title(f"{item['id']}\n{width:.0f}×{depth:.0f} mm\n{item['source_repo']}", fontsize=6)
    for ax in axes[len(entries):]: ax.axis("off")
    fig.suptitle("A0.3 Normalized Source Plan Blocks — no design resizing", fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out = PREVIEWS / "contact_sheet_v01.png"
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)
    return out


def build():
    selection = json.loads(SELECTION.read_text())["samples"]
    a02 = json.loads(A02_REPORT.read_text())
    a02_lookup = {(item["repo"], item["source_file"]): item for item in a02["samples"]}
    entries = []
    issues = []
    normalized_docs = []
    for item in selection:
        raw_path = ROOT / item["raw_file"]
        if sha(raw_path) != item["source_sha256"]:
            raise RuntimeError(f"raw source SHA changed: {raw_path}")
        source = source_doc(item)
        raw_entities = list(flatten_entities(source))
        raw_entities = [e for e in raw_entities if e.dxftype() in KEEP_TYPES]
        if not raw_entities:
            raise RuntimeError(f"no supported geometry: {item['id']}")
        units = a02_lookup[(item["source_repo"], item["source_file"])]
        factor = units["unit_scale_to_mm"]
        if factor is None:
            raise RuntimeError(f"source unit unresolved: {item['id']}")
        scaled = []
        for entity in raw_entities:
            c = entity.copy()
            c.transform(Matrix44.scale(factor, factor, factor))
            scaled.append(c)
        source_bbox = _bbox(scaled)
        base, convention = _base_point(item["category"], source_bbox)
        normalized_doc = ezdxf.new("R2018", setup=True)
        normalized_doc.header["$INSUNITS"] = 4
        _add_layers(normalized_doc)
        block = normalized_doc.blocks.new(name=item["id"])
        transformed = []
        for entity in scaled:
            c = entity.copy()
            c.translate(-base[0], -base[1], 0.0)
            c.dxf.layer = "LIB-ANNOTATION" if c.dxftype() in {"TEXT", "MTEXT"} else "LIB-PLAN"
            c.dxf.color = 256
            block.add_entity(c)
            transformed.append(c)
        normalized_bbox = _bbox(transformed)
        normalized_doc.saveas(str(NORMALIZED / f"{item['id']}.dxf"))
        normalized_path = NORMALIZED / f"{item['id']}.dxf"
        # Read-back is part of QA.
        readback = ezdxf.readfile(str(normalized_path))
        readback_block = readback.blocks.get(item["id"])
        readback_bbox = _bbox(list(readback_block))
        source_dims = [source_bbox[2] - source_bbox[0], source_bbox[3] - source_bbox[1]]
        norm_dims = [readback_bbox[2] - readback_bbox[0], readback_bbox[3] - readback_bbox[1]]
        bbox_delta = max(abs(a - b) for a, b in zip(source_dims, norm_dims))
        preview = _render_preview(item, normalized_path, {"normalized_bbox_mm": readback_bbox})
        metric = a02_lookup[(item["source_repo"], item["source_file"])]
        qa_status = "PASS" if bbox_delta <= 0.01 and not metric["xref"] and not metric["ole"] and not metric["proxy_or_unsupported_types"] else "FAIL"
        if qa_status != "PASS": issues.append({"id": item["id"], "reason": "readback QA"})
        manifest_item = {
            "id": item["id"], "category": item["category"], "block_name": item["id"],
            "source_repo": item["source_repo"], "source_file": item["source_file"], "source_url": item["source_url"],
            "source_raw_file": item["raw_file"], "source_sha256": item["source_sha256"],
            "source_units": metric["units"], "unit_scale_to_mm": factor,
            "source_bbox_mm": source_bbox, "normalized_bbox_mm": readback_bbox,
            "nominal_product_geometry_mm": metric.get("nominal_product_geometry_mm"),
            "actual_drawn_bbox_mm": metric.get("actual_drawn_bbox_mm"),
            "base_point_convention": convention, "base_point_mm": base, "normalized_base_point_mm": [0.0, 0.0],
            "entity_count": len(list(readback_block)), "layer_count": len(set(e.dxf.layer for e in readback_block)),
            "xref": metric["xref"], "ole": metric["ole"], "proxy": bool(metric["proxy_or_unsupported_types"]),
            "geometry_scaled": False, "normalized_units": "mm", "bbox_delta_mm": bbox_delta,
            "normalized_file": str(normalized_path.relative_to(LIB)), "preview_file": str(preview.relative_to(LIB)),
            "license_gate": item["license_gate"], "qa_status": qa_status,
        }
        entries.append((item, manifest_item, normalized_path))
    compiled = ezdxf.new("R2018", setup=True); compiled.header["$INSUNITS"] = 4; _add_layers(compiled)
    for item, metric, path in entries:
        source_doc_norm = ezdxf.readfile(str(path)); src_block = source_doc_norm.blocks.get(item["id"]); dst_block = compiled.blocks.new(item["id"])
        for entity in src_block:
            dst_block.add_entity(entity.copy())
    compiled.saveas(str(COMPILED_FILE))
    contact_sheet = _contact_sheet(entries)
    # compiled readback
    compiled_readback = ezdxf.readfile(str(COMPILED_FILE))
    report = {
        "status": "PASS" if not issues else "FAIL", "version": "v0.1", "geometry_scaled": False,
        "block_count": len(entries), "issues": issues,
        "raw_sources_sha_unchanged": all(sha(ROOT / item["raw_file"]) == item["source_sha256"] for item, _, _ in entries),
        "compiled_block_count": sum(1 for name in [item["id"] for item,_,_ in entries] if name in compiled_readback.blocks),
        "contact_sheet": str(contact_sheet.relative_to(ROOT)),
        "blocks": [metric for _, metric, _ in entries],
    }
    BLOCK_MANIFEST.write_text(json.dumps({"version":"v0.1","geometry_scaled":False,"blocks":[metric for _,metric,_ in entries]}, ensure_ascii=False, indent=2) + "\n")
    QA_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "blocks": len(entries), "compiled": str(COMPILED_FILE), "issues": issues}, ensure_ascii=False, indent=2))
    if report["status"] != "PASS": raise SystemExit(1)


if __name__ == "__main__":
    build()
