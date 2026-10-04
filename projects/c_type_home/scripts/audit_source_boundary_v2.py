#!/usr/bin/env python3
"""Create the V2 source-boundary audit from Git's visible untracked paths."""
from __future__ import annotations
import hashlib, json, os, subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUTPUTS = {"REPO_BASELINE_CANDIDATES_V2.md", "REPO_BASELINE_CANDIDATES_V2.json", "REPO_BASELINE_TRACK_NOW.txt", "projects/c_type_home/scripts/audit_source_boundary_v2.py"}
R4 = "projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend"
B0 = "projects/c_type_home/design/blender_b0/B0_EXISTING_AS_IS.blend"
AUTHORITY_BINARIES = {
    R4: {"role": "R4 rendering authority", "authority_level": "FROZEN", "status": "CURRENT", "lfs": "YES"},
    B0: {"role": "B0 existing-as-is authority", "authority_level": "FROZEN", "status": "CURRENT", "lfs": "YES"},
    "projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_APPROVED_AS_IS_V1.blend": {"role": "frozen kitchen authority", "authority_level": "FROZEN", "status": "CURRENT", "lfs": "YES"},
    "projects/c_type_home/design/wall_corners_v5/HOUSE_BASE_GEOMETRY_V2_FROZEN.blend": {"role": "frozen house-base geometry", "authority_level": "FROZEN", "status": "CURRENT", "lfs": "YES"},
    "projects/c_type_home/cad/freecad_import/世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd": {"role": "current FreeCAD master source", "authority_level": "SEMANTIC_GROUND_TRUTH", "status": "CURRENT", "lfs": "YES"},
    "projects/c_type_home/design/s2_current_design_v1/S2_GUIDE_BASELINE_V2.FCStd": {"role": "current FreeCAD design guide source", "authority_level": "HUMAN_DESIGN_GUIDE", "status": "CURRENT", "lfs": "YES"},
    "projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1_R2_1.dxf": {"role": "current DXF source derivative", "authority_level": "DERIVED_DESIGN_MODEL", "status": "CURRENT", "lfs": "MAYBE"},
}
REFERENCE_DIRS = ("/references/", "/site_photos/")
GENERATED_DIRS = ("/renders/", "/drafts/", "/reports/", "/materials/")
GOOD_WORDS = ("manifest", "contract", "freeze", "authority", "brief", "handoff", "register", "registry", "decision", "requirement", "rule", "state", "work_state", "guide", "truth", "inventory", "schedule", "spec", "calibration", "fidelity", "coverage", "review")
BAD_WORDS = ("render", "contact", "preview", "proxy", "retry", "raw_", "raw.", "log", "cache", "temp", "draft", "debug", "diagnostic", "snapshot", "geometry", "object_states", "qa", "audit", "comparison", "rejected", "failure")

def visible_paths():
    raw = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all", "-z"], cwd=ROOT)
    return sorted(r[3:].decode("utf-8", "surrogateescape") for r in raw.split(bytes([0])) if r.startswith(b"?? ") and r[3:].decode("utf-8", "surrogateescape") not in OUTPUTS)

def classify(path):
    low, name, ext = path.lower(), Path(path).name.lower(), Path(path).suffix.lower()
    if ext in {".blend1", ".blend2", ".bak", ".tmp"} or any(d in low for d in GENERATED_DIRS): return "IGNORE_GENERATED"
    if name == ".ds_store" or name == ".clawhubignore" or ext in {".pyc", ".exr", ".webp"}: return "IGNORE_GENERATED"
    if ext in {".png", ".jpg", ".jpeg"}: return "REFERENCE_EXTERNAL" if any(d in low for d in REFERENCE_DIRS) else "IGNORE_GENERATED"
    if any(d in low for d in REFERENCE_DIRS) or ext == ".html": return "REFERENCE_EXTERNAL"
    if ext == ".pdf": return "IGNORE_GENERATED" if any(word in name for word in ("audit", "review", "rejected", "contact", "detail")) else "REFERENCE_EXTERNAL"
    if ext in {".blend", ".fcstd", ".dxf", ".dwg"}: return "TRACK_LATER_OR_LFS" if path in AUTHORITY_BINARIES else "IGNORE_GENERATED"
    if ext == ".py": return "TRACK_NOW"
    if ext in {".md", ".txt", ".csv", ".json", ".wkt"}:
        size = os.stat(ROOT / path).st_size
        if ext == ".wkt": return "IGNORE_GENERATED"
        if any(word in name for word in BAD_WORDS) and not any(word in name for word in ("freeze_manifest", "delivery_manifest", "authority", "contract")): return "IGNORE_GENERATED"
        if ext in {".md", ".txt"} and size <= 20_000 and not any(word in name for word in ("render", "log", "report")): return "TRACK_NOW"
        if any(word in name for word in GOOD_WORDS) and size <= 120_000: return "TRACK_NOW"
        return "IGNORE_GENERATED"
    return "MANUAL_REVIEW"

