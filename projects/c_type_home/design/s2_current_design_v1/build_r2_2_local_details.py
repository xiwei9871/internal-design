#!/usr/bin/env python3
"""Produce local detail review sheets from existing R2.2 measurements only."""

from __future__ import annotations

from pathlib import Path
import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Arc, Patch, Rectangle


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"


def load():
    ingest = json.loads((OUT / "latest_fcstd_ingest_v2.json").read_text(encoding="utf-8"))
    audit = json.loads((OUT / "R2_2_geometry_audit.json").read_text(encoding="utf-8"))
    geometry = json.loads((BASE / "data/geometry.json").read_text(encoding="utf-8"))
    canonical = json.loads((BASE / "current_existing/canonical_plan_v1.json").read_text(encoding="utf-8"))
    windows = json.loads((BASE / "current_existing/window_register.json").read_text(encoding="utf-8"))["windows"]
    kitchen = json.loads((BASE / "current_existing/kitchen_cabinet_register.json").read_text(encoding="utf-8"))["cabinets"]
    bboxes = {}
    for row in ingest["objects"]:
        if row.get("bbox_abs_mm"):
            b = row["bbox_abs_mm"]
            bboxes[row["label"]] = [b[0] - 1298172.0, b[1] + 296458.0, b[2] - 1298172.0, b[3] + 296458.0]
    rooms = {row["id"]: [min(p[0] for p in row["polygon_mm"]), min(p[1] for p in row["polygon_mm"]), max(p[0] for p in row["polygon_mm"]), max(p[1] for p in row["polygon_mm"])] for row in geometry["spaces"]}
    openings = {row["id"]: row["rect_mm"] for row in canonical["openings"]}
    return ingest, audit, bboxes, rooms, openings, canonical, windows, kitchen


def overlap(a, b):
    x = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    y = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return x * y


def min_translation(a, b):
    """Minimum axis translation of b to separate AABBs, report alternatives."""
    dx_left = a[0] - b[2]
    dx_right = a[2] - b[0]
    dy_down = a[1] - b[3]
    dy_up = a[3] - b[1]
    candidates = [(abs(dx_left), dx_left, 0.0, "move left"), (abs(dx_right), dx_right, 0.0, "move right"), (abs(dy_down), 0.0, dy_down, "move down"), (abs(dy_up), 0.0, dy_up, "move up")]
    return min(candidates, key=lambda x: x[0])


def find_metric(audit, text):
    return next((m for m in audit["metrics"] if m["metric"] == text), None)


def draw_base(ax, canonical, windows, kitchen, bboxes, focus=None, xlim=None, ylim=None):
    for wall in canonical["walls"]:
        x0, y0, x1, y1 = wall["rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#f1f3f5", edgecolor="#adb5bd", linewidth=0.35))
    for window in windows:
        x0, y0, x1, y1 = window["opening_rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#bde0fe", edgecolor="#087f8c", linewidth=0.8, alpha=0.7))
    for cabinet in kitchen:
        x0, y0, x1, y1 = cabinet["rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#f4a261", edgecolor="#9d2b1f", linewidth=0.4, alpha=0.55))
    for opening in canonical["openings"]:
        x0, y0, x1, y1 = opening["rect_mm"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor="#6c757d", linewidth=0.65))
        r = max(x1 - x0, y1 - y0)
        ax.add_patch(Arc((x0, y0), 2 * r, 2 * r, angle=0, theta1=0, theta2=90, color="#6c757d", linewidth=0.45))
    for label, bbox in bboxes.items():
        if focus is not None and label not in focus: continue
        x0, y0, x1, y1 = bbox
        edge = "#495057" if focus is None else "#1d3557"
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#dbeafe" if focus else "none", edgecolor=edge, linewidth=1.0, alpha=0.65))
        if focus is not None:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, label, ha="center", va="center", fontsize=6, color="#1d3557")
    ax.set_aspect("equal", adjustable="box")
    if xlim: ax.set_xlim(*xlim)
    if ylim: ax.set_ylim(*ylim)
    ax.grid(False)
    ax.set_xlabel("Task01 X (mm)")
    ax.set_ylabel("Task01 Y (mm)")


def annotate_dim(ax, x0, y0, x1, y1, label, color="#d00000"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops={"arrowstyle": "<->", "color": color, "linewidth": 1.0})
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, label, color=color, fontsize=7, ha="center", va="bottom", bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.7})


