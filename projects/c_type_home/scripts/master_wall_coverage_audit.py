#!/usr/bin/env python3
"""
MASTER_WALL_COVERAGE_AUDIT

Compare wall evidence in FreeCAD MASTER_V2 object dump (source of truth)
against canonical walls in b1_model.json and Pascal arch scene export.

Inputs:
  design/b1_blockout/b1_fcstd_objects.json   (FC object dump, source)
  design/b1_blockout/b1_model.json           (canonical)
  design/pascal_b1/pascal_b1_arch_only_export.json (pascal walls)

Outputs: design/pascal_b1/wall_audit/  (PNG + JSON + MD)
"""
import json, math, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B1 = os.path.join(ROOT, "design/b1_blockout")
P  = os.path.join(ROOT, "design/pascal_b1")
OUT = os.path.join(P, "wall_audit")
os.makedirs(OUT, exist_ok=True)

DX, DY = -1298172.0, 296458.0  # canon = fc + (DX, DY)

def canon(bb):
    x0, y0, _, x1, y1, _ = bb
    return [x0 + DX, y0 + DY, x1 + DX, y1 + DY]

def rarea(r): return max(0, r[2]-r[0]) * max(0, r[3]-r[1])
def rinter(a, b):
    return max(0, min(a[2],b[2])-max(a[0],b[0])) * max(0, min(a[3],b[3])-max(a[1],b[1]))
def cov(r, pool):
    a = rarea(r)
    return sum(rinter(r,c) for c in pool)/a if a else 0.0
def inside_house(r): return -500 < r[0] < 17500 and -500 < r[1] < 15500

FC = json.load(open(os.path.join(B1, "b1_fcstd_objects.json")))["objects"]
M  = json.load(open(os.path.join(B1, "b1_model.json")))

CW = [w["rect"] for w in M["walls"] + M["parapets"]]
CFOOT = [f["rect"] for f in M["furniture"]] + [k["rect"] for k in M["kitchen_cabinets"]]
OPEN_RECTS = [o["rect"] for o in M["openings"]] + [w["rect"] for w in M["windows"]]

# ---------------------------------------------------------------- door-symbol clusters
# group unlabeled objects whose bboxes (expanded 600mm) touch a group containing Arc/Circle
objs = []
for name, o in FC.items():
    bb = o.get("bbox")
    if not bb:
        continue
    r = canon(bb)
    if not inside_house(r):
        continue
    lab = o.get("label") or ""
    generic = lab.startswith(("Line", "Rectangle", "Polyline", "Circle", "Arc", "line", "Feature"))
    objs.append({"name": name, "type": o["type"], "label": lab,
                 "rect": r, "generic": generic})

def expand(r, m): return [r[0]-m, r[1]-m, r[2]+m, r[3]+m]
def touch(a, b): return rinter(expand(a, 600), expand(b, 600)) > 0

n = len(objs)
parent = list(range(n))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for i in range(n):
    for j in range(i+1, n):
        if touch(objs[i]["rect"], objs[j]["rect"]) or \
           (abs(objs[i]["rect"][0]-objs[j]["rect"][0]) < 600 and abs(objs[i]["rect"][1]-objs[j]["rect"][1]) < 600
            and rinter(expand(objs[i]["rect"],600), expand(objs[j]["rect"],600)) > 0):
            a, b = find(i), find(j)
            if a != b: parent[a] = b
clusters = {}
for i in range(n): clusters.setdefault(find(i), []).append(i)
door_cluster_members = set()
for _, mem in clusters.items():
    if any("Arc" in objs[i]["type"] or "Circle" in objs[i]["type"] for i in mem):
        door_cluster_members.update(mem)

# ---------------------------------------------------------------- E1: thin-long closed-rect evidence
E1 = []
for i, o in enumerate(objs):
    r = o["rect"]
    thin = min(r[2]-r[0], r[3]-r[1]); long = max(r[2]-r[0], r[3]-r[1])
    if not o["generic"] or not (40 <= thin <= 350 and long >= 500):
        continue
    if i in door_cluster_members and long < 1200:
        o["why"] = "door-symbol cluster"; continue
    if any(rinter(r, q) / max(1.0, rarea(r)) > 0.5 for q in OPEN_RECTS):
        o["why"] = "inside opening rect (leaf/jamb)"; continue
    if cov(r, CFOOT) > 0.5:
        o["why"] = "furniture footprint"; continue
    E1.append(o)

