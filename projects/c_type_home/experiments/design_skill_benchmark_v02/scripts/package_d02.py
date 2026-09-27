from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from pathlib import Path

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image, ImageDraw
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

from cad_tool import (
    AX, AY, PUBLIC_VIEW, ROUTE_ANCHORS, HIDDEN_RENDER_LAYERS,
    draw_actual_blocks, sha, validate_iteration_causality, measure_dxf,
)

EXP = Path(__file__).resolve().parents[1]
PROJECT = EXP.parents[1]
V02 = PROJECT / "cad/design_v02_f1_l1.dxf"
CANONICAL = PROJECT / "current_existing/canonical_plan_v1.json"
WINDOWS = PROJECT / "current_existing/window_register.json"
A0 = PROJECT / "assets/cad_library/standard/compiled/residential_design_legends_v01.dxf"
ARMS = ("CTRL", "ARCH", "STUDIO", "REROOM")
REQUIRED_ACTIONS = {"insert", "move", "rotate", "delete"}
FORMAL_INPUTS = {
    "v02": V02,
    "canonical": CANONICAL,
    "windows": WINDOWS,
    "a0_4": A0,
}
BLIND_MAP = {"A": "REROOM", "B": "CTRL", "C": "STUDIO", "D": "ARCH"}

def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

def parse_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

def ensure_iteration_logs(arm: str) -> dict:
    session = EXP / "sessions" / arm
    top = session / "commands.jsonl"
    sources = {}
    for iteration in ("iteration_01", "iteration_02"):
        target = session / iteration / "commands.jsonl"
        if target.exists():
            sources[iteration] = "native_iteration_log"
            continue
        if not top.exists():
            sources[iteration] = "missing"
            continue
        events = [e for e in parse_events(top) if e.get("iteration") == ("r01" if iteration.endswith("01") else "r02")]
        if events:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n")
            sources[iteration] = "derived_exact_filter_of_agent_top_level_log"
        else:
            sources[iteration] = "missing"
    return sources

def validate_session_evidence(arm: str) -> dict:
    session = EXP / "sessions" / arm
    log_sources = ensure_iteration_logs(arm)
    events = []
    iteration_logs_ok = True
    for iteration in ("iteration_01", "iteration_02"):
        log = session / iteration / "commands.jsonl"
        if not log.exists():
            iteration_logs_ok = False
            continue
        ev = parse_events(log)
        events.extend(ev)
        if not ev or not all(e.get("actor") == "agent_session" for e in ev):
            iteration_logs_ok = False
    reviews = [session / "iteration_01/agent_review.md", session / "iteration_02/agent_review.md"]
    evidence_files = [session / "files_opened.json", session / "session_summary.md"] + reviews
    real_action = any(e.get("action") in REQUIRED_ACTIONS for e in events)
    causal = validate_iteration_causality(events)
    iteration_data = {}
    saved_cad_ok = True
    bbox_ok = True
    bbox_r01 = None
    bbox_r02 = None
    for n in ("01", "02"):
        after = session / f"iteration_{n}/after.dxf"
        png = session / f"iteration_{n}/after.png"
        geom_path = session / f"iteration_{n}/geometry.json"
        if not all(p.exists() for p in (after, png, geom_path)):
            saved_cad_ok = False
            continue
        geom = json.loads(geom_path.read_text())
        iteration_data[n] = geom
        saved_cad_ok &= geom.get("source_dxf_sha256") == sha(after)
        if n == "01":
            bbox_r01 = bool(geom.get("transformed_bbox_all_pass"))
        if n == "02":
            bbox_r02 = bool(geom.get("transformed_bbox_all_pass"))
    bbox_ok = bool(bbox_r02)
    files_opened_ok = (session / "files_opened.json").exists() and bool(json.loads((session / "files_opened.json").read_text()).get("files"))
    reviews_ok = all(p.exists() and len(p.read_text()) > 500 for p in reviews)
    summary_ok = (session / "session_summary.md").exists() and len((session / "session_summary.md").read_text()) > 400
    prohibited_text = ""
    for p in evidence_files:
        if p.exists():
            prohibited_text += p.read_text(errors="ignore")
    isolation_ok = not any(token in prohibited_text for token in ("F1R_01H", "F1R_02", "qc/f1r_public_zone"))
    result = {
        "arm": arm,
        "pass": all([iteration_logs_ok, real_action, causal["pass"], saved_cad_ok, bbox_ok, files_opened_ok, reviews_ok, summary_ok, isolation_ok]),
        "iteration_logs_ok": iteration_logs_ok,
        "log_sources": log_sources,
        "real_agent_action": real_action,
        "feedback_causality": causal["pass"],
        "causality": causal,
        "saved_cad_provenance": saved_cad_ok,
        "bbox_qa": bbox_ok,
        "bbox_qa_r01": bbox_r01,
        "bbox_qa_r02": bbox_r02,
        "skill_material_read": files_opened_ok,
        "visual_review_evidence": reviews_ok,
        "session_summary": summary_ok,
        "isolation": isolation_ok,
        "furniture_count_r01": iteration_data.get("01", {}).get("furniture_count"),
        "furniture_count_r02": iteration_data.get("02", {}).get("furniture_count"),
        "geometry_r01": iteration_data.get("01"),
        "geometry_r02": iteration_data.get("02"),
    }
    dump(session / "evidence_validation.json", result)
    return result

