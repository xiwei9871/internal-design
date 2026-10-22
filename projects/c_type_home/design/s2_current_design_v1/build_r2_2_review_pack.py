#!/usr/bin/env python3
"""Assemble the existing R2.2 measurements into a human-review pack."""

from __future__ import annotations

from pathlib import Path
import json
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Arc, Patch, Rectangle


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
INGEST = OUT / "latest_fcstd_ingest_v2.json"
AUDIT = OUT / "R2_2_geometry_audit.json"
GEOMETRY = BASE / "data/geometry.json"
CANONICAL = BASE / "current_existing/canonical_plan_v1.json"
WINDOWS = BASE / "current_existing/window_register.json"
KITCHEN = BASE / "current_existing/kitchen_cabinet_register.json"


def load():
    return (
        json.loads(INGEST.read_text(encoding="utf-8")),
        json.loads(AUDIT.read_text(encoding="utf-8")),
        json.loads(GEOMETRY.read_text(encoding="utf-8")),
        json.loads(CANONICAL.read_text(encoding="utf-8")),
        json.loads(WINDOWS.read_text(encoding="utf-8"))["windows"],
        json.loads(KITCHEN.read_text(encoding="utf-8"))["cabinets"],
    )


def task_bbox(row):
    b = row.get("bbox_abs_mm")
    if not b:
        return None
    return [b[0] - 1298172.0, b[1] + 296458.0, b[2] - 1298172.0, b[3] + 296458.0]


def source_bbox_by_label(ingest):
    return {row["label"]: task_bbox(row) for row in ingest["objects"] if task_bbox(row)}


def fmt(v):
    return "—" if v is None else f"{v:.1f} mm"


def decision(status):
    return "NO CHANGE REQUIRED" if status in {"PASS", "ACCEPTABLE_COMPACT"} else "HUMAN DECISION REQUIRED"


def row(label, actual, target, status, conflict, door, solve):
    return {"label": label, "actual": actual, "target": target, "status": status, "conflict": conflict, "door": door, "solve": solve, "decision": decision(status)}


