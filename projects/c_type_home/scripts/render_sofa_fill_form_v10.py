"""V7/V10 fixed camera comparison, same native cloth and V8 lighting."""
import bpy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_fill_form_v10'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
variant=args[0] if args else 'form1';stage=args[1] if len(args)>1 else 'clay'
RUN=OUT/variant;SOURCE=RUN/'SOFA_DIFFERENTIATED_FILL_V10.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;dest=RUN/stage;dest.mkdir(exist_ok=True)
if (dest/'render-manifest.json').exists():raise SystemExit('Preserved render batch exists; use a new stage output.')
clay=stage=='clay';scene.render.resolution_x=1000 if clay else 1500;scene.render.resolution_y=800 if clay else 1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.threads_mode='FIXED';scene.render.threads=2
if clay:
    scene.render.engine='BLENDER_WORKBENCH';s=scene.display.shading;s.light='STUDIO';s.color_type='SINGLE';s.single_color=(.53,.53,.53);s.show_shadows=True;s.show_cavity=False;s.show_specular_highlight=False;s.background_type='WORLD';scene.world.color=(.21,.23,.24)
else:
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.adaptive_threshold=.025;scene.cycles.use_denoising=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.cycles.denoising_use_gpu=True
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    scene.cycles.device='GPU'
records=[]
for family in ['V7','V10']:
    if variant=='delivery' and family=='V7':
        # The finishing step only changes V10. Reuse the already rendered V7
        # under identical comparison settings instead of rendering it again.
        previous=json.loads((OUT/'form2'/stage/'render-manifest.json').read_text())
        for entry in previous['images']:
            if entry['family']=='V7':
                assert Path(entry['path']).exists()
                records.append({**entry,'seconds':0,'reused':True,'origin_source_sha256':previous['source_sha256']})
        assert len(records)==3
        continue
    for f,name in [('V7','V7_COMPARISON_PAIR'),('V10','V10_FILL_FORM_PAIR')]:
        c=bpy.data.collections[name];c.hide_render=family!=f;c.hide_viewport=family!=f
    for camera in ['V6_FRONT','V6_SIDE','V6_THREE_QUARTER']:
        path=dest/(family+'_'+camera+'.png')
        if path.exists():raise RuntimeError('Do not overwrite render: '+str(path))
        scene.camera=bpy.data.objects[camera];scene.render.filepath=str(path);t=time.time();bpy.ops.render.render(write_still=True)
        records.append({'family':family,'camera':camera,'path':str(path),'size':[scene.render.resolution_x,scene.render.resolution_y],'seconds':round(time.time()-t,2),'reused':False})
(dest/'render-manifest.json').write_text(json.dumps({'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'stage':stage,'blender':bpy.app.version_string,'engine':scene.render.engine,'device':'WORKBENCH' if clay else 'METAL','samples':0 if clay else 64,'denoise':None if clay else 'OIDN GPU High Accurate','same_materials_studio_camera':True,'clay_cavity_enhancement':False,'images':records},indent=2)+'\n');print('V10_RENDER_READY',stage)