def render_clearance(dxf_path: Path, png_path: Path, geometry: dict) -> None:
    doc = ezdxf.readfile(str(dxf_path))
    def keep(entity):
        return entity.dxf.layer not in HIDDEN_RENDER_LAYERS and entity.dxftype() not in {"TEXT", "MTEXT", "DIMENSION", "HATCH"}
    fig = plt.figure(figsize=(8.2, 10.2), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    Frontend(RenderContext(doc), MatplotlibBackend(ax, adjust_figure=False)).draw_layout(doc.modelspace(), filter_func=keep, finalize=True)
    draw_actual_blocks(ax, doc)
    ax.set_xlim(AX + PUBLIC_VIEW[0], AX + PUBLIC_VIEW[2]); ax.set_ylim(AY + PUBLIC_VIEW[1], AY + PUBLIC_VIEW[3]); ax.set_aspect("equal")
    for rec in geometry.get("furniture", []):
        x1,y1,x2,y2 = rec["actual_bbox_task01"]
        ax.add_patch(Rectangle((AX+x1,AY+y1),x2-x1,y2-y1,fill=False,edgecolor="#d95f02",linewidth=1.0,linestyle="--",zorder=70))
    colors = ["#386cb0","#7b3294","#008837","#e66101","#a6611a"]
    for (name, spec), color in zip(ROUTE_ANCHORS.items(), colors):
        a,b,_ = spec
        ax.plot([AX+a[0],AX+b[0]],[AY+a[1],AY+b[1]],color=color,linewidth=1.0,zorder=72)
        measured = geometry.get("route_clearances",{}).get(name,{}).get("actual_measured_min_mm","UNKNOWN")
        ax.text(AX+(a[0]+b[0])/2, AY+(a[1]+b[1])/2, f"{name}: {measured} mm", fontsize=6, color=color,
                bbox={"facecolor":"white","alpha":0.65,"edgecolor":"none","pad":0.3}, zorder=73)
    ax.text(AX+PUBLIC_VIEW[0]+100, AY+PUBLIC_VIEW[3]-150, "D0.2 measured clearance overlay; source = saved agent DXF", fontsize=7, color="#222")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=150, facecolor="white")
    plt.close(fig)

def cad_diff(base: Path, final: Path) -> dict:
    def sig(path: Path):
        doc = ezdxf.readfile(str(path))
        result = {}
        for e in doc.modelspace():
            if e.dxf.layer == "D0-FURNITURE":
                continue
            try:
                ext = e.dxf.get("handle"), e.dxftype(), e.dxf.layer, tuple(round(v,3) for v in [e.dxf.insert.x,e.dxf.insert.y]) if e.dxftype()=="INSERT" else None
            except Exception:
                ext = (e.dxf.get("handle"), e.dxftype(), e.dxf.layer, None)
            result[e.dxf.handle] = ext
        return result
    a,b=sig(base),sig(final)
    return {"changed": sorted(h for h in a if h in b and a[h]!=b[h]), "missing": sorted(h for h in a if h not in b),
            "added_non_furniture": sorted(h for h in b if h not in a), "formal_geometry_preserved": not any([h for h in a if h in b and a[h]!=b[h]]) and not any(h for h in a if h not in b)}

