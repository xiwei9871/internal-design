"""Build C型_原始户型数字化基准模型.ifc (IFC4) from data/geometry.json.

Hierarchy: IfcProject -> IfcSite -> IfcBuilding -> IfcBuildingStorey.
For every door/window a real void relationship is created:

    IfcOpeningElement  (geometry = extruded box through the host wall)
    IfcRelVoidsElement (host IfcWall  -> opening)
    IfcRelFillsElement (opening       -> IfcDoor / IfcWindow)

Extrusion heights are visualization_only (NOT SOURCE DATA — no storey
height is present in the source plan).
"""
import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.guid

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import (  # noqa: E402
    PROJECT_ROOT, load_geometry, opening_world_rect)

OUT = PROJECT_ROOT / "ifc" / "C型_原始户型数字化基准模型.ifc"
VIS_H = 2800.0   # visualization_only_height_mm — NOT SOURCE DATA
DOOR_H = 2100.0  # visualization only
WIN_SILL = 900.0  # visualization only
WIN_H = 1500.0   # visualization only


def cartesian(model, x, y, z):
    return model.create_entity(
        "IfcCartesianPoint", Coordinates=[float(x), float(y), float(z)])


def axis3d(model, x, y, z):
    return model.create_entity("IfcAxis2Placement3D",
                               Location=cartesian(model, x, y, z))


def direction(model, x, y, z):
    return model.create_entity("IfcDirection",
                               DirectionRatios=[float(x), float(y), float(z)])


def extrusion(model, ctx, w, d, h):
    profile = model.create_entity(
        "IfcRectangleProfileDef", ProfileType="AREA",
        ProfileName=f"{w:.0f}x{d:.0f}", XDim=w, YDim=d)
    solid = model.create_entity(
        "IfcExtrudedAreaSolid", SweptArea=profile,
        Position=model.create_entity(
            "IfcAxis2Placement3D", Location=cartesian(model, 0, 0, 0),
            Axis=direction(model, 0, 0, 1),
            RefDirection=direction(model, 1, 0, 0)),
        ExtrudedDirection=direction(model, 0, 0, 1), Depth=h)
    return model.create_entity(
        "IfcShapeRepresentation", ContextOfItems=ctx,
        RepresentationIdentifier="Body", RepresentationType="SweptSolid",
        Items=[solid])