def build_pages(data):
    ingest, audit, bboxes, rooms, openings, canonical, windows, kitchen = data
    pages = []
    # A Owner ensuite
    fig, ax = plt.subplots(figsize=(10, 7), dpi=170); draw_base(ax, canonical, windows, kitchen, bboxes, focus={"次主卫湿区", "次主卫台盆和柜体", "次主卫马桶"}, xlim=(8900, 11600), ylim=(4300, 6800)); ax.set_title("DETAIL A — OWNER ENSUITE (latest FCStd; no changes)")
    wc=bboxes["次主卫马桶"]; door=openings["D-CLK"]; annotate_dim(ax,wc[0],wc[3]+120,wc[2],wc[3]+120,"WC footprint"); annotate_dim(ax,door[0],door[1]-150,door[2],door[1]-150,"door/opening"); ax.text(9050,6500,"WC front = -120.8 mm\nD-CLK overlap = 45,504.3 mm²\nminimum translation is report-only",color="#d00000",fontsize=8); pages.append(fig)
    # B mother
    fig, ax = plt.subplots(figsize=(10, 7), dpi=170); draw_base(ax, canonical, windows, kitchen, bboxes, focus={"主卧床","主卧床头柜占位","主卧衣柜","主卫湿区","主卫马桶","主卫洗手盆和柜体"}, xlim=(11600, 16500), ylim=(-200, 6900)); ax.set_title("DETAIL B — MOTHER BEDROOM + MOTHER BATH"); ax.text(11650,6500,"bed side = 173.6 mm\nWC front = -71.1 mm\nminimum translations report-only",color="#d00000",fontsize=8); pages.append(fig)
    # C guest bath
    fig, ax = plt.subplots(figsize=(9, 7), dpi=170); draw_base(ax, canonical, windows, kitchen, bboxes, focus={"客卫（湿区）","客卫马桶","客卫洗手盆柜体"}, xlim=(7700, 9900), ylim=(7600, 11200)); ax.set_title("DETAIL C — GUEST BATH"); ax.text(8000,10800,"3kg WASHER = MISSING HUMAN GUIDE\nNo position invented",color="#d00000",fontsize=9); pages.append(fig)
    # D middle guest
    fig, ax = plt.subplots(figsize=(9, 7), dpi=170); draw_base(ax, canonical, windows, kitchen, bboxes, focus={"次卧小床1.2","次卧衣柜","次卧凳子"}, xlim=(9600, 13050), ylim=(7600, 11200)); ax.set_title("DETAIL D — MIDDLE GUEST ROOM"); m=find_metric(audit,"次卧小床1.2 side clearance"); b=bboxes["次卧小床1.2"]; rb=rooms["R-STUDY"]; annotate_dim(ax,rb[0],(b[1]+b[3])/2,b[0],(b[1]+b[3])/2,f"left {b[0]-rb[0]:.1f} mm"); annotate_dim(ax,b[2],(b[1]+b[3])/2,rb[2],(b[1]+b[3])/2,f"right {rb[2]-b[2]:.1f} mm"); annotate_dim(ax,(b[0]+b[2])/2,b[3],(b[0]+b[2])/2,rb[3],f"foot {rb[3]-b[3]:.1f} mm"); pages.append(fig)
    # E balcony door/wardrobe exact reported conflict
    fig, ax = plt.subplots(figsize=(10, 6), dpi=170); draw_base(ax, canonical, windows, kitchen, bboxes, focus={"次卧衣柜"}, xlim=(9800, 12800), ylim=(10000, 11350)); ax.set_title("DETAIL E — BALCONY DOOR / WARDROBE CONFLICT"); ax.add_patch(Rectangle((10400,10700),2000,200,facecolor="none",edgecolor="#d00000",linewidth=1.5)); ax.text(10500,10950,"G-GB-BALC opening\nwardrobe overlap = 22,014.6 mm²\nminimum movement report-only",color="#d00000",fontsize=8); pages.append(fig)
    # F Study
    fig, ax = plt.subplots(figsize=(10, 7), dpi=170); draw_base(ax, canonical, windows, kitchen, bboxes, focus={"床背板+窄书桌占位","书柜","书柜001","茶台","主人椅","条凳","凳子"}, xlim=(12600, 16400), ylim=(6200, 11300)); ax.set_title("DETAIL F — STUDY"); ax.text(12700,10800,"Printer/NAS = MISSING GUIDE\nNo location invented",color="#d00000",fontsize=8); pages.append(fig)
    # G balcony
    fig, ax = plt.subplots(figsize=(10, 6), dpi=170); draw_base(ax, canonical, windows, kitchen, bboxes, focus={"洗衣机+烘干机（叠放）","冰柜"}, xlim=(7600, 13200), ylim=(10500, 13700)); ax.set_title("DETAIL G — NORTH BALCONY / LAUNDRY"); ax.add_patch(Rectangle((9800,11000),600,650,facecolor="none",edgecolor="#e76f00",linewidth=1.4,linestyle="--")); ax.add_patch(Rectangle((8500,11000),600,650,facecolor="none",edgecolor="#e76f00",linewidth=1.4,linestyle="--")); ax.text(8000,13400,"HUMAN_LOCKED stacked washer/dryer + freezer\nGeneric envelope overlay only\nservice / power / drainage = TO_VERIFY",color="#e76f00",fontsize=8); pages.append(fig)
    return pages


