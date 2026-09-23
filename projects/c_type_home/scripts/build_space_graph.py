"""Task 02 — adjacency & circulation graph.

adjacency_graph.json distinguishes:
  A. geometric adjacency — two space polygons have FACING boundary runs
     (parallel edges, gap <= wall-band tolerance, projected overlap
     >= MIN_OVERLAP along the boundary direction). Corner-only proximity
     never counts. shared_boundary_mm = projected facing overlap.
  B. circulation connectivity — a door/opening or an un-walled open
     passage lets people move between nodes.

Nodes: all geometry spaces + EXTERNAL_COMMON_AREA + derived zones
(ZONE-MASTER-CORRIDOR: bounded interior area with no source label —
see semantics/space_cells.json).
"""
import json
import math
import sys
from pathlib import Path

import networkx as nx
from shapely.geometry import Point

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import (  # noqa: E402
    PROJECT_ROOT, load_geometry)
from sem_common import (  # noqa: E402
    EXTERNAL_NODE, SEMANTICS_DIR, UNRESOLVED,
    save, space_polys, wall_box, zone_polys)

GAP_MAX = 600.0      # max wall-band gap between facing boundary edges
MIN_OVERLAP = 400.0  # min projected facing overlap for real adjacency
STEP = 50.0          # sampling step along boundaries
MIN_OPEN = 400.0     # min un-walled run that counts as an open passage


def load_elements():
    p = SEMANTICS_DIR / "element_semantics.json"
    return json.loads(p.read_text(encoding="utf-8"))


def wall_boxes(geo):
    return [(w["id"], wall_box(w)) for w in geo["walls"]]


def covered_by_wall(pt, wboxes, tol=30.0):
    return any(b.distance(pt) <= tol for _, b in wboxes)


def edges_of(poly):
    """Axis-aligned boundary edges -> (axis, fixed, lo, hi)."""
    out = []
    c = list(poly.exterior.coords)
    for i in range(len(c) - 1):
        (x1, y1), (x2, y2) = c[i], c[i + 1]
        if abs(y1 - y2) < 1e-6:
            out.append(("H", y1, min(x1, x2), max(x1, x2)))
        elif abs(x1 - x2) < 1e-6:
            out.append(("V", x1, min(y1, y2), max(y1, y2)))
    return out


def facing_segments(pa, pb):
    """Facing boundary runs between two polygons.
    Returns list of (axis, midline p0, p1, gap_mm, overlap_mm)."""
    segs = []
    for ax_a, pos_a, lo_a, hi_a in edges_of(pa):
        for ax_b, pos_b, lo_b, hi_b in edges_of(pb):
            if ax_a != ax_b:
                continue
            gap = abs(pos_a - pos_b)
            if gap > GAP_MAX:
                continue
            lo, hi = max(lo_a, lo_b), min(hi_a, hi_b)
            ov = hi - lo
            if ov < MIN_OVERLAP:
                continue
            mid = pos_a + (pos_b - pos_a) / 2
            if ax_a == "H":
                p0, p1 = (lo, mid), (hi, mid)
            else:
                p0, p1 = (mid, lo), (mid, hi)
            segs.append((ax_a, p0, p1, gap, ov))
    return segs


def segment_open_runs(p0, p1, wboxes, pa=None, pb=None):
    """Sample a segment; return (open runs [(t0,t1,len_mm)],
    frac_inside_wall, frac_inside_either_poly)."""
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    n = max(int(L / STEP), 1)
    open_ts, cur, in_wall, in_poly = [], [], 0, 0
    for i in range(n + 1):
        t = i / n
        pt = Point(p0[0] + (p1[0] - p0[0]) * t,
                   p0[1] + (p1[1] - p0[1]) * t)
        inside_p = ((pa is not None and pa.contains(pt)) or
                    (pb is not None and pb.contains(pt)))
        in_poly += inside_p
        if covered_by_wall(pt, wboxes):
            in_wall += 1
            if cur:
                open_ts.append(cur)
                cur = []
        elif not inside_p:
            cur.append(t)
        else:
            if cur:
                open_ts.append(cur)
                cur = []
    if cur:
        open_ts.append(cur)
    runs = [(r[0], r[-1], (r[-1] - r[0]) * L) for r in open_ts]
    return runs, in_wall / (n + 1), in_poly / (n + 1)


