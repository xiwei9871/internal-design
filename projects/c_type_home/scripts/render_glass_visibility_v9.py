"""Authored Cycles room renders and matching EEVEE outside-window check."""
import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/glass_visibility_v9';a=json.loads((D/'BUILD_AUDIT.json').read_text());O=D/'review';O.mkdir(exist_ok=True);bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
for l in s.view_layers:l.use=l.name=='INTERIOR_CLOSED_CEILING'
bpy.context.window.view_layer=s.view_layers['INTERIOR_CLOSED_CEILING']
s.render.engine='CYCLES';s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2;s.cycles.samples=96;s.cycles.adaptive_threshold=.02;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE';s.render.image_settings.file_format='PNG'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';records=[]
for name,cam in [('living','CAM_living_VIEW_01'),('bedroom','CAM_couple_bedroom_VIEW_01'),('privacy','CAM_guest_bedroom_VIEW_01')]:
 f=O/(name+'.png');assert not f.exists();s.camera=bpy.data.objects[cam];s.render.filepath=str(f);bpy.ops.render.render(write_still=True);records.append({'view':name,'camera':cam,'path':str(f),'engine':'CYCLES','size':[1600,900],'samples':96});print('V9_ROOM',name,flush=True)
# Matching direct view of source glass from outside. Forest world reproduces material preview; authored lights/ceiling omitted only in this read-only diagnostic.
s.render.engine='BLENDER_EEVEE'
for o in s.objects:
 if o.type=='LIGHT':o.hide_render=True
for n in ['V7_CEILING_LOW','V7_CEILING_HIGH','V7_CEILING_450MM_TRANSITION']:bpy.data.objects[n].hide_render=True
world=bpy.data.worlds.new('V9_FINAL_FOREST_VIEW_CHECK');world.use_nodes=True;env=world.node_tree.nodes.new('ShaderNodeTexEnvironment');env.image=bpy.data.images.load(bpy.context.preferences.studio_lights.get('forest.exr').path,check_existing=True);world.node_tree.links.new(env.outputs['Color'],world.node_tree.nodes.get('Background').inputs['Color']);s.world=world
cam=bpy.data.objects.new('V9_FINAL_OUTSIDE_WINDOW_CHECK',bpy.data.cameras.new('V9_FINAL_OUTSIDE_WINDOW_CHECK'));s.collection.objects.link(cam);cam.location=(6,17.6,2.7);cam.rotation_euler=(Vector((5.25,11.75,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=35;s.camera=cam
f=O/'viewport_check.png';assert not f.exists();s.render.filepath=str(f);bpy.ops.render.render(write_still=True);records.append({'view':'viewport_check','path':str(f),'engine':'EEVEE','matching_forest_material_preview':True});(O/'manifest.json').write_text(json.dumps({'source_sha256':a['sha256'],'images':records},indent=2)+'\n');print('V9_VIEW_CHECK',flush=True)
