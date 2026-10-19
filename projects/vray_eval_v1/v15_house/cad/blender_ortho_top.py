# blender -b V15_WORK.blend -P blender_ortho_top.py -- <out.png>
# 正交俯视: 模型坐标mm = 世界m*1000. 相机 +Z 俯视, ortho_scale=纵向跨度.
import bpy, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index('--')+1:]
out = argv[0]

# 建筑范围(米): 平面bbox x 0.5..15.8, y -1.0..15.2 留边
X0, X1, Y0, Y1 = map(float, argv[1:5]) if len(argv)>4 else (0.5, 15.8, -1.0, 15.2)
cx, cy, span = (X0+X1)/2, (Y0+Y1)/2, (Y1-Y0)

scn = bpy.context.scene
scn.render.engine = 'BLENDER_WORKBENCH'
scn.display.shading.light = 'STUDIO'
scn.display.shading.color_type = 'OBJECT'
scn.display.shading.show_shadows = True
scn.display.shading.show_cavity = True
scn.display.shading.cavity_type = 'BOTH'
scn.display.shading.curvature_ridge_factor = 1.2
scn.display.shading.curvature_valley_factor = 0.8
scn.render.film_transparent = True
scn.render.resolution_x = 2100
scn.render.resolution_y = int(2100*span/(X1-X0))
scn.render.resolution_percentage = 100
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGBA'

cam = bpy.data.objects.new('ORTHO_TOP', bpy.data.cameras.new('ORTHO_TOP'))
bpy.context.collection.objects.link(cam)
cam.location = (cx, cy, 30.0)
cam.rotation_euler = (0.0, 0.0, 0.0)   # 俯视: -Z视向, +Y为图上
cam.data.type = 'ORTHO'
cam.data.ortho_scale = span
scn.camera = cam
scn.render.filepath = out
bpy.ops.render.render(write_still=True)
print('ORTHO_TOP ->', out, '| extent_mm:', X0*1000, X1*1000, Y0*1000, Y1*1000)
