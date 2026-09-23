"""Task 02 — IFC semantic enrichment (metadata only).

Reads the Task 01 IFC and writes C型_现状语义约束模型.ifc with added
property sets. No placement or geometry is touched — a hard gate test
compares world bounds of every product before/after (<=0.1mm).

Psets:
  Pset_Task02SpaceSemantics    on IfcSpace
  Pset_Task02ElementSemantics  on IfcWall / IfcDoor / IfcWindow / IfcColumn
  Pset_Task02Constraints       on elements referenced by constraints
"""
import json
import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.api

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import PROJECT_ROOT  # noqa: E402

SRC_IFC = PROJECT_ROOT / "ifc" / "C型_原始户型数字化基准模型.ifc"
OUT_IFC = PROJECT_ROOT / "ifc" / "C型_现状语义约束模型.ifc"
SEM = PROJECT_ROOT / "semantics"

SEV_ORDER = {"INFORMATIONAL": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3,
             "BLOCKING": 4}


def design_id(el):
    """Read DesignID from the Task 01 SourcePlanReconstruction pset."""
    for rel in el.IsDefinedBy or []:
        ps = rel.RelatingPropertyDefinition
        if getattr(ps, "Name", None) == "SourcePlanReconstruction":
            for p in ps.HasProperties:
                if p.Name == "DesignID":
                    return p.NominalValue.wrappedValue
    return None


def add_pset(model, el, name, props):
    ps = ifcopenshell.api.run("pset.add_pset", model, product=el, name=name)
    ifcopenshell.api.run("pset.edit_pset", model, pset=ps,
                         properties=props)


def main():
    spaces = {s["space_id"]: s for s in json.loads(
        (SEM / "space_semantics.json").read_text(encoding="utf-8")
    )["spaces"]}
    elements = json.loads(
        (SEM / "element_semantics.json").read_text(encoding="utf-8"))
    constraints = json.loads(
        (SEM / "constraint_register.json").read_text(encoding="utf-8")
    )["constraints"]
    walls = {w["element_id"]: w for w in elements["walls"]}
    doors = {d["element_id"]: d for d in elements["doors"]}
    windows = {w["element_id"]: w for w in elements["windows"]}
    columns = {c["element_id"]: c for c in elements["columns"]}

    def constraint_pset(eid):
        rel = [c for c in constraints
               if c["status"] == "ACTIVE" and
               (eid in c["subject_refs"] or "*" in c["subject_refs"])]
        if not rel:
            return None
        worst = max(SEV_ORDER[c["severity_for_future_design"]]
                    for c in rel)
        worst = [k for k, v in SEV_ORDER.items() if v == worst][0]
        return {"ActiveConstraintCount": len(rel),
                "HighestConstraintSeverity": worst}

    model = ifcopenshell.open(str(SRC_IFC))
    n_psets = 0

    for el in model.by_type("IfcSpace"):
        sid = design_id(el) or el.Name
        s = spaces.get(sid) or next(
            (v for v in spaces.values() if v["source_label_zh"] == el.Name),
            None)
        if not s:
            continue
        add_pset(model, el, "Pset_Task02SpaceSemantics", {
            "SpaceID": s["space_id"],
            "SourceLabelZh": s["source_label_zh"],
            "CanonicalRole": s["canonical_role"],
            "WetServiceClass": s["wet_service_class"],
            "TouchesExterior": s["touches_exterior_envelope"],
            "FieldVerificationRequired": s["field_verification_required"]})
        n_psets += 1

    for el in model.by_type("IfcWall"):
        w = walls.get(el.Name)
        if not w:
            continue
        props = {
            "ExistingLocationClass": w["existing_location_class"],
            "PlanOrientation": w.get("plan_orientation") or "INTERIOR",
            "StructuralRole": "UNKNOWN",
            "DesignChangeStatus": w["design_change_status"],
            "VerificationBeforeModification":
                w["verification_before_modification"]}
        add_pset(model, el, "Pset_Task02ElementSemantics", props)
        n_psets += 1
        cp = constraint_pset(el.Name)
        if cp:
            add_pset(model, el, "Pset_Task02Constraints", cp)
            n_psets += 1

    for el in model.by_type("IfcDoor"):
        d = doors.get(el.Name)
        if not d:
            continue
        add_pset(model, el, "Pset_Task02ElementSemantics", {
            "ConnectedSpaceA": d["side_a_space"],
            "ConnectedSpaceB": d["side_b_space"],
            "ConnectsSpaces": bool(d["connects_spaces"]),
            "DoorType": d["door_type"],
            "DesignChangeStatus": "UNKNOWN",
            "VerificationBeforeModification": True})
        n_psets += 1
        cp = constraint_pset(el.Name)
        if cp:
            add_pset(model, el, "Pset_Task02Constraints", cp)
            n_psets += 1

    for el in model.by_type("IfcWindow"):
        w = windows.get(el.Name)
        if not w:
            continue
        add_pset(model, el, "Pset_Task02ElementSemantics", {
            "InteriorSpace": w["interior_space_id"],
            "PlanOrientation": w["plan_orientation"] or "UNKNOWN",
            "OutsideCondition": w["outside_condition"],
            "DesignChangeStatus": "UNKNOWN",
            "VerificationBeforeModification": True})
        n_psets += 1
        cp = constraint_pset(el.Name)
        if cp:
            add_pset(model, el, "Pset_Task02Constraints", cp)
            n_psets += 1

    for el in model.by_type("IfcColumn"):
        c = columns.get(el.Name)
        if not c:
            continue
        add_pset(model, el, "Pset_Task02ElementSemantics", {
            "ExistingLocationClass": c["existing_location_class"],
            "StructuralRole": "UNKNOWN",
            "DesignChangeStatus": "UNKNOWN",
            "VerificationBeforeModification": True})
        n_psets += 1

    model.write(str(OUT_IFC))
    print(f"wrote {OUT_IFC} — {n_psets} semantic psets added")


if __name__ == "__main__":
    main()
