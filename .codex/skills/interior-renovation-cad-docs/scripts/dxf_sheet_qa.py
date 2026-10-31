#!/usr/bin/env python3
"""Automated QA gate for a construction DXF sheet (model-space A1 1:50 convention).

Checks are file-level facts only. PASS here never proves buildability, dimensions on site,
or MEP feasibility; those stay SITE_VERIFY_REQUIRED.

Usage: dxf_sheet_qa.py SHEET.dxf [--src SRC.dxf] [--scale 50] [--paper 841x594]
                       [--require-layers A-WALL,A-DOOR] [--version AC1024]
                       [--anchors anchors.json] [--json out.json]
Anchors catch entities whose count is unchanged but whose coordinates moved.
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


def entity_points(e):
    t = e.dxftype()
    if t == 'LINE': return [tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]]
    if t == 'LWPOLYLINE': return [tuple(p) for p in e.get_points('xy')]
    if t == 'POLYLINE': return [tuple(v.dxf.location)[:2] for v in e.vertices]
    if t in ('CIRCLE', 'ARC'): return [tuple(e.dxf.center)[:2]]
    if t in ('TEXT', 'MTEXT', 'INSERT', 'POINT'):
        return [tuple(e.dxf.insert if t != 'POINT' else e.dxf.location)[:2]]
    return []


def check_dimensions(msp, tol=1.0):
    """Linear DIMENSION: stored measurement vs defpoint distance; numeric text override vs measurement."""
    import math
    bad, n = [], 0
    for d in msp.query('DIMENSION'):
        if d.dimtype not in (0, 1): continue          # linear / aligned only
        n += 1
        p1, p2 = d.dxf.defpoint2, d.dxf.defpoint3
        if d.dimtype == 0:
            a = math.radians(d.dxf.get('angle', 0))
            geo = abs((p2.x - p1.x) * math.cos(a) + (p2.y - p1.y) * math.sin(a))
        else:
            geo = math.dist(p1[:2], p2[:2])
        meas = d.get_measurement()
        txt = (d.dxf.get('text') or '').strip()
        ovr = None
        if txt and txt != '<>':
            try: ovr = float(txt.replace('<>', '').strip())
            except ValueError: ovr = None
        if abs(meas - geo) > tol or (ovr is not None and abs(ovr - geo) > tol):
            bad.append({'handle': d.dxf.handle, 'geo': round(geo, 1), 'measurement': round(meas, 1),
                        'text': txt})
    return n, bad


def check_anchors(msp, frozen, anchors):
    """anchors: [{id, layer, x, y, tol}] -> each must hit a vertex/insert of a visible entity on layer."""
    import math
    by_layer = {}
    for e in msp:
        if e.dxf.layer in frozen: continue
        by_layer.setdefault(e.dxf.layer, []).extend(entity_points(e))
    miss = []
    for a in anchors:
        pts = by_layer.get(a['layer'], [])
        dmin = min((math.dist((a['x'], a['y']), p) for p in pts), default=float('inf'))
        if dmin > a.get('tol', 5):
            miss.append({**a, 'nearest_mm': None if dmin == float('inf') else round(dmin, 1)})
    return miss


def run(path, src=None, scale=50, paper=(841, 594), require_layers=(), version='AC1024',
        anchors=None):
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

    frozen_set = {l.dxf.name for l in doc.layers if l.is_frozen() or not l.is_on()}
    if require_layers:
        cnt = Counter(e.dxf.layer for e in msp if e.dxf.layer not in frozen_set)
        empty = [n for n in require_layers if cnt.get(n, 0) == 0]
        out.append(_res('required_layers_visible', 'PASS' if not empty else 'FAIL',
                        f'no visible entities on: {empty}' if empty else
                        ', '.join(f'{n}={cnt[n]}' for n in require_layers)))
    n_dim, bad_dim = check_dimensions(msp)
    out.append(_res('dimension_values', 'FAIL' if bad_dim else ('PASS' if n_dim else 'WARN'),
                    f'{n_dim} linear dims; mismatched: {bad_dim[:5]}' if bad_dim else
                    f'{n_dim} linear dims, measurement == defpoint distance'))
    if anchors is not None:
        miss = check_anchors(msp, frozen_set, anchors)
        out.append(_res('anchor_coordinates', 'PASS' if not miss else 'FAIL',
                        f'{len(anchors)} anchors; missed: {miss[:5]}' if miss else
                        f'{len(anchors)} anchors all hit'))

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
    ap.add_argument('--anchors', help='JSON list of {id,layer,x,y,tol}')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    paper = tuple(float(v) for v in a.paper.lower().split('x'))
    req = [x for x in a.require_layers.split(',') if x]
    anc = json.loads(Path(a.anchors).read_text()) if a.anchors else None
    r = run(a.sheet, a.src, a.scale, paper, req, a.version, anc)
    txt = json.dumps(r, ensure_ascii=False, indent=1)
    if a.json: Path(a.json).write_text(txt)
    print(txt)
    return 0 if r['result'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
