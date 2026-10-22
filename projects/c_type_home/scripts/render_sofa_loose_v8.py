"""Three fixed diagnostic views, V7/V8, same studio and materials."""
import bpy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_soft_pilot_v8'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
variant=args[0] if args else 'form1';stage=args[1] if len(args)>1 else 'clay'
RUN=OUT/variant;SOURCE=RUN/'SOFA_LOOSE_COVER_V8.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;dest=RUN/stage;dest.mkdir(exist_ok=True)
clay=stage=='clay';scene.render.resolution_x=1000 if clay else 1500;scene.render.resolution_y=800 if clay else 1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.threads_mode='FIXED';scene.render.threads=2
if clay:
    scene.render.engine='BLENDER_WORKBENCH';s=scene.display.shading;s.light='STUDIO';s.color_type='SINGLE';s.single_color=(.53,.53,.53);s.show_shadows=True;s.show_cavity=True;s.cavity_type='BOTH';s.show_specular_highlight=False;s.background_type='WORLD';scene.world.color=(.21,.23,.24)
else:
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.adaptive_threshold=.025;scene.cycles.use_denoising=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.cycles.denoising_use_gpu=True
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    scene.cycles.device='GPU'
records=[]
for family in ['V7','V8']:
    for f,name in [('V7','V7_COMPARISON_PAIR'),('V8','V8_LOOSE_PAIR')]:
        c=bpy.data.collections[name];c.hide_viewport=family!=f;c.hide_render=family!=f
    for camera in ['V6_FRONT','V6_SIDE','V6_THREE_QUARTER']:
        scene.camera=bpy.data.objects[camera];scene.render.filepath=str(dest/(family+'_'+camera+'.png'));t=time.time();bpy.ops.render.render(write_still=True)
        records.append({'family':family,'camera':camera,'path':scene.render.filepath,'size':[scene.render.resolution_x,scene.render.resolution_y],'seconds':round(time.time()-t,2)})
(dest/'render-manifest.json').write_text(json.dumps({'stage':stage,'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'engine':scene.render.engine,'images':records,'samples':0 if clay else 64,'same_studio_materials':True},indent=2)+'\n');print('V8_RENDER_READY',stage)
