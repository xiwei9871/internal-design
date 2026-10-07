"""Workbench furniture decision views; temporary cutaways, no source saves."""
import bpy, json, shutil, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/bedrooms_wood_v1'
D=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/bedrooms_wood_v1/full')
reg=json.loads((R/'spatial-canvas.bindings.full.json').read_text())
bpy.ops.wm.open_mainfile(filepath=reg['source_locator'])
audit=json.loads((R/'EXISTING_BOUNDED_AUDIT.json').read_text())
allowed={b['native_id'] for b in reg['bindings']};original={o.name:o.hide_render for o in bpy.context.scene.objects}
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=1100;scene.render.resolution_y=850;scene.render.resolution_percentage=100
scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
scene.display.shading.background_type='WORLD';scene.world.color=(.82,.82,.82)
data=bpy.data.cameras.new('CAM_BEDROOM_REVIEW');cam=bpy.data.objects.new('CAM_BEDROOM_REVIEW',data)
scene.collection.objects.link(cam);scene.camera=cam
roomranges={'couple':(7.8,11.6,-.7,4.8),'mother':(11.4,15.5,-.7,4.8),'guest':(9.7,13.1,7.8,11.1)}
prefixes={'couple':('B11_Rectangle012','R3_WARDROBE','V4_W-SMB','R4_BEDROOM_DOOR','BW1_COUPLE'),
 'mother':('B11_Rectangle013','B11_Rectangle015','B11_Rectangle022','V4_W-MB','BW1_MOTHER'),
 'guest':('B11_Rectangle017','B11_Rectangle045','V4_D-GUEST-ROOM','V4_GUEST','BW1_GUEST')}
for zone in ['couple','mother','guest']:
 local=set(audit['wall_groups'][zone])|{n for n in allowed if n.startswith(prefixes[zone])}
 local|={'FLOOR_UPPER_SEAM_2','FLOOR_UPPER_SEAM_3'}
 for o in scene.objects:
  if o.type in ['MESH','CURVE','FONT']:o.hide_render=original[o.name] or o.name not in local
 # Top view keeps meaningful walls and plan. Headsoffits are the only topcutaways.
 for n in local:
  if 'SOFFIT' in n or 'INNER_HEAD' in n:
   if bpy.data.objects.get(n):bpy.data.objects[n].hide_render=True
 if zone=='guest':center=(11.50,9.45,11);scale=4.1
 elif zone=='couple':center=(9.70,2.13,12);scale=5.15
 else:center=(13.45,2.13,12);scale=5.15
 cam.location=center;cam.rotation_euler=(0,0,0);data.type='ORTHO';data.ortho_scale=scale
 scene.render.filepath=str(R/('BEDROOM_'+zone.upper()+'_TOP.png'));bpy.ops.render.render(write_still=True)
 # Readable threequarter outsidecornerwithrender-onlywalls removed.
 if zone=='guest':eye=(9.55,11.25,4.25);target=(11.58,9.32,1.12);hides=['VIEW_WALL_W_wall_md_0019','VIEW_WALL_W_wall_md_0055']
 elif zone=='couple':eye=(7.70,4.90,4.90);target=(9.82,1.80,1.08);hides=['VIEW_WALL_W_wall_md_0015','VIEW_WALL_W_wall_md_0045','VIEW_WALL_R3_SOUTH_POCKET_PARTITION','VIEW_WALL_R3_WEST_PARTITION']
 else:eye=(11.30,4.95,4.90);target=(13.62,1.84,1.08);hides=['VIEW_WALL_W_wall_md_0021','VIEW_WALL_W_wall_md_0046','VIEW_WALL_W_wall_md_0064']
 for n in hides:
  if bpy.data.objects.get(n):bpy.data.objects[n].hide_render=True
 cam.location=eye;cam.rotation_euler=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y').to_euler();data.type='PERSP';data.lens=32
 scene.render.filepath=str(R/('BEDROOM_'+zone.upper()+'.png'));bpy.ops.render.render(write_still=True)
 # Existingroomfixtures areunchanged; saveimages only.
 for suffix in ['.png','_TOP.png']:shutil.copy2(R/('BEDROOM_'+zone.upper()+suffix),D/('BEDROOM_'+zone.upper()+suffix))
print('BEDROOM_WORKBENCH_PREVIEWS_PASS',str(D))
