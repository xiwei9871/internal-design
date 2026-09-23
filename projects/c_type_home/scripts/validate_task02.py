"""Task 02 — semantic model audit -> qc/task02_semantic_audit.json

Checks cross-consistency between the frozen Task 01 contract and the
Task 02 semantic layer. Gate logic lives in tests/test_c_type_task02.py;
this script produces the evidence artifact.
"""
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import PROJECT_ROOT, load_geometry  # noqa: E402
from sem_common import SEMANTICS_DIR  # noqa: E402

SEM = SEMANTICS_DIR
QC = PROJECT_ROOT / "qc"
IFC_T01 = PROJECT_ROOT / "ifc" / "C型_原始户型数字化基准模型.ifc"
IFC_T02 = PROJECT_ROOT / "ifc" / "C型_现状语义约束模型.ifc"


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def world_bounds_mm(el):
    import ifcopenshell.geom
    st = ifcopenshell.geom.settings()
    st.set("use-world-coords", True)
    sh = ifcopenshell.geom.create_shape(st, el)
    v = sh.geometry.verts
    xs, ys, zs = v[0::3], v[1::3], v[2::3]
    return (min(xs) * 1000, min(ys) * 1000, min(zs) * 1000,
            max(xs) * 1000, max(ys) * 1000, max(zs) * 1000)


def pset_props(el, name):
    out = {}
    for rel in el.IsDefinedBy or []:
        ps = rel.RelatingPropertyDefinition
        if getattr(ps, "Name", None) == name:
            for p in ps.HasProperties:
                out[p.Name] = getattr(p, "NominalValue", None)
                if out[p.Name] is not None:
                    out[p.Name] = out[p.Name].wrappedValue
    return out


def main():
    geo = load_geometry()
    sem = json.loads((SEM / "space_semantics.json").read_text("utf-8"))
    elem = json.loads((SEM / "element_semantics.json").read_text("utf-8"))
    graph = json.loads((SEM / "adjacency_graph.json").read_text("utf-8"))
    cons = json.loads(
        (SEM / "constraint_register.json").read_text("utf-8"))[
        "constraints"]

    audit = {"hashes": {
        "geometry.json": sha256(PROJECT_ROOT / "data/geometry.json"),
        "dimensions.json": sha256(PROJECT_ROOT / "data/dimensions.json")}}

    # space coverage
    g_ids = {s["id"] for s in geo["spaces"]}
    s_ids = {s["space_id"] for s in sem["spaces"]}
    audit["space_coverage"] = {
        "geometry_spaces": len(g_ids), "semantic_spaces": len(s_ids),
        "missing": sorted(g_ids - s_ids), "extra": sorted(s_ids - g_ids)}

    # door/window binding status
    audit["door_bindings"] = {
        d["element_id"]: [d["side_a_space"], d["side_b_space"]]
        for d in elem["doors"]}
    audit["unresolved_doors"] = [
        d["element_id"] for d in elem["doors"]
        if "UNRESOLVED" in (d["side_a_space"], d["side_b_space"])]
    audit["unresolved_windows"] = [
        w["element_id"] for w in elem["windows"]
        if "UNRESOLVED" in w["interior_space_ids"]]

    # constraints
    active = [c for c in cons if c["status"] == "ACTIVE"]
    audit["constraints"] = {
        "total": len(cons), "active": len(active),
        "by_severity": {s: sum(
            1 for c in active if c["severity_for_future_design"] == s)
            for s in ("BLOCKING", "HIGH", "MEDIUM", "LOW",
                      "INFORMATIONAL")},
        "task01_issues_mapped": sorted(
            c["source_issue_ref"] for c in cons if c["source_issue_ref"]),
        "incomplete": [c["constraint_id"] for c in cons if not (
            c.get("evidence") and c.get("confidence")
            and c.get("verification_required") is not None)]}

    # graph sanity
    node_ids = {n["id"] for n in graph["nodes"]}
    bad = [e for e in graph["adjacency_edges"] + graph["circulation_edges"]
           if e["space_a"] not in node_ids or e["space_b"] not in node_ids]
    audit["graph"] = {
        "nodes": len(node_ids),
        "adjacency_edges": len(graph["adjacency_edges"]),
        "circulation_edges": len(graph["circulation_edges"]),
        "invalid_edge_refs": len(bad),
        "component_count": graph["component_count"],
    }

    # IFC semantics + geometry immutability
    import ifcopenshell
    m1, m2 = ifcopenshell.open(str(IFC_T01)), ifcopenshell.open(str(IFC_T02))
    audit["ifc"] = {"pset_counts": {}, "geometry_delta_mm": {}}
    for typ, psn in (("IfcSpace", "Pset_Task02SpaceSemantics"),
                     ("IfcWall", "Pset_Task02ElementSemantics")):
        audit["ifc"]["pset_counts"][typ] = sum(
            1 for el in m2.by_type(typ) if pset_props(el, psn))
    max_delta = 0.0
    worst = None
    for typ in ("IfcWall", "IfcColumn", "IfcOpeningElement",
                "IfcDoor", "IfcWindow"):
        e1 = {el.Name: el for el in m1.by_type(typ)}
        for el2 in m2.by_type(typ):
            b1 = world_bounds_mm(e1[el2.Name])
            b2 = world_bounds_mm(el2)
            d = max(abs(x - y) for x, y in zip(b1, b2))
            if d > max_delta:
                max_delta, worst = d, f"{typ}:{el2.Name}"
    audit["ifc"]["geometry_delta_mm"] = {
        "max": round(max_delta, 4), "worst": worst, "tolerance": 0.1,
        "pass": max_delta <= 0.1}
    audit["ifc"]["no_furniture"] = not m2.by_type("IfcFurniture")

    QC.mkdir(exist_ok=True)
    (QC / "task02_semantic_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
