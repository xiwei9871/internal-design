#!/usr/bin/env python3
"""Task03A RC4 — CAD-native renderer.

Formal images are rendered FROM the versioned DXF (ezdxf matplotlib backend).
JSON is no longer a drawing source: PNG/PDF = view of the CAD file.

Profiles:
  CAD_REVIEW    — everything: source entities, DEMO, SUPERSEDED, QC zones, tags
  PRESENTATION  — hides audit/demo/superseded/QC/tag layers + old survey text/dims
Each output carries a .render.json sidecar for provenance.
"""
import ezdxf, json, hashlib, datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf import bbox

ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / 'cad'
QC = ROOT / 'qc'

matplotlib.rcParams['font.family'] = ['PingFang SC', 'Arial Unicode MS', 'sans-serif']

PRESENTATION_HIDE_LAYERS = {
    'A-WALL-DEMO', 'A-SURVEY-SUPERSEDED', 'A-SURVEY-HATCH',
    'A-QC-ZONE', 'A-ELEM-TAG', 'F-TEXT', 'F-FURN', 'RC-GRILL',
}
PRESENTATION_HIDE_TYPES = {'HATCH', 'DIMENSION'}
REVIEW_HIDE_LAYERS = set()
REVIEW_HIDE_TYPES = set()


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def render(dxf_path, profile, name):
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    hide_l = PRESENTATION_HIDE_LAYERS if profile == 'PRESENTATION' else REVIEW_HIDE_LAYERS
    hide_t = PRESENTATION_HIDE_TYPES if profile == 'PRESENTATION' else REVIEW_HIDE_TYPES

    def keep(e):
        return e.dxf.layer not in hide_l and e.dxftype() not in hide_t

    # extents from plain linework only, clipped to the plan region —
    # INSERT attribs/DIMENSION defpoints report broken bboxes, and RC-GRILL
    # contains a far off-plan symbol legend; both must not set the view
    EXT_TYPES = {'LINE', 'LWPOLYLINE', 'CIRCLE', 'ARC', 'TEXT', 'MTEXT', 'POLYLINE'}
    AX, AY = 1298172.0, -296458.0          # task01 origin in abs coords
    PLAN = (AX - 3000, AY - 3000, AX + 22000, AY + 22000)
    in_plan = []
    for e in msp:
        if not (keep(e) and e.dxftype() in EXT_TYPES):
            continue
        try:
            eb = bbox.extents([e])
        except Exception:
            continue
        if (eb.extmax.x < PLAN[0] or eb.extmin.x > PLAN[2]
                or eb.extmax.y < PLAN[1] or eb.extmin.y > PLAN[3]):
            continue                        # off-plan legend/notes stay out of view
        in_plan.append(e)
    ext = bbox.extents(in_plan)
    w = ext.extmax.x - ext.extmin.x
    h = ext.extmax.y - ext.extmin.y
    scale = 13.0 / max(w, 1)
    fig = plt.figure(figsize=(w * scale, h * scale), dpi=160)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_facecolor('white')
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp, filter_func=keep, finalize=True)
    ax.set_xlim(ext.extmin.x - w * 0.02, ext.extmax.x + w * 0.02)
    ax.set_ylim(ext.extmin.y - h * 0.02, ext.extmax.y + h * 0.02)
    ax.set_aspect('equal')
    png = QC / f'{name}.png'
    pdf = QC / f'{name}.pdf'
    fig.savefig(png, dpi=160, facecolor='white')
    fig.savefig(pdf, facecolor='white')
    plt.close(fig)

    man = json.load(open(CAD / 'cad_version_manifest.json'))
    ver = {v['version']: v for v in man['versions']}
    side = {
        'source_dxf': str(dxf_path.relative_to(ROOT)),
        'source_dxf_sha256': sha(dxf_path),
        'parent_cad_sha256': next((v['parent_sha256'] for v in man['versions']
                                   if v['file'] == str(dxf_path.relative_to(ROOT))), None),
        'render_profile': profile,
        'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
        'visible_layers': sorted({e.dxf.layer for e in msp if keep(e)}),
        'hidden_layers': sorted(hide_l),
        'hidden_entity_types': sorted(hide_t),
    }
    json.dump(side, open(QC / f'{name}.render.json', 'w'), indent=1, ensure_ascii=False)
    print(f'{name}.png/.pdf  ({profile})  <- {dxf_path.name}')


render(CAD / 'design_v01_existing_sync.dxf', 'CAD_REVIEW', 'rc4_v01_cad_review')
render(CAD / 'design_v01_existing_sync.dxf', 'PRESENTATION', 'rc4_v01_presentation')
render(CAD / 'design_v02_f1_l1.dxf', 'CAD_REVIEW', 'rc4_v02_f1_cad_review')
render(CAD / 'design_v02_f1_l1.dxf', 'PRESENTATION', 'rc4_v02_f1_presentation')
