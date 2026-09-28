#!/usr/bin/env python3
"""Render the structure-only DXF directly, with no synthetic wall overlay."""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf import bbox
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend


ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / "cad"
QC = ROOT / "qc"
INPUT = CAD / "structure_only_source_sync.dxf"
PNG = QC / "structure_only_cad.png"
PDF = QC / "structure_only_cad.pdf"
SIDECAR = QC / "structure_only_cad.render.json"
AX, AY = 1298172.0, -296458.0
HIDDEN_LAYERS = {"RC-GRILL"}
HIDDEN_TYPES = {"DIMENSION"}
OVERLAY_WORDS = ("休闲厅", "平台", "LANDING", "LOUNGE", "RAMP")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_value(entity) -> str:
    if entity.dxftype() in {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}:
        return str(entity.dxf.get("text", ""))
    return ""


def render():
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)
    doc = ezdxf.readfile(str(INPUT))
    msp = doc.modelspace()

    def keep(entity):
        if entity.dxf.layer in HIDDEN_LAYERS or entity.dxftype() in HIDDEN_TYPES:
            return False
        text = text_value(entity).upper()
        return not any(word.upper() in text for word in OVERLAY_WORDS)

    ext_types = {"LINE", "LWPOLYLINE", "CIRCLE", "ARC", "TEXT", "MTEXT", "POLYLINE", "INSERT"}
    plan = (AX - 3000, AY - 3000, AX + 22000, AY + 22000)
    in_plan = []
    for entity in msp:
        if not keep(entity) or entity.dxftype() not in ext_types:
            continue
        try:
            ext = bbox.extents([entity])
        except Exception:
            continue
        if (
            ext.extmax.x < plan[0] or ext.extmin.x > plan[2]
            or ext.extmax.y < plan[1] or ext.extmin.y > plan[3]
        ):
            continue
        in_plan.append(entity)
    ext = bbox.extents(in_plan)
    width = ext.extmax.x - ext.extmin.x
    height = ext.extmax.y - ext.extmin.y
    vx1, vy1 = ext.extmin.x - width * 0.02, ext.extmin.y - height * 0.02
    vx2, vy2 = ext.extmax.x + width * 0.02, ext.extmax.y + height * 0.02
    scale = 13.0 / max(width, 1.0)
    fig = plt.figure(figsize=(width * scale, height * scale), dpi=160)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_facecolor("white")
    backend = MatplotlibBackend(ax, adjust_figure=False)
    Frontend(RenderContext(doc), backend).draw_layout(msp, filter_func=keep, finalize=True)
    ax.set_xlim(vx1, vx2)
    ax.set_ylim(vy1, vy2)
    ax.set_aspect("equal")
    fig.canvas.draw()
    mapping = {
        "view_box_absolute": [vx1, vy1, vx2, vy2],
        "view_box_task01": [vx1 - AX, vy1 - AY, vx2 - AX, vy2 - AY],
        "axes_pixel_bounds_bottom_origin": list(ax.bbox.bounds),
        "canvas_size": list(fig.canvas.get_width_height()),
        "figure_pixel_extent": list(fig.bbox.bounds),
    }
    fig.savefig(PNG, dpi=160, facecolor="white")
    fig.savefig(PDF, facecolor="white")
    plt.close(fig)

    visible_layers = sorted({e.dxf.layer for e in msp if keep(e)})
    visible_types = sorted({e.dxftype() for e in msp if keep(e)})
    sidecar = {
        "source_dxf": str(INPUT.relative_to(ROOT)),
        "source_dxf_sha256": sha(INPUT),
        "render_profile": "STRUCTURE_ONLY_CAD",
        "synthetic_wall_faces": False,
        "coordinate_mapping": mapping,
        "hidden_layers": sorted(HIDDEN_LAYERS),
        "hidden_entity_types": sorted(HIDDEN_TYPES),
        "visible_layers": visible_layers,
        "visible_entity_types": visible_types,
        "outputs": {
            "png": {"file": str(PNG.relative_to(ROOT)), "sha256": sha(PNG)},
            "pdf": {"file": str(PDF.relative_to(ROOT)), "sha256": sha(PDF)},
        },
        "renderer_sha256": sha(Path(__file__)),
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    SIDECAR.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(sidecar, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    render()
