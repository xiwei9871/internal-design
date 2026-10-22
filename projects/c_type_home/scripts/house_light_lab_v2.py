"""Controlled source-scene lighting comparison, geometry/materials unchanged."""
import bpy,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/whole_house_model_v2/light_lab';D.mkdir(parents=True,exist_ok=True)
if (D/'manifest.json').exists():raise SystemExit('Preserved lab exists')
src=R/'design/whole_house_model_v1/assembly/WHOLE_HOUSE_REVIEW_SUPPORTED_V2.blend'
bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene
s.render.engine='CYCLES';s.render.resolution_x=800;s.render.resolution_y=450;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2;s.cycles.samples=16;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
energy={o.name:o.data.energy for o in s.objects if o.type=='LIGHT'};rec=[]
for mode in ['baseline','contrast_only','soft_fill']:
 s.view_settings.look='AgX - Medium High Contrast' if mode=='baseline' else 'AgX - Medium High Contrast' if mode=='soft_fill' else 'AgX - Medium Low Contrast'
 s.view_settings.exposure=.15
 for n,v in energy.items():bpy.data.objects[n].data.energy=v
 if mode=='soft_fill':
  for o in s.objects:
   if o.type=='LIGHT' and o.name.startswith('LIGHT_'):o.data.energy=max(o.data.energy,65 if any(t in o.name for t in ['hallway','bath']) else 45)
  for n in ['DAYLIGHT_northliving','DAYLIGHT_northstudy','DAYLIGHT_northsunroom','DAYLIGHT_southbed']:bpy.data.objects[n].data.energy*=1.3
 for rid in ['living','hallway','secondary_bath']:
  s.camera=bpy.data.objects['CAM_'+rid+'_VIEW_01'];s.render.filepath=str(D/(rid+'_'+mode+'.png'));t=time.time();bpy.ops.render.render(write_still=True);rec.append({'room':rid,'mode':mode,'path':s.render.filepath,'seconds':round(time.time()-t,2)})
(D/'manifest.json').write_text(json.dumps({'source':str(src),'images':rec,'source_exposure_unchanged':.15,'fill':'existing practical max45/65 and existing daylight x1.3; rendering watts not electrical/lux calibration'},indent=2)+'\n')
