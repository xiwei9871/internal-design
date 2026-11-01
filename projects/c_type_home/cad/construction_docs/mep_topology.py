"""Route topology QA for A301 (per system: SOURCE -> every terminal reachable).
Segments are noded at every endpoint / crossing of the SAME system, then joined by shared nodes.
Snap tolerance is TOL_MM (numerical noise only); a 120 mm gap stays a gap."""
import json, math, sys
from collections import defaultdict
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

TOL_MM = 1.0


def _key(x, y):
    return (round(x / TOL_MM), round(y / TOL_MM))


def components(segs):
    """segs: list of ((x0,y0),(x1,y1)). Returns (pieces, node->component id, union-find root fn)."""
    lines = [LineString(s) for s in segs if math.dist(*s) > 1e-6]
    noded = unary_union(lines) if lines else None
    pieces = [] if noded is None else ([noded] if noded.geom_type == 'LineString' else list(noded.geoms))
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a

    def union(a, b): parent[find(a)] = find(b)
    for p in pieces:
        cs = list(p.coords)
        for (x0, y0), (x1, y1) in zip(cs[:-1], cs[1:]):
            union(_key(x0, y0), _key(x1, y1))
    return pieces, find


def system_report(routes, system, terminals):
    """routes: [{'system','kind','seg', 'to'?}] ; terminals: [{'id','x','y'}] for this system."""
    rs = [r for r in routes if r['system'] == system]
    segs = [tuple(map(tuple, r['seg'])) for r in rs]
    pieces, find = components(segs)
    src = [r for r in rs if r['kind'] == 'SOURCE']
    if not src:
        return {'system': system, 'source_found': False, 'segments_reachable': 0, 'segments_total': len(rs),
                'terminals_reachable': 0, 'terminals_total': len(terminals),
                'unreachable_terminals': [t['id'] for t in terminals]}
    # source root = component of the SOURCE run's start point (the panel / inlet itself)
    s0 = src[0]['seg'][0]
    root = find(_key(*s0))

    def on_net(x, y):
        for p in pieces:
            if p.distance(Point(x, y)) <= TOL_MM:
                cs = list(p.coords)
                return find(_key(*cs[0])) == root
        return False

    seg_ok = sum(1 for (a, b) in segs if find(_key(*a)) == root or find(_key(*b)) == root)
    bad = [t['id'] for t in terminals if not on_net(t['x'], t['y'])]
    return {'system': system, 'source_found': True, 'segments_reachable': seg_ok, 'segments_total': len(rs),
            'terminals_reachable': len(terminals) - len(bad), 'terminals_total': len(terminals),
            'unreachable_terminals': bad}


def report(routes, points, systems=('POWER', 'DATA', 'COLD', 'HOT')):
    out = []
    for s in systems:
        terms = [p for p in points if p.get('system') == s and p.get('routed', True)]
        out.append(system_report(routes, s, terms))
    ok = all(r['source_found'] and not r['unreachable_terminals'] for r in out)
    return {'result': 'PASS' if ok else 'FAIL', 'tolerance_mm': TOL_MM, 'systems': out}


if __name__ == '__main__':
    r = json.load(open(sys.argv[1]))
    p = json.load(open(sys.argv[2]))['points']
    print(json.dumps(report(r['segments'], p), ensure_ascii=False, indent=1))
