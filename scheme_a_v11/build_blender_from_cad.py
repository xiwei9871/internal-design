from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
CAD = ROOT / "cad"
OUT = ROOT / "renders"
OUT.mkdir(parents=True, exist_ok=True)
DATA = json.loads((ROOT.parent / "scheme_a_v7" / "scheme_a_geometry.json").read_text(encoding="utf-8"))
SCALE_MM = float(DATA["metres_per_pixel"]) * 1000.0
ORIGIN_X = 200.0
ORIGIN_Y = 1337.0


def world(px: float, py: float, z_mm: float = 0.0) -> tuple[float, float, float]:
    return ((px - ORIGIN_X) * SCALE_MM / 1000.0, (ORIGIN_Y - py) * SCALE_MM / 1000.0, z_mm / 1000.0)


def mat(name: str, color, roughness=0.5, metallic=0.0, alpha=1.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = (*color, alpha)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        material.surface_render_method = "DITHERED"
    return material


def mesh_material(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def add_prism(name: str, poly, z0: float, z1: float, material):
    verts = [world(x, y, z0) for x, y in poly] + [world(x, y, z1) for x, y in poly]
    n = len(poly)
    # The transformed plan polygon is clockwise in Blender XY. Keep the
    # bottom face outward (-Z) and reverse the top face so its normal is +Z;
    # this matters for the ceiling underside and for floor lighting.
    faces = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
    for i in range(n):
        faces.append((i, (i + 1) % n, (i + 1) % n + n, i + n))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh_material(obj, material)
    return obj


def add_box(name: str, rect_values, z0_mm: float, z1_mm: float, material, bevel=0.0):
    x, y, w, h = rect_values
    p = world(x, y + h, z0_mm)
    bpy.ops.mesh.primitive_cube_add(location=((p[0] + w * SCALE_MM / 2000.0), (p[1] + h * SCALE_MM / 2000.0), (z0_mm + z1_mm) / 2000.0))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (w * SCALE_MM / 1000.0, h * SCALE_MM / 1000.0, (z1_mm - z0_mm) / 1000.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mesh_material(obj, material)
    if bevel:
        modifier = obj.modifiers.new("edge softness", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


def add_floor_overlays(tile_material):
    # The FreeCAD floor export remains the reference. These thin overlays make wet areas
    # readable in the render without changing the source geometry or wall coordinates.
    for zone in DATA["zones"]:
        if zone["material"] != "wet":
            continue
        add_prism("WetFloor_" + zone["name"], zone["polygon"], 60, 64, tile_material)


def add_linear_light(name, location, energy, size, color=(1.0, 0.82, 0.66)):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = "RECTANGLE"
    light.data.size = size
    light.data.size_y = size * 0.45
    light.data.color = color
    return light


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def add_camera(name, camera_px, target_px, height_mm, lens):
    bpy.ops.object.camera_add(location=world(camera_px[0], camera_px[1], height_mm))
    camera = bpy.context.object
    camera.name = name
    camera.data.lens = lens
    camera.data.sensor_width = 36
    look_at(camera, world(target_px[0], target_px[1], 1100))
    return camera


def import_group(key: str, material):
    path = CAD / f"scheme_a11_{key}.obj"
    if not path.exists():
        raise FileNotFoundError(path)
    before = set(bpy.context.scene.objects)
    bpy.ops.wm.obj_import(filepath=str(path))
    imported = [obj for obj in bpy.context.scene.objects if obj not in before]
    for obj in imported:
        obj.scale = (0.001, 0.001, 0.001)
        # Blender's OBJ importer creates a +90° X rotation for the source
        # Z-up coordinate system. Clear that importer rotation so the
        # FreeCAD millimetre coordinates remain (x, y, z) in Blender.
        obj.rotation_euler[0] = 0.0
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        mesh_material(obj, material)
        obj.select_set(False)
    return imported


def configure_render():
    scene = bpy.context.scene
    # Blender 5.2 keeps the Eevee engine identifier as BLENDER_EEVEE.
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 760
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.image_settings.color_depth = "8"
    scene.render.resolution_percentage = 100
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.6
    world_data = scene.world or bpy.data.worlds.new("World")
    scene.world = world_data
    world_data.use_nodes = True
    # Neutral daylight outside the windows keeps the model readable while
    # leaving the interior lighting to the explicit area lights below.
    world_data.node_tree.nodes["Background"].inputs["Color"].default_value = (0.24, 0.27, 0.30, 1.0)
    world_data.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    bpy.ops.object.light_add(type="SUN", location=(6, -3, 8))
    sun = bpy.context.object
    sun.name = "全屋漫射日光"
    sun.data.energy = 1.25
    sun.data.angle = math.radians(30)
    sun.rotation_euler = (math.radians(28), math.radians(-18), math.radians(25))
    add_linear_light("客餐厅暖光", world(980, 1030, 2400), 650, 4.0)
    add_linear_light("厨房暖光", world(600, 230, 2400), 480, 3.0)
    add_linear_light("主卧暖光", world(600, 1000, 2400), 500, 3.0)
    add_linear_light("老人房暖光", world(980, 480, 2400), 450, 3.0)
    add_linear_light("儿童房暖光", world(1300, 950, 2400), 450, 3.0)
    add_linear_light("主卫暖光", world(320, 700, 2200), 320, 2.0)
    add_linear_light("次卫暖光", world(500, 470, 2200), 300, 2.0)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    wall_material = mat("墙面·暖白", (0.84, 0.82, 0.76), 0.86)
    floor_material = mat("地面·浅原木", (0.52, 0.34, 0.16), 0.55)
    tile_material = mat("湿区·暖灰砖", (0.48, 0.55, 0.53), 0.42)
    furniture_material = mat("定制家具·白蜡木", (0.63, 0.41, 0.20), 0.45)
    fixtures_material = mat("洁具家电·浅灰", (0.78, 0.80, 0.76), 0.25, 0.08)
    appliance_front = mat("服务墙设备正面·不锈钢", (0.36, 0.38, 0.37), 0.22, 0.18)
    oven_front = mat("服务墙蒸烤正面·黑玻", (0.045, 0.055, 0.055), 0.18, 0.12)
    opening_material = mat("门窗·半透明", (0.48, 0.72, 0.74), 0.10, 0.02, 0.18)
    door_material = mat("室内门·木饰面", (0.60, 0.44, 0.26), 0.62)
    ceiling_material = mat("吊顶·纯白", (0.92, 0.92, 0.89), 0.92)

    import_group("walls", wall_material)
    import_group("floors", floor_material)
    import_group("openings", opening_material)
    # Door leaves are opaque wood.  The OBJ importer merges each file into a
    # single mesh, so doors ship as their own group export from FreeCAD;
    # windows, sliding doors, and shower screens keep the translucent material.
    import_group("doors", door_material)
    import_group("furniture", furniture_material)
    import_group("fixtures", fixtures_material)
    # The grouped OBJ intentionally keeps CAD geometry compact, but a single
    # fixture material would hide the appliance order in the K verification
    # render. Add thin, non-structural front faces at the exact A7 footprints
    # so Blender visibly distinguishes the three columns without changing
    # wall coordinates or passage width.
    add_box("K_FridgeFront", [653, 322, 2, 91], 0, 1950, appliance_front)
    add_box("K_SteamOvenFront", [653, 413, 2, 70], 1250, 1845, oven_front)
    add_box("K_OvenFront", [653, 413, 2, 70], 550, 1145, oven_front)
    add_box("K_WasherFront", [653, 483, 2, 73], 100, 945, appliance_front)
    add_box("K_DryerFront", [653, 483, 2, 73], 1000, 1845, appliance_front)
    add_floor_overlays(tile_material)
    # The FreeCAD ceiling stays in the FCStd document and is recreated here as
    # a separate object so interior cameras have a real enclosure while the
    # source wall/furniture coordinates remain unchanged.
    add_prism("FlatCeiling_Render", DATA["outer"], 2600, 2650, ceiling_material)
    configure_render()

    anchors = {
        # L is set just north of the dining table so the fixed view includes
        # part of the dining set, the sofa/side table, coffee table, TV wall,
        # and south window in one legible composition.
        "living": ((1080, 760), (930, 1130), 1550, 22, "餐客厅·L"),
        # K is set in the corridor south of the service wall.  This keeps the
        # complete fridge/microwave/washer stack on the left side of the view,
        # with the kitchen worktop beyond it.
        "kitchen": ((735, 650), (620, 250), 1480, 25, "厨房服务墙·K"),
        # M stands in the clear floor strip between the window-side chair and
        # the east window-side cabinet; the previous anchor sat inside the
        # cabinet footprint so it filled half the frame.
        "master": ((650, 1170), (570, 980), 1550, 20, "主卧·M"),
        "child": ((1168, 1080), (1320, 1000), 1480, 20, "儿童房·C"),
        "elder": ((810, 620), (980, 480), 1500, 22, "老人房·E"),
        "main_bath": ((395, 835), (310, 690), 1420, 20, "主卫·B"),
        "secondary_bath": ((570, 625), (500, 470), 1420, 20, "次卫·S"),
    }
    cameras = {}
    for key, (camera_px, target_px, height_mm, lens, label) in anchors.items():
        cameras[key] = add_camera("Camera_" + key, camera_px, target_px, height_mm, lens)

    scene = bpy.context.scene
    for key, camera in cameras.items():
        scene.camera = camera
        scene.render.filepath = str(OUT / f"{key}.png")
        bpy.ops.render.render(write_still=True)

    scene["design_basis"] = "A7 PNG -> FreeCAD 1.1.3 parametric base -> OBJ -> Blender 5.2.1 render"
    scene["source_scale_mm_per_pixel"] = SCALE_MM
    scene["source_origin_px"] = "200,1337 bottom-left model origin"
    scene["camera_rule"] = "All camera anchors use source PNG pixel coordinates and are converted to metres"
    scene["status"] = "同一 CAD/3D 底模测试渲染；材质与具体 SKU 仍为设计阶段"
    blend_path = ROOT / "方案A11_CAD同模渲染.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    manifest = {
        "schema": "scheme-a11-cad-render-v1",
        "source_freecad": str(CAD / "方案A11_CAD底模.FCStd"),
        "source_obj_groups": {key: str(CAD / f"scheme_a11_{key}.obj") for key in ["walls", "floors", "openings", "doors", "furniture", "fixtures"]},
        "source_scale_mm_per_pixel": SCALE_MM,
        "origin_source_px": [ORIGIN_X, ORIGIN_Y],
        "blender_file": str(blend_path),
        "camera_anchors": {
            key: {"camera_px": list(value[0]), "target_px": list(value[1]), "height_mm": value[2], "lens_mm": value[3], "label": value[4]}
            for key, value in anchors.items()
        },
        "renders": [str(path) for path in sorted(OUT.glob("*.png"))],
        "status": "same CAD/OBJ geometry rendered in Blender; field measurement and product SKU verification pending",
    }
    (ROOT / "scene_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"blend": str(blend_path), "renders": len(manifest["renders"]), "scale": SCALE_MM}, ensure_ascii=False))


if __name__ == "__main__":
    main()