def build():
    geo = load_geometry()
    model = ifcopenshell.file(schema="IFC4")
    project = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcProject",
        name="C型户型 SOURCE PLAN RECONSTRUCTION")
    ifcopenshell.api.run("unit.assign_unit", model)
    ctx = ifcopenshell.api.run("context.add_context", model,
                             context_type="Model")
    body = ifcopenshell.api.run(
        "context.add_context", model, context_type="Model",
        context_identifier="Body", target_view="MODEL_VIEW", parent=ctx)

    site = ifcopenshell.api.run("root.create_entity", model,
                                ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.run("root.create_entity", model,
                                    ifc_class="IfcBuilding", name="C型住宅")
    storey = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcBuildingStorey",
        name="Storey (height unknown — visualization only)")
    ifcopenshell.api.run("aggregate.assign_object", model,
                         relating_object=project, products=[site])
    ifcopenshell.api.run("aggregate.assign_object", model,
                         relating_object=site, products=[building])
    ifcopenshell.api.run("aggregate.assign_object", model,
                         relating_object=building, products=[storey])

    def placement(x=0.0, y=0.0, z=0.0, rel_to=None):
        return model.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=rel_to or storey.ObjectPlacement,
            RelativePlacement=axis3d(model, x, y, z))

    def pset(el, props):
        ps = ifcopenshell.api.run("pset.add_pset", model, product=el,
                                  name="SourcePlanReconstruction")
        ifcopenshell.api.run("pset.edit_pset", model, pset=ps,
                             properties=props)

    def src_props(src):
        return {"DesignID": src["id"],
                "SourceBasis": src.get("provenance", "unknown"),
                "Confidence": src.get("confidence", "UNKNOWN"),
                "NeedsFieldVerification": bool(
                    src.get("needs_field_verification", True)),
                "StructuralRole": "UNKNOWN"}

    counts = {"wall": 0, "column": 0, "space": 0, "opening": 0,
              "door": 0, "window": 0, "voids": 0, "fills": 0}

    wall_elems = {}
    wall_by_id = {w["id"]: w for w in geo["walls"]}
    for w in geo["walls"]:
        el = ifcopenshell.api.run("root.create_entity", model,
                                  ifc_class="IfcWall", name=w["id"])
        el.ObjectPlacement = placement()
        x1, y1, x2, y2 = w["rect_mm"]
        rep = model.create_entity(
            "IfcProductDefinitionShape",
            Representations=[extrusion(model, body, x2 - x1, y2 - y1, VIS_H)])
        el.Representation = rep
        el.ObjectPlacement = placement(x1, y1, 0.0)
        pset(el, src_props(w))
        ifcopenshell.api.run("spatial.assign_container", model,
                             relating_structure=storey, products=[el])
        wall_elems[w["id"]] = el
        counts["wall"] += 1

    for c in geo.get("columns", []):
        el = ifcopenshell.api.run("root.create_entity", model,
                                  ifc_class="IfcColumn", name=c["id"])
        x1, y1, x2, y2 = c["rect_mm"]
        el.ObjectPlacement = placement(x1, y1, 0.0)
        el.Representation = model.create_entity(
            "IfcProductDefinitionShape",
            Representations=[extrusion(model, body, x2 - x1, y2 - y1, VIS_H)])
        pset(el, src_props(c))
        ifcopenshell.api.run("spatial.assign_container", model,
                             relating_structure=storey, products=[el])
        counts["column"] += 1

    for sp in geo.get("spaces", []):
        el = ifcopenshell.api.run("root.create_entity", model,
                                  ifc_class="IfcSpace",
                                  name=sp.get("name_zh", sp["id"]))
        el.ObjectPlacement = placement()
        pset(el, src_props(sp))
        ifcopenshell.api.run("aggregate.assign_object", model,
                             relating_object=storey, products=[el])
        counts["space"] += 1

    # doors / windows with real opening + void/fill relationships
    for kind, cls in (("doors", "IfcDoor"), ("windows", "IfcWindow")):
        for op in geo[kind]:
            host = wall_by_id.get(op.get("host_wall_id"))
            wall_el = wall_elems.get(op.get("host_wall_id"))
            if host is None or wall_el is None:
                continue
            ox1, oy1, ox2, oy2 = opening_world_rect(op, host)
            wx1, wy1 = host["rect_mm"][0], host["rect_mm"][1]
            op_h = DOOR_H if kind == "doors" else WIN_H
            op_z = 0.0 if kind == "doors" else WIN_SILL

            opening = ifcopenshell.api.run(
                "root.create_entity", model, ifc_class="IfcOpeningElement",
                name=f"{op['id']}-OPENING")
            opening.ObjectPlacement = placement(
                ox1 - wx1, oy1 - wy1, op_z, rel_to=wall_el.ObjectPlacement)
            opening.Representation = model.create_entity(
                "IfcProductDefinitionShape",
                Representations=[extrusion(model, body,
                                           ox2 - ox1, oy2 - oy1, op_h)])
            pset(opening, {**src_props(op),
                           "HostWallID": op["host_wall_id"]})
            counts["opening"] += 1

            fill = ifcopenshell.api.run(
                "root.create_entity", model, ifc_class=cls, name=op["id"])
            fill.ObjectPlacement = placement(
                ox1 - wx1, oy1 - wy1, op_z, rel_to=wall_el.ObjectPlacement)
            pset(fill, {**src_props(op),
                        "HostWallID": op["host_wall_id"],
                        "OpeningWidthMm": float(
                            op.get("opening_width_mm") or 0)})
            counts[kind[:-1]] += 1

            model.create_entity(
                "IfcRelVoidsElement",
                GlobalId=ifcopenshell.guid.new(),
                RelatingBuildingElement=wall_el,
                RelatedOpeningElement=opening)
            counts["voids"] += 1
            model.create_entity(
                "IfcRelFillsElement",
                GlobalId=ifcopenshell.guid.new(),
                RelatingOpeningElement=opening,
                RelatedBuildingElement=fill)
            counts["fills"] += 1

    ps = ifcopenshell.api.run("pset.add_pset", model, product=project,
                              name="SourcePlanReconstruction")
    ifcopenshell.api.run("pset.edit_pset", model, pset=ps, properties={
        "SourceStatus": "Source Plan Reconstruction",
        "FieldVerified": False,
        "VisualizationOnlyHeightMm": VIS_H,
        "VisualizationHeightIsSourceData": False})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    model.write(str(OUT))
    print(f"IFC written: {OUT} {counts}")


if __name__ == "__main__":
    build()
