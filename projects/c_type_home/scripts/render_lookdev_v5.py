"""Controlled material comparison plus only the decision views needed for this repair."""
import bpy,json,sys,time
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/lookdev_v5'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];stage=args[0] if args else 'preview'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'LIVING_DINING_LOOKDEV_V5.blend'));scene=bpy.context.scene;dest=OUT/stage;dest.mkdir(exist_ok=True)
is_preview=stage.startswith('preview')
scene.render.engine='CYCLES';scene.cycles.samples=24 if is_preview else 96;scene.cycles.adaptive_threshold=.06 if is_preview else .02
scene.cycles.use_denoising=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.cycles.denoising_use_gpu=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='METAL'
scene.cycles.device='GPU';scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.image_settings.file_format='PNG'
images=[]
def render(camera,x,y,name=None):
    scene.camera=camera;scene.render.resolution_x=x;scene.render.resolution_y=y;scene.render.resolution_percentage=100
    scene.render.filepath=str(dest/((name or camera.name)+'.png'));t=time.time();bpy.ops.render.render(write_still=True)
    images.append({'camera':camera.name,'path':scene.render.filepath,'size':[x,y],'seconds':round(time.time()-t,2)})
for name in ['V4_CAM_SOFA_COMPLETE','V4_CAM_DINING_DETAIL','CAM_living_VIEW_01']:
    render(bpy.data.objects[name],960 if is_preview else 1920,540 if is_preview else 1080)
if not is_preview:render(bpy.data.objects['V4_CAM_DINING_COMPLETE'],1440,1920)
# Same neutral studio light and camera for before/after wood plates, a separate test.
for c in bpy.data.collections:c.hide_render=False
for o in scene.objects:o.hide_render=True
for name in ['V5_STUDY_WOOD_OLD','V5_STUDY_WOOD_NEW']:bpy.data.objects[name].hide_render=False
scene.world=bpy.data.worlds.new('V5 neutral lookdev');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.65,.65,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
data=bpy.data.lights.new('V5 neutral area','AREA');data.energy=450;data.shape='DISK';data.size=3;light=bpy.data.objects.new('V5 neutral area',data);scene.collection.objects.link(light);light.location=(-1,-1.5,2.8);light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('V5_MATERIAL_CONTROL');camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera);data.lens=42;camera.location=(0,-2.6,2.3);camera.rotation_euler=(Vector((0,0,.12))-camera.location).to_track_quat('-Z','Y').to_euler()
render(camera,1400,700,'WOOD_FIXED_LIGHT_COMPARE')
(dest/'render-manifest.json').write_text(json.dumps({'stage':stage,'engine':'CYCLES','device':'METAL','samples':scene.cycles.samples,'denoise':'OIDN GPU High Accurate','room_light_camera_color':'V4 unchanged','images':images},indent=2)+'\n');print('V5_RENDER_COMPLETE',stage)
