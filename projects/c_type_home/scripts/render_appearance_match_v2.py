"""Bounded actual material evidence, reopened .blend with authored illumination."""
import bpy,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/appearance_match_v2';DEST=OUT/'review_renders';DEST.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'LIVING_DINING_APPEARANCE_V2.blend'));scene=bpy.context.scene
scene.render.engine='CYCLES';scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.cycles.samples=128;scene.cycles.use_denoising=True;scene.cycles.denoiser='OPENIMAGEDENOISE';scene.cycles.denoising_use_gpu=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.cycles.adaptive_threshold=.012
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU';scene.render.threads_mode='FIXED';scene.render.threads=2
images=[]
for n in ['CAM_living_VIEW_01','AM2_CAM_SOFA_MATERIAL','LD_CAM_dining_DETAIL','CAM_living_VIEW_02']:
 scene.camera=bpy.data.objects[n];scene.render.filepath=str(DEST/(n+'.png'));t=time.time();bpy.ops.render.render(write_still=True);images.append({'camera':n,'path':scene.render.filepath,'seconds':round(time.time()-t,2),'size':[1920,1080]})
(DEST/'render-manifest.json').write_text(json.dumps({'blender_version':bpy.app.version_string,'engine':scene.render.engine,'device':'METAL','samples':scene.cycles.samples,'denoiser':scene.cycles.denoiser,'denoising_use_gpu':scene.cycles.denoising_use_gpu,'denoising_quality':scene.cycles.denoising_quality,'color_management':{'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure},'images':images},indent=2)+'\n')
print('APPEARANCE_V2_RENDER_DONE',len(images))
