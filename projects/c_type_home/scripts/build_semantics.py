"""Task 02 — build semantic model from the frozen Task 01 contract.

Generates into projects/c_type_home/semantics/:
  space_semantics.json, element_semantics.json, room_schedule.json,
  room_schedule.csv, constraint_register.json

Rules: reference Task 01 IDs only; never duplicate coordinate truth;
UNRESOLVED instead of guessing; structural_role stays UNKNOWN.
"""
import csv
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import (  # noqa: E402
    PROJECT_ROOT, load_geometry, opening_world_rect, wall_axis)
from sem_common import (  # noqa: E402
    CANONICAL_ROLE, EXTERNAL_NODE, SEMANTICS_DIR, UNMODELED_ZONE,
    WALL_LOCATION_CLASS,
    WET_CLASS_BY_LABEL, envelope_wall_ids, opening_side_spaces,
    plan_orientation_of_wall, save, space_polys, wall_box)

ISSUES_MD = PROJECT_ROOT / "qc" / "unresolved_issues.md"
TOL_BOUNDARY = 450.0  # mm — space poly edge to wall band for "touching"


def parse_unresolved_issues():
    """Parse qc/unresolved_issues.md -> {id: {title, status}}."""
    issues = {}
    cur = None
    for line in ISSUES_MD.read_text(encoding="utf-8").splitlines():
        m = re.match(r"## (ISSUE-\d+) — (.+)", line)
        if m:
            cur = m.group(1)
            issues[cur] = {"title": m.group(2).strip(), "status": "ACTIVE"}
            continue
        if cur and "RESOLVED" in line and "status" in line.lower():
            issues[cur]["status"] = "RESOLVED"
    return issues


def build_space_semantics(geo):
    polys = space_polys(geo)
    wall_by_id = {w["id"]: w for w in geo["walls"]}
    wboxes = [(w["id"], wall_box(w)) for w in geo["walls"]]
    envelope = envelope_wall_ids(geo)
    envelope_boxes = [(w["id"], wall_box(w)) for w in geo["walls"]
                      if w["id"] in envelope]
    shaft_ids = {w["id"] for w in geo["walls"] if w["type"] == "shaft"}
    ac_boxes = [(b["id"], wall_box(b)) for b in geo.get("ac_bays", [])]

    # opening -> interior spaces lookup
    opening_spaces = {}
    for kind in ("doors", "windows"):
        for op in geo[kind]:
            host = wall_by_id.get(op.get("host_wall_id"))
            if host is None:
                opening_spaces[op["id"]] = []
                continue
            a, b = opening_side_spaces(op, host, polys, wboxes)
            opening_spaces[op["id"]] = a + b

    spaces = []
    for s in geo["spaces"]:
        poly = polys[s["id"]]
        label = s["name_zh"]
        wet, wet_reason = WET_CLASS_BY_LABEL.get(
            label, ("DRY", "no wet/service indication in source label"))
        ext_len = 0.0
        ext_walls = []
        for wid, wb in envelope_boxes:
            seg = poly.boundary.intersection(wb.buffer(TOL_BOUNDARY))
            L = seg.length
            if L > 50:
                ext_len += L
                ext_walls.append(wid)
        touches_shaft = any(
            poly.distance(wall_box(w)) <= TOL_BOUNDARY
            for w in geo["walls"] if w["id"] in shaft_ids)
        near_ac = [bid for bid, bb in ac_boxes
                   if poly.distance(bb) <= TOL_BOUNDARY + 600]
        ext_openings = sorted(
            op["id"] for op in geo["doors"] + geo["windows"]
            if op.get("host_wall_id") in envelope
            and s["id"] in opening_spaces.get(op["id"], []))
        doors_of = sorted(o["id"] for o in geo["doors"]
                          if s["id"] in opening_spaces.get(o["id"], []))
        spaces.append({
            "space_id": s["id"],
            "geometry_ref": s["id"],
            "source_label_zh": label,
            "canonical_role": CANONICAL_ROLE.get(label, "unknown"),
            "area_m2": round(poly.area / 1e6, 2),
            "perimeter_m": round(poly.length / 1000, 2),
            "source_confidence": s.get("confidence", "UNKNOWN"),
            "touches_exterior_envelope": bool(ext_walls),
            "envelope_walls": ext_walls,
            "external_wall_length_m": round(ext_len / 1000, 2),
            "exterior_openings": ext_openings,
            "connected_openings": doors_of,
            "touches_service_shaft": touches_shaft,
            "near_ac_bays": near_ac,
            "wet_service_class": wet,
            "wet_class_reason": wet_reason,
            "design_change_status": "UNKNOWN",
            "field_verification_required": s.get("confidence") != "HIGH",
            "notes": [],
        })
    return spaces, polys


