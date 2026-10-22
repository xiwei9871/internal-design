"""Glass sliding leaf and console substance details; scene source preserved."""
import bpy,json,time
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/pale_ash_review_v7';a=json.loads((D/'BUILD_AUDIT.json').read_text());O=D/'review_final'
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
for layer in s.view_layers:layer.use=layer.name=='INTERIOR_CLOSED_CEILING'
bpy.context.window.view_layer=s.view_layers['INTERIOR_CLOSED_CEILING']
s.render.engine='CYCLES';s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2;s.cycles.samples=128;s.cycles.adaptive_threshold=.015;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE';s.render.image_settings.file_format='PNG'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for dev in p.devices:dev.use=dev.type=='METAL'
s.cycles.device='GPU';records=[]
for name,camera in [('after_slider','V7_SLIDER_DETAIL'),('after_console','HUNYUAN_V3_CONSOLE')]:
 if name=='after_slider':
  camera=bpy.data.objects.new(camera,bpy.data.cameras.new(camera));s.collection.objects.link(camera);camera.location=(10.55,6.25,1.48);camera.rotation_euler=(Vector((10.55,4.74,1.48))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=18;camera.data.clip_start=.01
 else:camera=bpy.data.objects[camera]
 f=O/(name+'.png');assert not f.exists();s.camera=camera;s.render.filepath=str(f);t=time.time();bpy.ops.render.render(write_still=True);records.append({'view':name,'path':str(f),'camera':camera.name,'resolution':[1600,900],'samples':128,'seconds':round(time.time()-t,2)})
 (O/'detail_manifest.json').write_text(json.dumps(records,indent=2)+'\n');print('V7_DETAIL',name,flush=True)
