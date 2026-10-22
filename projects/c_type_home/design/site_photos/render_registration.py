"""Generate honest baseline comparison views; no geometric correction or saved viewing changes."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'B1_1_SITE_REGISTERED_V1.blend'))
report=json.loads((OUT/'PHOTO_REGISTRATION_REPORT.json').read_text())
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD';scene.world.color=(.85,.87,.88)
scene.view_settings.view_transform='Standard';scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.resolution_percentage=100
# Focus displayed content on kitchen/adjacent lower-level area, preserving mesh/pose.
for o in bpy.data.objects:
    if o.type=='FONT':o.hide_render=True
    if o.type=='MESH':
        pts=[o.matrix_world@Vector(v) for v in o.bound_box]
        lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
        if hi[0]<1.2 or lo[0]>8.1 or hi[1]<-.3 or lo[1]>4.75:o.hide_render=True
        if o.name=='SITE_GROUND' or o.name.startswith('GLZ_'):o.hide_render=True
for r in report['photos']:
    scene.camera=bpy.data.objects[r['camera_name']]
    scene.render.resolution_x=r['preview_size'][0];scene.render.resolution_y=r['preview_size'][1]
    scene.render.filepath=str(OUT/f"MODEL_REG_{r['photo_id']}.png")
    bpy.ops.render.render(write_still=True)
    print('PHOTO_VIEW_DONE '+r['photo_id'],flush=True)