def build_sections(audit):
    metrics = audit["metrics"]
    doors = audit["door_collision_report"]
    by_metric = {x["metric"]: x for x in metrics}
    sections = [
        {
            "title": "1. OWNER ENSUITE",
            "description": "最新 FCStd 已有次主卫湿区、台盆柜体和马桶对象。当前布局、顺序、朝向和出入口关系均按人工方案保留；本包只汇总测量结果。",
            "rows": [
                row("次主卫马桶 front clearance", by_metric["次主卫马桶 front clearance"]["available_mm"], by_metric["次主卫马桶 front clearance"]["target_mm"], "CONFLICT", "shortfall 920.8 mm", "D-CLK overlaps 次主卫马桶 (45,504.3 mm²)", "Would require a human decision on fixture/door/partition relationship; no automatic move."),
                row("次主卫湿区 internal footprint", by_metric["次主卫湿区 internal footprint"]["available_mm"], None, "TO_VERIFY", "area is reference only", "D-CLK overlaps wet-zone guide (1,309.2 mm²)", "Confirm actual internal boundary and door opening before judging usability."),
                row("Owner ensuite door/opening", None, None, "TO_VERIFY", "not measurable as a named FCStd door", "D-CLK is the canonical candidate; swing remains TO_VERIFY", "Confirm the real door/opening in field or FreeCAD."),
            ],
        },
        {
            "title": "2. MOTHER BEDROOM + MOTHER BATH",
            "description": "母亲主卧床、衣柜、床头柜和主卫三件套均来自最新 FCStd。母亲卧室与主卫关系保持不变。",
            "rows": [
                row("主卧床 side clearance", by_metric["主卧床 side clearance"]["available_mm"], by_metric["主卧床 side clearance"]["target_mm"], "CONFLICT", "shortfall 426.4 mm", "No direct door overlap in this metric", "Human decision required if assisted-side clearance is to be increased."),
                row("主卧床 foot clearance", by_metric["主卧床 foot clearance"]["available_mm"], by_metric["主卧床 foot clearance"]["target_mm"], "PASS", "none", "none", "none"),
                row("主卫马桶 front clearance", by_metric["主卫马桶 front clearance"]["available_mm"], by_metric["主卫马桶 front clearance"]["target_mm"], "CONFLICT", "shortfall 871.1 mm", "D-BATHM low clearance to 主卫洗手盆和柜体: 38.5 mm", "Human decision required; do not move fixture automatically."),
                row("主卫湿区 footprint", by_metric["主卫湿区 internal footprint"]["available_mm"], None, "TO_VERIFY", "area reference only", "door/fixture usability requires field check", "Verify wet/dry and assisted-use clearances."),
            ],
        },
        {
            "title": "3. GUEST BATH",
            "description": "客卫边界和最新 FCStd 的客卫湿区、马桶、台盆柜体保持不变。3kg 小洗衣机在最新 FCStd 中没有命名对象。",
            "rows": [
                row("客卫马桶 front clearance", by_metric["客卫马桶 front clearance"]["available_mm"], by_metric["客卫马桶 front clearance"]["target_mm"], "PASS", "none", "none", "none"),
                row("客卫（湿区） footprint", by_metric["客卫（湿区） internal footprint"]["available_mm"], None, "TO_VERIFY", "area reference only", "door swing remains part of audit", "Verify shower/wet-zone usable arrangement without enlarging boundary."),
                row("3kg small washer", None, 600, "TO_VERIFY", "not available: no named latest-FCStd object", "no washer-specific door conflict measured", "Human decision required: add/confirm its exact position in FreeCAD."),
            ],
        },
        {
            "title": "4. MIDDLE GUEST ROOM + OWNER BEDROOM",
            "description": "中间客房与 owner bedroom 的最新人工对象均按 FCStd 保持；本节记录床侧/床尾和既有门洞关系。",
            "rows": [
                row("次卧小床1.2 side clearance", by_metric["次卧小床1.2 side clearance"]["available_mm"], by_metric["次卧小床1.2 side clearance"]["target_mm"], "CONFLICT", "shortfall 384.6 mm", "D-GBATH overlap 57,256.8 mm²; D-GBED overlap 110,275.0 mm²", "Human decision required; no bed rotation or relocation applied."),
                row("次卧小床1.2 foot clearance", by_metric["次卧小床1.2 foot clearance"]["available_mm"], by_metric["次卧小床1.2 foot clearance"]["target_mm"], "PASS", "none", "none", "none"),
                row("次主卧床 side clearance", by_metric["次主卧床 side clearance"]["available_mm"], by_metric["次主卧床 side clearance"]["target_mm"], "CONFLICT", "shortfall 366.6 mm", "none in direct metric", "Human decision required if owner bed access is to be widened."),
                row("次主卧床 foot clearance", by_metric["次主卧床 foot clearance"]["available_mm"], by_metric["次主卧床 foot clearance"]["target_mm"], "PASS", "none", "none", "none"),
                row("次卧衣柜 / balcony door", None, 100, "CONFLICT", "0 mm minimum distance; overlap 22,014.6 mm²", "G-GB-BALC overlap 次卧衣柜", "Human decision required; do not move wardrobe automatically."),
            ],
        },
        {
            "title": "5. STUDY",
            "description": "书房按最新 FCStd 的床背板+窄书桌、书柜、茶台、椅、条凳和凳子读取。正式办公设备没有单独命名对象。",
            "rows": [
                row("Formal workstation / chair pull-back", None, 900, "TO_VERIFY", "no named printer/NAS or explicit operating-zone object", "no dedicated door collision measured", "Human decision required: verify workstation operation, dual monitors, printer and NAS access."),
                row("Bookcase / tea-table topology", None, None, "PASS", "no numerical target in source report", "none directly reported", "No change required for topology; usability still needs human review."),
                row("Study printer/NAS provision", None, None, "TO_VERIFY", "missing named object in latest FCStd", "none", "Human decision required: add/confirm only if desired in FreeCAD."),
            ],
        },
        {
            "title": "6. DINING + NORTH BALCONY / LAUNDRY",
            "description": "餐桌、三把命名餐椅和未命名辅助餐椅按最新 FCStd 读取。北阳台洗衣机+烘干机叠放对象已存在；本包只核验，不改变并排/叠放关系。",
            "rows": [
                row("餐椅 table gap", by_metric["餐椅 table gap"]["available_mm"], by_metric["餐椅 table gap"]["target_mm"], "CONFLICT", "shortfall 28.9 mm", "none direct; G-DIN-LIV / 鞋柜 overlap 4,490.6 mm²", "Human decision required; do not shift table/chairs automatically."),
                row("餐椅003 table gap", by_metric["餐椅003 table gap"]["available_mm"], by_metric["餐椅003 table gap"]["target_mm"], "CONFLICT", "shortfall 28.9 mm", "none direct", "Human decision required."),
                row("餐椅004 table gap", by_metric["餐椅004 table gap"]["available_mm"], by_metric["餐椅004 table gap"]["target_mm"], "PASS", "none", "none", "none"),
                row("洗衣机+烘干机（叠放）", None, None, "TO_VERIFY", "latest object present; generic/SKU envelope not measured here", "glass-door/service relationship remains TO_VERIFY", "Human decision required for SKU, service, ventilation and balcony conditions."),
                row("Main laundry service", None, None, "TO_VERIFY", "drainage/power/SKU not verified", "none", "Human decision required; no equipment movement applied."),
            ],
        },
    ]
    return sections