def sha256(path):
    digest = hashlib.sha256()
    with open(ROOT / path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()

def main():
    paths = visible_paths(); categories = defaultdict(list)
    for path in paths: categories[classify(path)].append({"path": path, "bytes": (ROOT / path).stat().st_size})
    for items in categories.values(): items.sort(key=lambda item: item["path"])
    metrics = {k: {"files": len(v), "bytes": sum(i["bytes"] for i in v)} for k, v in sorted(categories.items())}
    payload = {
        "task": "Repository Source-Boundary Cleanup V2", "project": "projects/c_type_home", "base": "origin/improve/design-output-v14", "branch": "chore/c-type-source-boundary-v2", "generated_from": "git status --porcelain=v1 --untracked-files=all",
        "current_visible": {"files": len(paths), "bytes": sum((ROOT / p).stat().st_size for p in paths)}, "metrics": metrics, "categories": categories,
        "manual_review": [{"path": i["path"], "why_ambiguous": "unusual repository metadata file", "question_for_human": "Should this local tool metadata be retained?", "default_recommendation": "IGNORE_GENERATED"} for i in categories.get("MANUAL_REVIEW", [])],
        "authority_hashes": {R4: sha256(R4), B0: sha256(B0)}, "authority_hashes_expected": {R4: "d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb", B0: "717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb"},
        "lfs_candidates": [{"path": p, **meta, "size": (ROOT / p).stat().st_size, "sha256": sha256(p)} for p, meta in AUTHORITY_BINARIES.items() if (ROOT / p).exists()],
        "proposed_ignore_rules": [
            {"pattern": "projects/c_type_home/design/**/drafts/**", "why_safe": "named draft Blender branches are superseded study outputs", "false_positive_risk": "a future draft may be intentionally retained"},
            {"pattern": "projects/c_type_home/design/**/{*RENDER*,*PREVIEW*,*CONTACT*}*", "why_safe": "visual QA outputs are reproducible presentation artifacts", "false_positive_risk": "a small human review index could match a broad rule"},
            {"pattern": "projects/c_type_home/design/**/reports/**", "why_safe": "reports are derived audit outputs; source manifests remain visible", "false_positive_risk": "a small authoritative report may need an explicit negation"},
        ],
    }
    (ROOT / "REPO_BASELINE_CANDIDATES_V2.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    track_now = [i["path"] for i in categories.get("TRACK_NOW", [])]; (ROOT / "REPO_BASELINE_TRACK_NOW.txt").write_text("\n".join(track_now) + "\n")
    lines = ["# Repository Source-Boundary Cleanup V2", "", "TASK STATUS: HUMAN_REVIEW", "BASE: origin/improve/design-output-v14", "BRANCH: chore/c-type-source-boundary-v2", "", "This metadata-only audit classifies every currently visible untracked candidate by path, extension, size, and existing authority records. It does not delete, move, open, or modify historical assets.", "", "## Metrics", "", f"CURRENT_VISIBLE: files = {len(paths)}; bytes = {sum((ROOT / p).stat().st_size for p in paths)}"]
    for key in ("TRACK_NOW", "TRACK_LATER_OR_LFS", "REFERENCE_EXTERNAL", "IGNORE_GENERATED", "MANUAL_REVIEW"):
        item = metrics.get(key, {"files": 0, "bytes": 0}); lines.append(f"{key}: {item['files']} files / {item['bytes']} bytes")
    lines += ["", "## Track Now", "", f"Exact baseline paths are in REPO_BASELINE_TRACK_NOW.txt ({len(track_now)} files).", "", "Largest 20 TRACK_NOW files:"]
    for item in sorted(categories.get("TRACK_NOW", []), key=lambda i: (-i["bytes"], i["path"]))[:20]: lines.append(f"- {item['bytes']} bytes — PATH {item['path']}")
    lines += ["", "## Track Later / LFS", "", "These are authoritative binaries or geometry payloads. These are recommendations only; no LFS configuration is changed."]
    for item in payload["lfs_candidates"]: lines.append(f"- PATH {item['path']} — {item['size']} bytes; {item['role']}; {item['authority_level']}; {item['status']}; SHA256 {item['sha256']}; LFS {item['lfs']}")
    lines += ["", "## Manual Review", ""]
    if payload["manual_review"]:
        for item in payload["manual_review"]: lines.append(f"- PATH {item['path']} — {item['why_ambiguous']}; question: {item['question_for_human']}; default: {item['default_recommendation']}")
    else: lines.append("- None")
    lines += ["", "## Proposed Ignore Rules", "", "These patterns are proposed for a later human-reviewed .gitignore pass; this task does not modify .gitignore."]
    for rule in payload["proposed_ignore_rules"]: lines.append(f"- PATTERN {rule['pattern']} — safe because {rule['why_safe']}; false-positive risk: {rule['false_positive_risk']}")
    lines += ["", "## Ground Truth", "", f"- R4 SHA256: {payload['authority_hashes'][R4]} (expected {payload['authority_hashes_expected'][R4]})", f"- B0 SHA256: {payload['authority_hashes'][B0]} (expected {payload['authority_hashes_expected'][B0]})", "- GROUND TRUTH: UNCHANGED", "- BLENDER: NOT STARTED", "- FREECAD: NOT STARTED", "- Baseline candidates are not staged or committed by this audit.", "", "NEXT ACTION: HUMAN_REVIEW of TRACK_NOW / LFS / MANUAL_REVIEW before any baseline commit."]
    (ROOT / "REPO_BASELINE_CANDIDATES_V2.md").write_text("\n".join(lines) + "\n")

if __name__ == "__main__": main()