def adjacency_and_passages(polys, zones, wboxes):
    """Wall-aware adjacency: facing parallel boundary runs with
    wall-band gap and projected overlap. Midline must not run through
    either polygon's interior. Zones participate so their real
    open boundaries (e.g. corridor -> leisure band) are detected."""
    all_p = {**polys, **zones}
    adj, passages = [], []
    ids = sorted(all_p)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            sa, sb = ids[i], ids[j]
            pa, pb = all_p[sa], all_p[sb]
            shared = 0.0
            open_runs = []
            for ax, p0, p1, gap, ov in facing_segments(pa, pb):
                runs, f_wall, f_poly = segment_open_runs(
                    p0, p1, wboxes, pa, pb)
                # the facing strip must not lie inside either polygon
                if f_poly > 0.3:
                    continue
                shared += ov
                for t0, t1, seg_mm in runs:
                    if seg_mm >= MIN_OPEN:
                        open_runs.append(round(seg_mm, 0))
            if shared > 0:
                adj.append({
                    "space_a": sa, "space_b": sb,
                    "shared_boundary_mm": round(shared, 0),
                    "shared_boundary_basis":
                        "projected facing-edge overlap",
                    "involves_zone": sa in zones or sb in zones,
                    "confidence": "HIGH" if shared > 1000 else "MEDIUM"})
                for seg_mm in open_runs:
                    passages.append({
                        "space_a": sa, "space_b": sb,
                        "kind": "OPEN_PASSAGE",
                        "open_run_mm": seg_mm,
                        "confidence": "MEDIUM"})
    return adj, passages


def main():
    geo = load_geometry()
    polys = space_polys(geo)
    zones = zone_polys(geo)
    wboxes = wall_boxes(geo)
    elements = load_elements()

    adj, passages = adjacency_and_passages(polys, zones, wboxes)

    circ = []
    unresolved = []
    for d in elements["doors"]:
        sa, sb = d["side_a_space"], d["side_b_space"]
        if UNRESOLVED in (sa, sb):
            unresolved.append(d["element_id"])
            continue
        circ.append({
            "space_a": sa, "space_b": sb,
            "opening_id": d["element_id"],
            "opening_type": d.get("door_type", "door"),
            "intra_space": sa == sb,
            "confidence": d.get("semantic_confidence")})
    for p in passages:
        circ.append({"space_a": p["space_a"], "space_b": p["space_b"],
                     "opening_id": None,
                     "opening_type": "OPEN_PASSAGE",
                     "open_run_mm": p["open_run_mm"],
                     "confidence": p["confidence"]})

    # zone adjacency/passages are detected generically above; no manual
    # zone edges — connectivity must come from geometric evidence only

    g = nx.Graph()
    nodes = list(polys) + list(zones) + [EXTERNAL_NODE]
    g.add_nodes_from(nodes)
    for e in circ:
        if not e.get("intra_space"):
            g.add_edge(e["space_a"], e["space_b"])
    comps = [sorted(c) for c in nx.connected_components(g)]

    # backfill room_schedule adjacency/connectivity
    sched_p = SEMANTICS_DIR / "room_schedule.json"
    if sched_p.exists():
        sched = json.loads(sched_p.read_text(encoding="utf-8"))
        adj_map = {n: [] for n in nodes}
        for e in adj:
            adj_map[e["space_a"]].append(e["space_b"])
            adj_map[e["space_b"]].append(e["space_a"])
        con_map = {n: [] for n in nodes}
        for e in circ:
            if e.get("intra_space"):
                continue
            con_map[e["space_a"]].append(e["space_b"])
            con_map[e["space_b"]].append(e["space_a"])
        for room in sched["rooms"]:
            sid = room["space_id"]
            room["adjacent_spaces"] = sorted(adj_map.get(sid, []))
            room["directly_connected_spaces"] = sorted(
                set(con_map.get(sid, [])))
        sched_p.write_text(json.dumps(sched, ensure_ascii=False, indent=1),
                           encoding="utf-8")
        import csv
        with open(SEMANTICS_DIR / "room_schedule.csv", "w", newline="",
                  encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(sched["rooms"][0].keys()))
            w.writeheader()
            w.writerows(sched["rooms"])
        print("room_schedule backfilled")

    out = {
        "meta": {
            "task": "task02",
            "adjacency": "facing-edge projected overlap with wall-band "
                         "gap; corner proximity excluded",
            "circulation": "movement through doors / un-walled passages",
            "note": "adjacency != circulation; zones are distinct located "
                    "derived nodes (see space_cells.json)"},
        "nodes": [{"id": n,
                   "kind": ("space" if n in polys else
                            "external" if n == EXTERNAL_NODE else
                            "derived_zone")}
                  for n in nodes],
        "adjacency_edges": adj,
        "circulation_edges": circ,
        "unresolved_edges": unresolved,
        "connected_components": comps,
        "component_count": len(comps),
    }
    save("adjacency_graph.json", out)
    print(f"adjacency={len(adj)} circulation={len(circ)} "
          f"unresolved={unresolved} components={len(comps)}")
    for c in comps:
        print("  comp:", c)


if __name__ == "__main__":
    main()
