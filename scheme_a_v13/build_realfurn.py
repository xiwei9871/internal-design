"""全屋真实家具装配：方块占位 → Poly Haven / Sweet Home 3D 资产，footprint 锁定。

用法: blender --background 方案A11_CAD同模渲染.blend --python build_realfurn.py [view1 view2 ...]
默认渲 master/living 两个视角到 scheme_a_v13/realfurn_<view>.png。
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
CAD = ROOT.parent / "scheme_a_v11" / "cad"
ASSETS = ROOT.parent / "assets"
SH3D = ASSETS / "sh3d"
ORIGIN_X, ORIGIN_Y, SCALE_MM = 200.0, 1337.0, 9.82


def world(px, py, z_mm=0.0):
    return ((px - ORIGIN_X) * SCALE_MM / 1000.0, (ORIGIN_Y - py) * SCALE_MM / 1000.0, z_mm / 1000.0)


def cname(o):
    try:
        return bytes(o.name, "ascii").decode("unicode_escape")
    except Exception:
        return o.name


def reimport_furniture_split():
    for o in list(bpy.data.objects):
        if "furniture" in o.name.lower():
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.wm.obj_import(filepath=str(CAD / "scheme_a11_furniture.obj"), use_split_groups=True)
    return [o for o in bpy.context.selected_objects]


def bbox_world(objs):
    pts = []
    for o in objs:
        if o.type != "MESH":
            continue
        for v in o.bound_box:
            pts.append(o.matrix_world @ Vector(v))
    if not pts:
        return None
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


def join_objects(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [o for o in objs if o.type == "MESH"]
    nonmesh = [o for o in objs if o.type != "MESH"]
    for o in nonmesh:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    return ob


def import_sh3d(name, label):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=str(SH3D / f"{name}.obj"))
    return join_objects([o for o in bpy.data.objects if o not in before], label)


def append_ph(asset, label):
    blend_path = ASSETS / asset / "main.blend"
    before_o = set(bpy.data.objects)
    before_i = set(bpy.data.images)
    with bpy.data.libraries.load(str(blend_path)) as (data_from, data_to):
        data_to.collections = data_from.collections
    for coll in data_to.collections:
        bpy.context.scene.collection.children.link(coll)
    new = [o for o in bpy.data.objects if o not in before_o]
    for img in bpy.data.images:
        if img not in before_i and img.source == "FILE":
            cand = blend_path.parent / "textures" / Path(img.filepath).name
            if cand.exists():
                img.filepath = str(cand)
                img.reload()
    return join_objects(new, label)


def make_mat(name, rgb, rough=0.6):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def set_mat(ob, mat):
    if hasattr(ob.data, "materials"):
        ob.data.materials.clear()
        ob.data.materials.append(mat)


def place(ob, rect, rot=0.0, z_mm=0.0, z_top=None, label=""):
    """旋转→XY 非均匀缩放贴 footprint→平移。z_top: 底面放到该对象顶面。"""
    b = bbox_world([ob])
    cx, cy = (b[0].x + b[1].x) / 2, (b[0].y + b[1].y) / 2
    ob.location.x -= cx
    ob.location.y -= cy
    ob.rotation_euler.z = math.radians(rot)
    bpy.context.view_layer.update()
    b = bbox_world([ob])
    rw, rh = rect[2] * SCALE_MM / 1000.0, rect[3] * SCALE_MM / 1000.0
    dx, dy = b[1].x - b[0].x, b[1].y - b[0].y
    sx, sy = rw / dx, rh / dy
    sz = (sx + sy) / 2
    ob.scale = (ob.scale[0] * sx, ob.scale[1] * sy, ob.scale[2] * sz)
    bpy.context.view_layer.update()
    b = bbox_world([ob])
    wx0, wy1 = world(rect[0], rect[1] + rect[3])[:2]
    wx1, wy0 = world(rect[0] + rect[2], rect[1])[:2]
    tcx, tcy = (wx0 + wx1) / 2, (wy0 + wy1) / 2
    ob.location.x += tcx - (b[0].x + b[1].x) / 2
    ob.location.y += tcy - (b[0].y + b[1].y) / 2
    zbase = bbox_world([z_top])[1].z if z_top else z_mm / 1000.0
    ob.location.z += zbase - b[0].z
    print(f"placed {label}: s=({sx:.2f},{sy:.2f}) rot={rot} center=({tcx:.2f},{tcy:.2f})")
    return ob


# (drop 前缀, 资产来源, 资产名, rect, rot_z, z_mm, z_top名, 材质)
MAP = [
    ("夫妻主卧床", "sh3d", "bed140x190", [551, 906, 214, 187], -90, 0, None, "WoodLight"),
    ("老人床", "sh3d", "bed140x190", [945, 390, 215, 185], -90, 0, None, "WoodLight"),
    ("儿童床", "sh3d", "bed140x190", [1244, 917, 214, 158], 90, 0, None, "WoodLight"),
    ("客厅沙发", "sh3d", "sofa2", [1020, 1090, 92, 224], 90, 0, None, "FabricGrey"),
    ("餐桌", "sh3d", "table", [870, 824, 145, 82], 0, 0, None, "WoodLight"),
    ("餐椅", "sh3d", "chair2", [888, 782, 38, 38], 180, 0, None, "White"),
    ("餐椅", "sh3d", "chair2", [953, 782, 38, 38], 180, 0, None, "White"),
    ("餐椅", "sh3d", "chair2", [888, 915, 38, 38], 0, 0, None, "White"),
    ("餐椅", "sh3d", "chair2", [953, 915, 38, 38], 0, 0, None, "White"),
    ("电视影音矮柜", "ph", "modern_wooden_cabinet", [792, 1110, 35, 184], 90, 0, None, None),
    ("客厅茶几", "ph", "modern_coffee_table_01", [920, 1195, 56, 91], 90, 0, None, None),
    ("客厅沙发边几", "ph", "side_table_01", [1047, 1038, 42, 42], 0, 0, None, None),
    ("主卧窗边梳妆/阅读台", "sh3d", "desk", [489, 1268, 122, 46], 180, 0, None, "WoodLight"),
    ("儿童窗边学习桌", "sh3d", "desk", [1200, 1252, 183, 61], 180, 0, None, "WoodLight"),
    ("客厅·55–65寸电视", "sh3d", "flatTV", [800, 1110, 28, 120], 90, 0, "电视影音矮柜", "Dark"),
]
ADD = [  # 只加不删（底模没这些组）
    ("sh3d", "chair2", [530, 1208, 46, 49], 0, 0, None, "White", "主卧窗边活动椅"),
    ("sh3d", "chair2", [1255, 1200, 45, 49], 0, 0, None, "White", "儿童学习椅"),
    ("sh3d", "bedsideTable", [505, 906, 42, 40], 0, 0, None, "WoodLight", "主卧床头柜"),
    ("ph", "potted_plant_01", [960, 1240, 55, 55], 0, 0, None, None, "客厅绿植"),
    ("ph", "modern_ceiling_lamp_01", [930, 850, 45, 45], 0, 2000, None, None, "餐厅吊灯"),
]


def main():
    parts = reimport_furniture_split()
    drop_prefixes = {m[0] for m in MAP}
    keep, drop = [], []
    for o in parts:
        (drop if any(cname(o).startswith(p) for p in drop_prefixes) else keep).append(o)
    for o in drop:
        bpy.data.objects.remove(o, do_unlink=True)
    print(f"furniture kept={len(keep)} dropped={len(drop)}")

    wood = make_mat("Wood", (0.55, 0.38, 0.22), 0.65)
    for o in keep:
        set_mat(o, wood)
    make_mat("WoodLight", (0.72, 0.55, 0.35), 0.7)
    make_mat("FabricGrey", (0.55, 0.55, 0.58), 0.9)
    make_mat("White", (0.9, 0.9, 0.9), 0.6)
    make_mat("Dark", (0.06, 0.06, 0.06), 0.4)

    placed = {}
    for prefix, src, asset, rect, rot, z, ztop, mat in MAP:
        ob = import_sh3d(asset, f"Real_{asset}") if src == "sh3d" else append_ph(asset, f"Real_{asset}")
        if mat:
            set_mat(ob, bpy.data.materials[mat])
        place(ob, rect, rot=rot, z_mm=z, z_top=placed.get(ztop), label=prefix)
        placed[prefix] = ob
    for src, asset, rect, rot, z, ztop, mat, label in ADD:
        ob = import_sh3d(asset, f"Real_{asset}") if src == "sh3d" else append_ph(asset, f"Real_{asset}")
        if mat:
            set_mat(ob, bpy.data.materials[mat])
        place(ob, rect, rot=rot, z_mm=z, z_top=placed.get(ztop), label=label)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1100, 760
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    views = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["master", "living"]
    for v in views:
        if v == "top":
            cam = bpy.data.objects.new("Camera_top", bpy.data.cameras.new("Camera_top"))
            scene.collection.objects.link(cam)
            cam.data.type = "ORTHO"
            cam.data.ortho_scale = 13.5
            cam.location = (5.7, 0, 2.55)  # 吊顶下俯视
            cam.rotation_euler = (0, 0, 0)
        else:
            cam = bpy.data.objects.get(f"Camera_{v}")
        if not cam:
            print("no camera", v)
            continue
        scene.camera = cam
        out = ROOT / f"realfurn_{v}.png"
        scene.render.filepath = str(out)
        bpy.ops.render.render(write_still=True)
        print("saved", out)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "方案A13_真实家具.blend"))
    print("saved blend")


main()
