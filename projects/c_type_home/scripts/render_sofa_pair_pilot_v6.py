"""Fixed before/after cameras: shape first, then approved bounded fabric evidence."""
import bpy,json,sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_soft_pilot_v6'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];mode=args[0] if args else 'macro'
is_macro=mode.startswith('macro');is_clay=is_macro or mode.startswith('detail_clay');SOURCE=OUT/('SOFA_SEAT_BACK_MACRO_V6.blend' if is_macro else 'SOFA_SEAT_BACK_DETAIL_V6.blend')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;dest=OUT/mode;dest.mkdir(exist_ok=True)
scene.render.resolution_x=1000 if is_clay else 1500;scene.render.resolution_y=800 if is_clay else 1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.threads_mode='FIXED';scene.render.threads=2
if is_clay:
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.53,.53,.53);scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=False;scene.display.shading.background_type='WORLD';scene.world.color=(.21,.23,.24)
else:
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.adaptive_threshold=.025;scene.cycles.use_denoising=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.cycles.denoising_use_gpu=True
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    scene.cycles.device='GPU'
images=[]
for family in ['V5','V6']:
    bpy.data.collections['V5_COMPARISON_PAIR'].hide_render=family!='V5';bpy.data.collections['V6_CUSTOM_PAIR'].hide_render=family!='V6'
    bpy.data.collections['V5_COMPARISON_PAIR'].hide_viewport=family!='V5';bpy.data.collections['V6_CUSTOM_PAIR'].hide_viewport=family!='V6'
    for n in ['V6_FRONT','V6_SIDE','V6_THREE_QUARTER']:
        scene.camera=bpy.data.objects[n];scene.render.filepath=str(dest/(family+'_'+n+'.png'));t=time.time();bpy.ops.render.render(write_still=True)
        images.append({'family':family,'camera':n,'path':scene.render.filepath,'size':[scene.render.resolution_x,scene.render.resolution_y],'seconds':round(time.time()-t,2)})
(dest/'render-manifest.json').write_text(json.dumps({'stage':mode,'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'engine':scene.render.engine,'device':'Workbench' if is_clay else 'METAL','samples':0 if is_clay else scene.cycles.samples,'denoise':'OIDN GPU High Accurate' if not is_clay else None,'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'fixed_comparison_lighting':True,'images':images},indent=2)+'\n');print('V6_COMPARISON_RENDER_DONE',mode)
