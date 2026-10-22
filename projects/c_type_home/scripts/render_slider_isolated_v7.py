"""Supplemental glass assembly evidence; isolated studio, not room lighting."""
import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/pale_ash_review_v7';a=json.loads((D/'BUILD_AUDIT.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
keep=set(a['slider_frame_created']+a['slider_clamp_created']+['R3_SLIDING_RECESSED_PULL_N','R3_SLIDING_RECESSED_PULL_S'])
for col in bpy.data.collections:col.hide_render=False;col.hide_viewport=False
for o in s.objects:o.hide_render=o.name not in keep;o.hide_viewport=False;o.hide_set(False)
for l in s.view_layers:l.use=l.name=='INTERIOR_CLOSED_CEILING'
bpy.context.window.view_layer=s.view_layers['INTERIOR_CLOSED_CEILING']
world=bpy.data.worlds.new('V7_ISOLATED_NEUTRAL_WORLD');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.35,.35,.35,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.5;s.world=world
m=bpy.data.materials.new('V7_ISOLATED_CHECKER');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.9;tex=m.node_tree.nodes.new('ShaderNodeTexChecker');tex.inputs['Color1'].default_value=(.12,.18,.20,1);tex.inputs['Color2'].default_value=(.52,.47,.38,1);tex.inputs['Scale'].default_value=5;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
bpy.ops.mesh.primitive_plane_add(size=3,location=(10.55,5.1,1.5));o=bpy.context.object;o.rotation_euler=(1.570796,0,0);o.data.materials.append(m)
floor=bpy.data.materials.new('V7_STUDIO_FLOOR');floor.use_nodes=True;floor.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.45,.45,.45,1);floor.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.7
bpy.ops.mesh.primitive_plane_add(size=8,location=(10.55,4.75,.44));bpy.context.object.data.materials.append(floor)
light=bpy.data.objects.new('V7_STUDIO_AREA',bpy.data.lights.new('V7_STUDIO_AREA','AREA'));s.collection.objects.link(light);light.location=(10,2.5,3.8);light.rotation_euler=(Vector((10.55,4.74,1.5))-light.location).to_track_quat('-Z','Y').to_euler();light.data.energy=350;light.data.shape='DISK';light.data.size=2
cam=bpy.data.objects.new('V7_STUDIO_GLASS_CAMERA',bpy.data.cameras.new('V7_STUDIO_GLASS_CAMERA'));s.collection.objects.link(cam);cam.location=(12.25,1.7,2.0);cam.rotation_euler=(Vector((10.55,4.74,1.48))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=42;s.camera=cam
s.render.engine='CYCLES';s.render.resolution_x=1000;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.cycles.samples=64;s.cycles.adaptive_threshold=.025;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.render.threads_mode='FIXED';s.render.threads=2
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for dev in p.devices:dev.use=dev.type=='METAL'
s.cycles.device='GPU';s.render.image_settings.file_format='PNG';dest=D/'review_final/slider_isolated.png';assert not dest.exists();s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);print('ISOLATED_GLASS',str(dest))