def build_element_semantics(geo, polys):
    wall_by_id = {w["id"]: w for w in geo["walls"]}
    wboxes = [(w["id"], wall_box(w)) for w in geo["walls"]]
    envelope = envelope_wall_ids(geo)

    walls = []
    for w in geo["walls"]:
        walls.append({
            "element_id": w["id"],
            "element_type": "wall",
            "existing_location_class": WALL_LOCATION_CLASS.get(
                w["type"], "UNKNOWN"),
            "plan_orientation": plan_orientation_of_wall(w)
            if w["type"] in ("exterior", "railing_parapet") else None,
            "structural_role": "UNKNOWN",
            "design_change_status": "UNKNOWN",
            "verification_before_modification": True,
            "source_basis": w.get("provenance"),
            "source_confidence": w.get("confidence"),
        })

    doors = []
    for d in geo["doors"]:
        host = wall_by_id.get(d["host_wall_id"])
        a, b = opening_side_spaces(d, host, polys, wboxes)
        # A probe side that hits no modeled space is either outside the
        # apartment (exterior host) or a bounded interior zone that the
        # source never labeled (e.g. the corridor strip x11300-12900
        # y4650-6500 in front of cloak/master-bath/bed-n doors).
        def fill(hits):
            if hits:
                return hits
            return ([EXTERNAL_NODE]
                    if host["type"] in ("exterior", "railing_parapet")
                    else [UNMODELED_ZONE])
        a, b = fill(a), fill(b)
        notes = []
        side_a, side_b = a[0], b[0]
        connects = (side_a != side_b)
        if len(a) > 1 or len(b) > 1:
            notes.append(f"multiple space hits per side: a={a} b={b}")
        if UNMODELED_ZONE in (side_a, side_b):
            notes.append("one side is an interior zone with no source "
                         "label and no modeled polygon")
        if d["id"] == "D-10":
            notes.append("ISSUE-009 cased opening; west side lands in the "
                         "unmodeled sliver between W-INT-NICHE (LOW conf) "
                         "and the host wall — likely part of 休闲厅 if the "
                         "niche is a recess, not a full wall")
        if d["id"] == "D-13":
            notes.append("type=sliding_door_candidate (ISSUE-013); "
                         "do not upgrade without evidence")
        sem_conf = d.get("confidence", "UNKNOWN")
        doors.append({
            "element_id": d["id"],
            "element_type": "door",
            "host_wall_id": d["host_wall_id"],
            "side_a_space": side_a,
            "side_b_space": side_b,
            "side_a_all": a,
            "side_b_all": b,
            "connects_spaces": connects,
            "door_type": "sliding_door_candidate" if d["id"] == "D-13"
            else ("cased_opening_candidate" if d["id"] == "D-10"
                  else "swing_door"),
            "source_confidence": d.get("confidence"),
            "semantic_confidence": sem_conf,
            "notes": notes,
        })

    windows = []
    for w in geo["windows"]:
        host = wall_by_id.get(w["host_wall_id"])
        a, b = opening_side_spaces(w, host, polys, wboxes)
        sides = a + [x for x in b if x not in a]
        if host["type"] in ("exterior", "railing_parapet"):
            interior = sides
            outside = "EXTERIOR"
        else:
            interior = sides
            outside = "UNKNOWN"
        notes = []
        if len(interior) > 1:
            notes.append("opening spans multiple modeled spaces: "
                         + ",".join(interior))
        if not interior:
            interior = ["UNRESOLVED"]
        if w["id"] == "WIN-W1":
            notes.append("nature of thin-line zone uncertain (ISSUE-012)")
        windows.append({
            "element_id": w["id"],
            "element_type": "window",
            "host_wall_id": w["host_wall_id"],
            "interior_space_ids": interior,
            "interior_space_id": interior[0],
            "plan_orientation": plan_orientation_of_wall(host),
            "outside_condition": outside,
            "source_confidence": w.get("confidence"),
            "semantic_confidence": "LOW" if len(interior) > 1
            else w.get("confidence"),
            "notes": notes,
        })

    columns = [{
        "element_id": c["id"], "element_type": "column",
        "existing_location_class": "UNKNOWN",
        "structural_role": "UNKNOWN",
        "design_change_status": "UNKNOWN",
        "verification_before_modification": True,
        "source_basis": c.get("provenance"),
        "source_confidence": c.get("confidence"),
    } for c in geo.get("columns", [])]

    ac_bays = [{
        "element_id": b["id"], "element_type": "ac_bay",
        "existing_location_class": "SERVICE_BOUNDARY",
        "structural_role": "UNKNOWN",
        "design_change_status": "UNKNOWN",
        "verification_before_modification": True,
        "source_basis": b.get("provenance"),
        "source_confidence": b.get("confidence"),
    } for b in geo.get("ac_bays", [])]

    return {"walls": walls, "doors": doors, "windows": windows,
            "columns": columns, "ac_bays": ac_bays}


