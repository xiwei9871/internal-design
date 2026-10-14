"""Bounded same-camera architectural glass/privacy review with ceiling retained."""
import bpy,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/glass_privacy_v8';a=json.loads((D/'BUILD_AUDIT.json').read_text());O=D/'review_final';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
for layer in s.view_layers:layer.use=layer.name=='INTERIOR_CLOSED_CEILING'
bpy.context.window.view_layer=s.view_layers['INTERIOR_CLOSED_CEILING']
s.render.engine='CYCLES';s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2;s.cycles.samples=96;s.cycles.adaptive_threshold=.02;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE';s.render.image_settings.file_format='PNG'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for dev in p.devices:dev.use=dev.type=='METAL'
s.cycles.device='GPU';records=[]
for name,cam in [('living','CAM_living_VIEW_01'),('master_bath','CAM_master_bath_VIEW_01'),('secondary_bath','CAM_secondary_bath_VIEW_01'),('guest_bath','CAM_guest_bath_VIEW_01'),('guest_balcony','CAM_guest_bedroom_VIEW_01')]:
 out=O/(name+'.png')
 if out.exists():print('PRESERVED',name,flush=True);continue
 s.camera=bpy.data.objects[cam];s.render.filepath=str(out);t=time.time();bpy.ops.render.render(write_still=True);records.append({'view':name,'camera':cam,'path':str(out),'size':[1600,900],'samples':96,'source_sha256':a['sha256'],'seconds':round(time.time()-t,2)});(O/'manifest.json').write_text(json.dumps(records,indent=2)+'\n');print('GLASS_SHOT',name,flush=True)
