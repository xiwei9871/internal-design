"""Pinned cameras before/after and ceiling coverage evidence, no scene writeback."""
import bpy,json,time,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/pale_ash_review_v7';a=json.loads((D/'BUILD_AUDIT.json').read_text());O=D/('review_final' if '--final' in sys.argv else 'review');O.mkdir(exist_ok=True);rec=[]
def setup(path):
 bpy.ops.wm.open_mainfile(filepath=path);s=bpy.context.scene
 for layer in s.view_layers:layer.use=layer.name!='OVERVIEW_CEILING_HIDDEN'
 interior=s.view_layers.get('INTERIOR_CLOSED_CEILING') or s.view_layers[0]
 bpy.context.window.view_layer=interior
 s.render.engine='CYCLES';s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2
 s.cycles.samples=128;s.cycles.adaptive_threshold=.015;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE'
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
 for dev in p.devices:dev.use=dev.type=='METAL'
 s.cycles.device='GPU';s.render.image_settings.file_format='PNG'
 return s
for version,path,shots in [('before',a['source'],[('bed','CAM_couple_bedroom_VIEW_01'),('living','CAM_living_VIEW_01')]),('after',a['output'],[('bed','CAM_couple_bedroom_VIEW_01'),('living','CAM_living_VIEW_01'),('entry','CAM_entry_VIEW_01'),('hallway','CAM_hallway_VIEW_01')])]:
 s=setup(path)
 for name,camera in shots:
  f=O/(version+'_'+name+'.png')
  if f.exists():print('PRESERVED',str(f),flush=True);continue
  s.camera=bpy.data.objects[camera];s.render.filepath=str(f);t=time.time();bpy.ops.render.render(write_still=True)
  rec.append({'version':version,'view':name,'camera':camera,'path':str(f),'resolution':[1600,900],'samples':128,'seconds':round(time.time()-t,2)});(O/'render_manifest.json').write_text(json.dumps(rec,indent=2)+'\n');print('V7_RENDER',version,name,flush=True)
for version,path,hide in [('before_ceiling',a['source'],False),('after_ceiling',a['output'],False),('after_open',a['output'],True)]:
 s=setup(path)
 if hide:
  for n in a['new_ceiling_objects']:bpy.data.objects[n].hide_render=True
 cam=bpy.data.objects.new('V7_REVIEW_AXON_CAMERA',bpy.data.cameras.new('V7_REVIEW_AXON_CAMERA'));s.collection.objects.link(cam);cam.location=(-8,-9,24);cam.rotation_euler=(Vector((8,6,1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=24;s.camera=cam
 s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.display.shading.background_type='WORLD';s.world.color=(.13,.13,.13);s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0
 f=O/(version+'.png')
 if not f.exists():s.render.filepath=str(f);bpy.ops.render.render(write_still=True)
 rec.append({'version':version,'view':'axon','path':str(f),'engine':'WORKBENCH','geometry_evidence_only':True});(O/'render_manifest.json').write_text(json.dumps(rec,indent=2)+'\n');print('V7_AXON',version,flush=True)
