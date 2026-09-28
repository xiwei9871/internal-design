#!/usr/bin/env python3
"""Build A0.4 design-standard plan legends from A0.3 normalized source blocks."""
from __future__ import annotations

import json
import math
from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Ellipse
from ezdxf import bbox


ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "assets/cad_library"
SRC_MANIFEST = LIB / "manifests/block_manifest.json"
STANDARD = LIB / "standard"
NORMALIZED = STANDARD / "normalized"
PREVIEWS = STANDARD / "previews"
MANIFESTS = STANDARD / "manifests"
COMPILED = STANDARD / "compiled"
QA_REPORT = MANIFESTS / "design_legend_qa_v01.json"

for folder in (NORMALIZED, PREVIEWS, MANIFESTS, COMPILED):
    folder.mkdir(parents=True, exist_ok=True)

SPECS = [
    ("BED_1800x2100_PLAN", "bed", "SRC_GS_BED_KING_PLAN", [1800, 2100], False, "bed head-center"),
    ("BED_1500x2000_PLAN", "bed", "SRC_GS_BED_QUEEN_PLAN", [1500, 2000], False, "bed head-center"),
    ("BED_900x2000_PLAN", "bed", "SRC_GS_BED_SINGLE_PLAN", [900, 2000], False, "bed head-center"),
    ("SOFA_3S_2200x900_PLAN", "sofa", "SRC_GS_SOFA_3S_PLAN", [2200, 900], False, "sofa back-center"),
    ("SOFA_2S_1800x850_PLAN", "sofa", "SRC_GS_SOFA_2S_PLAN", [1800, 850], False, "sofa back-center"),
    ("LOUNGE_CHAIR_900x900_PLAN", "lounge_chair", "SRC_GS_OFFICE_CHAIR_PLAN", [900, 900], True, "semantic proxy from office chair; center"),
    ("DESK_1700x800_PLAN", "desk", "SRC_GS_DESK_PLAN", [1700, 800], False, "desk center"),
    ("DINING_TABLE_1500x600_PLAN", "dining_table", "SRC_GS_DINING_TABLE_PLAN", [1500, 600], False, "table center"),
    ("DINING_CHAIR_450x500_PLAN", "dining_chair", "SRC_GS_DINING_CHAIR_PLAN", [450, 500], False, "chair center"),
    ("WC_STD_450x700_PLAN", "wc", "SRC_GS_WC_PLAN", [450, 700], False, "WC rear-center / wall connection side"),
    ("VANITY_600x500_PLAN", "vanity", "SRC_UNC_VANITY_600_PLAN", [600, 500], False, "vanity center"),
    ("VANITY_900x500_PLAN", "vanity", "SRC_UNC_VANITY_600_PLAN", [900, 500], False, "vanity center"),
    ("SHOWER_900x1200_PLAN", "shower", "SRC_GS_SHOWER_PLAN", [900, 1200], False, "shower center"),
    ("WARDROBE_D600_PLAN", "wardrobe", "SRC_GS_WARDROBE_PLAN", None, False, "wardrobe back-left; source width retained"),
    ("WASHER_600x650_PLAN", "washer", "SRC_GS_WASHER_PLAN", [600, 650], False, "appliance back-left"),
    ("DRYER_600x650_PLAN", "dryer", "SRC_GS_WASHER_PLAN", [600, 650], True, "semantic proxy from washer; appliance back-left"),
]


def _bbox(entities):
    ext = bbox.extents(list(entities))
    if not ext.has_data:
        raise ValueError("no geometry")
    return [float(ext.extmin.x), float(ext.extmin.y), float(ext.extmax.x), float(ext.extmax.y)]


def _sample_arc(entity, count=32):
    c = entity.dxf.center; radius = entity.dxf.radius
    start = math.radians(entity.dxf.start_angle); end = math.radians(entity.dxf.end_angle)
    if end < start: end += 2 * math.pi
    return [(c.x + radius * math.cos(start + (end - start) * i / count),
             c.y + radius * math.sin(start + (end - start) * i / count)) for i in range(count + 1)]


def _sample_circle(entity, count=64):
    c = entity.dxf.center; r = entity.dxf.radius
    return [(c.x + r * math.cos(2 * math.pi * i / count), c.y + r * math.sin(2 * math.pi * i / count)) for i in range(count + 1)]