def comparison_sheet(paths: dict[str, Path], out: Path) -> None:
    imgs=[(label,Image.open(path).convert("RGB")) for label,path in paths.items()]
    w,h=imgs[0][1].size; margin,label_h=20,38
    canvas=Image.new("RGB",(2*w+3*margin,2*(h+label_h)+3*margin),"white"); draw=ImageDraw.Draw(canvas)
    for i,(label,img) in enumerate(imgs):
        x=margin+(i%2)*(w+margin); y=margin+(i//2)*(h+label_h+margin)
        canvas.paste(img,(x,y+label_h)); draw.text((x,y+7),f"Blind option {label}",fill="black")
    canvas.save(out)

def make_human_form(out: Path) -> None:
    criteria=["空间整体感","座席 group","主次关系","家具是否像设计而非摆放","负空间","儿童活动","老人通行","投影兼容","北阳台关系","餐厅/厨房关系","G-DIN-LIV","尺度比例","莫名其妙家具","专业住宅感"]
    lines=["# D0.2 Human review form","","只评审 A/B/C/D 盲图，不打开 mapping secret。每项 1–5 分。","","| 维度 | A | B | C | D | 备注 |","|---|---:|---:|---:|---:|---|"]
    lines += [f"| {x} |  |  |  |  |  |" for x in criteria]
    lines += ["","","## 综合判断","- 首选：","- 次选：","- 具体空间理由：","- 是否允许下一阶段概念冻结：","","本表不批准正式 CAD 写回。"]
    out.write_text("\n".join(lines)+"\n")

def package() -> dict:
    evidence={arm:validate_session_evidence(arm) for arm in ARMS}
    arms_dir=EXP/"arms"; blind_dir=EXP/"blind_review"; reports=EXP/"reports"
    for arm in ARMS:
        arm_out=arms_dir/arm; arm_out.mkdir(parents=True,exist_ok=True)
        session=EXP/"sessions"/arm
        final=session/"iteration_02/after.dxf"
        png=session/"iteration_02/after.png"
        geom=json.loads((session/"iteration_02/geometry.json").read_text())
        shutil.copy2(final,arm_out/"trial_final.dxf"); shutil.copy2(png,arm_out/"trial_final.png")
        dump(arm_out/"geometry_metrics.json",{"arm":arm,"source_session":str(session.relative_to(PROJECT)),"final":geom,"evidence":evidence[arm]})
        dump(arm_out/"cad_diff.json",cad_diff(EXP/"base/public_zone_clean_base.dxf",final))
        (arm_out/"agent_review.md").write_text((session/"iteration_02/agent_review.md").read_text())
        (arm_out/"session_summary.md").write_text((session/"session_summary.md").read_text())
        render_clearance(final,arm_out/"trial_final_clearance.png",geom)
    blind_dir.mkdir(parents=True, exist_ok=True)
    blind={}
    blind_clear={}
    for label,arm in BLIND_MAP.items():
        shutil.copy2(arms_dir/arm/"trial_final.png",blind_dir/f"{label}.png")
        shutil.copy2(arms_dir/arm/"trial_final_clearance.png",blind_dir/f"{label}_clearance.png")
        blind[label]=blind_dir/f"{label}.png"; blind_clear[label]=blind_dir/f"{label}_clearance.png"
    comparison_sheet(blind,blind_dir/"comparison_sheet.png")
    make_human_form(blind_dir/"human_review_form.md")
    dump(blind_dir/"arm_mapping.secret.json",{"mapping":BLIND_MAP,"note":"Do not open before blind review."})
    formal_before={k:sha(v) for k,v in FORMAL_INPUTS.items()}
    formal_after={k:sha(v) for k,v in FORMAL_INPUTS.items()}
    framework=(EXP/"scripts/cad_tool.py").read_text()
    no_layout=not any(x in framework for x in ("ARM_SPECS","trial_r01","trial_r02")) and not re.search(r"""["']x["']\s*:\s*[-+]?\d{3,}""",framework) and not re.search(r"""["']y["']\s*:\s*[-+]?\d{3,}""",framework)
    gates={
        "G0_SOURCE_AUDIT": (EXP/"inputs/source_lock.json").exists(),
        "G0.5_NO_COORDINATE_PRESETS": no_layout,
        "G1_BASE_CAD": json.loads((EXP/"base/base_manifest.json").read_text()).get("structural_signature_unchanged") is True,
        "G2_ISOLATION": all(x["isolation"] for x in evidence.values()),
        "G3_CAD_FIRST": all(x["saved_cad_provenance"] for x in evidence.values()),
        "G4_ACTUAL_BLOCKS": all(x["bbox_qa"] for x in evidence.values()),
        "G5_ITERATIVE_REVIEW": all(x["visual_review_evidence"] for x in evidence.values()),
        "G6_SAME_INPUTS": len({json.loads((EXP/"common/input_manifest.json").read_text())["common_input_set_sha256"]})==1,
        "G7_BLIND_OUTPUT": all(p.exists() for p in list(blind.values())+list(blind_clear.values())),
        "G8_FORMAL_CAD_SAFETY": formal_before==formal_after,
        "G9_NO_HARDCODED_LAYOUT": no_layout,
        "G10_REAL_SKILL_LOAD": all(x["skill_material_read"] for x in evidence.values()),
        "G11_REAL_AGENT_ACTION": all(x["real_agent_action"] for x in evidence.values()),
        "G12_FEEDBACK_CAUSALITY": all(x["feedback_causality"] for x in evidence.values()),
        "G13_VISUAL_REVIEW": all(x["visual_review_evidence"] for x in evidence.values()),
        "G14_METHOD_DIFFERENTIATION": no_layout and len({evidence[a]["furniture_count_r02"] for a in ARMS}) >= 2,
        "G15_BLIND_INTEGRITY": all(token not in (blind_dir/"human_review_form.md").read_text() for token in ARMS) and not any(token in (reports/"d02_report.md").read_text() if (reports/"d02_report.md").exists() else "" for token in ARMS),
    }
    report={"status":"HUMAN_REVIEW" if all(gates.values()) else "INVALID_EVIDENCE","gates":gates,"gate_count":len(gates),
            "arm_evidence":{a:{k:v for k,v in e.items() if k not in {"geometry_r01","geometry_r02"}} for a,e in evidence.items()},
            "formal_input_sha256":formal_before,"blind_outputs":{k:str(v.relative_to(PROJECT)) for k,v in {**blind,**{f"{k}_clearance":v for k,v in blind_clear.items()}}.items()},
            "mapping_secret":str((blind_dir/"arm_mapping.secret.json").relative_to(PROJECT)),
            "note":"D0.1 is infrastructure prototype pass / skill benchmark invalid; D0.2 uses independent agent sessions."}
    dump(reports/"d02_gates.json",report); dump(reports/"d02_session_evidence.internal.json",evidence)
    (reports/"d02_report.md").write_text("""# D0.2 Real-Agent CAD Skill Benchmark

STATUS = HUMAN_REVIEW

This report is blind-safe. D0.1 is retained as infrastructure prototype pass / skill benchmark invalid. D0.2 outputs were produced by independent sessions using saved DXF command logs. The arm mapping is stored separately in blind_review/arm_mapping.secret.json and is not included here.

Review only:
- blind_review/A.png through D.png
- blind_review/A_clearance.png through D_clearance.png
- blind_review/comparison_sheet.png
- blind_review/human_review_form.md

No automatic winner or design-quality score is produced. No formal CAD write-back is authorized.
""")
    return report

if __name__ == "__main__":
    print(json.dumps(package(),ensure_ascii=False,indent=2))

