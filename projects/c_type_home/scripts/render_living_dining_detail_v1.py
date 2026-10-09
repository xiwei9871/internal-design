"""Reopen saved scene; bounded named geometry/look/final evidence."""
import bpy, json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/living_dining_detail_v1'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
stage=args[0] if args else 'geometry'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'LIVING_DINING_DETAIL_V1.blend'))
scene=bpy.context.scene;dest=OUT/stage;dest.mkdir(exist_ok=True)
names=['CAM_living_VIEW_01','CAM_living_VIEW_02','CAM_dining_VIEW_01','LD_CAM_living_DETAIL','LD_CAM_dining_DETAIL']
if stage=='geometry':
 scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_percentage=45
 scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=True
elif stage=='look':
 scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.adaptive_threshold=.07;scene.render.resolution_percentage=50
 names=['CAM_living_VIEW_01','CAM_dining_VIEW_01','LD_CAM_living_DETAIL','LD_CAM_dining_DETAIL']
else:
 scene.render.engine='CYCLES';scene.render.resolution_percentage=100;scene.cycles.samples=128
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU'
renders=[]
for n in names:
 if n=='CAM_dining_VIEW_01':scene.render.resolution_x=1440;scene.render.resolution_y=1920
 else:scene.render.resolution_x=1920;scene.render.resolution_y=1080
 scene.camera=bpy.data.objects[n];p=dest/(n+'.png');scene.render.filepath=str(p);t=time.time();bpy.ops.render.render(write_still=True)
 renders.append({'camera':n,'path':str(p),'size':[round(scene.render.resolution_x*scene.render.resolution_percentage/100),round(scene.render.resolution_y*scene.render.resolution_percentage/100)],'seconds':round(time.time()-t,2)})
(dest/'render-manifest.json').write_text(json.dumps({'stage':stage,'engine':scene.render.engine,'device':'METAL','samples':scene.cycles.samples,'denoiser':scene.cycles.denoiser,'denoising_use_gpu':scene.cycles.denoising_use_gpu,'color_management':{'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure},'renders':renders},indent=2))
print('LD_RENDER_COMPLETE',stage)