# ---------------------------------------------------------------- E2: parallel line-pair evidence
segs = []
for o in objs:
    if o["type"] != "Part::Line":
        continue
    r = o["rect"]; w = r[2]-r[0]; d = r[3]-r[1]
    if max(w, d) >= 400:
        h = w >= d
        segs.append(dict(obj=o, h=h,
                         c=(r[1]+r[3])/2 if h else (r[0]+r[2])/2,
                         a=r[0] if h else r[1], b=r[2] if h else r[3]))
pairs = []
for i, s in enumerate(segs):
    for t in segs[i+1:]:
        if t["h"] != s["h"]: continue
        gap = abs(s["c"]-t["c"])
        if not (60 <= gap <= 400): continue
        ov = min(s["b"],t["b"]) - max(s["a"],t["a"])
        if ov <= 0 or ov < 0.5 * min(s["b"]-s["a"], t["b"]-t["a"]): continue
        a0 = min(s["a"],t["a"]); b0 = max(s["b"],t["b"])
        c0, c1 = sorted([s["c"], t["c"]])
        pairs.append({"h": s["h"], "a": a0, "b": b0, "c0": c0, "c1": c1,
                      "src": [s["obj"]["name"], t["obj"]["name"]],
                      "rect": [a0, c0, b0, c1] if s["h"] else [c0, a0, c1, b0]})

def in_opening_band(p):
    r = p["rect"]
    if not (r[2]-r[0]) or not (r[3]-r[1]): return False
    return any(rinter(r, q) / max(1.0, rarea(r)) > 0.5 for q in OPEN_RECTS)

E2 = [p for p in pairs if not in_opening_band(p) and cov(p["rect"], CFOOT) <= 0.5]

# ---------------------------------------------------------------- coverage of evidence by canonical
def band_cov(r): return cov(r, CW)

E1_miss = [o for o in E1 if band_cov(o["rect"]) < 0.5]
E2_miss = [p for p in E2 if band_cov(p["rect"]) < 0.5]

# merge E2 pairs into segments: same orientation, overlapping centers±50, overlapping extent
def merge_pairs(ps):
    ps = sorted(ps, key=lambda p: (not p["h"], round((p["c0"]+p["c1"])/2/50), p["a"]))
    merged = []
    for p in ps:
        placed = False
        for m in merged:
            if m["h"] == p["h"] and abs(m["cm"] - (p["c0"]+p["c1"])/2) < 150 and \
               min(m["b"], p["b"]) - max(m["a"], p["a"]) > 0:
                m["a"] = min(m["a"], p["a"]); m["b"] = max(m["b"], p["b"])
                m["c0"] = min(m["c0"], p["c0"]); m["c1"] = max(m["c1"], p["c1"])
                m["cm"] = (m["c0"]+m["c1"])/2
                m["src"] += p["src"]; placed = True; break
        if not placed:
            merged.append(dict(p, cm=(p["c0"]+p["c1"])/2, src=list(p["src"])))
    return merged

E2_seg = merge_pairs(E2_miss)

def gap_dist(r, w):
    dx = max(r[0]-w[2], w[0]-r[2], 0); dy = max(r[1]-w[3], w[1]-r[3], 0)
    return (dx*dx + dy*dy) ** 0.5

missing = []
for o in E1_miss:
    r = o["rect"]
    d = min((gap_dist(r, w) for w in CW), default=9999)
    cls = "ALIGNMENT_VARIANT" if d <= 350 else "UNNAMED_PHYSICAL_GEOMETRY"
    missing.append(dict(kind="THIN_RECT", source=o["name"], type=o["type"], rect=r,
                        length=max(r[2]-r[0], r[3]-r[1]),
                        thickness=min(r[2]-r[0], r[3]-r[1]),
                        nearest_canon_mm=round(d), classification=cls))
