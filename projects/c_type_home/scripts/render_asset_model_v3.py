"""Named physical-camera previews and supplier-derived look evidence."""
import bpy,sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/asset_model_v3'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
stage=args[0] if args else 'geometry';dest=OUT/stage;dest.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'LIVING_KITCHEN_LIBRARY_V3.blend'));scene=bpy.context.scene
names=['CAM_living_VIEW_01','LD_CAM_living_DETAIL','AM2_CAM_SOFA_MATERIAL','CAM_kitchen_VIEW_01','CAM_kitchen_VIEW_05']
scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=50 if stage!='review_renders' else 100
if stage=='geometry':
 scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.display.shading.show_shadows=True
else:
 scene.render.engine='CYCLES';scene.cycles.samples=40 if stage=='look' else 128;scene.cycles.use_denoising=True;scene.cycles.denoising_use_gpu=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.cycles.adaptive_threshold=.015
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 scene.cycles.device='GPU'
scene.render.threads_mode='FIXED';scene.render.threads=2
renders=[]
for n in names:
 scene.camera=bpy.data.objects[n];scene.render.filepath=str(dest/(n+'.png'));t=time.time();bpy.ops.render.render(write_still=True);renders.append({'camera':n,'path':scene.render.filepath,'size':[int(scene.render.resolution_x*scene.render.resolution_percentage/100),int(scene.render.resolution_y*scene.render.resolution_percentage/100)],'seconds':round(time.time()-t,2)})
(dest/'render-manifest.json').write_text(json.dumps({'stage':stage,'engine':scene.render.engine,'device':'METAL' if stage!='geometry' else 'Workbench','samples':scene.cycles.samples,'images':renders,'blender_version':bpy.app.version_string,'denoising_quality':'OIDN High Accurate GPU','color_management':{'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure}},indent=2)+'\n')
print('V3_RENDER_STAGE_DONE',stage)
