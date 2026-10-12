import bpy,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/whole_house_model_v2';a=json.loads((D/'BUILD_AUDIT.json').read_text());dest=D/'review_remaining';dest.mkdir(exist_ok=True)
if (dest/'manifest.json').exists():raise SystemExit('Preserved completion exists')
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene;s.render.engine='CYCLES';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2;s.cycles.samples=32;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE';s.cycles.adaptive_threshold=.04;s.render.image_settings.file_format='PNG'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';rec=[]
for rid,title,cam in [('north_sofa','北阳台软包','HOUSE_V2_NORTH_SOFA'),('living','客厅照明','CAM_living_VIEW_01'),('dining','餐厅照明','CAM_dining_VIEW_01')]:
 s.camera=next(o for o in bpy.data.objects if o.type=='CAMERA' and o.name.startswith(cam));s.render.filepath=str(dest/(rid+'.png'));t=time.time();bpy.ops.render.render(write_still=True);rec.append({'id':rid,'title':title,'camera':s.camera.name,'path':s.render.filepath,'size':[1280,720],'seconds':round(time.time()-t,2),'source_sha256':a['output_sha256']});(dest/(rid+'.meta.json')).write_text(json.dumps(rec[-1],ensure_ascii=False,indent=2));print('REMAINING_DONE',rid,flush=True)
(dest/'manifest.json').write_text(json.dumps({'source':a['output'],'source_sha256':a['output_sha256'],'images':rec,'engine':'CYCLES','samples':32,'image2_requests':0},ensure_ascii=False,indent=2)+'\n')
