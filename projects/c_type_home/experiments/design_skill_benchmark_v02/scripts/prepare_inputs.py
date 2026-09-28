from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import ezdxf

EXP = Path(__file__).resolve().parents[1]
PROJECT = EXP.parents[1]
V02 = PROJECT / "cad/design_v02_f1_l1.dxf"
A0 = PROJECT / "assets/cad_library/standard/compiled/residential_design_legends_v01.dxf"
A0_MANIFEST = PROJECT / "assets/cad_library/standard/manifests/design_legend_manifest_v01.json"
BRIEF_JSON = PROJECT / "brief/owner_brief_v1.json"
BRIEF_MD = PROJECT / "brief/owner_brief_v1.md"
A1 = PROJECT / "knowledge/design_rules/design_rulebook_v01.json"
A2 = PROJECT / "knowledge/precedents/pattern_library_v01.json"
CANONICAL = PROJECT / "current_existing/canonical_plan_v1.json"
WINDOWS = PROJECT / "current_existing/window_register.json"
KITCHEN = PROJECT / "current_existing/kitchen_cabinet_register.json"
AX, AY = 1298172.0, -296458.0

SOURCE_READ = PROJECT.parent / "c_type_home/experiments/design_skill_benchmark_v01/sources/read"

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def dump(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

def copy_clean_base() -> dict:
    out = EXP / "base/public_zone_clean_base.dxf"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.readfile(str(V02))
    before = [(e.dxf.handle, e.dxftype(), e.dxf.layer) for e in doc.modelspace()
              if e.dxf.layer in {"S-S.WALL","A-WALL-EXST-CORR","F-DOOR","A-GLAZ-EXST","A-OPEN-EXST","S-COLUMN","S-楼梯"}]
    removed = []
    for entity in list(doc.modelspace()):
        if entity.dxftype() == "INSERT" and entity.dxf.layer == "A-FURN-PROP":
            removed.append(entity.dxf.handle)
            doc.modelspace().delete_entity(entity)
    after = [(e.dxf.handle, e.dxftype(), e.dxf.layer) for e in doc.modelspace()
             if e.dxf.layer in {"S-S.WALL","A-WALL-EXST-CORR","F-DOOR","A-GLAZ-EXST","A-OPEN-EXST","S-COLUMN","S-楼梯"}]
    if before != after:
        raise RuntimeError("D0.2 base changed structural/opening signatures")
    doc.saveas(str(out))
    record = {"source_v02": str(V02.relative_to(PROJECT)), "source_v02_sha256": sha(V02),
              "base_file": str(out.relative_to(PROJECT)), "base_sha256": sha(out),
              "removed_a_furn_prop_insert_handles": removed,
              "structural_signature_unchanged": True,
              "note": "D0.2 clean base removes all old A-FURN-PROP INSERTs without reading D0.1 placement data."}
    dump(EXP / "base/base_manifest.json", record)
    return record

def copy_common() -> dict:
    files = {
        "brief.json": BRIEF_JSON, "brief.md": BRIEF_MD, "a0_4.dxf": A0,
        "a0_4_manifest.json": A0_MANIFEST, "a1_rulebook.json": A1,
        "a2_pattern_library.json": A2, "canonical.json": CANONICAL,
        "window_register.json": WINDOWS, "kitchen_register.json": KITCHEN,
    }
    out = EXP / "common"
    records = {}
    for name, src in files.items():
        dst = out / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        records[name] = {"file": str(dst.relative_to(EXP)), "sha256": sha(dst)}
    base = EXP / "base/public_zone_clean_base.dxf"
    shutil.copy2(base, out / "public_zone_clean_base.dxf")
    records["public_zone_clean_base.dxf"] = {"file": "common/public_zone_clean_base.dxf", "sha256": sha(out / "public_zone_clean_base.dxf")}
    manifest_hash = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    result = {"common_inputs": records, "common_input_set_sha256": manifest_hash,
              "prohibited_inputs": ["D0.1 experiment directories", "D0.1 trial DXFs", "F1R outputs", "any prewritten furniture coordinate list"]}
    dump(EXP / "common/input_manifest.json", result)
    return result

def copy_adapter_sources() -> dict:
    adapters = EXP / "adapters"
    for arm in ("CTRL", "ARCH", "STUDIO", "REROOM"):
        (adapters / arm / "references").mkdir(parents=True, exist_ok=True)
    (adapters / "CTRL/SKILL.md").write_text("""# CTRL adapter

Use only the C-type owner brief, A0.4 block library, A1 rulebook, A2 pattern library, canonical geometry and window register. Do not load or search any third-party method material. Decide the furniture topology and coordinates yourself. Execute all CAD edits through the D0.2 cad_tool.py command interface.
""")
    arch_refs = [
        "Skills-Architects__skills__architect-foundations__SKILL.md",
        "Skills-Architects__skills__spatial-planning__SKILL.md",
        "Skills-Architects__skills__building-typology__SKILL.md",
        "Skills-Architects__skills__accessibility-design__SKILL.md",
        "Skills-Architects__skills__design-theory__SKILL.md",
        "Skills-Architects__skills__concept-design__SKILL.md",
    ]
    for src_name in arch_refs:
        src = SOURCE_READ / src_name
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy2(src, adapters / "ARCH/references" / src_name)
    (adapters / "ARCH/SKILL.md").write_text("""# ARCH adapter — residential Skills-Architects method

Before CAD, read every file in references/ and record the exact filenames and SHA256 values in files_opened.json. Apply only the relevant sequence: room/program reading, spatial hierarchy, functional zoning, circulation, residential typology, accessibility and concept organization. Do not use jurisdiction-specific code as an automatic project gate. Decide furniture count, blocks, positions and rotations yourself. Use cad_tool.py for every DXF edit.
""")
    studio_refs = [
        "arch-skills__skills__asset-management-interior__references__benchmark.md",
        "arch-skills__skills__asset-management-interior__references__case-anatomy.md",
        "arch-skills__skills__asset-management-interior__references__concept-engine.md",
        "arch-skills__skills__asset-management-interior__references__plan-review.md",
        "arch-skills__skills__asset-management-interior__references__spatial-devices.md",
        "arch-skills__skills__asset-management-interior__references__aesthetic-canon.md",
        "arch-skills__skills__asset-management-interior__SKILL.md",
    ]
    for src_name in studio_refs:
        src = SOURCE_READ / src_name
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy2(src, adapters / "STUDIO/references" / src_name)
    (adapters / "STUDIO/SKILL.md").write_text("""# STUDIO adapter — residentialized asset-management-interior method

Read every reference file and record it in files_opened.json. Use the workflow Benchmark -> Concept -> Plan -> one dominant spatial device -> red-team review -> CAD revision. The source material is office-oriented, so transfer only its workflow and spatial-device discipline to this home. Choose the dominant concept yourself; the prompt must not name one. Write the concept before any CAD commands, then render, red-team the saved DXF, and revise.
""")
    (adapters / "REROOM/SKILL.md").write_text("""# REROOM adapter — Appendix S6 method

Source: ReRoom paper arXiv:2609.03596, Appendix S6; no public code implementation is assumed. Record the paper version and local source hash in files_opened.json. Execute the sequence: Functional Grouping -> Anchor Furniture Selection -> Geometry-Guided Refinement -> Render -> Review -> Revise. Decide groups, anchors, furniture topology, positions and rotations yourself. r02 commands are forbidden until r01 render, geometry report and written visual review exist. Use cad_tool.py for every DXF edit.
""")
    return {"ARCH": arch_refs, "STUDIO": studio_refs, "REROOM": ["paper arXiv:2609.03596 Appendix S6 note"], "CTRL": ["project inputs only"]}

def make_sessions() -> None:
    source_map = copy_adapter_sources()
    for arm in ("CTRL", "ARCH", "STUDIO", "REROOM"):
        s = EXP / "sessions" / arm
        (s / "common").mkdir(parents=True, exist_ok=True)
        for src in (EXP / "common").iterdir():
            shutil.copy2(src, s / "common" / src.name)
        shutil.copy2(EXP / "adapters" / arm / "SKILL.md", s / "SKILL.md")
        if (EXP / "adapters" / arm / "references").exists():
            shutil.copytree(EXP / "adapters" / arm / "references", s / "references", dirs_exist_ok=True)
        dump(s / "session_manifest.json", {
            "arm": arm,
            "allowed_inputs": ["common/*", "SKILL.md", "references/*", "scripts/cad_tool.py"],
            "prohibited_inputs": ["D0.1 experiment", "F1R outputs", "other arm sessions", "other arm mapping"],
            "source_material": source_map[arm],
            "iteration_limit": 2,
            "agent_must_generate": ["commands.jsonl", "iteration_01/agent_review.md", "iteration_02/agent_review.md"],
        })

def main() -> None:
    base = copy_clean_base()
    common = copy_common()
    sources = copy_adapter_sources()
    make_sessions()
    dump(EXP / "inputs/source_lock.json", {
        "Skills-Architects_commit": "30a0845dddcaebd765fc396059573d02e99c5b63",
        "arch-skills_commit": "478d5ae32806e5a95dfcbeb70ba5a68126c22e9e",
        "ReRoom_paper": "arXiv:2609.03596",
        "ReRoom_paper_sha256": sha(SOURCE_READ / "ReRoom__paper.pdf"),
        "adapter_sources": sources,
    })
    print(json.dumps({"base": base, "common": common, "sessions": sorted(sources)}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

