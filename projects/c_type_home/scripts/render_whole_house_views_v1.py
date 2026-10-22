"""Cached ordered camera previews/final faithful rendering from authored presentation."""
import bpy,json,sys,time,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/whole_house_final_study_v1';M=OUT/'00_MANIFEST'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];mode=args[0] if args else 'gate';only=args[1] if len(args)>1 else None
reg=json.loads((M/'CAMERA_REGISTER_V1.json').read_text());bpy.ops.wm.open_mainfile(filepath=reg['render_scene']);scene=bpy.context.scene
if mode=='gate':
 scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=960;scene.render.resolution_y=540
 scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
 scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=False
 # Workbenchdoesnottrace transmission;hideonlyclearpanesforcompositiongate,framesstay.
 for o in bpy.context.scene.objects:
  if o.type=='MESH' and ('GLASS' in o.name.upper() or o.name.startswith('G_wall_g')):o.hide_render=True
else:
 scene.render.engine='CYCLES';p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
 for d in p.devices:d.use=d.type=='METAL'
 scene.cycles.device='GPU';scene.render.resolution_x=960 if mode=='looktest' else 1920;scene.render.resolution_y=540 if mode=='looktest' else 1080;scene.cycles.samples=8 if mode=='looktest' else 32
scene.render.threads_mode='FIXED';scene.render.threads=2
records=[]
for c in reg['cameras']:
 if only and c['room_id']!=only:continue
 directory=OUT/c['room_id']/('00_camera_gate' if mode in ['gate','looktest'] else '01_faithful');directory.mkdir(parents=True,exist_ok=True);path=directory/(c['view_id']+('_preview' if mode=='gate' else '_light_test' if mode=='looktest' else '')+'.png')
 cam=bpy.data.objects[c['camera_name']];scene.camera=cam
 # Camera tweaks are retainedinregisterfor reproducibilityandlaterbaseconditioning.
 cam.location=c['eye'];direction=Vector(c['target'])-Vector(c['eye'])
 if c.get('controlled_verticals'):
  horizontal=Vector((direction.x,direction.y,0));cam.rotation_euler=horizontal.to_track_quat('-Z','Y').to_euler();cam.data.shift_y=c['shift_y']
 else:cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
 cam.data.lens=c['lens_mm']
 if path.exists():print('CACHE',mode,c['room_id'],c['view_id'],flush=True);continue
 t=time.time();scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 r={'room_id':c['room_id'],'view_id':c['view_id'],'mode':mode,'path':str(path),'seconds':time.time()-t,'engine':scene.render.engine,'samples':scene.cycles.samples if mode!='gate' else None,'source_design_sha256':reg['source_sha256']}
 records.append(r)
 with (M/'RENDER_EVENTS.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
 print('RENDER_DONE',mode,c['room_id'],c['view_id'],round(r['seconds'],2),flush=True)
print('RENDER_BATCH_PASS',mode,len(records),flush=True)