def issues_for_image(ingest, audit):
    bbox_by_label = {row["label"]: task_bbox(row) for row in ingest["objects"] if task_bbox(row)}
    issues = []
    seen = set()
    def add(label, text, color="#d00000"):
        bbox = bbox_by_label.get(label)
        if not bbox: return
        key = (label, text)
        if key in seen: return
        seen.add(key)
        issues.append({"label": label, "text": text, "bbox": bbox, "color": color})
    for metric in audit["metrics"]:
        if metric["status"] in {"CONFLICT", "TO_VERIFY"}:
            label = metric["metric"].split(" ")[0]
            add(label, metric["status"])
    for collision in audit["door_collision_report"]:
        if collision["status"] in {"CONFLICT", "CLEARANCE_LOW"}:
            add(collision["object"], collision["status"])
    add("洗衣机+烘干机（叠放）", "TO_VERIFY", "#e76f00")
    return issues


def render_issues(ingest, audit, geometry, canonical, windows, kitchen):
    fig, ax = plt.subplots(figsize=(16, 12), dpi=180)
    for wall in canonical["walls"]:
        x0, y0, x1, y1 = wall["rect_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#e9ecef", edgecolor="#6c757d", linewidth=0.4))
    for window in windows:
        x0, y0, x1, y1 = window["opening_rect_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#bde0fe", edgecolor="#087f8c", linewidth=0.8, alpha=0.65))
    for cabinet in kitchen:
        x0, y0, x1, y1 = cabinet["rect_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#f4a261", edgecolor="#9d2b1f", linewidth=0.4, alpha=0.5))
    for row in ingest["objects"]:
        bbox = task_bbox(row)
        if bbox: ax.add_patch(Rectangle((bbox[0], bbox[1]), bbox[2] - bbox[0], bbox[3] - bbox[1], facecolor="none", edgecolor="#adb5bd", linewidth=0.35, alpha=0.7))
    issues = issues_for_image(ingest, audit)
    for index, issue in enumerate(issues, 1):
        x0, y0, x1, y1 = issue["bbox"]; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        ax.add_patch(plt.Circle((cx, cy), 120, facecolor=issue["color"], edgecolor="white", linewidth=1.0, zorder=5))
        ax.text(cx, cy, str(index), ha="center", va="center", color="white", fontsize=8, weight="bold", zorder=6)
    ax.set_aspect("equal", adjustable="box"); ax.set_xlim(1000, 16600); ax.set_ylim(-1000, 14500); ax.set_xlabel("Task01 X (mm)"); ax.set_ylabel("Task01 Y (mm)"); ax.set_title("R2.2 Critical Issues — current latest-FCStd positions only")
    ax.legend(handles=[Patch(facecolor="#e9ecef", edgecolor="#6c757d", label="Current structure / guide geometry"), Patch(facecolor="#d00000", label="Conflict / low clearance"), Patch(facecolor="#e76f00", label="TO_VERIFY")], loc="upper left", fontsize=8)
    fig.tight_layout(); out = OUT / "R2_2_CRITICAL_ISSUES.png"; fig.savefig(out, dpi=220); plt.close(fig)
    return out, issues


