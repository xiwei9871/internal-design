"""Workbench doorway/wardrobe decision views; source model stays saved-open."""
import bpy,json,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/secondary_bath850_review'
D=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/secondary_bath850_review/full')
reg=json.loads((R/'spatial-canvas.bindings.full.json').read_text());bpy.ops.wm.open_mainfile(filepath=reg['source_locator'])
prefix=('R3_WARDROBE','R3_FRAME','R3_SPLIT_JAMB','R3_CASING','R3_SLIDER','R3_SLIDING','VIEW_WALL_R3_',
 'BW1_COUPLE','B11_Rectangle012','V4_W-SMB')
keep={b['native_id'] for b in reg['bindings'] if b['native_id'].startswith(prefix)}|{'FLOOR_UPPER_SEAM_2','FLOOR_UPPER_SEAM_3','R3_BATH_FLOOR'}
for o in bpy.context.scene.objects:
 if o.type in ['MESH','CURVE']:o.hide_render=o.hide_render or o.name not in keep
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1100;s.render.resolution_y=850;s.render.resolution_percentage=100
s.display.shading.light='STUDIO';s.display.shading.studio_light='paint.sl';s.display.shading.color_type='MATERIAL'
s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
d=bpy.data.cameras.new('CAM_BATH850');o=bpy.data.objects.new('CAM_BATH850',d);s.collection.objects.link(o);s.camera=o
for name,eye,target,typ,lens in [('BATH850_ENTRY.png',(8.55,1.95,3.30),(10.03,4.43,1.53),'PERSP',32),
 ('BATH850_TOP.png',(10.25,4.4,10),(10.25,4.4,.5),'ORTHO',3.35)]:
 o.location=eye;o.rotation_euler=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y').to_euler();d.type=typ
 if typ=='ORTHO':d.ortho_scale=lens
 else:d.lens=lens
 s.render.filepath=str(R/name);bpy.ops.render.render(write_still=True);shutil.copy2(R/name,D/name)
print('BATH850_PREVIEW_PASS')
