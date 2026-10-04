#!/usr/bin/env python3
"""Generate the V2.1 semantic source-boundary audit."""
from __future__ import annotations
import hashlib, json, os, subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUTPUTS = {"REPO_BASELINE_CANDIDATES_V2.md", "REPO_BASELINE_CANDIDATES_V2.json", "REPO_BASELINE_TRACK_NOW.txt", "projects/c_type_home/scripts/audit_source_boundary_v2.py"}
R4 = "projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend"
B0 = "projects/c_type_home/design/blender_b0/B0_EXISTING_AS_IS.blend"
AUTHORITY_BINARIES = {
    R4: {"role": "R4 rendering authority", "authority_level": "FROZEN", "status": "CURRENT", "lfs": "LFS_OPTIONAL"},
    B0: {"role": "B0 existing-as-is authority", "authority_level": "FROZEN", "status": "CURRENT", "lfs": "LFS_OPTIONAL"},
    "projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_APPROVED_AS_IS_V1.blend": {"role": "frozen kitchen authority", "authority_level": "FROZEN", "status": "CURRENT", "lfs": "LFS_OPTIONAL"},
    "projects/c_type_home/design/wall_corners_v5/HOUSE_BASE_GEOMETRY_V2_FROZEN.blend": {"role": "frozen house-base geometry", "authority_level": "FROZEN", "status": "CURRENT", "lfs": "LFS_OPTIONAL"},
    "projects/c_type_home/cad/freecad_import/世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd": {"role": "current architectural CAD geometry source", "authority_level": "PHYSICAL_GROUND_TRUTH", "status": "CURRENT", "lfs": "LFS_OPTIONAL"},
    "projects/c_type_home/design/s2_current_design_v1/S2_GUIDE_BASELINE_V2.FCStd": {"role": "current FreeCAD design guide source", "authority_level": "HUMAN_DESIGN_GUIDE", "status": "CURRENT", "lfs": "LFS_OPTIONAL"},
    "projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1_R2_1.dxf": {"role": "current DXF source derivative", "authority_level": "DERIVED_DESIGN_MODEL", "status": "CURRENT", "lfs": "NORMAL_GIT_ACCEPTABLE"},
}
REFERENCE_DIRS = ("/references/",)
GENERATED_DIRS = ("/renders/", "/drafts/", "/proxies/", "/raw/", "/contact_sheet/", "/contact_sheets/")
REPORT_SOURCE_NAMES = {"branch_contract.json", "current_stage.json", "source_preflight.json", "ramp_feasibility.json", "ramp_feasibility.md", "section_measurement.json", "transition_clearance.json"}
SITE_SOURCE_NAMES = {"add_island_and_utility.py", "build_registered_scene.py", "correct_kitchen_logic.py", "correct_windows_and_buffet_v4.py", "ingest_photos.py", "package_evidence.py", "refine_narrow_front_v3.py", "registration_inputs.py", "solve_registration.py"}
ACTIVE_SCRIPT_PREFIXES = ("build_", "correct_", "extract_", "export_", "prepare_", "restore_", "solve_", "write_")
SCRIPT_ARTIFACT_WORDS = ("render", "review", "inspect", "validate", "qa", "package", "generate", "contact", "camera")

def visible_paths():
    raw = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all", "-z"], cwd=ROOT)
    return sorted(r[3:].decode("utf-8", "surrogateescape") for r in raw.split(bytes([0])) if r.startswith(b"?? ") and r[3:].decode("utf-8", "surrogateescape") not in OUTPUTS)

def manual(path, question, default):
    return "MANUAL_REVIEW", {"path": path, "current_classification_candidates": ["REFERENCE_EXTERNAL", "IGNORE_GENERATED"], "why_ambiguous": "The file is a review/document payload whose source role cannot be established from shallow metadata alone.", "default_recommendation": default, "question_for_human": question}

