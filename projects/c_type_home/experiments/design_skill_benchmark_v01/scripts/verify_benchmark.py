from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
PROJECT = EXP.parents[1]
ARMS = ("CTRL", "ARCH", "STUDIO", "REROOM")
GATE_NAMES = tuple(f"G{i}_{name}" for i, name in enumerate([
    "SOURCE_AUDIT", "BASE_CAD", "ISOLATION", "CAD_FIRST", "ACTUAL_BLOCKS",
    "ITERATIVE_REVIEW", "SAME_INPUTS", "BLIND_OUTPUT", "FORMAL_CAD_SAFETY"
]))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify() -> dict:
    gates_path = EXP / "reports/gates.json"
    gates = json.loads(gates_path.read_text())
    checks = {}
    checks["gate_file_has_all_gates"] = all(name in gates.get("gates", {}) for name in GATE_NAMES)
    checks["all_recorded_gates_true"] = all(gates.get("gates", {}).get(name) is True for name in GATE_NAMES)
    checks["status_human_review"] = gates.get("status") == "HUMAN_REVIEW"
    base_manifest = json.loads((EXP / "base/base_manifest.json").read_text())
    checks["base_removed_exact_six"] = base_manifest.get("removed_count") == 6
    checks["base_source_matches_v02"] = base_manifest.get("source_sha256") == gates["formal_input_sha_before"]["v02"]["sha256"]
    source_manifest = json.loads((EXP / "reports/source_manifest.json").read_text())
    checks["source_files_read"] = all(
        all(item.get("status") == "READ" for item in src.get("files_read", [])) and src.get("files_read")
        for src in source_manifest.get("sources", [])
    )
    checks["rerroom_paper_present"] = bool(source_manifest["sources"][2].get("paper_sha256"))
    for arm in ARMS:
        d = json.loads((EXP / "arms" / arm / "geometry_metrics.json").read_text())
        final = d["final"]
        final_path = EXP / "arms" / arm / "trial_final.dxf"
        checks[f"{arm}_final_sha"] = sha(final_path) == d["final_dxf_sha256"] == gates["arms"][arm]["final_dxf_sha256"]
        checks[f"{arm}_iterations"] = len(d["trials"]) == 2 and d["iteration_limit"] == 2
        checks[f"{arm}_bbox_qa"] = final["transformed_block_bbox_qa"]["all_pass"] and final["transformed_block_bbox_qa"]["count"] == 8
        checks[f"{arm}_cad_diff"] = json.loads((EXP / "arms" / arm / "cad_diff.json").read_text()).get("formal_geometry_preserved") is True
        sidecar = json.loads((EXP / "arms" / arm / "trial_final.render.json").read_text())
        checks[f"{arm}_render_provenance"] = sidecar.get("source_dxf_sha256") == sha(final_path)
        checks[f"{arm}_old_f1r_isolated"] = d.get("prohibited_old_f1r_inputs_read") is False
    blind = [EXP / "blind_review" / f"{label}.png" for label in "ABCD"]
    clearance = [EXP / "blind_review" / f"{label}_clearance.png" for label in "ABCD"]
    checks["blind_images_present"] = all(p.exists() for p in blind + clearance)
    checks["blind_images_not_identical"] = len({sha(p) for p in blind}) == 4
    mapping = json.loads((EXP / "blind_review/arm_mapping.json").read_text()).get("mapping", {})
    checks["blind_mapping_complete"] = set(mapping) == set("ABCD") and set(mapping.values()) == set(ARMS)
    checks["formal_inputs_unchanged"] = gates.get("formal_input_sha_before") == gates.get("formal_input_sha_after")
    checks["comparison_sheet_present"] = (EXP / "blind_review/comparison_sheet.png").exists()
    checks["human_review_form_present"] = (EXP / "blind_review/human_review_form.md").exists()
    return {
        "all_pass": all(checks.values()),
        "check_count": len(checks),
        "failed_checks": [k for k, v in checks.items() if not v],
        "passed_checks": [k for k, v in checks.items() if v],
        "gate_count": len(GATE_NAMES),
        "checks": checks,
        "status": gates.get("status"),
    }

if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))