def _sample_ellipse(entity, count=64):
    c = entity.dxf.center; major = entity.dxf.major_axis; ratio = entity.dxf.ratio
    length = math.hypot(major.x, major.y); ux, uy = major.x / length, major.y / length
    vx, vy = -uy, ux
    return [(c.x + length * math.cos(2 * math.pi * i / count) * ux + length * ratio * math.sin(2 * math.pi * i / count) * vx,
             c.y + length * math.cos(2 * math.pi * i / count) * uy + length * ratio * math.sin(2 * math.pi * i / count) * vy) for i in range(count + 1)]


def _source_polylines(block):
    for entity in block:
        typ = entity.dxftype()
        if typ == "LINE":
            yield [(entity.dxf.start.x, entity.dxf.start.y), (entity.dxf.end.x, entity.dxf.end.y)], False
        elif typ == "LWPOLYLINE":
            pts = [(x, y) for x, y, *_ in entity.get_points("xy")]
            if pts: yield pts, bool(entity.closed)
        elif typ == "POLYLINE":
            pts = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
            if pts: yield pts, bool(entity.is_polygon_mesh)
        elif typ == "ARC":
            yield _sample_arc(entity), False
        elif typ == "CIRCLE":
            yield _sample_circle(entity), True
        elif typ == "ELLIPSE":
            yield _sample_ellipse(entity), True
        elif typ == "SPLINE":
            pts = [(p.x, p.y) for p in entity.flattening(0.5)]
            if pts: yield pts, False


def _make_block(doc, name, source_block, sx, sy):
    block = doc.blocks.new(name=name)
    for pts, closed in _source_polylines(source_block):
        scaled = [(x * sx, y * sy) for x, y in pts]
        if len(scaled) == 2:
            block.add_line(scaled[0], scaled[1], dxfattribs={"layer": "LIB-PLAN"})
        else:
            block.add_lwpolyline(scaled, close=closed, dxfattribs={"layer": "LIB-PLAN"})
    return block


def _render_block(path, block_name, out, title):
    doc = ezdxf.readfile(str(path)); block = doc.blocks.get(block_name); rect = _bbox(list(block)); w, h = rect[2] - rect[0], rect[3] - rect[1]
    fig = plt.figure(figsize=(5,5),dpi=160); ax=fig.add_axes([.08,.08,.84,.78]); ax.set_xlim(rect[0]-100,rect[2]+100);ax.set_ylim(rect[1]-100,rect[3]+100);ax.set_aspect('equal');ax.axis('off')
    for pts,closed in _source_polylines(block):
        ax.plot([p[0] for p in pts],[p[1] for p in pts],color='#222',lw=.8)
        if closed: ax.plot([pts[-1][0],pts[0][0]],[pts[-1][1],pts[0][1]],color='#222',lw=.8)
    ax.set_title(f"{title}\n{w:.0f} × {h:.0f} mm",fontsize=8);fig.savefig(out,dpi=160,facecolor='white');plt.close(fig)


