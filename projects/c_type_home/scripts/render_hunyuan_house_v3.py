"""Authored original camera comparisons and supplemental asset decision views."""
import bpy,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/hunyuan_asset_v3';a=json.loads((D/'BUILD_AUDIT.json').read_text());args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];mode=args[0] if args else 'clay';is_clay=mode=='clay' or mode.endswith('_clay');dest=D/mode;dest.mkdir(exist_ok=True)
if (dest/'manifest.json').exists():raise SystemExit('Preserved image batch exists')
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene;s.render.resolution_x=960 if is_clay else 1280;s.render.resolution_y=540 if is_clay else 720;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.threads_mode='FIXED';s.render.threads=2
if is_clay:s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='TEXTURE';s.display.shading.show_shadows=True
else:
 s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.adaptive_threshold=.04;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE';p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
 for d in p.devices:d.use=d.type=='METAL'
 s.cycles.device='GPU'
shots=[('living','客厅整体','CAM_living_VIEW_01'),('sofa','客厅沙发整件','HUNYUAN_V3_SOFA_WHOLE'),('bed','夫妻次主卧床','CAM_couple_bedroom_VIEW_01'),('bed_reverse','床与床头柜关系','HUNYUAN_V3_BED_REVERSE'),('console','次主卧电视柜','HUNYUAN_V3_CONSOLE'),('sofa_detail','沙发软包细节','HOUSE_V1_LIVING_SOFA_DETAIL')];rec=[]
for rid,title,cam in shots:
 s.camera=bpy.data.objects[cam];s.render.filepath=str(dest/(rid+'.png'));t=time.time();bpy.ops.render.render(write_still=True);rec.append({'id':rid,'title':title,'camera':cam,'path':s.render.filepath,'size':[s.render.resolution_x,s.render.resolution_y],'seconds':round(time.time()-t,2)});(dest/(rid+'.meta.json')).write_text(json.dumps({'source_sha256':a['output_sha256'],'image':rec[-1]},ensure_ascii=False,indent=2));print('HUNYUAN_SHOT',rid,flush=True)
(dest/'manifest.json').write_text(json.dumps({'source':a['output'],'source_sha256':a['output_sha256'],'images':rec,'engine':s.render.engine,'samples':0 if mode=='clay' else 32},ensure_ascii=False,indent=2)+'\n')
