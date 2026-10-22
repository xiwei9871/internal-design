"""Same V7 geometry: isolate Workbench enhancement, cloth and light direction.

No geometry edits, no fabric preset guessing, no changed exposure or grading.
"""
import bpy,hashlib,json,sys,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_soft_pilot_v8/render_diagnosis';OUT.mkdir(exist_ok=True)
SOURCE=ROOT/'design/sofa_soft_pilot_v7/local_final/SOFA_RELAXED_COVER_V7.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='5bb0f004a9501bff61a017975cf65c8205f46e3af3a39d9a83c91096db46ec4f'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];mode=args[0] if args else 'diagnostic'

def config(scene):
    scene.render.engine='CYCLES';scene.render.resolution_x=1500;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.cycles.samples=64;scene.cycles.adaptive_threshold=.025;scene.cycles.use_denoising=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.cycles.denoising_use_gpu=True
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    scene.cycles.device='GPU'

def render(scene,case,camera):
    scene.camera=bpy.data.objects[camera];p=OUT/(case+'_'+camera+'.png')
    if p.exists():raise RuntimeError('Preserved render exists: '+str(p))
    scene.render.filepath=str(p);t=time.time();bpy.ops.render.render(write_still=True)
    return {'case':case,'camera':camera,'path':str(p),'size':[1500,1200],'seconds':round(time.time()-t,2)}

candidate=OUT/'V7_SAME_MESH_DIRECTIONAL_LIGHT_V8.blend'
if mode=='diagnostic':
    if candidate.exists():raise SystemExit('Preserved diagnosis exists; use a new version.')
    records=[]
    for case in ['cycles_neutral','directional_fabric']:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;config(scene)
        if case=='cycles_neutral':
            mat=bpy.data.materials.new('V8_DIAGNOSTIC_18_PERCENT_GRAY');mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.18,.18,.18,1);p.inputs['Roughness'].default_value=.8;p.inputs['Sheen Weight'].default_value=0
            for name in ['V7_SEAT_COMPLETE_COVER','V7_BACK_COMPLETE_COVER']:
                obj=bpy.data.objects[name]
                for i in range(len(obj.data.materials)):obj.data.materials[i]=mat
        else:
            # Window-like side light, reduced all-around fill. Material is exact V7.
            key=bpy.data.objects['V6_KEY'];key.location=(-2.4,-.3,1.65);key.data.energy=320;key.data.size=1.0;key.rotation_euler=(Vector((0,0,.50))-key.location).to_track_quat('-Z','Y').to_euler()
            bpy.data.objects['V6_FILL'].data.energy=55
            bpy.data.objects['V6_RIM'].data.energy=80
            scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18
            scene.camera=bpy.data.objects['V6_THREE_QUARTER']
            bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
        records.append(render(scene,case,'V6_THREE_QUARTER'))
    report={'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'candidate':str(candidate),'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'original_fabric':str(ROOT/'design/sofa_soft_pilot_v7/local_final/fabric/V7_V6_THREE_QUARTER.png'),'original_workbench':str(ROOT/'design/sofa_soft_pilot_v7/local_final/clay/V7_V6_THREE_QUARTER.png'),'images':records,'mesh_changes':0,'fabric_changes_in_directional_case':0,'camera_exposure_grade_changes':0,'lighting_changes':{'key_location':[-2.4,-.3,1.65],'key_power':320,'key_size':1,'fill_power':55,'rim_power':80,'world_strength':.18},'physical_site_light_claim':False}
    (OUT/'DIAGNOSIS_MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n');print('V8_DIAGNOSIS_READY',json.dumps(report))
elif mode=='workbench_control':
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
    scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    s=scene.display.shading;s.light='STUDIO';s.color_type='SINGLE';s.single_color=(.53,.53,.53);s.show_shadows=True;s.show_cavity=False;s.cavity_type='BOTH';s.show_specular_highlight=False;s.background_type='WORLD';scene.world.color=(.21,.23,.24)
    scene.camera=bpy.data.objects['V6_THREE_QUARTER'];p=OUT/'workbench_no_cavity_V6_THREE_QUARTER.png'
    if p.exists():raise SystemExit('Preserved Workbench control exists.')
    scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    (OUT/'WORKBENCH_CONTROL.json').write_text(json.dumps({'image':str(p),'same_geometry_studio_shading_as_original_workbench':True,'only_workbench_change':'show_cavity false','native_size':[1000,800]},indent=2)+'\n')
    print('V8_WORKBENCH_CONTROL_READY',p)
else:
    assert mode=='delivery'
    a=json.loads((OUT/'DIAGNOSIS_MANIFEST.json').read_text());assert hashlib.sha256(candidate.read_bytes()).hexdigest()==a['candidate_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(candidate));scene=bpy.context.scene;config(scene)
    records=[r for r in a['images'] if r['case']=='directional_fabric']
    for camera in ['V6_FRONT','V6_SIDE']:records.append(render(scene,'directional_fabric',camera))
    (OUT/'DELIVERY_MANIFEST.json').write_text(json.dumps({'source':str(candidate),'source_sha256':a['candidate_sha256'],'images':records,'geometry_materials_unchanged':True,'engine':'CYCLES','device':'METAL','samples':64,'denoise':'OIDN GPU High Accurate'},indent=2)+'\n');print('V8_DELIVERY_READY',json.dumps(records))