def build_constraints(geo, issues):
    cons = []

    def add(cid, cat, subj, desc, evidence, sev, ver_req, ver_m,
             status="ACTIVE", issue=None):
        cons.append({
            "constraint_id": cid, "category": cat,
            "subject_refs": subj, "description": desc,
            "evidence": evidence,
            "source_refs": [issue] if issue else [],
            "source_issue_ref": issue,
            "confidence": "HIGH" if issue is None else "MEDIUM",
            "severity_for_future_design": sev,
            "verification_required": ver_req,
            "verification_method": ver_m,
            "status": status,
        })

    # --- import every Task 01 issue ---
    ISSUE_MAP = {
        "ISSUE-001": ("GEOMETRY", "BLOCKING",
                      "底部外链左端基准 X0 无对应墙体，西缘定位基准悬空"),
        "ISSUE-002": ("GEOMETRY", "INFORMATIONAL",
                      "底部内链尾部数字已解为 200+100（历史记录）"),
        "ISSUE-003": ("GEOMETRY", "MEDIUM",
                      "底部内链 +400mm 基准偏移构件不明"),
        "ISSUE-004": ("STRUCTURE", "BLOCKING",
                      "全部墙体 structural_role=UNKNOWN；黑粗墙不能判定承重"),
        "ISSUE-005": ("SOURCE_CONFLICT", "HIGH",
                      "WIN-E1 尺寸标注与像素窗位冲突 ~500-800mm（按尺寸建模）"),
        "ISSUE-006": ("GEOMETRY", "MEDIUM",
                      "右链 12900 北端基准落在机位凹槽带，无墙线对应"),
        "ISSUE-007": ("OPENING", "INFORMATIONAL",
                      "厨房/阳台门位已解（历史记录）"),
        "ISSUE-008": ("OPENING", "INFORMATIONAL",
                      "厨房南 1400 段已解为 WIN-S3（历史记录）"),
        "ISSUE-009": ("OPENING", "MEDIUM",
                      "D-10 休闲厅↔走廊 1780mm 开口无门扇，垭口/漏绘未定"),
        "ISSUE-010": ("GEOMETRY", "HIGH",
                      "东北角机位/凹槽区几何不完整"),
        "ISSUE-011": ("ENVELOPE", "MEDIUM",
                      "客厅西墙外皮线 Y6650-10940 段缺失（贴公共走廊侧）"),
        "ISSUE-012": ("ENVELOPE", "HIGH",
                      "WIN-W1 薄线区性质不明（窗带/未填充墙）"),
        "ISSUE-013": ("OPENING", "MEDIUM",
                      "D-13 推拉门类型为推断，无轨道/门扇细节"),
    }
    for iid, info in issues.items():
        cat, sev, desc = ISSUE_MAP.get(iid, ("GEOMETRY", "MEDIUM",
                                           info["title"]))
        status = "RESOLVED_HISTORICAL" if info["status"] == "RESOLVED" \
            else "ACTIVE"
        subj = {"ISSUE-005": ["WIN-E1", "W-EXT-E1"],
                "ISSUE-009": ["D-10"], "ISSUE-011": ["W-EXT-W"],
                "ISSUE-012": ["WIN-W1", "W-EXT-W"],
                "ISSUE-013": ["D-13", "W-BALC-N"],
                "ISSUE-010": ["W-EXT-NE", "W-EXT-NE2"],
                "ISSUE-004": [w["id"] for w in geo["walls"]],
                }.get(iid, [])
        add(f"CONSTRAINT-{iid.replace('ISSUE-', 'T01-')}", cat, subj,
            desc, f"qc/unresolved_issues.md#{iid}", sev,
            status == "ACTIVE", "原始图纸/现场复核", status, iid)

    # --- Task 02 derived constraints ---
    add("CONSTRAINT-STRUCT-ALL", "STRUCTURE",
        [w["id"] for w in geo["walls"]] +
        [c["id"] for c in geo.get("columns", [])],
        "无任何结构资料：拆改任何墙体/柱前必须获得结构图或现场鉴定；"
        "外墙≠不可动、内墙≠可拆",
        "geometry.json structural_policy: 全部 structural_role=UNKNOWN",
        "BLOCKING", True, "结构图/现场勘测")

    add("CONSTRAINT-HEIGHT-001", "GEOMETRY", ["*"],
        "层高/吊顶净空/梁位全部未知；IFC 中 2800mm 为可视化占位非源数据",
        "源图为平面户型图，无剖面/标高信息", "HIGH", True,
        "现场量测层高、梁底、门槛/窗台/窗顶高度")

    add("CONSTRAINT-SVC-KITCHEN", "SERVICE", ["R-KITCHEN", "W-SHAFT-K"],
        "厨房邻近竖向服务井 W-SHAFT-K(LOW)；管线走向/管径/坡度未知",
        "W-SHAFT-K x7150-7250 y750-3650 位于厨房范围内", "HIGH", True,
        "现场确认管道井性质/排水立管/燃气表位")

    for sid, lbl in (("R-BATH-M", "主卫"), ("R-BATH-P", "公卫")):
        add(f"CONSTRAINT-SVC-{sid}", "SERVICE", [sid],
            f"{lbl} 湿区：排水立管/地漏/沉箱位置未知",
            "source label 为卫生间", "HIGH", True, "现场/物业资料")

    add("CONSTRAINT-ENVELOPE-PERM", "ENVELOPE",
        sorted(envelope_wall_ids(geo)),
        "外围护构件（含阳台栏板）的改造权限未知：物业/规划/外立面管制",
        "外墙事实 ≠ 可改许可", "HIGH", True, "物业/管理规约/法规确认")

    add("CONSTRAINT-ORIENT-001", "GEOMETRY", ["*"],
        "源图无指北针：所有方向为 PLAN_* 图像相对方向，非地理方位",
        "source plan 无 North arrow", "LOW", False, "如需要由业主确认朝向")

    add("CONSTRAINT-MEP-001", "SERVICE", ["*"],
        "源图无给排水/电气/燃气/暖通信息；燃气管是否存在都未确认",
        "sales plan 不含 MEP", "HIGH", True, "现场/物业资料")

    add("CONSTRAINT-REG-001", "REGULATORY_UNKNOWN", ["*"],
        "适用规范/管辖地要求未建模", "无规范输入", "INFORMATIONAL",
        True, "确认项目所在地规范体系")

    add("CONSTRAINT-CIRC-KITCHEN", "ACCESS", ["R-KITCHEN", "D-11", "D-13"],
        "按当前模型，厨房唯一通行路径为 餐厅→D-13→生活阳台→D-11→厨房",
        "adjacency/circulation graph", "MEDIUM", True,
        "现场确认是否另有厨房入口（图面未见）")

    add("CONSTRAINT-AC-001", "SERVICE",
        [b["id"] for b in geo.get("ac_bays", [])],
        "空调机位 LOW confidence；NE 机位区几何不完整（ISSUE-010）",
        "ac_bays pixel_scaled", "MEDIUM", True, "现场确认机位/冷凝水")

    return cons


