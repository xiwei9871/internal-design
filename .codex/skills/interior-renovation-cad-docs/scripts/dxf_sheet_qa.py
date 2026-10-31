#!/usr/bin/env python3
"""Automated QA gate for a construction DXF sheet (model-space A1 1:50 convention).

Checks are file-level facts only. PASS here never proves buildability, dimensions on site,
or MEP feasibility; those stay SITE_VERIFY_REQUIRED.

Usage: dxf_sheet_qa.py SHEET.dxf [--src SRC.dxf] [--scale 50] [--paper 841x594]
                       [--require-layers A-WALL,A-DOOR] [--version AC1024] [--json out.json]
Exit code: 0 if no FAIL, 1 otherwise.
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

import ezdxf
from ezdxf import bbox

CJK = re.compile(r'[㐀-鿿豈-﫿]')
# QCAD 3.33 GUI verified (QCAD_VERIFY_V01): gbcbig.shx big font and these TTFs render CJK;
# txt.shx + hztxt.shx rendered '??'. AutoCAD/ZWCAD/GstarCAD ship gbenor/gbcbig.
CJK_BIGFONTS = {'gbcbig.shx'}
CJK_TTF = {'simhei.ttf', 'simsun.ttf', 'simsun.ttc', 'msyh.ttf', 'msyh.ttc', 'noto-sans-sc.lff'}
FRAME_LAYER = 'A-FRAME'


def _res(name, status, detail):
    return {'check': name, 'status': status, 'detail': detail}


def style_is_cjk_capable(style):
    font = (style.dxf.get('font') or '').lower()
    big = (style.dxf.get('bigfont') or '').lower()
    return big in CJK_BIGFONTS or Path(font).name in CJK_TTF


def entity_text(e):
    if e.dxftype() == 'TEXT': return e.dxf.text
    if e.dxftype() == 'MTEXT': return e.plain_text()
    return ''


def run(path, src=None, scale=50, paper=(841, 594), require_layers=(), version='AC1024'):
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    out = []
    out.append(_res('dxf_version', 'PASS' if doc.dxfversion == version else 'FAIL',
                    f'{doc.dxfversion} (want {version})'))
    aud = doc.audit()
    out.append(_res('ezdxf_audit', 'PASS' if not aud.errors else 'FAIL',
                    f'errors={len(aud.errors)} fixes={len(aud.fixes)}'))
    units = doc.header.get('$INSUNITS', 0)
    out.append(_res('insunits_mm', 'PASS' if units == 4 else 'FAIL', f'$INSUNITS={units}'))

    abs_fonts = [(s.dxf.name, s.dxf.font) for s in doc.styles
                 if re.match(r'^(/|[A-Za-z]:\\)', s.dxf.get('font') or '')]
    out.append(_res('font_paths_portable', 'PASS' if not abs_fonts else 'FAIL',
                    f'absolute font paths: {abs_fonts}' if abs_fonts else 'no absolute font paths'))

    bad_cjk = Counter()
    n_cjk = 0
    layouts = [msp] + [l for l in doc.layouts if l.name != 'Model']
    for lay in layouts:
        for e in lay.query('TEXT MTEXT'):
            if not CJK.search(entity_text(e)): continue
            n_cjk += 1
            st = doc.styles.get(e.dxf.get('style', 'Standard'))
            if st is None or not style_is_cjk_capable(st):
                bad_cjk[e.dxf.get('style', 'Standard')] += 1
    out.append(_res('cjk_text_styles', 'PASS' if not bad_cjk else 'FAIL',
                    f'{n_cjk} CJK texts; not CJK-capable by style: {dict(bad_cjk)}'))

    vps = [e for l in doc.layouts if l.name != 'Model' for e in l.query('VIEWPORT')
           if e.dxf.get('id', 0) != 1]
    out.append(_res('no_paperspace_viewports', 'PASS' if not vps else 'WARN',
                    f'{len(vps)} viewport(s); QCAD 3.33 showed paper-space viewports blank'))

    W, H = paper[0] * scale, paper[1] * scale
    frames = [e for e in msp.query('LWPOLYLINE') if e.dxf.layer == FRAME_LAYER and e.closed]
    frame = None
    for e in frames:
        b = bbox.extents([e])
        if abs(b.size.x - W) < 1 and abs(b.size.y - H) < 1:
            frame = b; break
    out.append(_res('frame_a1_scale', 'PASS' if frame else 'FAIL',
                    f'{FRAME_LAYER} sheet border {W:.0f}x{H:.0f} found' if frame else
                    f'no closed {FRAME_LAYER} polyline of {W:.0f}x{H:.0f} (paper {paper} x {scale})'))

    if frame:
        frozen = {l.dxf.name for l in doc.layers if l.is_frozen() or not l.is_on()}
        live = [e for e in msp if e.dxf.layer not in frozen and e.dxf.layer != FRAME_LAYER]
        ext = bbox.extents(live)
        inside = ext.has_data and ext.extmin.x >= frame.extmin.x - 1 and ext.extmin.y >= frame.extmin.y - 1 \
            and ext.extmax.x <= frame.extmax.x + 1 and ext.extmax.y <= frame.extmax.y + 1
        out.append(_res('content_inside_frame', 'PASS' if inside else 'FAIL',
                        f'content {ext.extmin.x:.0f},{ext.extmin.y:.0f} .. {ext.extmax.x:.0f},{ext.extmax.y:.0f}'))

    missing = [n for n in require_layers if n not in doc.layers]
    if require_layers:
        out.append(_res('required_layers', 'PASS' if not missing else 'FAIL', f'missing: {missing}'))

    if src:
        s = ezdxf.readfile(src)
        n_src = len(s.modelspace())
        n_out = sum(1 for e in msp if e.dxf.layer != FRAME_LAYER)
        out.append(_res('entities_preserved', 'PASS' if n_src == n_out else 'FAIL',
                        f'src={n_src} out_excl_frame={n_out}'))

    summary = {
        'file': str(path),
        'entities_by_layer': dict(Counter(e.dxf.layer for e in msp)),
        'frozen_or_off_layers': sorted(l.dxf.name for l in doc.layers if l.is_frozen() or not l.is_on()),
        'checks': out,
        'result': 'FAIL' if any(c['status'] == 'FAIL' for c in out) else 'PASS',
        'scope_note': 'File-level QA only; not proof of site dimensions or construction feasibility.',
    }
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('sheet'); ap.add_argument('--src')
    ap.add_argument('--scale', type=float, default=50)
    ap.add_argument('--paper', default='841x594')
    ap.add_argument('--require-layers', default='')
    ap.add_argument('--version', default='AC1024')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    paper = tuple(float(v) for v in a.paper.lower().split('x'))
    req = [x for x in a.require_layers.split(',') if x]
    r = run(a.sheet, a.src, a.scale, paper, req, a.version)
    txt = json.dumps(r, ensure_ascii=False, indent=1)
    if a.json: Path(a.json).write_text(txt)
    print(txt)
    return 0 if r['result'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
