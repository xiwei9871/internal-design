"""EEVEE mother bed and whole-house decision views; source remains closed-roof render capable."""
import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/mother_hunyuan_v12';a=json.loads((D/'BUILD_AUDIT.json').read_text());O=D/'review';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
for l in s.view_layers:l.use=l.name=='INTERIOR_CLOSED_CEILING'
bpy.context.window.view_layer=s.view_layers['INTERIOR_CLOSED_CEILING']
for n in ['V7_CEILING_LOW','V7_CEILING_HIGH','V7_CEILING_450MM_TRANSITION']:bpy.data.objects[n].hide_render=True
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=32
if 'shadow_pool_size' in s.eevee.bl_rna.properties:
    prop=s.eevee.bl_rna.properties['shadow_pool_size']
    if prop.type=='ENUM' and '4096' in {x.identifier for x in prop.enum_items}:s.eevee.shadow_pool_size='4096'
s.render.resolution_x=1440;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
cam=bpy.data.objects.new('V12_REVIEW_CAMERA',bpy.data.cameras.new('V12_REVIEW_CAMERA'));s.collection.objects.link(cam);s.camera=cam;cam.data.clip_start=.01;cam.data.clip_end=200
for n,eye,target,lens in [('mother_bed',(11.95,4.0,2.3),(14.1,2.18,1.03),26),('whole_house',(0,-9,23),(8.8,6.3,.2),44)]:
    dest=O/(n+'.png');assert not dest.exists();cam.location=eye;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);print('V12_PREVIEW',n,flush=True)
