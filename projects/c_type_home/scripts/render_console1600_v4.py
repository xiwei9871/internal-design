"""Two unchanged decision cameras for1200/1600 comparison."""
import bpy,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/console1600_v4';a=json.loads((D/'AUDIT.json').read_text());dest=D/'review';dest.mkdir(exist_ok=True)
if (dest/'manifest.json').exists():raise SystemExit('Preserved render exists')
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene;s.render.engine='CYCLES';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2;s.cycles.samples=32;s.cycles.adaptive_threshold=.04;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE';s.render.image_settings.file_format='PNG'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';rec=[]
for rid,cam in [('console','HUNYUAN_V3_CONSOLE'),('bed_reverse','HUNYUAN_V3_BED_REVERSE')]:
 s.camera=bpy.data.objects[cam];s.render.filepath=str(dest/(rid+'.png'));t=time.time();bpy.ops.render.render(write_still=True);rec.append({'id':rid,'camera':cam,'path':s.render.filepath,'size':[1280,720],'seconds':round(time.time()-t,2)});print('CONSOLE_SHOT',rid,flush=True)
(dest/'manifest.json').write_text(json.dumps({'source_sha256':a['sha256'],'images':rec},indent=2)+'\n')