def classify(path):
    low, name, ext = path.lower(), Path(path).name.lower(), Path(path).suffix.lower()
    if ext in {".blend1", ".blend2", ".bak", ".tmp", ".pyc", ".exr", ".webp"}: return "IGNORE_GENERATED", None
    if name in {".ds_store", ".clawhubignore"}: return manual(path, "Should this local tool metadata be retained in the source baseline?", "IGNORE_GENERATED")
    if any(marker in low for marker in GENERATED_DIRS): return "IGNORE_GENERATED", None
    if "/materials/" in low: return ("TRACK_NOW", None) if name == "asset-manifest.json" else ("IGNORE_GENERATED", None)
    if ext in {".png", ".jpg", ".jpeg"}: return ("REFERENCE_EXTERNAL", None) if "/site_photos/" in low or any(d in low for d in REFERENCE_DIRS) else ("IGNORE_GENERATED", None)
    if "/site_photos/" in low:
        if ext == ".py": return ("TRACK_NOW", None) if name in SITE_SOURCE_NAMES else ("IGNORE_GENERATED", None)
        if ext in {".blend", ".fcstd", ".dxf", ".dwg"}: return "IGNORE_GENERATED", None
        if name.endswith("_render_log.txt") or "render_manifest" in name or "_qa." in name or "_build_log." in name: return "IGNORE_GENERATED", None
        if ext in {".json", ".md", ".csv", ".txt"}: return "TRACK_NOW", None
    if any(d in low for d in REFERENCE_DIRS) or ext == ".html": return "REFERENCE_EXTERNAL", None
    if ext == ".pdf": return manual(path, "Is this document an external reference to retain, or a derived review artifact to ignore?", "REFERENCE_EXTERNAL")
    if ext in {".blend", ".fcstd", ".dxf", ".dwg"}: return ("TRACK_LATER_OR_LFS", None) if path in AUTHORITY_BINARIES else ("IGNORE_GENERATED", None)
    if ext == ".py":
        if "/pascal_poc/" in low or "/secondary_bath_options/r2/" in low or "/living_correction_v1/" in low or "/living_correction_v2/" in low: return "IGNORE_GENERATED", None
        if any(word in name for word in SCRIPT_ARTIFACT_WORDS): return "IGNORE_GENERATED", None
        if "/secondary_bath_options/r3/" in low or "/living_correction_v3/" in low or "/site_photos/" in low: return ("TRACK_NOW", None) if name.startswith(ACTIVE_SCRIPT_PREFIXES) or name in SITE_SOURCE_NAMES else ("IGNORE_GENERATED", None)
        return ("TRACK_NOW", None) if path.startswith("projects/c_type_home/scripts/") or name.startswith(ACTIVE_SCRIPT_PREFIXES) else ("IGNORE_GENERATED", None)
    if ext in {".md", ".txt", ".csv", ".json", ".wkt"}:
        if name in {"furniture_dimension_register_v01.json", "furniture_dimension_register_v02.json", "s2_guide_baseline_v1.json", "delivery_manifest_historical_r1.json", "option_spec_historical_r1.md"}: return "IGNORE_GENERATED", None
        if "/reports/" in low: return ("TRACK_NOW", None) if name in REPORT_SOURCE_NAMES else ("IGNORE_GENERATED", None)
        if "/pascal_poc/" in low or "historical_r1" in name or "/r2/" in low: return "IGNORE_GENERATED", None
        if name.endswith("_states.json") or "_mesh_dump" in name or "_render_manifest" in name or "_qa" in name or "_audit" in name or "_diagnostic" in name or "_comparison" in name: return "IGNORE_GENERATED", None
        if ext == ".wkt": return "IGNORE_GENERATED", None
        size = os.stat(ROOT / path).st_size
        if ext in {".md", ".txt"} and size <= 20_000 and not any(word in name for word in ("render", "log")): return "TRACK_NOW", None
        if ext in {".csv", ".json"} and size <= 120_000: return "TRACK_NOW", None
        return "IGNORE_GENERATED", None
    return manual(path, "Should this uncommon file be retained as source or excluded as generated/local metadata?", "IGNORE_GENERATED")

