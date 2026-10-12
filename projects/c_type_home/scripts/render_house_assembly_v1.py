"""Fifteen named room previews, retaining source light and chosen view matrices."""
import bpy,json,sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/whole_house_model_v1';RUN=OUT/'assembly';a=json.loads((RUN/'BUILD_AUDIT.json').read_text())
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];stage=args[0] if args else 'clay';DEST=RUN/stage;DEST.mkdir(exist_ok=True)
if (DEST/'render-manifest.json').exists():raise SystemExit('Preserved batch exists; use a new stage/version.')
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene;s.render.resolution_x=960 if stage=='clay' else 1280;s.render.resolution_y=540 if stage=='clay' else 720;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.threads_mode='FIXED';s.render.threads=2
if stage=='clay':
 s.render.engine='BLENDER_WORKBENCH';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=False;sh.show_specular_highlight=False
else:
 s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.adaptive_threshold=.04;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE'
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 s.cycles.device='GPU'
reg=json.loads((ROOT/'renders/whole_house_final_study_v1/00_MANIFEST/WHOLE_HOUSE_ROOM_MANIFEST_V1.json').read_text());records=[]
for r in reg['rooms']:
 rid=r['room_id'];view='VIEW_03' if rid=='kitchen' else 'VIEW_05' if rid=='mother_bedroom' else 'VIEW_01'
 selected={'reading_transition':'HOUSE_V1_READING_OPPOSITE_WALL','master_bath':'HOUSE_V1_MASTER_CABINET'}
 cam=bpy.data.objects[selected.get(rid,'CAM_'+rid+'_'+view)];s.camera=cam;p=DEST/(rid+'_'+view+'.png');s.render.filepath=str(p);t=time.time();bpy.ops.render.render(write_still=True);records.append({'room_id':rid,'display_name':r['display_name'],'view':view,'camera':cam.name,'path':str(p),'seconds':round(time.time()-t,2),'native_size':[s.render.resolution_x,s.render.resolution_y]});print('ROOM_PREVIEW_DONE',rid,records[-1]['seconds'],flush=True)
if stage!='clay':
 cam=bpy.data.objects['HOUSE_V1_MOTHER_CREATIVE_BED'];s.camera=cam;p=DEST/'mother_bedroom_bed.png';s.render.filepath=str(p);t=time.time();bpy.ops.render.render(write_still=True);records.append({'room_id':'mother_bedroom','display_name':'母亲主卧床体','view':'bed_supplement','camera':cam.name,'path':str(p),'seconds':round(time.time()-t,2),'native_size':[s.render.resolution_x,s.render.resolution_y]})
 for rid,title,name in [('living','客厅沙发细节','HOUSE_V1_LIVING_SOFA_DETAIL'),('dining','餐厅整体','HOUSE_V1_DINING_WHOLE')]:
  s.camera=bpy.data.objects[name];p=DEST/(rid+'_detail.png');s.render.filepath=str(p);t=time.time();bpy.ops.render.render(write_still=True);records.append({'room_id':rid,'display_name':title,'view':'supplement','camera':name,'path':str(p),'seconds':round(time.time()-t,2),'native_size':[s.render.resolution_x,s.render.resolution_y]})
(DEST/'render-manifest.json').write_text(json.dumps({'stage':stage,'source':a['output'],'source_sha256':a['output_sha256'],'engine':s.render.engine,'samples':0 if stage=='clay' else 32,'images':records,'lights':'original latest whole-house lookdev retained, no per-room photo grading','image2_requests':0},ensure_ascii=False,indent=2)+'\n')