def build_room_schedule(spaces, elements, graph=None):
    rows = []
    for s in spaces:
        sid = s["space_id"]
        doors = [d for d in elements["doors"]
                 if sid in (d["side_a_space"], d["side_b_space"])]
        wins = [w for w in elements["windows"] if sid in
                w["interior_space_ids"]]
        rows.append({
            "space_id": sid,
            "source_name": s["source_label_zh"],
            "canonical_role": s["canonical_role"],
            "area_m2": s["area_m2"],
            "perimeter_m": s["perimeter_m"],
            "external_wall_length_m": s["external_wall_length_m"],
            "number_of_doors": len(doors),
            "number_of_windows": len(wins),
            "total_window_width_mm": sum(
                _win_width(w) for w in wins),
            "adjacent_spaces": [],
            "directly_connected_spaces": [],
            "wet_service_class": s["wet_service_class"],
            "source_confidence": s["source_confidence"],
            "field_verification_required": s["field_verification_required"],
        })
    return rows


def _win_width(wsem):
    return _WIN_WIDTHS.get(wsem["element_id"], 0)


_WIN_WIDTHS = {}


def main():
    geo = load_geometry()
    issues = parse_unresolved_issues()
    spaces, polys = build_space_semantics(geo)
    elements = build_element_semantics(geo, polys)
    global _WIN_WIDTHS
    _WIN_WIDTHS = {w["id"]: w.get("opening_width_mm") or 0
                   for w in geo["windows"]}
    constraints = build_constraints(geo, issues)
    schedule = build_room_schedule(spaces, elements)

    modeled = round(sum(s["area_m2"] for s in spaces), 2)
    wet = round(sum(s["area_m2"] for s in spaces
                    if s["wet_service_class"] in ("WET", "SEMI_WET",
                                                  "SERVICE")), 2)
    summary = {
        "note": "modeled_plan_area is NOT official sale/gross area",
        "space_count": len(spaces),
        "modeled_plan_area_m2": modeled,
        "wet_service_area_m2": wet,
        "dry_area_m2": round(modeled - wet, 2),
    }

    save("space_semantics.json",
         {"meta": {"task": "task02", "unit": "mm/m2",
                   "source": "geometry.json (frozen Task 01)"},
          "summary": summary, "spaces": spaces})
    save("element_semantics.json",
         {"meta": {"task": "task02",
                   "structural_policy": "all structural_role UNKNOWN"},
          **elements})
    save("constraint_register.json",
         {"meta": {"task": "task02", "severity_meaning":
                   "assumption-risk for future design agents, NOT "
                   "demolish-permission"},
          "constraints": constraints})
    save("room_schedule.json", {"meta": {"task": "task02"},
                                "summary": summary, "rooms": schedule})

    fields = list(schedule[0].keys())
    with open(SEMANTICS_DIR / "room_schedule.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(schedule)
    print("schedule csv written;",
          f"active constraints: "
          f"{sum(1 for c in constraints if c['status'] == 'ACTIVE')}")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
