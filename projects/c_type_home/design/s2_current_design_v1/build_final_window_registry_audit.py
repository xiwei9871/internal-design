#!/usr/bin/env python3
"""Verify the historical 95ab90e window registry and compare it read-only."""

from __future__ import annotations

from pathlib import Path
import csv
import json
import subprocess


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
FCSTD = BASE / "cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd"


def git_bytes(ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)


def rect_from_record(record):
    return record.get("opening_rect_mm")


def overlap(a, b, pad=0.0):
    return not (a[2] < b[0] - pad or a[0] > b[2] + pad or a[3] < b[1] - pad or a[1] > b[3] + pad)


def task_bbox(row):
    b = row["bbox_abs_mm"]
    return [b[0] - 1298172.0, b[1] + 296458.0, b[2] - 1298172.0, b[3] + 296458.0]


def expected_geometry_region(record):
    rect = record["opening_rect_mm"]
    points = [rect]
    if record.get("bay"):
        points += [record["bay"]["front"]] + record["bay"]["jambs"]
    x0 = min(p[0] for p in points); y0 = min(p[1] for p in points); x1 = max(p[2] for p in points); y1 = max(p[3] for p in points)
    return [x0, y0, x1, y1]


def main():
    ref = "95ab90e"
    registry_path = "projects/c_type_home/current_existing/window_register.json"
    csv_path = "projects/c_type_home/current_existing/window_register.csv"
    gates_path = "projects/c_type_home/qc/task03a_gates.json"
    historical_registry_bytes = git_bytes(ref, registry_path)
    historical_csv_bytes = git_bytes(ref, csv_path)
    historical_gates = json.loads(git_bytes(ref, gates_path))
    historical_registry = json.loads(historical_registry_bytes)
    gates_pass = len(historical_gates.get("gates", [])) == 28 and sum(x.get("result") == "PASS" for x in historical_gates.get("gates", [])) == 28 and historical_gates.get("overall") == "PASS"
    registry_pass = len(historical_registry.get("windows", [])) == 9
    if not registry_pass or not gates_pass:
        raise RuntimeError("HISTORICAL_SOURCE_MISMATCH")
    (OUT / "FINAL_WINDOW_REGISTER_95ab90e.json").write_bytes(historical_registry_bytes)
    (OUT / "FINAL_WINDOW_REGISTER_95ab90e.csv").write_bytes(historical_csv_bytes)
    # Use the latest FCStd extraction generated in this task, not old R2/R2.1 data.
    structure = json.loads((OUT / "latest_fcstd_structure_v3.json").read_text(encoding="utf-8"))
    names = json.loads((OUT / "latest_fcstd_names_v3.json").read_text(encoding="utf-8"))
    named_labels = {row["label"] for row in names["labels"]}
    geometry_rows = []
    for row in structure["rows"]:
        geometry_rows.append({"name": row["name"], "type": row["type"], "bbox_task01_mm": task_bbox(row)})
    comparisons = []
    restore = []
    for record in historical_registry["windows"]:
        rect = record["opening_rect_mm"]
        region = expected_geometry_region(record)
        named_hits = [label for label in named_labels if record["window_id"] in label or label == record["window_id"]]
        geometry_hits = [row for row in geometry_rows if overlap(row["bbox_task01_mm"], region, pad=8.0)]
        if named_hits:
            status = "PRESENT_NAMED"; action = "NO_ACTION"
        elif geometry_hits:
            status = "PRESENT_UNNAMED_GEOMETRY"; action = "CREATE_SEMANTIC_REFERENCE"
        else:
            status = "MISSING"; action = "RESTORE_MISSING_OPENING_FROM_FINAL_REGISTRY"
        comparisons.append({"final_registry_id": record["window_id"], "type": record["type"], "host_wall": record.get("host_wall_id"), "opening_rect_mm": rect, "source_status": record.get("current_status"), "current_fcstd_status": status, "matched_current_objects": [row["name"] for row in geometry_hits] + named_hits, "geometry_region_checked_mm": region})
        restore.append({"final_registry_id": record["window_id"], "current_status": status, "matched_current_objects": [row["name"] for row in geometry_hits] + named_hits, "required_action": action})
    summary = {"historical_commit": ref, "historical_registry_count": len(historical_registry["windows"]), "historical_task03a_gates": "28/28 PASS", "current_fcstd_sha256": names["source_sha256"], "current_fcstd_structure_count": structure["count"], "comparison": comparisons, "window_history_source": "VERIFIED", "window_restore": "HUMAN_REVIEW", "blender": "HOLD", "formal_cad_allowed": False}
    (OUT / "CURRENT_FCSTD_VS_FINAL_WINDOW_REGISTER.md").write_text("# Current FCStd vs Final Window Registry (95ab90e)\n\n" + f"Historical source: `{ref}`\n\n" + "| ID | Final type | Host wall | Current FCStd status | Matched geometry objects |\n|---|---|---|---|---|\n" + "\n".join(f"| {x['final_registry_id']} | {x['type']} | {x['host_wall'] or '—'} | `{x['current_fcstd_status']}` | {', '.join(x['matched_current_objects']) or '—'} |" for x in comparisons) + "\n\nNo modifications were made.\n", encoding="utf-8")
    (OUT / "window_restore_plan_v02.json").write_text(json.dumps({"schema": "window-restore-plan-v02", "status": "HUMAN_REVIEW", "historical_source": ref, "allowed_actions": ["RENAME_EXISTING_GEOMETRY", "CREATE_SEMANTIC_REFERENCE", "RESTORE_MISSING_OPENING_FROM_FINAL_REGISTRY", "NO_ACTION"], "items": restore, "no_execution": True}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = ["# FINAL WINDOW REGISTER — 95ab90e", "", "Historical source verified: `95ab90e`", "", "- Registry count: 9", "- Task03A gates: 28/28 PASS", "- Current FCStd comparison is read-only.", "", "| ID | Type | Host wall | Start | End | Center | Width | Orientation | Source status |", "|---|---|---|---|---|---|---:|---|---|"]
    for record in historical_registry["windows"]:
        x0,y0,x1,y1=record["opening_rect_mm"]; center=((x0+x1)/2,(y0+y1)/2); width=record.get("clear_width_mm",record.get("span_mm"))
        md.append(f"| {record['window_id']} | {record['type']} | {record.get('host_wall_id') or '—'} | ({x0}, {y0}) | ({x1}, {y1}) | ({center[0]}, {center[1]}) | {width} | {record['orientation']} | {record['current_status']} |")
    md += ["", "Current FCStd source of comparison:", f"`{names['source_sha256']}`", "", "The registry is copied from Git history unchanged. No restore was applied."]
    (OUT / "FINAL_WINDOW_REGISTER_95ab90e.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (OUT / "window_history_verification_v02.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "VERIFIED", "registry_count": 9, "gates": "28/28 PASS", "comparison": {x["current_fcstd_status"]: sum(y["current_fcstd_status"] == x["current_fcstd_status"] for y in comparisons) for x in comparisons}, "restore": "HUMAN_REVIEW"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
