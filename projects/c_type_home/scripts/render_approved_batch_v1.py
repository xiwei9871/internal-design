"""Approved per-view camera and source rendering, cache keyed to production contract."""
import bpy,json,time,sys,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/whole_house_final_study_v1/production_batch_v1';M=OUT/'00_MANIFEST';args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];mode=args[0] if args else 'final';only=args[1] if len(args)>1 else None
reg=json.loads((M/'CAMERA_REGISTER.json').read_text());bpy.ops.wm.open_mainfile(filepath=reg['render_scene']);s=bpy.context.scene;source=Path(reg['source_design']);assert hashlib.sha256(source.read_bytes()).hexdigest()==reg['source_sha256']
if mode=='gate':
 s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=960;s.render.resolution_y=540;s.display.shading.light='STUDIO';s.display.shading.studio_light='paint.sl';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.display.shading.show_specular_highlight=False
 for o in s.objects:
  if o.type=='MESH' and ('GLASS' in o.name.upper() or o.name.startswith('G_wall_g')):o.hide_render=True
else:
 s.render.engine='CYCLES';prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 s.cycles.device='GPU';s.cycles.samples=32 if mode=='look' else 256;s.render.resolution_x=960 if mode=='look' else 1920;s.render.resolution_y=540 if mode=='look' else 1080
s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2
for c in reg['cameras']:
 if only and c['room_id']!=only:continue
 if mode=='look' and c['view_id']!='VIEW_01':continue
 directory=OUT/c['room_id']/('00_camera_gate' if mode=='gate' else 'look_preview_verified' if mode=='look' else '01_faithful');directory.mkdir(exist_ok=True,parents=True);dest=directory/(c['view_id']+'.png');meta=dest.with_suffix('.render.json')
 if dest.exists() and meta.exists():print('CACHE',c['room_id'],c['view_id'],mode,flush=True);continue
 cam=bpy.data.objects[c['camera_name']];s.camera=cam
 s.render.filepath=str(dest);t=time.time();bpy.ops.render.render(write_still=True);metadata={'room_id':c['room_id'],'view_id':c['view_id'],'mode':mode,'path':str(dest),'engine':s.render.engine,'samples':s.cycles.samples,'source_sha256':reg['source_sha256'],'matrix_world':c['matrix_world'],'seconds':time.time()-t,'color':{'view':'AgX','look':s.view_settings.look,'exposure':s.view_settings.exposure,'white_balance':s.view_settings.white_balance_temperature}}
 meta.write_text(json.dumps(metadata,indent=2))
 with (M/'RENDER_EVENTS.jsonl').open('a') as f:f.write(json.dumps(metadata)+'\n')
 print('RENDER_DONE',c['room_id'],c['view_id'],mode,round(metadata['seconds'],1),flush=True)
print('RENDER_QUEUE_COMPLETE',mode,flush=True)
