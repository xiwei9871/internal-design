#!/usr/bin/env python3
"""Coverage / overlap / gap QA for finish or ceiling zones built from real geometry.

Input JSON: {"zones": [{"id": str, "name": str, "polygon": [[x, y], ...],
                         "holes": [[[x, y], ...]]?, ...}],
             "interior": [[[x, y], ...], ...]?}   # optional reference interior polygons
Output: per-zone area, pairwise overlaps above tolerance, gaps (interior minus zones).
Without an independent "interior", coverage is NOT_RUN and the result is PARTIAL, never PASS.
Usage: zone_qa.py zones.json [--overlap-tol-m2 0.01] [--gap-tol-m2 0.05] [--json out.json]
"""
import argparse, itertools, json, sys
from pathlib import Path

from shapely.geometry import Polygon
from shapely.ops import unary_union


def poly(z):
    return Polygon(z['polygon'], z.get('holes') or [])


def parts(g):
    if g.is_empty: return []
    return [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']


def run(data, overlap_tol_m2=0.01, gap_tol_m2=0.05):
    zones = [(z, poly(z)) for z in data['zones']]
    rows, invalid = [], []
    for z, p in zones:
        if not p.is_valid: invalid.append(z['id'])
        rows.append({'id': z['id'], 'name': z.get('name', ''), 'area_m2': round(p.area / 1e6, 3)})
    overlaps = []
    for (za, pa), (zb, pb) in itertools.combinations(zones, 2):
        a = pa.intersection(pb).area / 1e6
        if a > overlap_tol_m2:
            overlaps.append({'a': za['id'], 'b': zb['id'], 'area_m2': round(a, 3)})
    gaps = []
    if data.get('interior'):
        interior = unary_union([Polygon(r) for r in data['interior']])
        rest = interior.difference(unary_union([p for _, p in zones]))
        for g in parts(rest):
            if g.area / 1e6 > gap_tol_m2:
                c = g.representative_point()
                gaps.append({'area_m2': round(g.area / 1e6, 3), 'at': [round(c.x), round(c.y)],
                             'bounds': [round(v) for v in g.bounds]})
    coverage = 'CHECKED' if data.get('interior') else 'NOT_RUN'
    if overlaps or gaps or invalid:
        status = 'FAIL'
    elif coverage == 'NOT_RUN':
        status = 'PARTIAL'      # overlaps checked only; no independent interior => no coverage PASS
    else:
        status = 'PASS'
    return {'zones': rows, 'invalid': invalid, 'overlaps': overlaps, 'gaps': gaps,
            'coverage': coverage,
            'total_m2': round(sum(r['area_m2'] for r in rows), 3), 'result': status}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('zones'); ap.add_argument('--json')
    ap.add_argument('--overlap-tol-m2', type=float, default=0.01)
    ap.add_argument('--gap-tol-m2', type=float, default=0.05)
    a = ap.parse_args(argv)
    r = run(json.loads(Path(a.zones).read_text()), a.overlap_tol_m2, a.gap_tol_m2)
    txt = json.dumps(r, ensure_ascii=False, indent=1)
    if a.json: Path(a.json).write_text(txt)
    print(txt)
    return 0 if r['result'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
