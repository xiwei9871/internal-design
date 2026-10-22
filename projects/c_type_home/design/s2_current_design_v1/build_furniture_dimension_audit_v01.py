#!/usr/bin/env python3
"""Audit plausible furniture/fixture footprints from the latest FCStd only."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
INGEST = OUT / "fresh_fcstd_dimension_audit.json"
ASSET_MANIFEST = BASE / "assets/cad_library/standard/manifests/design_legend_manifest_v01.json"


EXCLUDE = {"Rectangle", "Rectangle033", "Circle013", "Text", "Text001", "Text002", "Line517", "Line518", "Line519"}


def task_bbox(row):
    b = row.get("bbox_abs_mm")
    if not b:
        return None
    return [b[0] - 1298172.0, b[1] + 296458.0, b[2] - 1298172.0, b[3] + 296458.0]


def room_for(label):
    if any(x in label for x in ("沙发", "角几", "茶几", "lounge", "电视柜", "三人位")): return "living"
    if "餐" in label: return "dining"
    if "次主卧" in label: return "owner_bedroom"
    if "主卧" in label: return "mother_bedroom"
    if "次卧" in label: return "middle_guest_room"
    if any(x in label for x in ("书柜", "矮书柜", "茶台", "主人椅", "条凳", "凳子", "床背板", "打印机", "nas")): return "study"
    if "客卫" in label: return "guest_bath"
    if "次主卫" in label: return "owner_ensuite"
    if "主卫" in label: return "mother_bath"
    if any(x in label for x in ("洗衣", "烘干", "冰柜")): return "north_balcony_laundry"
    if any(x in label for x in ("橱柜", "现有橱柜")): return "kitchen"
    if "斜坡" in label: return "transition"
    if "鞋柜" in label: return "entry"
    return "unknown"


def category_for(label):
    if "床" in label: return "bed"
    if "沙发" in label or label == "lounge": return "seating"
    if "餐桌" in label: return "dining_table"
    if "餐椅" in label or "Circle013" in label: return "dining_chair"
    if "茶几" in label: return "coffee_table"
    if "角几" in label: return "side_table"
    if "衣柜" in label: return "wardrobe"
    if "书柜" in label or "矮书柜" in label: return "bookcase"
    if "书桌" in label or "书桌" in label or "床背板" in label: return "desk"
    if "茶台" in label: return "tea_table"
    if "主人椅" in label or label in {"凳子", "次卧凳子", "条凳"}: return "chair_bench_stool"
    if "马桶" in label: return "wc"
    if "台盆" in label or "洗手盆" in label: return "vanity"
    if "湿区" in label: return "shower_zone"
    if "洗衣机" in label or "烘干" in label: return "washer_dryer"
    if "冰柜" in label: return "freezer"
    if "打印机" in label or "nas" in label: return "equipment"
    if "橱柜" in label: return "cabinet"
    if "鞋柜" in label: return "shoe_storage"
    if "斜坡" in label: return "ramp"
    if "电视柜" in label: return "media_edge"
    return "other"


def spec(label, width, depth, width_range, depth_range, rec_width, rec_depth, classification, reason, source_type, user_confirmed=False, rec_height=None):
    return {
        "reference_width_range_mm": width_range,
        "reference_depth_range_mm": depth_range,
        "recommended_blockout_width_mm": rec_width,
        "recommended_blockout_depth_mm": rec_depth,
        "recommended_blockout_height_mm": rec_height,
        "classification": classification,
        "reason": reason,
        "source_type": source_type,
        "user_confirmed_dimension": user_confirmed,
    }


def audit_spec(label, width, depth):
    # User-confirmed beds: preserve the current guide axes and do not override.
    if label == "主卧床":
        return spec(label, width, depth, [1500, 1500], [2100, 2100], width, depth, "USER_CONFIRMED_DO_NOT_CHANGE", "User-confirmed 1500x2100 mother bed; current axes preserve the locked guide orientation.", "USER_CONFIRMED", True)
    if label == "次主卧床":
        return spec(label, width, depth, [1500, 1500], [2100, 2100], width, depth, "USER_CONFIRMED_DO_NOT_CHANGE", "User-confirmed 1500x2100 owner bed; current axes preserve the locked guide orientation.", "USER_CONFIRMED", True)
    if label == "次卧小床1.2":
        return spec(label, width, depth, [1200, 1200], [1800, 1800], width, depth, "USER_CONFIRMED_DO_NOT_CHANGE", "User-confirmed 1200x1800 guest bed; current axes preserve the locked guide orientation.", "USER_CONFIRMED", True)
    if label in {"三人位沙发", "Rectangle"}:
        return spec(label, width, depth, [2000, 2400], [850, 1000], 2200 if depth > width else 2200, 900, "RECOMMEND_RESIZE", "Current guide aspect is much longer/narrower than a normal 3-seat sofa; preserve orientation, resize only after human decision.", "MARKET_REFERENCE")
    if label == "双人位沙发":
        return spec(label, width, depth, [1500, 1900], [850, 1000], 1800, 850, "MINOR_ADJUSTMENT", "Depth is slightly below the compact reference; no automatic change.", "ASSET_LIBRARY")
    if label == "lounge":
        return spec(label, width, depth, [800, 1000], [1500, 1900], 1700, 900, "RECOMMEND_RESIZE", "Current footprint is a long shallow guide; chaise reference should be elongated with a more usable depth. Preserve long-axis direction.", "MARKET_REFERENCE")
    if label == "茶几":
        return spec(label, width, depth, [450, 600], [800, 1000], 500, 900, "RECOMMEND_RESIZE", "Current long axis is plausible as a coffee table only after a depth/length calibration; no automatic rotation.", "GENERIC_REFERENCE")
    if label == "角几":
        return spec(label, width, depth, [400, 500], [400, 500], 450, 450, "MINOR_ADJUSTMENT", "Current side table is larger than the common compact reference.", "GENERIC_REFERENCE")
    if "电视柜" in label:
        return spec(label, width, depth, None, None, None, None, "SKU_TO_VERIFY", "Media edge intent is ambiguous (cabinet or suspended media wall); no generic resize should be applied.", "TO_VERIFY")
    if "床头柜占位" in label:
        return spec(label, width, depth, [450, 500], [400, 450], 450, 450, "RECOMMEND_RESIZE", "This is a placeholder guide, not a literal nightstand footprint.", "GENERIC_REFERENCE")
    if "衣柜" in label:
        rec_w = width if width >= 1000 else 2000
        rec_d = 600
        return spec(label, width, depth, [550, 650], [550, 650], rec_w, rec_d, "OK" if abs(depth - 600) <= 50 or abs(width - 600) <= 50 else "MINOR_ADJUSTMENT", "Wardrobe depth is assessed against the 600 mm generic reference while preserving wall/axis intent.", "MARKET_REFERENCE")
    if "餐桌" in label:
        return spec(label, width, depth, [1400, 1600], [750, 850], 1500, 800, "MINOR_ADJUSTMENT", "Current table is slightly shallow versus the compact reference; preserve long-axis direction.", "USER_CONFIRMED")
    if "餐椅" in label or label == "Circle013":
        return spec(label, width, depth, [450, 550], [500, 600], 500, 550, "MINOR_ADJUSTMENT", "Current circular guide is a compact placeholder; chair product envelope is larger.", "GENERIC_REFERENCE")
    if "书桌" in label or "床背板" in label:
        return spec(label, width, depth, [1600, 1800], [700, 800], 1700, 800, "RECOMMEND_RESIZE", "Current object is a narrow backboard/desk placeholder and does not represent a dual-monitor workstation footprint.", "MARKET_REFERENCE")
    if label in {"书柜", "矮书柜"}:
        return spec(label, width, depth, [300, 350], [300, 350], width, depth, "CUSTOM_FURNITURE_PLAUSIBLE", "Custom full-height/low bookcase guide; depth and joinery require furniture design/SKU review.", "GENERIC_REFERENCE")
    if label == "茶台":
        return spec(label, width, depth, [600, 900], [800, 1500], 800, 1200, "RECOMMEND_RESIZE", "Current 2200 mm long tea-table guide is unusually large for a tea surface; preserve guide axis.", "GENERIC_REFERENCE")
    if label in {"主人椅", "凳子", "次卧凳子"}:
        return spec(label, width, depth, [450, 550], [500, 600], 500, 550, "MINOR_ADJUSTMENT", "Current 400 mm circular placeholder is below a common seated footprint.", "GENERIC_REFERENCE")
    if label == "条凳":
        return spec(label, width, depth, [350, 500], [1200, 1800], 400, 1500, "MINOR_ADJUSTMENT", "Bench depth is slightly below a comfortable reference; preserve long axis.", "GENERIC_REFERENCE")
    if "马桶" in label:
        if width >= 650 and depth <= 450:
            return spec(label, width, depth, [650, 750], [380, 420], 700, 400, "MINOR_ADJUSTMENT", "Current footprint is plausible but shallow; confirm actual SKU and orientation.", "GENERIC_REFERENCE")
        return spec(label, width, depth, [380, 420], [650, 750], width, depth, "SKU_TO_VERIFY", "Axis-swapped WC guide is plausible but fixture orientation/SKU must be verified.", "TO_VERIFY")
    if "台盆" in label or "洗手盆" in label:
        if width >= 900 and depth <= 550:
            return spec(label, width, depth, [600, 1200], [500, 550], width, 500, "OK", "Vanity depth is in the normal range; width is room-specific.", "GENERIC_REFERENCE")
        return spec(label, width, depth, [600, 900], [500, 550], width, depth, "SKU_TO_VERIFY", "Guide appears composite or axis-swapped; verify actual cabinet product before Blender.", "TO_VERIFY")
    if "湿区" in label:
        return spec(label, width, depth, [900, 1000], [900, 1200], width, depth, "SKU_TO_VERIFY", "Wet-zone guide is a region, not a final shower product footprint.", "TO_VERIFY")
    if "洗衣机+烘干机" in label:
        return spec(label, width, depth, [600, 600], [600, 650], 600, 650, "SKU_TO_VERIFY", "Current stacked arrangement is human-locked; generic appliance depth/SKU and service clearances remain to verify.", "TO_VERIFY")
    if label == "3kg洗衣机":
        return spec(label, width, depth, [450, 600], [450, 650], width, depth, "SKU_TO_VERIFY", "Small-washer guide is present; final product and service clearances remain to verify.", "TO_VERIFY")
    if label == "冰柜":
        return spec(label, width, depth, [600, 1000], [600, 750], 800, 650, "SKU_TO_VERIFY", "Freezer footprint is market-plausible but needs selected SKU, door and ventilation check.", "TO_VERIFY")
    if label in {"打印机", "nas"}:
        return spec(label, width, depth, [300, 600], [300, 600], width, depth, "OK", "Current equipment placeholder is a plausible generic envelope; final model is TO_VERIFY.", "GENERIC_REFERENCE")
    if "斜坡" in label:
        return spec(label, width, depth, None, None, width, depth, "SKU_TO_VERIFY", "Assisted route guide; slope, landings and code status remain field verification.", "TO_VERIFY")
    if "橱柜" in label or "鞋柜" in label:
        return spec(label, width, depth, None, None, width, depth, "CUSTOM_FURNITURE_PLAUSIBLE", "Existing/custom fixed item; field/SKU verification required.", "USER_CONFIRMED")
    return spec(label, width, depth, None, None, width, depth, "TO_VERIFY", "No reliable category reference without inventing a product assumption.", "TO_VERIFY")


def main():
    report = json.loads(INGEST.read_text(encoding="utf-8"))
    objects = []
    for row in report["objects"]:
        label = row["label"]
        if label in EXCLUDE or not row.get("bbox_abs_mm") or label in {"Text", "Text001", "Text002"}:
            continue
        bbox = task_bbox(row)
        width, depth = bbox[2] - bbox[0], bbox[3] - bbox[1]
        category = category_for(label)
        spec_row = audit_spec(label, width, depth)
        objects.append({
            "object_name": row["name"],
            "object_label": label,
            "room": room_for(label),
            "category": category,
            "current_width_mm": round(width, 3),
            "current_depth_mm": round(depth, 3),
            "current_height_mm": None,
            "user_confirmed_dimension": spec_row.pop("user_confirmed_dimension"),
            "reference_width_range_mm": spec_row.pop("reference_width_range_mm"),
            "reference_depth_range_mm": spec_row.pop("reference_depth_range_mm"),
            **spec_row,
            "difference_width_mm": None if spec_row["recommended_blockout_width_mm"] is None else round(spec_row["recommended_blockout_width_mm"] - width, 3),
            "difference_depth_mm": None if spec_row["recommended_blockout_depth_mm"] is None else round(spec_row["recommended_blockout_depth_mm"] - depth, 3),
            "source_bbox_task01_mm": [round(v, 3) for v in bbox],
        })
    asset_manifest = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    legends = asset_manifest.get("legends", [])
    asset_candidates = [{"id": x.get("id"), "category": x.get("category"), "normalized_bbox_mm": x.get("design_target_bbox_mm"), "file": x.get("normalized_file")} for x in legends]
    audit = {"schema": "furniture-dimension-audit-v01", "status": "HUMAN_REVIEW", "source_fcstd": str(BASE / "cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd"), "source_mtime": report["source_mtime"], "source_sha256": report["source_sha256"], "freecad_object_count": report["freecad_object_count"], "named_object_count": report["named_object_count"], "fcstd_modified": False, "asset_library_candidates": asset_candidates, "objects": objects, "policy": {"position": "HUMAN_LOCKED", "orientation": "HUMAN_LOCKED", "topology": "HUMAN_LOCKED", "no_auto_modification": True, "blender": "HOLD", "formal_cad_allowed": False}}
    (OUT / "furniture_dimension_register_v03.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = list(objects[0].keys())
    with (OUT / "FURNITURE_DIMENSION_AUDIT_V01.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore"); writer.writeheader(); writer.writerows(objects)
    md = ["# FURNITURE DIMENSION AUDIT V01", "", "Status: `FURNITURE_DIMENSION_GATE = HUMAN_REVIEW`", "", f"Source mtime: `{report['source_mtime']}`", f"Source SHA256: `{report['source_sha256']}`", f"FreeCAD objects: {report['freecad_object_count']}; named objects audited: {len(objects)}", "", "No FCStd object was moved, rotated, resized, replaced or redesigned.", "", "## Classification legend", "", "- `OK`: plausible generic footprint.", "- `MINOR_ADJUSTMENT`: small reference mismatch; human may update FreeCAD later.", "- `RECOMMEND_RESIZE`: visible footprint is materially unlike the reference; recommendation only.", "- `CUSTOM_FURNITURE_PLAUSIBLE`: custom/placeholder geometry can be valid; field or joinery review required.", "- `SKU_TO_VERIFY`: generic envelope is insufficient for a final product.", "- `USER_CONFIRMED_DO_NOT_CHANGE`: user-confirmed bed dimensions are preserved.", "", "## Per-object audit", "", "| Object | Room | Category | Current W×D | Reference W | Reference D | Recommended W×D | Classification | Source | Reason |", "|---|---|---|---:|---:|---:|---:|---|---|---|"]
    for x in objects:
        md.append(f"| {x['object_label']} | {x['room']} | {x['category']} | {x['current_width_mm']:.0f}×{x['current_depth_mm']:.0f} | {x['reference_width_range_mm'] or '—'} | {x['reference_depth_range_mm'] or '—'} | {(str(x['recommended_blockout_width_mm'])+'×'+str(x['recommended_blockout_depth_mm'])) if x['recommended_blockout_width_mm'] is not None else '—'} | `{x['classification']}` | `{x['source_type']}` | {x['reason']} |")
    md += ["", "## Asset library", "", "The existing normalized library is reference-only. It is not inserted into or substituted for the human FCStd objects.", "", "| ID | Category | Target bbox | File |", "|---|---|---:|---|"]
    for x in asset_candidates: md.append(f"| {x['id']} | {x['category']} | {x['normalized_bbox_mm']} | {x['file']} |")
    (OUT / "FURNITURE_DIMENSION_AUDIT_V01.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    proposals = [x for x in objects if x["classification"] in {"MINOR_ADJUSTMENT", "RECOMMEND_RESIZE", "SKU_TO_VERIFY"}]
    priority = {"seating": 0, "bed": 0, "dining_table": 0, "wardrobe": 0, "desk": 0, "tea_table": 0, "coffee_table": 1, "side_table": 1, "dining_chair": 1, "bookcase": 1}
    proposals.sort(key=lambda x: (priority.get(x["category"], 2), x["object_label"]))
    summary = ["# Furniture Dimension Change Proposal", "", "These are recommendations only. No FCStd object was modified.", "", "| Priority | Object | CURRENT | RECOMMENDED | WHY |", "|---:|---|---:|---:|---|"]
    for x in proposals:
        summary.append(f"| {priority.get(x['category'], 2)} | {x['object_label']} | {x['current_width_mm']:.0f}×{x['current_depth_mm']:.0f} | {(str(x['recommended_blockout_width_mm'])+'×'+str(x['recommended_blockout_depth_mm'])) if x['recommended_blockout_width_mm'] is not None else 'SKU_TO_VERIFY'} | {x['reason']} |")
    (OUT / "FURNITURE_DIMENSION_CHANGE_PROPOSAL.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps({"status": "HUMAN_REVIEW", "audited_objects": len(objects), "proposals": len(proposals), "asset_candidates": len(asset_candidates)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
