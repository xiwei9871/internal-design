"""Two Workbench views for freezer/cabinet proportions, source remains unchanged."""
import bpy,json,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/freezer816_review'
D=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/freezer816_review/full')
reg=json.loads((R/'spatial-canvas.bindings.full.json').read_text());bpy.ops.wm.open_mainfile(filepath=reg['source_locator'])
keep={'B11_Rectangle039_BODY','B11_Rectangle039_LID_SEAM','B11_Rectangle040_BODY_0','B11_Rectangle040_BODY_1',
 'B11_Rectangle040_DOOR_0','B11_Rectangle040_DOOR_1','FLOOR_LOWER','VIEW_WALL_W_wall_md_0054',
 'VIEW_WALL_W_wall_md_0055','VIEW_WALL_W_wall_md_0026','NORTH_BALCONY_GLASS_EAST',
 'V4_GUEST_B11_G-GB-BALC_HOST_GLASS0','V4_GUEST_B11_G-GB-BALC_HOST_GLASS1'}
keep|={b['native_id'] for b in reg['bindings'] if b['native_id'].startswith('SUNROOM_')}
for o in bpy.context.scene.objects:
 if o.type in ['MESH','CURVE']:o.hide_render=o.hide_render or o.name not in keep
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1100;s.render.resolution_y=850;s.render.resolution_percentage=100
s.display.shading.light='STUDIO';s.display.shading.studio_light='paint.sl';s.display.shading.color_type='MATERIAL'
s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
d=bpy.data.cameras.new('CAM_FREEZER816');o=bpy.data.objects.new('CAM_FREEZER816',d);s.collection.objects.link(o);s.camera=o
for name,eye,target,typ,scale in [('FREEZER816_AXON.png',(9.3,14.7,4.7),(11.4,12.45,.85),'PERSP',32),
 ('FREEZER816_TOP.png',(10.55,12.25,10),(10.55,12.25,0),'ORTHO',5.5)]:
 o.location=eye;o.rotation_euler=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y').to_euler();d.type=typ
 if typ=='ORTHO':d.ortho_scale=scale
 else:d.lens=scale
 s.render.filepath=str(R/name);bpy.ops.render.render(write_still=True);shutil.copy2(R/name,D/name)
print('FREEZER816_PREVIEW_PASS')