for m in E2_seg:
    r = [m["a"], m["c0"], m["b"], m["c1"]] if m["h"] else [m["c0"], m["a"], m["c1"], m["b"]]
    d = min((gap_dist(r, w) for w in CW), default=9999)
    # skip duplicates of E1 hits (same band already covered by thin rect)
    if any(cov(r, [o["rect"]]) > 0.5 for o in E1_miss):
        cls = "UNNAMED_PHYSICAL_GEOMETRY"
    elif d <= 350:
        cls = "ALIGNMENT_VARIANT"
    else:
        cls = "SINGLE_LINE_WALL" if m["c1"]-m["c0"] < 100 else "EXTRACTOR_DROPPED"
    missing.append(dict(kind="LINE_PAIR", source="/".join(sorted(set(m["src"]))),
                        type="Part::Line x2", rect=r, length=m["b"]-m["a"],
                        thickness=m["c1"]-m["c0"], nearest_canon_mm=round(d),
                        classification=cls))

# metrics
true_missing = [m for m in missing if m["classification"] != "ALIGNMENT_VARIANT"]
master_total = sum(max(o["rect"][2]-o["rect"][0], o["rect"][3]-o["rect"][1]) for o in E1) \
             + sum(p["b"]-p["a"] for p in E2)
covered_len = sum(max(o["rect"][2]-o["rect"][0], o["rect"][3]-o["rect"][1]) for o in E1 if band_cov(o["rect"]) >= 0.5) \
            + sum(p["b"]-p["a"] for p in E2 if band_cov(p["rect"]) >= 0.5) \
            + sum(m["length"] for m in missing if m["classification"] == "ALIGNMENT_VARIANT")
missing_len = sum(m["length"] for m in true_missing)

metrics = {
    "MASTER_EVIDENCE_SEGMENTS": len(E1) + len(E2),
    "CANONICAL_WALL_SEGMENTS": len(M["walls"]) + len(M["parapets"]),
    "MISSING_SEGMENTS": len(true_missing),
    "ALIGNMENT_VARIANTS": len(missing) - len(true_missing),
    "MASTER_TOTAL_CENTERLINE_MM": round(master_total),
    "CANONICAL_COVERED_MM": round(covered_len),
    "MISSING_TOTAL_MM": round(missing_len),
    "LARGEST_MISSING_MM": round(max((m["length"] for m in missing), default=0)),
    "CANONICAL_COVERAGE_PCT": round(100*covered_len/master_total, 1) if master_total else None,
}
json.dump({"metrics": metrics, "missing": missing},
          open(os.path.join(OUT, "wall_coverage_audit.json"), "w"), indent=2)

# ---------------------------------------------------------------- plots
def base_ax(ax):
    ax.set_aspect("equal"); ax.set_xlim(-700, 17200); ax.set_ylim(-700, 15200)
    ax.set_xticks([]); ax.set_yticks([])

fig, ax = plt.subplots(figsize=(12, 10)); base_ax(ax)
for o in objs:  # entire FC linework, faint
    r = o["rect"]
    ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], max(1, r[3]-r[1]),
                           fc="none", ec="#bbbbbb", lw=0.4))
for w in M["walls"] + M["parapets"]:
    r = w["rect"]
    ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], fc="#000000", ec="none"))
fig.savefig(os.path.join(OUT, "CANONICAL_WALL_ONLY.png"), dpi=160, bbox_inches="tight"); plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 10)); base_ax(ax)
for o in objs:
    r = o["rect"]
    ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], max(1, r[3]-r[1]),
                           fc="none", ec="#bbbbbb", lw=0.4))
for w in M["walls"] + M["parapets"]:
    r = w["rect"]
    ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1],
                           fc="none", ec="#1f6fd6", lw=2.2))
for m in missing:
    r = m["rect"]
    ax.add_patch(Rectangle((r[0], r[1]), max(60, r[2]-r[0]), max(60, r[3]-r[1]),
                           fc="none", ec="#e02020", lw=2.2))
fig.savefig(os.path.join(OUT, "MASTER_VS_CANONICAL_WALL_OVERLAY.png"), dpi=160, bbox_inches="tight")
plt.close(fig)

print(json.dumps(metrics, indent=2))
for m in missing:
    print(f"MISS {m['kind']:9} {m['source'][:30]:32} {m['classification']:28} L={m['length']:.0f} t={m['thickness']:.0f} rect={[round(v) for v in m['rect']]}")
print("OUT:", OUT)
