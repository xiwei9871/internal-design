"""Task 02 — adjacency & circulation graph.

adjacency_graph.json distinguishes:
  A. geometric adjacency — two space polygons share a boundary strip
     (regardless of whether a wall blocks it)
  B. circulation connectivity — an actual door/opening or an un-walled
     open passage lets people move between the two nodes

Nodes: all geometry spaces + EXTERNAL_COMMON_AREA (outside the entry door)
+ UNMODELED_INTERIOR_ZONE (interior area bounded by walls but with no
source label / modeled polygon — verified unlabeled on the source image).
"""
import json
import sys
from pathlib import Path

import networkx as nx
from shapely.geometry import Point

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import (  # noqa: E402
    PROJECT_ROOT, load_geometry, opening_world_rect, wall_axis)
from sem_common import (  # noqa: E402
    EXTERNAL_NODE, SEMANTICS_DIR, UNMODELED_ZONE, save, space_polys,
    wall_box)

T_ADJ = 350.0     # buffer bridging polygon-edge gaps across wall bands
STEP = 50.0       # sampling step along shared boundaries
MIN_OPEN = 400.0  # min un-walled run that counts as an open passage


def load_elements():
    p = SEMANTICS_DIR / "element_semantics.json"
    return json.loads(p.read_text(encoding="utf-8"))


def wall_boxes(geo):
    return [(w["id"], wall_box(w)) for w in geo["walls"]]


def covered_by_wall(pt, wboxes, tol=60.0):
    return any(b.distance(pt) <= tol for _, b in wboxes)


def open_runs_on_segment(p0, p1, wboxes):
    """Sample a straight segment; return list of un-walled (a,b) runs
    in segment parameter t, plus total open length in mm."""
    import math
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    n = max(int(L / STEP), 1)
    open_ts, cur = [], []
    for i in range(n + 1):
        t = i / n
        pt = Point(p0[0] + (p1[0] - p0[0]) * t,
                   p0[1] + (p1[1] - p0[1]) * t)
        if covered_by_wall(pt, wboxes):
            if cur:
                open_ts.append(cur)
                cur = []
        else:
            cur.append(t)
    if cur:
        open_ts.append(cur)
    runs = [(r[0], r[-1], (r[-1] - r[0]) * L) for r in open_ts]
    return runs, L


def adjacency_and_passages(geo, polys, wboxes):
    adj, passages = [], []
    ids = list(polys)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = polys[ids[i]], polys[ids[j]]
            inter = a.buffer(T_ADJ).intersection(b.buffer(T_ADJ))
            if inter.is_empty:
                continue
            shared = a.boundary.intersection(b.buffer(T_ADJ)).length
            if shared < 100:
                continue
            adj.append({"space_a": ids[i], "space_b": ids[j],
                        "shared_boundary_mm": round(shared, 0),
                        "confidence": "HIGH" if shared > 1000 else "MEDIUM"})

            # --- open passage detection ---
            runs_total = []
            if a.intersects(b):
                # nested/overlapping polygons (cloak inside leisure):
                # sample the smaller polygon's boundary
                smaller = a if a.area < b.area else b
                line = smaller.boundary
                n = max(int(line.length / STEP), 1)
                blocked = [covered_by_wall(
                    line.interpolate(k / n, normalized=True), wboxes)
                    for k in range(n + 1)]
                # longest open run along the boundary
                best = 0.0
                run = 0.0
                for bl in blocked:
                    run = run + STEP if not bl else 0.0
                    best = max(best, run)
                if best >= MIN_OPEN:
                    passages.append({
                        "space_a": ids[i], "space_b": ids[j],
                        "kind": "OPEN_PASSAGE",
                        "open_run_mm": round(best, 0),
                        "confidence": "MEDIUM"})
            else:
                strip = inter.envelope.bounds
                sx1, sy1, sx2, sy2 = strip
                if (sx2 - sx1) >= (sy2 - sy1):
                    p0, p1 = (sx1, (sy1 + sy2) / 2), (sx2, (sy1 + sy2) / 2)
                else:
                    p0, p1 = ((sx1 + sx2) / 2, sy1), ((sx1 + sx2) / 2, sy2)
                runs, L = open_runs_on_segment(p0, p1, wboxes)
                for t0, t1, seg_mm in runs:
                    if seg_mm >= MIN_OPEN:
                        passages.append({
                            "space_a": ids[i], "space_b": ids[j],
                            "kind": "OPEN_PASSAGE",
                            "open_run_mm": round(seg_mm, 0),
                            "confidence": "MEDIUM"})
    return adj, passages


def main():
    geo = load_geometry()
    polys = space_polys(geo)
    wboxes = wall_boxes(geo)
    elements = load_elements()

    adj, passages = adjacency_and_passages(geo, polys, wboxes)

    circ = []
    for d in elements["doors"]:
        sa, sb = d["side_a_space"], d["side_b_space"]
        if sa == "UNRESOLVED" or sb == "UNRESOLVED":
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

    # zone <-> leisure NE band: verify the gap x12100-12900 @ y~6450 is
    # really un-walled before asserting the edge
    runs, _ = open_runs_on_segment((11300, 6450), (12900, 6450), wboxes)
    zone_leisure_open = sum(r[2] for r in runs)
    if zone_leisure_open >= MIN_OPEN:
        circ.append({"space_a": UNMODELED_ZONE, "space_b": "R-LEISURE",
                     "opening_id": None,
                     "opening_type": "OPEN_PASSAGE",
                     "open_run_mm": round(zone_leisure_open, 0),
                     "confidence": "MEDIUM",
                     "note": "gap x12100-12900 below y6500 — no wall "
                             "object between corridor zone and leisure "
                             "NE band"})

    # build graph & connected components on real connections only
    g = nx.Graph()
    nodes = list(polys) + [EXTERNAL_NODE, UNMODELED_ZONE]
    g.add_nodes_from(nodes)
    for e in circ:
        if not e.get("intra_space"):
            g.add_edge(e["space_a"], e["space_b"])
    comps = [sorted(c) for c in nx.connected_components(g)]

    # backfill room_schedule adjacency/connectivity now that the graph exists
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
        print("room_schedule backfilled with graph edges")

    out = {
        "meta": {
            "task": "task02",
            "adjacency": "geometric boundary sharing (polygon buffers)",
            "circulation": "movement through doors / un-walled passages",
            "note": "adjacency != circulation; intra-space openings kept "
                    "but excluded from component analysis"},
        "nodes": [{"id": n,
                   "kind": ("space" if n in polys else
                            "external" if n == EXTERNAL_NODE else
                            "unmodeled_interior_zone")}
                  for n in nodes],
        "adjacency_edges": adj,
        "circulation_edges": circ,
        "connected_components": comps,
        "component_count": len(comps),
    }
    save("adjacency_graph.json", out)
    print(f"adjacency edges={len(adj)} circulation edges={len(circ)} "
          f"components={len(comps)}")
    for c in comps:
        print("  comp:", c)


if __name__ == "__main__":
    main()
