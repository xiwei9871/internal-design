"""Controlled outdoor-exposure and EEVEE view-mode tests; preserve all source files."""
import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/glass_visibility_v9';S=R/'design/glass_privacy_v8/WHOLE_HOUSE_GLASS_PRIVACY_DELIVERY_V8.blend'
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
for layer in s.view_layers:layer.use=layer.name=='INTERIOR_CLOSED_CEILING'
bpy.context.window.view_layer=s.view_layers['INTERIOR_CLOSED_CEILING']
s.render.resolution_x=1200;s.render.resolution_y=675;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2;s.render.image_settings.file_format='PNG';s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.adaptive_threshold=.035
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.camera=bpy.data.objects['CAM_living_VIEW_01'];report={'material_rna':[p.identifier for p in bpy.data.materials['V8_COLORLESS_CLEAR_ARCHITECTURAL_GLASS'].bl_rna.properties if any(k in p.identifier for k in ['ray','thick','surface'])],'world_background_strengths':{}}
for gain in [2.4,3.6]:
 for name in ['Background.001','LD Neutral exterior presentation']:
  s.world.node_tree.nodes[name].inputs['Strength'].default_value=gain
 # Original diffuse/environment illumination Background remains .22; no interior light changes.
 name='outdoor_'+str(gain).replace('.','_');f=D/(name+'.png');assert not f.exists();s.render.filepath=str(f);bpy.ops.render.render(write_still=True);print('EXPOSURE_CONTROL',gain,flush=True)
report['world_background_strengths']={n.name:n.inputs['Strength'].default_value for n in s.world.node_tree.nodes if n.type=='BACKGROUND'}
# Reproduce forest Material Preview using its environment, roof hidden and authored lights off.
s.render.engine='BLENDER_EEVEE'
for o in s.objects:
 if o.type=='LIGHT':o.hide_render=True
for n in ['V7_CEILING_LOW','V7_CEILING_HIGH','V7_CEILING_450MM_TRANSITION']:bpy.data.objects[n].hide_render=True
world=bpy.data.worlds.new('V9_VIEWPORT_FOREST_CONTROL');world.use_nodes=True;env=world.node_tree.nodes.new('ShaderNodeTexEnvironment')
studio=bpy.context.preferences.studio_lights.get('forest.exr');report['studio_path']=studio.path
env.image=bpy.data.images.load(studio.path,check_existing=True);world.node_tree.links.new(env.outputs['Color'],world.node_tree.nodes.get('Background').inputs['Color']);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=1;s.world=world
cam=bpy.data.objects.new('V9_OUTSIDE_WINDOW_CAMERA',bpy.data.cameras.new('V9_OUTSIDE_WINDOW_CAMERA'));s.collection.objects.link(cam);cam.location=(6.0,17.6,2.7);cam.rotation_euler=(Vector((5.25,11.75,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=35;s.camera=cam
for enable in [False,True]:
 s.eevee.use_raytracing=enable
 for name in ['V8_COLORLESS_CLEAR_ARCHITECTURAL_GLASS','V8_COLORLESS_PRIVACY_FROSTED_GLASS']:
  m=bpy.data.materials[name]
  if hasattr(m,'use_raytrace_refraction'):m.use_raytrace_refraction=enable
  if enable:
   if hasattr(m,'thickness_mode'):m.thickness_mode='SLAB'
   if 'Thickness' in m.node_tree.nodes.get('Material Output').inputs:m.node_tree.nodes.get('Material Output').inputs['Thickness'].default_value=.008
 f=D/('eevee_'+('trace_on' if enable else 'trace_off')+'.png');assert not f.exists();s.render.filepath=str(f);bpy.ops.render.render(write_still=True);print('EEVEE_CONTROL',enable,flush=True)
report['eevee_settings']={'raytracing':s.eevee.use_raytracing,'method':s.eevee.ray_tracing_method}
(D/'PRESENTATION_CONTROLS.json').write_text(json.dumps(report,indent=2)+'\n')
