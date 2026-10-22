"""Two EEVEE decision previews; render-only roof hide never writes source."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[1];D=R/'design/finishes_v11';a=json.loads((D/'BUILD_AUDIT.json').read_text());O=D/'review';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
for l in s.view_layers:l.use=l.name=='INTERIOR_CLOSED_CEILING'
bpy.context.window.view_layer=s.view_layers['INTERIOR_CLOSED_CEILING']
for n in ['V7_CEILING_LOW','V7_CEILING_HIGH','V7_CEILING_450MM_TRANSITION']:bpy.data.objects[n].hide_render=True
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=32
s.render.resolution_x=1440;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
cam=bpy.data.objects.new('V11_REVIEW_CAMERA',bpy.data.cameras.new('V11_REVIEW_CAMERA'));s.collection.objects.link(cam);s.camera=cam;cam.data.clip_start=.01;cam.data.clip_end=200
def render(n,eye,target,lens):
    dest=O/(n+'.png');assert not dest.exists();cam.location=eye;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP';cam.data.lens=lens;cam.data.sensor_fit='AUTO';s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);print('V11_PREVIEW',n,flush=True)
render('whole_house_finishes',(0,-9,23),(8.8,6.3,.2),44)
render('reading_grounded',(5.95,6.15,2.28),(8.98,5.67,1.15),31)