def main():
    ingest, audit, geometry, canonical, windows, kitchen = load()
    sections = build_sections(audit)
    issue_png, issues = render_issues(ingest, audit, geometry, canonical, windows, kitchen)
    md = ["# R2.2 HUMAN REVIEW PACK", "", "Status: `HUMAN_REVIEW`", "", "Layout fidelity: `PASS`", "", "This pack only reorganizes existing R2.2 measurements. It does not recalculate layout, move objects, rotate objects, or propose replacement layouts.", "", f"Latest FCStd SHA256: `{audit['source_fcstd_sha256']}`", ""]
    for section in sections:
        md += [f"## {section['title']}", "", section["description"], "", "| Finding | Actual measured clearance | Target/reference | Status | Conflict amount | Door collision | What would need to change to solve it | Decision |", "|---|---:|---:|---|---|---|---|---|"]
        for r in section["rows"]:
            md.append(f"| {r['label']} | {r['actual'] if r['actual'] is not None else '—'} | {r['target'] if r['target'] is not None else '—'} | `{r['status']}` | {r['conflict']} | {r['door']} | {r['solve']} | **{r['decision']}** |")
        md.append("")
    md += ["## Critical issue map", "", "Numbers correspond to `R2_2_CRITICAL_ISSUES.png`. No alternative layout is shown.", "", "| # | Object / source | Existing status |", "|---:|---|---|"]
    for index, issue in enumerate(issues, 1): md.append(f"| {index} | {issue['label']} | `{issue['text']}` |")
    md += ["", "## Stop gate", "", "`LATEST_HUMAN_GUIDE = HUMAN_REVIEW`", "`S2_LAYOUT = HOLD`", "`Blender = HOLD`", "`formal_cad_allowed = false`", "", "No furniture position, orientation, room assignment or wall anchor was changed in this pack."]
    md_path = OUT / "R2_2_HUMAN_REVIEW_PACK.md"; md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    pdf_path = OUT / "R2_2_HUMAN_REVIEW_PACK.pdf"
    with PdfPages(pdf_path) as pages:
        fig, ax = plt.subplots(figsize=(11, 8.5)); ax.axis("off"); ax.text(0.02, 0.98, "R2.2 HUMAN REVIEW PACK", va="top", fontsize=18, weight="bold")
        y = 0.92
        for section in sections:
            ax.text(0.02, y, section["title"], va="top", fontsize=11, weight="bold"); y -= 0.035
            ax.text(0.02, y, textwrap.fill(section["description"], 125), va="top", fontsize=7); y -= 0.065
            for r in section["rows"]:
                line = f"{r['label']}: {r['actual'] or '—'} / target {r['target'] or '—'} / {r['status']} / {r['conflict']} / {r['decision']}"
                ax.text(0.03, y, textwrap.fill(line, 135), va="top", fontsize=6.3); y -= 0.033
                if y < 0.08:
                    pages.savefig(fig); plt.close(fig); fig, ax = plt.subplots(figsize=(11, 8.5)); ax.axis("off"); y = 0.95
            y -= 0.015
        pages.savefig(fig); plt.close(fig)
        image = plt.imread(issue_png); fig, ax = plt.subplots(figsize=(11, 8.5)); ax.imshow(image); ax.axis("off"); ax.set_title("R2.2 Critical Issues"); pages.savefig(fig, bbox_inches="tight"); plt.close(fig)
    print(json.dumps({"status": "HUMAN_REVIEW", "markdown": str(md_path), "pdf": str(pdf_path), "issue_png": str(issue_png), "issues": len(issues)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