def build():
    source_manifest = json.loads(SRC_MANIFEST.read_text())
    source_lookup = {item["id"]: item for item in source_manifest["blocks"]}
    entries=[]; issues=[]
    normalized_docs={}
    for legend_id, category, derived_from, target, semantic_proxy, convention in SPECS:
        src = source_lookup[derived_from]
        source_path = LIB / src["normalized_file"]
        source_doc = ezdxf.readfile(str(source_path)); source_block = source_doc.blocks.get(derived_from)
        source_rect = list(src["normalized_bbox_mm"]); source_w = source_rect[2]-source_rect[0]; source_h=source_rect[3]-source_rect[1]
        if target is None:
            target = [source_w, 600.0]
        sx, sy = target[0]/source_w, target[1]/source_h
        doc = ezdxf.new("R2018", setup=True); doc.header["$INSUNITS"] = 4
        for layer_name, color in {"LIB-PLAN":7,"LIB-ANNOTATION":8}.items(): doc.layers.add(layer_name,color=color)
        block = _make_block(doc, legend_id, source_block, sx, sy)
        path = NORMALIZED / f"{legend_id}.dxf"; doc.saveas(str(path))
        readback=ezdxf.readfile(str(path)); rb=_bbox(list(readback.blocks.get(legend_id))); target_delta=max(abs(a-b) for a,b in zip([rb[2]-rb[0],rb[3]-rb[1]],target))
        preview=PREVIEWS/f"{legend_id}.png"; _render_block(path,legend_id,preview,legend_id)
        item={
            "id":legend_id,"category":category,"derived_from":derived_from,"semantic_proxy":semantic_proxy,"proxy_reason":("source block is a semantic proxy; geometry is footprint-only" if semantic_proxy else None),
            "source_bbox_mm":source_rect,"design_target_bbox_mm":target,"normalized_bbox_mm":rb,
            "scale_x":sx,"scale_y":sy,"unit_conversion_applied":False,"geometry_scaled":True,"design_geometry_rescaled":True,
            "base_point_convention":convention,"normalized_base_point_mm":[0.0,0.0],"entity_count":len(list(readback.blocks.get(legend_id))),"layer_count":len(set(e.dxf.layer for e in readback.blocks.get(legend_id))),
            "xref":False,"ole":False,"proxy":False,"normalized_units":"mm","target_bbox_delta_mm":target_delta,"normalized_file":str(path.relative_to(STANDARD)),"preview_file":str(preview.relative_to(STANDARD)),
            "qa_status":"PASS" if target_delta<=0.01 else "FAIL",
        }
        if item["qa_status"]!="PASS": issues.append({"id":legend_id,"reason":"target bbox delta"})
        entries.append(item)
    compiled=ezdxf.new("R2018",setup=True); compiled.header["$INSUNITS"]=4; compiled.layers.add("LIB-PLAN",color=7);compiled.layers.add("LIB-ANNOTATION",color=8)
    for item in entries:
        srcdoc=ezdxf.readfile(str(STANDARD/"normalized"/f"{item['id']}.dxf")); srcblock=srcdoc.blocks.get(item["id"]); dst=compiled.blocks.new(item["id"])
        for e in srcblock: dst.add_entity(e.copy())
    compiled.saveas(str(COMPILED/"residential_design_legends_v01.dxf"))
    # contact sheet using the same normalized block drawings
    cols,rows=4,math.ceil(len(entries)/4); fig,axes=plt.subplots(rows,cols,figsize=(16,rows*3.7),dpi=160);axes=list(axes.flat)
    for i,item in enumerate(entries):
        ax=axes[i];ax.axis('off');rect=item['normalized_bbox_mm'];w,h=rect[2]-rect[0],rect[3]-rect[1];ax.set_xlim(rect[0]-100,rect[2]+100);ax.set_ylim(rect[1]-100,rect[3]+100);ax.set_aspect('equal')
        doc=ezdxf.readfile(str(STANDARD/"normalized"/f"{item['id']}.dxf"));
        for pts,closed in _source_polylines(doc.blocks.get(item['id'])):
            ax.plot([p[0] for p in pts],[p[1] for p in pts],color='#222',lw=.65)
            if closed: ax.plot([pts[-1][0],pts[0][0]],[pts[-1][1],pts[0][1]],color='#222',lw=.65)
        ax.set_title(f"{item['id']}\n{w:.0f}×{h:.0f} mm",fontsize=6)
    for ax in axes[len(entries):]: ax.axis('off')
    fig.suptitle('A0.4 Design Standard Legends v0.1 — target footprints',fontsize=15);fig.tight_layout(rect=[0,0,1,.97]);fig.savefig(PREVIEWS/'contact_sheet_v01.png',dpi=160,facecolor='white');plt.close(fig)
    QA_REPORT.write_text(json.dumps({"status":"PASS" if not issues else "FAIL","version":"v0.1","legend_count":len(entries),"issues":issues,"compiled_block_count":len(entries)},ensure_ascii=False,indent=2)+"\n")
    MANIFESTS.joinpath('design_legend_manifest_v01.json').write_text(json.dumps({"version":"v0.1","geometry_scaled":True,"legends":entries},ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":"PASS" if not issues else "FAIL","legends":len(entries),"issues":issues},ensure_ascii=False,indent=2))
    if issues: raise SystemExit(1)


if __name__=='__main__': build()
