"""Bonsai visual + geometric check for the Task 01 IFC.

Run with:
  Blender -b --python bonsai_check.py

Loads the IFC via the Bonsai extension, renders orthographic top views to
qc/bonsai_ifc_overview.png and qc/bonsai_ifc_openings.png, and dumps each
imported object's world-space XY AABB to qc/bonsai_scene_audit.json so the
"no half-width translation" claim is checked on actual imported meshes.
"""
import json
import sys
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
PROJ = SCRIPT_DIR.parent
IFC = PROJ / "ifc" / "C型_原始户型数字化基准模型.ifc"
QC = PROJ / "qc"

# --- load -----------------------------------------------------------------
bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.bim.load_project(filepath=str(IFC))

# --- audit: world AABB of every imported IFC object ------------------------
audit = {}
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    if obj.parent and obj.parent.type == 'MESH':
        pass
    bb = [obj.matrix_world @ __import__('mathutils').Vector(c)
          for c in obj.bound_box]
    xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
    audit[obj.name] = {"x": [round(min(xs), 4), round(max(xs), 4)],
                       "y": [round(min(ys), 4), round(max(ys), 4)],
                       "z": [round(min(zs), 4), round(max(zs), 4)]}
QC.mkdir(parents=True, exist_ok=True)
(QC / "bonsai_scene_audit.json").write_text(
    json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("AUDIT_OBJECTS", len(audit))

# --- renders ---------------------------------------------------------------
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'FLAT'
scene.display.shading.color_type = 'RANDOM'
scene.display.shading.show_shadows = False
scene.render.resolution_x = 1400
scene.render.resolution_y = 1400
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("W")
scene.world.color = (0.05, 0.05, 0.05)

cam_data = bpy.data.cameras.new("cam")
cam_data.type = 'ORTHO'
cam_data.clip_start = 0.01
cam_data.clip_end = 500
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
cam.rotation_euler = (0, 0, 0)          # straight down
scene.camera = cam

# plan extents (meters): X 1.3-16.5, Y -0.75-14.2 -> centre ~ (8.9, 6.7)
def shoot(cx, cy, ortho_scale, out):
    cam.location = (cx, cy, 30)
    cam_data.ortho_scale = ortho_scale
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    print("RENDER", out)

shoot(8.9, 6.7, 17.5, QC / "bonsai_ifc_overview.png")
# openings detail: dining/kitchen/balcony + corridor door cluster region
shoot(8.0, 5.0, 7.0, QC / "bonsai_ifc_openings.png")
print("DONE")
