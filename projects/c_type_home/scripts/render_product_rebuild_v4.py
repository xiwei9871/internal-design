"""Whole products and actual house: bounded named evidence."""
import bpy,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/product_rebuild_v4'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];stage=args[0] if args else 'geometry'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'LIVING_DINING_PRODUCT_REBUILD_V4.blend'));scene=bpy.context.scene;dest=OUT/stage;dest.mkdir(exist_ok=True)
names=['CAM_living_VIEW_01','V4_CAM_SOFA_COMPLETE','V4_CAM_DINING_COMPLETE','V4_CAM_CHAIR_COMPLETE','V4_CAM_DINING_DETAIL','CAM_living_VIEW_02']
if stage=='geometry':
 scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.display.shading.show_shadows=True
else:
 scene.render.engine='CYCLES';scene.cycles.samples=32 if stage=='look' else 128;scene.cycles.adaptive_threshold=.05 if stage=='look' else .015;scene.cycles.use_denoising=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.cycles.denoising_use_gpu=True
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 scene.cycles.device='GPU'
scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=50 if stage!='review_renders' else 100
images=[]
for n in names:
 scene.render.resolution_x=1440 if n=='V4_CAM_DINING_COMPLETE' else 1920;scene.render.resolution_y=1920 if n=='V4_CAM_DINING_COMPLETE' else 1080
 scene.camera=bpy.data.objects[n];scene.render.filepath=str(dest/(n+'.png'));t=time.time();bpy.ops.render.render(write_still=True);images.append({'camera':n,'path':scene.render.filepath,'seconds':round(time.time()-t,2),'size':[int(scene.render.resolution_x*scene.render.resolution_percentage/100),int(scene.render.resolution_y*scene.render.resolution_percentage/100)]})
(dest/'render-manifest.json').write_text(json.dumps({'stage':stage,'engine':scene.render.engine,'device':'METAL' if stage!='geometry' else 'Workbench','samples':scene.cycles.samples,'images':images,'blender_version':bpy.app.version_string,'denoiser':'OIDN GPU High Accurate','view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure},indent=2)+'\n')
print('V4_RENDER_EVIDENCE_COMPLETE',stage)