def sha256(path):
    digest = hashlib.sha256()
    with open(ROOT / path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()

def main():
    paths, categories, manual_items = visible_paths(), defaultdict(list), []
    for path in paths:
        category, detail = classify(path); categories[category].append({"path": path, "bytes": (ROOT / path).stat().st_size})
        if detail: manual_items.append(detail)
    for items in categories.values(): items.sort(key=lambda item: item["path"])
    metrics = {key: {"files": len(items), "bytes": sum(item["bytes"] for item in items)} for key, items in sorted(categories.items())}
    payload = {"task": "Repository Source-Boundary Cleanup V2.1", "project": "projects/c_type_home", "base": "origin/improve/design-output-v14", "branch": "chore/c-type-source-boundary-v2", "supersedes_commit": "67b8677355ecc7efd97b5b057d319bb7e658124b", "generated_from": "git status --porcelain=v1 --untracked-files=all", "current_visible": {"files": len(paths), "bytes": sum((ROOT / path).stat().st_size for path in paths)}, "metrics": metrics, "categories": categories, "manual_review": sorted(manual_items, key=lambda item: item["path"]), "authority_hashes": {R4: sha256(R4), B0: sha256(B0)}, "authority_hashes_expected": {R4: "d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb", B0: "717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb"}, "authority_corrections": {"projects/c_type_home/cad/freecad_import/世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd": "PHYSICAL_GROUND_TRUTH", "projects/c_type_home/design/s2_current_design_v1/S2_GUIDE_BASELINE_V2.FCStd": "HUMAN_DESIGN_GUIDE"}, "lfs_candidates": [{"path": path, **meta, "size": (ROOT / path).stat().st_size, "sha256": sha256(path), "reason": "Advisory only: future binary version-history growth or repository policy, not current size alone."} for path, meta in AUTHORITY_BINARIES.items() if (ROOT / path).exists()], "proposed_ignore_rules": [{"pattern": "projects/c_type_home/design/**/drafts/**", "why_safe": "named draft branches are superseded studies", "false_positive_risk": "a future draft may be intentionally retained"}, {"pattern": "projects/c_type_home/design/**/proxies/**", "why_safe": "proxy images are derived review outputs", "false_positive_risk": "a future source proxy contract would need an explicit exception"}]}
    (ROOT / "REPO_BASELINE_CANDIDATES_V2.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    track_now = [item["path"] for item in categories.get("TRACK_NOW", [])]; (ROOT / "REPO_BASELINE_TRACK_NOW.txt").write_text("\n".join(track_now) + "\n")
    lines = ["# Repository Source-Boundary Cleanup V2.1", "", "TASK STATUS: HUMAN_REVIEW", "BASE: origin/improve/design-output-v14", "BRANCH: chore/c-type-source-boundary-v2", "", "This correction pass classifies by semantic role, current version, and authority records. Directory names and extensions are not sufficient evidence by themselves.", "", "## Metrics", "", f"CURRENT_VISIBLE: files = {len(paths)}; bytes = {sum((ROOT / path).stat().st_size for path in paths)}"]
    for key in ("TRACK_NOW", "TRACK_LATER_OR_LFS", "REFERENCE_EXTERNAL", "IGNORE_GENERATED", "MANUAL_REVIEW"): metric = metrics.get(key, {"files": 0, "bytes": 0}); lines.append(f"{key}: {metric['files']} files / {metric['bytes']} bytes")
    lines += ["", "## V2 to V2.1", "", "V2: TRACK_NOW 275; TRACK_LATER_OR_LFS 7; REFERENCE_EXTERNAL 296; IGNORE_GENERATED 687; MANUAL_REVIEW 0.", f"V2.1: TRACK_NOW {metrics.get('TRACK_NOW', {}).get('files', 0)}; TRACK_LATER_OR_LFS {metrics.get('TRACK_LATER_OR_LFS', {}).get('files', 0)}; REFERENCE_EXTERNAL {metrics.get('REFERENCE_EXTERNAL', {}).get('files', 0)}; IGNORE_GENERATED {metrics.get('IGNORE_GENERATED', {}).get('files', 0)}; MANUAL_REVIEW {metrics.get('MANUAL_REVIEW', {}).get('files', 0)}.", "", "## Track Now", "", f"Exact baseline paths are in REPO_BASELINE_TRACK_NOW.txt ({len(track_now)} files).", "", "Largest 20 TRACK_NOW files:"]
    for item in sorted(categories.get("TRACK_NOW", []), key=lambda item: (-item["bytes"], item["path"]))[:20]: lines.append(f"- {item['bytes']} bytes — PATH {item['path']}")
    lines += ["", "## Track Later / LFS", "", "Advisory only. LFS_REQUIRED_FOR_POLICY is not established; current small authority binaries are LFS_OPTIONAL and the current DXF is NORMAL_GIT_ACCEPTABLE."]
    for item in payload["lfs_candidates"]: lines.append(f"- PATH {item['path']} — {item['size']} bytes; {item['role']}; {item['authority_level']}; {item['status']}; SHA256 {item['sha256']}; {item['lfs']}")
    lines += ["", "## Manual Review", ""]
    if manual_items:
        for item in sorted(manual_items, key=lambda item: item["path"]): lines.append(f"- PATH {item['path']} — candidates: {', '.join(item['current_classification_candidates'])}; why: {item['why_ambiguous']}; default: {item['default_recommendation']}; question: {item['question_for_human']}")
    else: lines.append("- None")
    lines += ["", "## Proposed Ignore Rules", "", "No blanket /reports/ rule is proposed. These narrower patterns are proposed for later human review; .gitignore was not modified."]
    for rule in payload["proposed_ignore_rules"]: lines.append(f"- PATTERN {rule['pattern']} — safe because {rule['why_safe']}; false-positive risk: {rule['false_positive_risk']}")
    lines += ["", "## Required Validation", "", "- material asset-manifest.json => TRACK_NOW", "- material texture payload => IGNORE_GENERATED", "- site_photos/*.jpg/png => REFERENCE_EXTERNAL", "- site_photos source .py evaluated by filename/role, not directory", "- reports/BRANCH_CONTRACT.json => TRACK_NOW", "- historical versions are not tracked solely by extension", "- FreeCAD master => PHYSICAL_GROUND_TRUTH", f"- R4 SHA256: {payload['authority_hashes'][R4]} (expected {payload['authority_hashes_expected'][R4]})", f"- B0 SHA256: {payload['authority_hashes'][B0]} (expected {payload['authority_hashes_expected'][B0]})", "- category counts and bytes reconcile exactly", "", "GROUND TRUTH: UNCHANGED", "BLENDER: NOT STARTED", "FREECAD: NOT STARTED", "", "NEXT ACTION: HUMAN_REVIEW before any baseline candidate commit."]
    (ROOT / "REPO_BASELINE_CANDIDATES_V2.md").write_text("\n".join(lines) + "\n")

if __name__ == "__main__": main()
