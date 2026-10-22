"""Isolated supplier native nodes + original geometry verification before adapting."""
import bpy, json, math, time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/asset_model_v3'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'SUPPLIER_FLY_SC2_INSPECT.blend'))
o=bpy.data.objects['SC2_medium']
for v in o.data.vertices:v.co=(v.co.x*.001,v.co.z*.001,-v.co.y*.001)
o.data.update()
materials={}
for id in ['linen','ash']:
 p=OUT/'assets'/f'{id}_native_1k'/('rough_linen_1k.blend' if id=='linen' else 'ash_veneer_1k.blend')
 with bpy.data.libraries.load(str(p),link=False) as (a,b):b.materials=a.materials
 material=b.materials[0];materials[id]=material
 for n in material.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image:
   file=Path(n.image.filepath).name;n.image.filepath=str(p.parent/'textures'/file);n.image.reload()
parts=json.loads((OUT/'SUPPLIER_COMPONENTS.json').read_text())[0]['parts']
cloth_ids={i for p in parts if p['vertices']>2500 for i in p['indices']}
o.data.materials.clear();o.data.materials.append(materials['ash']);o.data.materials.append(materials['linen'])
for p in o.data.polygons:p.material_index=1 if all(i in cloth_ids for i in p.vertices) else 0;p.use_smooth=True
# Native UV is retained for the unmodified supplier baseline.
def camera(n,pos,target,lens):
 d=bpy.data.cameras.new(n);obj=bpy.data.objects.new(n,d);bpy.context.scene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;return obj
scene=bpy.context.scene;scene.camera=camera('SUPPLIER_CAMERA',(2.1,-2.2,1.35),(0,0,.38),47)
def area(n,pos,target,power,size):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;obj=bpy.data.objects.new(n,d);scene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
area('Neutral key',(-1.4,-1.5,2.8),(0,0,.3),300,2.0);area('Neutral fill',(1.5,.8,2),(0,0,.4),100,2)
world=bpy.data.worlds.new('Neutral supplier test');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.6,.6,.6,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.25;scene.world=world
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.001));ground=bpy.context.object;mat=bpy.data.materials.new('Neutral ground');mat.diffuse_color=(.5,.5,.5,1);ground.data.materials.append(mat)
scene.render.resolution_x=1280;scene.render.resolution_y=960;scene.render.resolution_percentage=100;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.show_cavity=True;scene.render.filepath=str(OUT/'SUPPLIER_GEOMETRY_PREVIEW.png');bpy.ops.render.render(write_still=True)
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
for d in pref.devices:d.use=d.type=='METAL'
scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.denoising_use_gpu=True;scene.render.filepath=str(OUT/'SUPPLIER_NATIVE_MATERIAL_TEST.png');bpy.ops.render.render(write_still=True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SUPPLIER_NATIVE_TEST.blend'))
print('SUPPLIER_GEOMETRY_AND_NATIVE_MATERIAL_READY')
