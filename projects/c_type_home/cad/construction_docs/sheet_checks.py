#!/usr/bin/env python3
"""Sheet-level review helpers for CD_V01: text-overlap check and crop previews.
Usage: sheet_checks.py overlaps SHEET.dxf LAYER[,LAYER] [--json out.json]
       sheet_checks.py crops SHEET.dxf OUT_DIR name:x0,y0,x1,y1 [...]"""
import json, sys
from pathlib import Path

import ezdxf
from ezdxf import bbox
from shapely.geometry import box

from cd_common import render_png


def text_overlaps(path, layers, min_overlap_mm2=2000):
    doc = ezdxf.readfile(path)
    items = []
    for e in doc.modelspace().query('TEXT MTEXT'):
        if e.dxf.layer not in layers: continue
        b = bbox.extents([e])
        if b.has_data:
            items.append((e.dxf.text if e.dxftype() == 'TEXT' else e.plain_text(),
                          box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)))
    hits = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a = items[i][1].intersection(items[j][1]).area
            if a > min_overlap_mm2:
                hits.append({'a': items[i][0], 'b': items[j][0], 'overlap_mm2': round(a),
                             'at': [round(v) for v in items[i][1].centroid.coords[0]]})
    return {'file': Path(path).name, 'texts': len(items), 'overlaps': hits,
            'result': 'PASS' if not hits else 'FAIL'}


def crops(path, out_dir, specs):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for s in specs:
        name, coords = s.split(':')
        x0, y0, x1, y1 = map(float, coords.split(','))
        p = out_dir / f'{name}.png'
        render_png(path, p, ((x0, y0), (x1, y1)), width_in=12, dpi=110)
        made.append(str(p))
    return made


if __name__ == '__main__':
    cmd, sheet = sys.argv[1], sys.argv[2]
    if cmd == 'overlaps':
        r = text_overlaps(sheet, set(sys.argv[3].split(',')))
        if '--json' in sys.argv: Path(sys.argv[sys.argv.index('--json') + 1]).write_text(
            json.dumps(r, ensure_ascii=False, indent=1))
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print('\n'.join(crops(sheet, sys.argv[3], sys.argv[4:])))
