"""Render material-only A/B: same V7 geometry and V8 lights, sourced linen shader.

The test changes a microfiber surface layer, not the filling's mechanics.
"""
import bpy,hashlib,json,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_material_pilot_v9';RUN=OUT/'surface_test';RUN.mkdir(exist_ok=True)
SOURCE=ROOT/'design/sofa_soft_pilot_v8/render_diagnosis/V7_SAME_MESH_DIRECTIONAL_LIGHT_V8.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='cbed4cc4b34c9ebe5fc1bf8a388a860d620493b7f8bd609770499b967c37862f'
candidate=RUN/'SOFA_SURFACE_FIBER_TEST_V9.blend'
if candidate.exists() or (RUN/'RENDER_MANIFEST.json').exists():
    raise SystemExit('Preserved material pilot exists; use a new output version.')
records=[];parameters=[]
for case in ['A_original','B_microfiber']:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.render.resolution_x=1500;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.cycles.samples=64;scene.cycles.adaptive_threshold=.025;scene.cycles.use_denoising=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.cycles.denoising_use_gpu=True
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    scene.cycles.device='GPU'
    mat=bpy.data.materials['V5_NATURAL_FLAX_COTTON']
    if case=='B_microfiber':
        mat=mat.copy();mat.name='V9_MICROFIBER_SURFACE_TEST'
        p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        p.inputs['Sheen Weight'].default_value=.5;p.inputs['Sheen Roughness'].default_value=.8
        for name in ['V7_SEAT_COMPLETE_COVER','V7_BACK_COMPLETE_COVER']:
            o=bpy.data.objects[name]
            for i in range(len(o.data.materials)):o.data.materials[i]=mat
    p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    assert p.inputs['Subsurface Weight'].default_value==0 and p.inputs['Coat Weight'].default_value==0 and p.inputs['Transmission Weight'].default_value==0
    parameters.append({'case':case,'material':mat.name,'sheen_weight':p.inputs['Sheen Weight'].default_value,'sheen_roughness':p.inputs['Sheen Roughness'].default_value,'SSS':0,'coat':0,'transmission':0})
    data=bpy.data.cameras.new('V9_FABRIC_CLOSEUP');camera=bpy.data.objects.new('V9_FABRIC_CLOSEUP',data);bpy.data.collections['V6_STUDIO'].objects.link(camera)
    camera.location=(.82,-.80,.92);camera.rotation_euler=(Vector((.18,-.05,.42))-camera.location).to_track_quat('-Z','Y').to_euler();data.lens=70;data.clip_start=.01
    scene.camera=bpy.data.objects['V6_THREE_QUARTER']
    if case=='B_microfiber':bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
    for view in ['V6_THREE_QUARTER','V9_FABRIC_CLOSEUP']:
        if case=='A_original' and view=='V6_THREE_QUARTER':
            path=ROOT/'design/sofa_soft_pilot_v8/render_diagnosis/directional_fabric_V6_THREE_QUARTER.png'
            assert path.exists();records.append({'case':case,'camera':view,'path':str(path),'size':[1500,1200],'reused':True,'seconds':0});continue
        scene.camera=bpy.data.objects[view];path=RUN/(case+'_'+view+'.png')
        if path.exists():raise RuntimeError('Preserved render exists: '+str(path))
        scene.render.filepath=str(path);t=time.time();bpy.ops.render.render(write_still=True)
        records.append({'case':case,'camera':view,'path':str(path),'size':[1500,1200],'reused':False,'seconds':round(time.time()-t,2)})
report={'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'candidate':str(candidate),'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'engine':'CYCLES','device':'METAL','samples':64,'denoising':'OIDN GPU High Accurate','images':records,'material_parameters':parameters,'allowed_material_changes':['Sheen Weight','Sheen Roughness'],'maps_color_roughness_normal_ior_uv_unchanged':True,'mesh_light_exposure_changes':0,'filling_mechanics_simulated':False,'owner_accepted':False}
(RUN/'RENDER_MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n');print('V9_MATERIAL_TEST_READY',json.dumps(report))
