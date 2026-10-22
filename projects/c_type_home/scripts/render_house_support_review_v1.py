"""Three bounded repaired-bedroom views; remaining house images retain their provenance."""
import bpy,json,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'design/whole_house_model_v1/assembly';a=json.loads((RUN/'BUILD_AUDIT.json').read_text());dest=RUN/'support_review';dest.mkdir(exist_ok=True)
if (dest/'render-manifest.json').exists():raise SystemExit('Preserved review exists.')
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.adaptive_threshold=.04;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE';s.render.threads_mode='FIXED';s.render.threads=2;s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';records=[]
for rid,title,view,cam,file in [('mother_bedroom','母亲主卧','VIEW_05','CAM_mother_bedroom_VIEW_05','mother_bedroom_VIEW_05.png'),('mother_bedroom','母亲主卧床体','bed_supplement','HOUSE_V1_MOTHER_CREATIVE_BED','mother_bedroom_bed.png'),('couple_bedroom','夫妻次主卧','VIEW_01','CAM_couple_bedroom_VIEW_01','couple_bedroom_VIEW_01.png')]:
 s.camera=bpy.data.objects[cam];p=dest/file;s.render.filepath=str(p);t=time.time();bpy.ops.render.render(write_still=True);records.append({'room_id':rid,'display_name':title,'view':view,'camera':cam,'path':str(p),'seconds':round(time.time()-t,2),'native_size':[1280,720],'source_sha256':a['output_sha256']})
(dest/'render-manifest.json').write_text(json.dumps({'source':a['output'],'source_sha256':a['output_sha256'],'engine':'CYCLES','samples':32,'images':records},ensure_ascii=False,indent=2)+'\n')
