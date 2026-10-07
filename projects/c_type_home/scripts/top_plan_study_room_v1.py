"""Dimensioned decision top views; cameraclipsat1.4m so baywindowhead does nothideDaybed."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/study_room_v1'
mode=sys.argv[sys.argv.index('--')+1]
reg=json.loads((R/('spatial-canvas.bindings.'+mode+'.json')).read_text())
bpy.ops.wm.open_mainfile(filepath=reg['source_locator']);bpy.context.view_layer.update()
allowed={b['native_id'] for b in reg['bindings']}
for o in bpy.context.scene.objects:
 if o.type in ['MESH','CURVE','FONT']:o.hide_render=o.hide_render or o.name not in allowed
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=900;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl'
scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=False
scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
d=bpy.data.cameras.new('TOP_PLAN_CAMERA');c=bpy.data.objects.new('TOP_PLAN_CAMERA',d);scene.collection.objects.link(c)
c.location=(14.65,9.18,14);c.rotation_euler=(0,0,0);d.type='ORTHO';d.ortho_scale=5.7;d.clip_start=12.60;d.clip_end=30
scene.camera=c;scene.render.filepath=str(R/('STUDY_ROOM_TOP_'+mode.upper()+'.png'))
bpy.ops.render.render(write_still=True);print('TOP_PLAN_SAVED',mode)
