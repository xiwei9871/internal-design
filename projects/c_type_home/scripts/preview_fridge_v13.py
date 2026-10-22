import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/fridge_finish_v13';a=json.loads((D/'BUILD_AUDIT.json').read_text());O=D/'review';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
for l in s.view_layers:l.use=l.name=='INTERIOR_CLOSED_CEILING'
bpy.context.window.view_layer=s.view_layers['INTERIOR_CLOSED_CEILING']
for n in ['V7_CEILING_LOW','V7_CEILING_HIGH','V7_CEILING_450MM_TRANSITION']:bpy.data.objects[n].hide_render=True
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=32;s.render.resolution_x=1200;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
cam=bpy.data.objects.new('V13_FRIDGE_REVIEW_CAMERA',bpy.data.cameras.new('V13_FRIDGE_REVIEW_CAMERA'));s.collection.objects.link(cam);s.camera=cam;cam.location=(5.36,2.12,1.75);cam.rotation_euler=(Vector((6.79,4.11,1.65))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=26;cam.data.clip_start=.01;dest=O/'fridge_overhead_ash.png';assert not dest.exists();s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);print('V13_PREVIEW',dest)

