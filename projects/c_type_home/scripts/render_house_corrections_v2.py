"""Only owner-corrected rooms plus unchanged living/dining lighting comparisons."""
import bpy,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/whole_house_model_v2';a=json.loads((D/'BUILD_AUDIT.json').read_text());args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];mode=args[0] if args else 'clay';dest=D/mode;dest.mkdir(exist_ok=True)
if (dest/'manifest.json').exists():raise SystemExit('Preserved render exists')
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene;s.render.resolution_x=960 if mode=='clay' else 1280;s.render.resolution_y=540 if mode=='clay' else 720;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.threads_mode='FIXED';s.render.threads=2
if mode=='clay':s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='MATERIAL';s.display.shading.light='STUDIO';s.display.shading.show_shadows=True
else:
 s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE';s.cycles.adaptive_threshold=.04;p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
 for d in p.devices:d.use=d.type=='METAL'
 s.cycles.device='GPU'
shots=[('reading','阅读架与书本','HOUSE_V1_READING_OPPOSITE_WALL'),('hallway','木门框走廊','CAM_hallway_VIEW_01'),('vanity','母亲梳妆台','HOUSE_V2_VANITY_WHOLE'),('mother','母亲床头柜','HOUSE_V1_MOTHER_CREATIVE_BED'),('couple','夫妻床与床头柜','CAM_couple_bedroom_VIEW_01'),('guest','客房1.2×2m床','CAM_guest_bedroom_VIEW_01'),('master_bath','主卫全景','HOUSE_V2_MASTER_WHOLE'),('secondary_bath','次主卫磨砂玻璃','CAM_secondary_bath_VIEW_01'),('north','北阳台全景','CAM_north_sunroom_VIEW_01'),('north_sofa','北阳台软包','HOUSE_V2_NORTH_SOFA'),('living','客厅灯光','CAM_living_VIEW_01'),('dining','餐厅灯光','CAM_dining_VIEW_01')];rec=[]
for rid,title,cam in shots:
 s.camera=next(o for o in bpy.data.objects if o.name.startswith(cam) and o.type=='CAMERA');path=dest/(rid+'.png');s.render.filepath=str(path);t=time.time();bpy.ops.render.render(write_still=True);rec.append({'id':rid,'title':title,'camera':s.camera.name,'path':str(path),'size':[s.render.resolution_x,s.render.resolution_y],'seconds':round(time.time()-t,2)});(dest/(rid+'.meta.json')).write_text(json.dumps({'source':a['output'],'source_sha256':a['output_sha256'],'image':rec[-1]},ensure_ascii=False,indent=2));print('SHOT_DONE',rid,flush=True)
(dest/'manifest.json').write_text(json.dumps({'source':a['output'],'source_sha256':a['output_sha256'],'mode':mode,'images':rec,'engine':s.render.engine,'samples':0 if mode=='clay' else 32,'image2_requests':0},ensure_ascii=False,indent=2)+'\n')