def main():
    data=load(); pages=build_pages(data)
    png=OUT/"R2_2_LOCAL_DETAIL_REVIEW.png"; pdf=OUT/"R2_2_LOCAL_DETAIL_REVIEW.pdf"
    # Contact sheet PNG
    fig, axes=plt.subplots(4,2,figsize=(16,24),dpi=150)
    for ax, page in zip(axes.flat,pages):
        canvas=page.canvas; canvas.draw(); w,h=canvas.get_width_height(); argb=__import__('numpy').frombuffer(canvas.tostring_argb(),dtype='uint8').reshape(h,w,4); image=argb[:, :, 1:]; ax.imshow(image); ax.axis('off'); plt.close(page)
    axes.flat[-1].axis('off'); fig.tight_layout(); fig.savefig(png,dpi=180); plt.close(fig)
    pages=build_pages(data)
    with PdfPages(pdf) as out:
        for page in pages: out.savefig(page,bbox_inches='tight'); plt.close(page)
    measurements=[
        "# R2.2 Local Measurements", "", "Status: `HUMAN_REVIEW`", "", "All values are copied from R2.2 audit outputs and latest FCStd positions. No layout object was changed.", "",
        "## Owner ensuite", "- WC front clearance: `-120.8 mm`; D-CLK overlap with 次主卫马桶: `45,504.3 mm²`.", "- Next ensuite wet-zone footprint reference: `1.44 m²`.", "- Minimum translation is report-only; not applied.", "",
        "## Mother bedroom + bath", "- Bed side clearance: `173.6 mm`.", "- Bed foot clearance: `1387.9 mm`.", "- Mother WC front clearance: `-71.1 mm`.", "- D-BATHM to vanity minimum distance: `38.5 mm`.", "",
        "## Guest bath", "- Guest WC front clearance: `1044.0 mm`.", "- 3kg washer: `MISSING HUMAN GUIDE`.", "",
        "## Middle guest room", "- Bed left/right/foot: `215.4 / 1437.8 / 1437.8 mm` based on the existing R2.2 source metric and room bounds.", "- D-GBATH and D-GBED overlap the guest bed; no move applied.", "",
        "## Owner bedroom / balcony door", "- G-GB-BALC and 次卧衣柜 overlap: `22,014.6 mm²`; minimum distance `0.0 mm`.", "- Minimum movement is report-only.", "",
        "## Study", "- Named desk/bookcase/tea-table/chair geometry exists.", "- Printer/NAS: `MISSING GUIDE`.", "",
        "## North balcony", "- Latest FCStd has stacked washer/dryer and freezer.", "- Generic envelope overlay only; service/power/drainage/ventilation remain `TO_VERIFY`.", "",
        "## Stop gate", "- `Blender = HOLD`", "- `formal_cad_allowed = false`", "- `HUMAN_REVIEW` only; no alternatives are shown.", ""]
    (OUT/"R2_2_LOCAL_MEASUREMENTS.md").write_text('\n'.join(measurements)+'\n',encoding='utf-8')
    print(json.dumps({"status":"HUMAN_REVIEW","png":str(png),"pdf":str(pdf),"measurements":str(OUT/"R2_2_LOCAL_MEASUREMENTS.md")},ensure_ascii=False))


if __name__ == '__main__': main()
