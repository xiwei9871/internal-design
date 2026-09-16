"""可行性验证：把主卧的"方块床/梳妆台"换成 Poly Haven 真实模型，EEVEE 出图。

流程：加载 A11 blend → 删合并家具对象 → 按 g 组重导家具 OBJ →
删掉主卧床+梳妆台的方块件（其余家具保留并补木材质）→
append GothicBed_01 / SchoolDesk_01 → 按 CAD footprint 定位缩放 → 渲 Camera_master。
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
ORIGIN_X, ORIGIN_Y, SCALE_MM = 200.0, 1337.0, 9.82


def world(px, py, z_mm=0.0):
    return ((px - ORIGIN_X) * SCALE_MM / 1000.0, (ORIGIN_Y - py) * SCALE_MM / 1000.0, z_mm / 1000.0)


def reimport_furniture_split():
    """删除合并家具体，按 g 组重导成独立部件。"""
    for o in list(bpy.data.objects):
        if "furniture" in o.name.lower():
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.wm.obj_import(filepath=str(CAD / "scheme_a11_furniture.obj"), use_split_groups=True)
    return [o for o in bpy.context.selected_objects]


def main():
    def cname(o):  # OBJ 组名是 \uXXXX 字面转义，解码后再匹配
        try:
            return bytes(o.name, "ascii").decode("unicode_escape")
        except Exception:
            return o.name

    parts = reimport_furniture_split()
    keep, drop = [], []
    for o in parts:
        if any(t in cname(o) for t in ("夫妻主卧床", "梳妆")):
            drop.append(o)
        else:
            keep.append(o)
    for o in drop:
        bpy.data.objects.remove(o, do_unlink=True)
    print(f"furniture parts kept={len(keep)} dropped={len(drop)}")

    # 其余家具补一个暖木材质（原来在合并对象上赋过，拆分后丢失）
    wood = bpy.data.materials.get("Wood") or bpy.data.materials.new("Wood")
    wood.use_nodes = True
    bsdf = wood.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.55, 0.38, 0.22, 1)
    bsdf.inputs["Roughness"].default_value = 0.65
    for o in keep:
        if hasattr(o.data, "materials"):
            o.data.materials.clear()
            o.data.materials.append(wood)

    def append_blend(blend_path, obj_prefix):
        before_o = set(bpy.data.objects)
        before_i = set(bpy.data.images)
        with bpy.data.libraries.load(str(blend_path)) as (data_from, data_to):
            data_to.collections = data_from.collections
        for coll in data_to.collections:
            bpy.context.scene.collection.children.link(coll)
        new = [o for o in bpy.data.objects if o not in before_o]
        for o in new:
            o.name = obj_prefix + o.name
        # 修复贴图相对路径：// 解析到当前 blend，改成资产目录绝对路径
        for img in bpy.data.images:
            if img not in before_i and img.source == "FILE":
                cand = blend_path.parent / "textures" / Path(img.filepath).name
                if cand.exists():
                    img.filepath = str(cand)
                    img.reload()
        return new

    def place(objs, rect, label):
        """objs 组合 bbox 缩放平移到 px rect；long_axis=家具长轴对齐 rect 长边方向。"""
        xs, ys = [], []
        for o in objs:
            if o.type != "MESH":
                continue
            for v in o.bound_box:
                w = o.matrix_world @ Vector(v)
                xs.append((w.x, w.y))
        if not xs:
            return
        (x0, x1), (y0, y1) = (min(p[0] for p in xs), max(p[0] for p in xs)), (min(p[1] for p in xs), max(p[1] for p in xs))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rx, ry = rect[0], rect[1]
        rw = (rect[2]) * SCALE_MM / 1000.0
        rh = (rect[3]) * SCALE_MM / 1000.0
        wx, wy = world(rx, ry + rect[3]), world(rx + rect[2], ry)
        tcx, tcy = (wx[0] + wy[0]) / 2, (wx[1] + wy[1]) / 2
        s = max(rw, rh) / max(x1 - x0, y1 - y0)
        for o in objs:
            o.location.x += tcx - cx
            o.location.y += tcy - cy
            o.scale = (o.scale[0] * s, o.scale[1] * s, o.scale[2] * s)
        print(f"placed {label}: scale={s:.3f} center=({tcx:.2f},{tcy:.2f})")

    bed = append_blend(ASSETS / "GothicBed_01" / "main.blend", "RealBed_")
    place(bed, [551, 906, 214, 187], "bed")

    desk = append_blend(ASSETS / "SchoolDesk_01" / "main.blend", "RealDesk_")
    place(desk, [489, 1268, 122, 46], "desk")

    scene = bpy.context.scene
    scene.camera = bpy.data.objects["Camera_master"]
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1100, 760
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    out = ROOT / "test_realfurn_master.png"
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    print("saved", out)


main()
