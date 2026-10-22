"""V6/V7 controlled softness evidence: identical shape-view and studio settings."""
import bpy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_soft_pilot_v7'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];variant=args[0] if args else 'solve1';stage=args[1] if len(args)>1 else 'clay';RUN=OUT/variant
SOURCE=RUN/'SOFA_RELAXED_COVER_V7.blend';bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;dest=RUN/stage;dest.mkdir(exist_ok=True)
clay=stage=='clay';scene.render.resolution_x=1000 if clay else 1500;scene.render.resolution_y=800 if clay else 1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.threads_mode='FIXED';scene.render.threads=2
if clay:
    scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.color_type='SINGLE';sh.single_color=(.53,.53,.53);sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=False;sh.background_type='WORLD';scene.world.color=(.21,.23,.24)
else:
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.adaptive_threshold=.025;scene.cycles.use_denoising=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.cycles.denoising_use_gpu=True
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    scene.cycles.device='GPU'
records=[]
for family in ['V6','V7']:
    for f,n in [('V6','V6_COMPARISON_PAIR'),('V7','V7_RELAXED_PAIR')]:
        c=bpy.data.collections[n];c.hide_render=family!=f;c.hide_viewport=family!=f
    for camera in ['V6_FRONT','V6_SIDE','V6_THREE_QUARTER']:
        scene.camera=bpy.data.objects[camera];scene.render.filepath=str(dest/(family+'_'+camera+'.png'));start=time.time();bpy.ops.render.render(write_still=True)
        records.append({'family':family,'camera':camera,'path':scene.render.filepath,'size':[scene.render.resolution_x,scene.render.resolution_y],'seconds':round(time.time()-start,2)})
(dest/'render-manifest.json').write_text(json.dumps({'stage':stage,'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'engine':scene.render.engine,'samples':0 if clay else 64,'device':'WORKBENCH' if clay else 'METAL','denoise':None if clay else 'OIDN GPU High Accurate','same_materials_camera_lights':True,'images':records},indent=2)+'\n');print('V7_RENDER_READY',stage)
