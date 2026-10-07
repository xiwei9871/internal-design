"""One Workbench decision view per requested room; no source writes."""
import bpy,json,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/console_bath_mirrors_review'
D=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/console_bath_mirrors_review/full')
reg=json.loads((R/'spatial-canvas.bindings.full.json').read_text());bpy.ops.wm.open_mainfile(filepath=reg['source_locator'])
audit=json.loads((R/'VANITY_BOUNDED_AUDIT.json').read_text());orig={o.name:o.hide_render for o in bpy.context.scene.objects}
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1100;s.render.resolution_y=850;s.render.resolution_percentage=100
s.display.shading.light='STUDIO';s.display.shading.studio_light='paint.sl';s.display.shading.color_type='MATERIAL'
s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
d=bpy.data.cameras.new('CAM_CONSOLE_BATH');o=bpy.data.objects.new('CAM_CONSOLE_BATH',d);s.collection.objects.link(o);s.camera=o
views=[('couple',(10.62,3.55,2.62),(8.20,2.10,1.15),28),('master',(14.25,4.74,2.05),(13.82,6.36,1.69),24),
 ('secondary',(10.12,4.97,2.02),(9.84,6.41,1.72),22),('guest',(9.36,9.22,2.03),(8.045,8.68,1.71),22)]
for room,eye,target,lens in views:
 keep={b['native_id'] for b in reg['bindings'] if b['native_id'].startswith('CBM_') and room.upper() in b['native_id'].upper()}
 if room=='couple':keep|={'B11_Rectangle012_CATALOG_00_00','FLOOR_UPPER_SEAM_2','FLOOR_UPPER_SEAM_3','VIEW_WALL_W_wall_md_0015'};keep|={b['native_id'] for b in reg['bindings'] if b['native_id'].startswith('CBM_CONSOLE') or b['native_id'].startswith('CBM_DRAWER')}
 elif room=='master':keep|={'B11_Rectangle035_DIMENSIONAL_BODY'}|set(audit['wall_groups'][room])
 elif room=='guest':keep|={'B11_Rectangle030_DIMENSIONAL_BODY'}|set(audit['wall_groups'][room])
 else:keep|={b['native_id'] for b in reg['bindings'] if b['native_id'].startswith('R3_VANITY')}|set(audit['wall_groups'][room])
 # Closeviewcontextneedsbackwallonly;forewalls aretemporaryrender cutaways.
 if room=='master':keep-= {'VIEW_WALL_W_wall_md_0046','VIEW_WALL_W_wall_md_0047'}
 if room=='secondary':keep-= {'VIEW_WALL_R3_SOUTH_POCKET_PARTITION','VIEW_WALL_R3_WEST_PARTITION','VIEW_WALL_W_wall_md_0018'}
 if room=='guest':keep-= {'VIEW_WALL_W_wall_md_0051','VIEW_WALL_W_wall_md_0052','VIEW_WALL_W_wall_md_0019'}
 for obj in bpy.context.scene.objects:
  if obj.type in ['MESH','CURVE']:obj.hide_render=orig[obj.name] or obj.name not in keep
 o.location=eye;o.rotation_euler=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y').to_euler();d.lens=lens
 name='REVIEW_'+room.upper()+'.png';s.render.filepath=str(R/name);bpy.ops.render.render(write_still=True);shutil.copy2(R/name,D/name)
print('CONSOLE_BATH_PREVIEW_PASS')
