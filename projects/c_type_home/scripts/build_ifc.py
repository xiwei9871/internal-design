"""Build C型_原始户型数字化基准模型.ifc (IFC4) from data/geometry.json.

Hierarchy: IfcProject -> IfcSite -> IfcBuilding -> IfcBuildingStorey.
Walls/columns are extruded with visualization_only_height_mm=2800 which is
NOT SOURCE DATA / NOT FOR CONSTRUCTION — the plan carries no storey height.
Project properties record SourceStatus and FieldVerified=false.
"""
import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.guid

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geo_common import PROJECT_ROOT, load_geometry, wall_polygon_mm  # noqa: E402

OUT = PROJECT_ROOT / "ifc" / "C型_原始户型数字化基准模型.ifc"
VIS_H = 2800.0  # visualization_only_height_mm — NOT SOURCE DATA


def rect_profile(model, rect):
    x1, y1, x2, y2 = rect
    w, d = x2 - x1, y2 - y1
    return model.create_entity(
        "IfcRectangleProfileDef", ProfileType="AREA",
        ProfileName=f"{w:.0f}x{d:.0f}",
        XDim=w, YDim=d), (x1, y1)


def extrude_wall(model, ctx, rect, h):
    profile, (ox, oy) = rect_profile(model, rect)
    solid = model.create_entity(
        "IfcExtrudedAreaSolid", SweptArea=profile,
        Position=model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity("IfcCartesianPoint",
                                         Coordinates=[float(ox), float(oy), 0.0]),
            Axis=model.create_entity("IfcDirection",
                                     DirectionRatios=[0.0, 0.0, 1.0]),
            RefDirection=model.create_entity(
                "IfcDirection", DirectionRatios=[1.0, 0.0, 0.0])),
        ExtrudedDirection=model.create_entity(
            "IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
        Depth=h)
    shape = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=ctx, RepresentationIdentifier="Body",
        RepresentationType="SweptSolid", Items=[solid])
    return model.create_entity(
        "IfcProductDefinitionShape", Representations=[shape])


def build():
    geo = load_geometry()
    model = ifcopenshell.file(schema="IFC4")
    project = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcProject",
        name="C型户型 SOURCE PLAN RECONSTRUCTION")
    ifcopenshell.api.run("unit.assign_unit", model)
    ctx = ifcopenshell.api.run(
        "context.add_context", model, context_type="Model")
    body = ifcopenshell.api.run(
        "context.add_context", model, context_type="Model",
        context_identifier="Body", target_view="MODEL_VIEW",
        parent=ctx)

    site = ifcopenshell.api.run("root.create_entity", model,
                                ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.run("root.create_entity", model,
                                    ifc_class="IfcBuilding",
                                    name="C型住宅")
    storey = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcBuildingStorey",
        name="Storey (height unknown — visualization only)")
    ifcopenshell.api.run("aggregate.assign_object", model,
                         relating_object=project, products=[site])
    ifcopenshell.api.run("aggregate.assign_object", model,
                         relating_object=site, products=[building])
    ifcopenshell.api.run("aggregate.assign_object", model,
                         relating_object=building, products=[storey])

    def placement():
        return model.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=storey.ObjectPlacement,
            RelativePlacement=model.create_entity(
                "IfcAxis2Placement3D",
                Location=model.create_entity(
                    "IfcCartesianPoint", Coordinates=[0.0, 0.0, 0.0])))

    def set_props(el, src):
        pset = ifcopenshell.api.run(
            "pset.add_pset", model, product=el,
            name="SourcePlanReconstruction")
        ifcopenshell.api.run(
            "pset.edit_pset", model, pset=pset, properties={
                "DesignID": src["id"],
                "SourceBasis": src.get("provenance", "unknown"),
                "Confidence": src.get("confidence", "UNKNOWN"),
                "NeedsFieldVerification": bool(
                    src.get("needs_field_verification", True)),
                "StructuralRole": "UNKNOWN",
            })

    created = []
    for w in geo["walls"]:
        el = ifcopenshell.api.run(
            "root.create_entity", model, ifc_class="IfcWall",
            name=w["id"])
        el.ObjectPlacement = placement()
        el.Representation = extrude_wall(model, body, w["rect_mm"], VIS_H)
        set_props(el, w)
        ifcopenshell.api.run(
            "spatial.assign_container", model,
            relating_structure=storey, products=[el])
        created.append(("wall", w["id"]))

    for c in geo.get("columns", []):
        el = ifcopenshell.api.run(
            "root.create_entity", model, ifc_class="IfcColumn",
            name=c["id"])
        el.ObjectPlacement = placement()
        el.Representation = extrude_wall(model, body, c["rect_mm"], VIS_H)
        set_props(el, c)
        ifcopenshell.api.run(
            "spatial.assign_container", model,
            relating_structure=storey, products=[el])
        created.append(("column", c["id"]))

    for sp in geo.get("spaces", []):
        xs = [p[0] for p in sp["polygon_mm"]]
        ys = [p[1] for p in sp["polygon_mm"]]
        el = ifcopenshell.api.run(
            "root.create_entity", model, ifc_class="IfcSpace",
            name=sp.get("name_zh", sp["id"]))
        el.ObjectPlacement = placement()
        set_props(el, sp)
        ifcopenshell.api.run(
            "aggregate.assign_object", model,
            relating_object=storey, products=[el])
        created.append(("space", sp["id"]))

    # doors/windows: no openings are cut (faces not booleaned in this pass);
    # they are registered as IfcDoor/IfcWindow placeholders with host refs.
    wall_elems = {w.Name: w for w in model.by_type("IfcWall")}
    for kind, cls in (("doors", "IfcDoor"), ("windows", "IfcWindow")):
        for op in geo.get(kind, []):
            el = ifcopenshell.api.run(
                "root.create_entity", model, ifc_class=cls,
                name=op["id"])
            el.ObjectPlacement = placement()
            pset = ifcopenshell.api.run(
                "pset.add_pset", model, product=el,
                name="SourcePlanReconstruction")
            ifcopenshell.api.run(
                "pset.edit_pset", model, pset=pset, properties={
                    "DesignID": op["id"],
                    "HostWallID": op.get("host_wall_id") or "NONE",
                    "OpeningWidthMm": float(
                        op.get("opening_width_mm") or 0),
                    "Confidence": op.get("confidence", "UNKNOWN"),
                    "NeedsFieldVerification": True,
                })
            ifcopenshell.api.run(
                "spatial.assign_container", model,
                relating_structure=storey, products=[el])
            created.append((kind[:-1], op["id"]))

    # project-level provenance properties
    pset = ifcopenshell.api.run(
        "pset.add_pset", model, product=project,
        name="SourcePlanReconstruction")
    ifcopenshell.api.run(
        "pset.edit_pset", model, pset=pset, properties={
            "SourceStatus": "Source Plan Reconstruction",
            "FieldVerified": False,
            "VisualizationOnlyHeightMm": VIS_H,
            "VisualizationHeightIsSourceData": False,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    model.write(str(OUT))
    print(f"IFC written: {OUT} ({len(created)} objects)")


if __name__ == "__main__":
    build()
