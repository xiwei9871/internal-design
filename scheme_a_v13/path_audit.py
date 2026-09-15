"""漫游路径平面核对图：路径叠加在 A7 平面几何上，标注方向与关键节点。"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Rectangle

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT.parent / "scheme_a_v7" / "scheme_a_geometry.json").read_text(encoding="utf-8"))

PATH = [(1120, 715), (980, 735), (1040, 820), (1040, 1000), (960, 1060),
        (870, 1120), (855, 1250), (880, 1130), (980, 1030), (1085, 940),
        (1085, 800), (970, 735), (860, 735), (770, 735), (710, 745),
        (700, 860), (640, 870), (540, 870), (515, 1050), (545, 1180),
        (600, 1205)]

fig, ax = plt.subplots(figsize=(10, 10))
for w in DATA["walls"]:
    ax.add_patch(MplPoly(w["polygon"], closed=True, facecolor="#333", edgecolor="none"))
ax.add_patch(MplPoly(DATA["outer"], closed=True, fill=False, edgecolor="#333", lw=1.5))
for f in DATA["furniture"]:
    x, y, w_, h = f["rect"]
    ax.add_patch(Rectangle((x, y), w_, h, facecolor="#e8d9c0", edgecolor="#b09a72", lw=0.8))
for name, px, py in DATA["labels"]:
    ax.text(px, py, name, ha="center", va="center", fontsize=9, color="#555")

xs = [p[0] for p in PATH]
ys = [p[1] for p in PATH]
ax.plot(xs, ys, "-o", color="#c0392b", lw=2, ms=4, zorder=5)
for i, p in enumerate(PATH):
    ax.annotate(str(i + 1), p, fontsize=7, ha="center", va="center",
                color="white", zorder=6,
                bbox=dict(boxstyle="circle,pad=0.15", fc="#c0392b", ec="none"))
ax.annotate("起点·入户", PATH[0], xytext=(PATH[0][0] - 60, PATH[0][1] - 70),
            fontsize=9, color="#c0392b",
            arrowprops=dict(arrowstyle="->", color="#c0392b"))
ax.annotate("终点·窗边", PATH[-1], xytext=(PATH[-1][0] - 130, PATH[-1][1] + 30),
            fontsize=9, color="#c0392b",
            arrowprops=dict(arrowstyle="->", color="#c0392b"))

ax.set_aspect("equal")
ax.invert_yaxis()  # 源像素坐标 Y 向下
ax.set_title("A13 漫游路径（24.5s 一镜到底，相机 H1550 注视 H1350）", fontsize=12)
plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Arial Unicode MS"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.unicode_minus"] = False
out = ROOT / "walkthrough_path_audit.png"
fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
print(out)
