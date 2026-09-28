#!/usr/bin/env python3
"""Audit temporary 2D CAD block samples and build a uniform contact sheet.

This tool reads a temporary download manifest and writes only QC evidence into
the project. It never copies source blocks into the formal library.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Ellipse, Rectangle
from matplotlib.lines import Line2D
from ezdxf import bbox


ROOT = Path(__file__).resolve().parent.parent
QC = ROOT / "qc"

LICENSE_GATE = {
    "GSStnb/dxfBlocks": "CONFLICT",
    "uncreatednet/DXF-library": "UNKNOWN",
    "Lendres/CAD-Support-Files": "MIT",
}


def _unit_info(doc, source, category):
    code = doc.header.get("$INSUNITS")
    if code == 1:
        return "inch", 25.4, "header:$INSUNITS=1"
    if code == 4:
        return "mm", 1.0, "header:$INSUNITS=4"
    stem = source.lower()
    native_max = 0.0
    try:
        ext = bbox.extents(list(doc.modelspace()))
        native_max = max(abs(ext.extmax.x - ext.extmin.x), abs(ext.extmax.y - ext.extmin.y))
    except Exception:
        pass
    if native_max < 10:
        return "meter_inferred", 1000.0, "sub-10 native footprint implies meters"
    if any(token in stem for token in ["inch", "ft", "king", "queen", "toilet", "washer", "refridgerator", "desk", "sofa"]):
        return "inch_inferred", 25.4, "filename/known imperial source"
    if any(token in stem for token in ["600", "1200", "1500", "1800", "2200", "2500"]):
        return "mm_inferred", 1.0, "dimension token / native footprint implies mm"
    return "unknown", None, "no reliable unit evidence"


def _nominal_product_geometry(source):
    """Use only explicit dimension tokens; never invent nominal sizes."""
    stem = Path(source).stem
    match = re.search(r"(?<!\d)(\d{3,4})\s*[xX]\s*(\d{2,4})(?!\d)", stem)
    if match:
        a, b = float(match.group(1)), float(match.group(2))
        if a <= 300 and b <= 300:
            return [a * 10.0, b * 10.0], "filename_dimension_cm"
        return [a, b], "filename_dimension_mm"
    match = re.search(r"(?<!\d)(\d{2})\s*[xX]\s*(\d{2})(?!\d)", stem)
    if match and any(token in stem.lower() for token in ["inch", "ft", "table", "desk", "shower"]):
        return [float(match.group(1)) * 25.4, float(match.group(2)) * 25.4], "filename_dimension_inch"
    return None, "not_stated"


def _entity_bbox(entity):
    try:
        ext = bbox.extents([entity])
        if ext.has_data:
            return [float(ext.extmin.x), float(ext.extmin.y), float(ext.extmax.x), float(ext.extmax.y)]
    except Exception:
        pass
    return None


def _iter_render_entities(doc):
    for entity in doc.modelspace():
        if entity.dxftype() == "INSERT":
            try:
                yield from entity.virtual_entities()
            except Exception:
                yield entity
        else:
            yield entity


def _collect_metrics(doc, source, category, repo):
    entities = list(doc.modelspace())
    boxes = [_entity_bbox(e) for e in entities]
    boxes = [b for b in boxes if b]
    if boxes:
        minx = min(b[0] for b in boxes); miny = min(b[1] for b in boxes)
        maxx = max(b[2] for b in boxes); maxy = max(b[3] for b in boxes)
        width_native, depth_native = maxx - minx, maxy - miny
        center_native = [(minx + maxx) / 2, (miny + maxy) / 2]
    else:
        minx = miny = maxx = maxy = 0.0
        width_native = depth_native = 0.0
        center_native = [0.0, 0.0]
    units, factor, unit_evidence = _unit_info(doc, source, category)
    width_mm = width_native * factor if factor else None
    depth_mm = depth_native * factor if factor else None
    base = doc.header.get("$INSBASE") or (0.0, 0.0, 0.0)
    base = [float(base[0]), float(base[1]), float(base[2])]
    far_from_origin = max(abs(center_native[0]), abs(center_native[1])) > max(width_native, depth_native, 1.0) * 10
    types = Counter(e.dxftype() for e in entities)
    layers = Counter(e.dxf.layer for e in entities)
    special = sorted({
        e.dxftype() for e in entities
        if e.dxftype() in {"ACAD_PROXY_ENTITY", "OLE2FRAME", "IMAGE", "3DSOLID", "BODY", "REGION", "MESH", "XLINE"}
    })
    has_xref = any(getattr(block, "is_xref", False) for block in doc.blocks)
    planar = True
    z_values = []
    for entity in entities:
        for attr in ("start", "end", "center", "insert"):
            if entity.dxf.hasattr(attr):
                p = entity.dxf.get(attr)
                if hasattr(p, "z"):
                    z_values.append(float(p.z))
    if z_values and max(z_values) - min(z_values) > 0.01:
        planar = False
    unsupported = bool(special)
    two_d_plan = bool(boxes) and planar and not unsupported
    # A single 2D outline with manageable entity count is suitable as a legend.
    plan_suitable = two_d_plan and width_mm is not None and depth_mm is not None and width_mm > 50 and depth_mm > 50
    legal = LICENSE_GATE.get(repo, "UNKNOWN")
    unit_confidence = "high" if units in {"inch", "mm"} else ("medium" if factor else "low")
    nominal_mm, nominal_basis = _nominal_product_geometry(source)
    if not plan_suitable or has_xref or special or factor is None or width_mm is None or depth_mm is None:
        classification = "REJECT_TECHNICAL"
    else:
        needs_normalization = (
            units != "mm" or far_from_origin or len(layers) > 1
            or any(not math.isclose(v, round(v), abs_tol=0.01) for v in [width_mm, depth_mm])
        )
        classification = "NORMALIZE" if needs_normalization else "APPROVED_AS_IS"
    reject_reasons = []
    if not two_d_plan: reject_reasons.append("not a clean planar 2D symbol")
    if has_xref: reject_reasons.append("XREF present")
    if special: reject_reasons.append("unsupported/proxy-like entity type")
    if factor is None: reject_reasons.append("units unresolved")
    if far_from_origin: reject_reasons.append("geometry far from origin")
    return {
        "source_file": source,
        "category": category,
        "dxf_or_dwg": Path(source).suffix.lower().lstrip("."),
        "units": units,
        "unit_scale_to_mm": factor,
        "unit_evidence": unit_evidence,
        "bbox_native": [minx, miny, maxx, maxy],
        "width_depth_native": [width_native, depth_native],
        "actual_width_depth_mm": [width_mm, depth_mm],
        "actual_drawn_bbox_mm": [width_mm, depth_mm],
        "nominal_product_geometry_mm": nominal_mm,
        "nominal_geometry_basis": nominal_basis,
        "unit_confidence": unit_confidence,
        "base_point_native": base,
        "far_from_origin": far_from_origin,
        "modelspace_entity_count": len(entities),
        "entity_types": dict(types),
        "block_count": len(list(doc.blocks)),
        "layer_count": len(layers),
        "layers": dict(layers),
        "xref": has_xref,
        "ole": "OLE2FRAME" in special,
        "proxy_or_unsupported_types": special,
        "planar_z": planar,
        "two_d_plan_available": two_d_plan,
        "plan_legend_suitable": plan_suitable,
        "license_gate": legal,
        "license_is_informational_only": True,
        "classification": classification,
        "reject_or_normalize_reasons": reject_reasons,
    }


def _draw_entity(ax, entity, scale, tx, ty, color="#222", lw=0.7):
    typ = entity.dxftype()
    def x(v): return (v - tx) * scale
    def y(v): return (v - ty) * scale
    try:
        if typ == "LINE":
            ax.plot([x(entity.dxf.start.x), x(entity.dxf.end.x)], [y(entity.dxf.start.y), y(entity.dxf.end.y)], color=color, lw=lw)
        elif typ == "LWPOLYLINE":
            pts = list(entity.get_points("xy"))
            if pts:
                if entity.closed: pts.append(pts[0])
                ax.plot([x(p[0]) for p in pts], [y(p[1]) for p in pts], color=color, lw=lw)
        elif typ == "ARC":
            c = entity.dxf.center
            ax.add_patch(Arc((x(c.x), y(c.y)), 2 * entity.dxf.radius * scale, 2 * entity.dxf.radius * scale,
                             angle=0, theta1=entity.dxf.start_angle, theta2=entity.dxf.end_angle, color=color, lw=lw))
        elif typ == "CIRCLE":
            c = entity.dxf.center
            ax.add_patch(Circle((x(c.x), y(c.y)), entity.dxf.radius * scale, fill=False, color=color, lw=lw))
        elif typ == "ELLIPSE":
            c = entity.dxf.center
            major = entity.dxf.major_axis
            width = 2 * math.hypot(major.x, major.y) * scale
            height = width * math.sqrt(max(0.0, 1.0 - entity.dxf.ratio ** 2))
            angle = math.degrees(math.atan2(major.y, major.x))
            ax.add_patch(Ellipse((x(c.x), y(c.y)), width, height, angle=angle, fill=False, color=color, lw=lw))
        elif typ == "SPLINE":
            points = list(entity.flattening(0.5))
            if points: ax.plot([x(p.x) for p in points], [y(p.y) for p in points], color=color, lw=lw)
        elif typ == "POLYLINE":
            pts = list(entity.vertices)
            if pts:
                ax.plot([x(p.dxf.location.x) for p in pts], [y(p.dxf.location.y) for p in pts], color=color, lw=lw)
    except Exception:
        return


def render_sample(doc, metric, ax, cell_w_mm, cell_h_mm, title, color):
    bbox_native = metric["bbox_native"]
    factor = metric["unit_scale_to_mm"] or 1.0
    width_mm = metric["width_depth_native"][0] * factor
    depth_mm = metric["width_depth_native"][1] * factor
    pad = 80.0
    scale = min((cell_w_mm - 2 * pad) / max(width_mm, 1.0), (cell_h_mm - 2 * pad) / max(depth_mm, 1.0))
    origin_x = (cell_w_mm - width_mm * scale) / 2 - bbox_native[0] * factor * scale
    origin_y = (cell_h_mm - depth_mm * scale) / 2 - bbox_native[1] * factor * scale
    for entity in _iter_render_entities(doc):
        # transform helper expects native coordinate and native scale; fold unit conversion into scale.
        _draw_entity(ax, entity, scale * factor, bbox_native[0], bbox_native[1], color="#222", lw=0.8)
    # reset transformed content into local cell by translating artists through an axes transform is
    # cumbersome, so use native coordinate limits per cell with identical scale instead.


def make_contact_sheet(samples):
    cols, rows = 5, math.ceil(len(samples) / 5)
    fig, axes = plt.subplots(rows, cols, figsize=(20, rows * 4.0), dpi=160)
    axes = list(axes.flat) if hasattr(axes, "flat") else [axes]
    # Use a common mm scale: every cell has identical 2,800 x 2,800 mm limits.
    cell_mm = 2800.0
    for idx, (sample, metric) in enumerate(samples):
        ax = axes[idx]
        ax.set_xlim(0, cell_mm); ax.set_ylim(0, cell_mm); ax.set_aspect("equal"); ax.axis("off")
        path = Path(sample["converted_path"] if "converted_path" in sample else sample["local_path"])
        try: doc = ezdxf.readfile(str(path))
        except Exception: doc = None
        if doc:
            bb = metric["bbox_native"]
            factor = metric["unit_scale_to_mm"] or 1.0
            width = metric["width_depth_native"][0] * factor
            depth = metric["width_depth_native"][1] * factor
            scale = min((cell_mm - 220) / max(width, 1.0), (cell_mm - 220) / max(depth, 1.0))
            # Local transform in mm coordinates.
            ox = (cell_mm - width * scale) / 2 - bb[0] * factor * scale
            oy = (cell_mm - depth * scale) / 2 - bb[1] * factor * scale
            for entity in _iter_render_entities(doc):
                # Convert each entity via a temporary local affine by drawing with native coordinates.
                typ = entity.dxftype()
                try:
                    if typ == "LINE":
                        ax.plot([entity.dxf.start.x * factor * scale + ox, entity.dxf.end.x * factor * scale + ox],
                                [entity.dxf.start.y * factor * scale + oy, entity.dxf.end.y * factor * scale + oy], color="#222", lw=0.8)
                    elif typ == "LWPOLYLINE":
                        pts=list(entity.get_points("xy"));
                        if pts:
                            if entity.closed: pts.append(pts[0])
                            ax.plot([p[0]*factor*scale+ox for p in pts],[p[1]*factor*scale+oy for p in pts],color="#222",lw=0.8)
                    elif typ == "ARC":
                        c=entity.dxf.center
                        ax.add_patch(Arc((c.x*factor*scale+ox,c.y*factor*scale+oy),2*entity.dxf.radius*factor*scale,2*entity.dxf.radius*factor*scale,angle=0,theta1=entity.dxf.start_angle,theta2=entity.dxf.end_angle,color="#222",lw=0.8))
                    elif typ == "CIRCLE":
                        c=entity.dxf.center
                        ax.add_patch(Circle((c.x*factor*scale+ox,c.y*factor*scale+oy),entity.dxf.radius*factor*scale,fill=False,color="#222",lw=0.8))
                    elif typ == "ELLIPSE":
                        c=entity.dxf.center; major=entity.dxf.major_axis; w=2*math.hypot(major.x,major.y)*factor*scale; h=w*math.sqrt(max(0,1-entity.dxf.ratio**2)); angle=math.degrees(math.atan2(major.y,major.x)); ax.add_patch(Ellipse((c.x*factor*scale+ox,c.y*factor*scale+oy),w,h,angle=angle,fill=False,color="#222",lw=0.8))
                    elif typ == "SPLINE":
                        pts=list(entity.flattening(0.5)); ax.plot([p.x*factor*scale+ox for p in pts],[p.y*factor*scale+oy for p in pts],color="#222",lw=0.8)
                    elif typ == "POLYLINE":
                        pts=list(entity.vertices); ax.plot([p.dxf.location.x*factor*scale+ox for p in pts],[p.dxf.location.y*factor*scale+oy for p in pts],color="#222",lw=0.8)
                except Exception:
                    pass
        status=metric["classification"]
        color={"APPROVED_AS_IS":"#2a9d8f","NORMALIZE":"#e9c46a","REJECT_TECHNICAL":"#e76f51"}.get(status,"#777")
        for spine in ax.spines.values(): spine.set_visible(True); spine.set_color(color); spine.set_linewidth(3)
        source_name=f"{sample['repo'].split('/')[0]} / {Path(sample['path']).name}"
        dims=metric["actual_width_depth_mm"]
        dim_txt=f"{dims[0]:.0f}×{dims[1]:.0f} mm" if dims[0] is not None else "unit unknown"
        ax.set_title(f"#{idx+1} {sample['category']}\n{source_name}\n{dim_txt} · {status}",fontsize=7,color="#111")
    for ax in axes[len(samples):]: ax.axis("off")
    fig.suptitle("A0.2R Technical-only 2D CAD Plan Symbol Contact Sheet — common scale / mm footprint",fontsize=16)
    fig.tight_layout(rect=[0,0,1,0.97])
    out=QC/"a0_2_cad_contact_sheet.png";fig.savefig(out,dpi=160,facecolor="white");plt.close(fig);return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--manifest",default="/tmp/a0_2_download_manifest.json");args=ap.parse_args()
    manifest=json.loads(Path(args.manifest).read_text()); rows=[]; pairs=[]
    for sample in manifest["samples"]:
        path=sample.get("converted_path",sample["local_path"])
        doc=ezdxf.readfile(path); metric=_collect_metrics(doc,sample["path"],sample["category"],sample["repo"])
        metric.update({"repo":sample["repo"],"path":sample["path"],"url":sample.get("url"),"local_path":sample["local_path"],"converted_path":sample.get("converted_path")})
        rows.append(metric);pairs.append((sample,metric))
    contact=make_contact_sheet(pairs)
    report={"date":"2026-09-26","sample_count":len(rows),"scope":"temporary sample audit only; no formal library import","classification_basis":"technical_only","license_is_informational_only":True,"samples":rows,"contact_sheet":str(contact.relative_to(ROOT)),"license_notes":{"GSStnb/dxfBlocks":"API metadata CC0-1.0 conflicts with README CC BY-NC-SA-4.0; metadata retained, does not affect technical classification","uncreatednet/DXF-library":"no repository license; metadata retained, does not affect technical classification","Lendres/CAD-Support-Files":"MIT repo license; metadata retained, does not affect technical classification"}}
    out=QC/"a0_2_cad_sample_report.json";out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    md=QC/"a0_2_cad_sample_report.md"
    lines=["# A0.2R Technical-only 2D CAD Block Sample Audit","","No formal library files were added. Samples remain in `/tmp/a0_2_cad_samples`.","","Classification is technical-only; license is metadata and does not affect APPROVED_AS_IS / NORMALIZE / REJECT_TECHNICAL.","",f"Contact sheet: `{contact.relative_to(ROOT)}`","", "|#|source|category|units|nominal W×D mm|actual bbox W×D mm|bbox/layers|base/far|XREF/OLE/proxy|plan legend|classification|", "|-:|---|---|---|---:|---:|---|---|---|---|---|"]
    for i,(s,m) in enumerate(zip(manifest['samples'],rows),1):
        actual=m['actual_drawn_bbox_mm']; actual='×'.join(f'{x:.0f}' for x in actual) if actual[0] is not None else 'unknown'
        nominal=m['nominal_product_geometry_mm']; nominal='×'.join(f'{x:.0f}' for x in nominal) if nominal and nominal[0] is not None else 'not stated'
        lines.append(f"|{i}|{s['repo']}:{s['path']}|{s['category']}|{m['units']}|{nominal}|{actual}|{m['bbox_native']} / {m['layer_count']} layers|{m['base_point_native']} / {m['far_from_origin']}|{m['xref']}/{m['ole']}/{m['proxy_or_unsupported_types']}|{m['plan_legend_suitable']}|**{m['classification']}**|")
    lines += ["", "## Classification rules", "", "- `APPROVED_AS_IS`: clean 2D plan, reliable units/base point, no technical cleanup required.", "- `NORMALIZE`: technically usable plan; unit conversion, base-point relocation, layer cleanup, block wrapping, or minor geometry cleanup is required.", "- `REJECT_TECHNICAL`: geometry/scale/meaning is genuinely unsuitable or cannot be normalized safely.", "- License is recorded separately and never changes this technical classification.", "", "## No formal import", "", "No V02/V03 CAD, canonical data, or furniture library was modified."]
    md.write_text('\n'.join(lines)+'\n')
    print(json.dumps({"report":str(out),"markdown":str(md),"contact_sheet":str(contact),"counts":dict(Counter(m['classification'] for m in rows))},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
