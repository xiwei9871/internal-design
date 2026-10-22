import bpy, time, sys, json, hashlib, traceback
from pathlib import Path
from vray_blender.engine.zmq_process import ZMQ

OUT = Path('/Users/xiwei/interior_design/projects/vray_eval_v1')
TEX = Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/oak_wood_planks')
try:
    scn = bpy.context.scene
    scn.render.engine = 'VRAY_RENDER_RT'
    scn.render.resolution_x, scn.render.resolution_y = 2500, 1727
    scn.render.resolution_percentage = 100
    scn.render.image_settings.file_format = 'PNG'

    # World: single sky env, keep original sky params
    w = scn.world; nt = w.node_tree
    orig_sky = next((n for n in nt.nodes if n.bl_idname=='ShaderNodeTexSky'), None)
    sky_p = {}
    if orig_sky:
        sky_p = {p: getattr(orig_sky, p) for p in ('sky_type','sun_elevation','sun_rotation','altitude','air_density','dust_density','ozone_density') if hasattr(orig_sky, p)}
    nt.nodes.clear()
    n_out  = nt.nodes.new('ShaderNodeOutputWorld'); n_out.location=(400,0)
    n_bg   = nt.nodes.new('ShaderNodeBackground');  n_bg.location=(200,0)
    n_sky  = nt.nodes.new('ShaderNodeTexSky');      n_sky.location=(-200,0)
    for k,v in sky_p.items():
        try: setattr(n_sky, k, v)
        except Exception: pass
    n_bg.inputs['Strength'].default_value = 1.0
    nt.links.new(n_sky.outputs[0], n_bg.inputs['Color'])
    nt.links.new(n_bg.outputs[0], n_out.inputs['Surface'])

    # Material: real oak plank PBR set on Generated coords (exporter handles TexImage+Generated)
    m = bpy.data.materials.get('Natural oak floor')
    mt = m.node_tree
    bsdf = next(n for n in mt.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
    texc = mt.nodes.new('ShaderNodeTexCoord')
    mapn = mt.nodes.new('ShaderNodeMapping')
    mapn.inputs['Scale'].default_value = (6.0, 6.0, 6.0)   # ~2.1m tiles over the 12.6m floor
    mt.links.new(texc.outputs['Generated'], mapn.inputs['Vector'])
    img_d = mt.nodes.new('ShaderNodeTexImage'); img_d.image = bpy.data.images.load(str(TEX/'oak_wood_planks_diffuse_4k.jpg'))
    mt.links.new(mapn.outputs['Vector'], img_d.inputs['Vector'])
    mt.links.new(img_d.outputs['Color'], bsdf.inputs['Base Color'])
    img_r = mt.nodes.new('ShaderNodeTexImage'); img_r.image = bpy.data.images.load(str(TEX/'oak_wood_planks_roughness_4k.png'))
    img_r.image.colorspace_settings.name = 'Non-Color'
    mt.links.new(mapn.outputs['Vector'], img_r.inputs['Vector'])
    mt.links.new(img_r.outputs['Color'], bsdf.inputs['Roughness'])
    img_n = mt.nodes.new('ShaderNodeTexImage'); img_n.image = bpy.data.images.load(str(TEX/'oak_wood_planks_normal_4k.png'))
    img_n.image.colorspace_settings.name = 'Non-Color'
    nrm = mt.nodes.new('ShaderNodeNormalMap')
    mt.links.new(mapn.outputs['Vector'], img_n.inputs['Vector'])
    mt.links.new(img_n.outputs['Color'], nrm.inputs['Color'])
    mt.links.new(nrm.outputs['Normal'], bsdf.inputs['Normal'])

    # Camera: physical camera + EV exposure
    cam = bpy.data.objects['Camera_living']
    cam.data.vray.use_physical = True
    cam.data.vray.CameraPhysical.exposure = '2'
    cam.data.vray.CameraPhysical.exposure_value = 12.0
    scn.camera = cam

    scn.vray.SettingsColorMapping.adaptation_only = '0'
    scn.vray.SettingsImageSampler.type = '3'
    scn.vray.SettingsImageSampler.progressive_maxTime = 5.0
    scn.vray.SettingsImageSampler.progressive_threshold = 0.005

    ZMQ.ensureRunning()
    t0=time.time()
    while not ZMQ.isRunning() and time.time()-t0 < 90: time.sleep(0.5)
    print('ZMQ_RUNNING:', ZMQ.isRunning(), flush=True)

    fp = OUT/'living_vray_full4.png'
    scn.render.filepath = str(fp)
    t=time.time()
    bpy.ops.render.render(write_still=True)
    info={'key':'living','engine':'vray-v4-EV12-oaktex-full','seconds':round(time.time()-t,1),
          'sha256':hashlib.sha256(fp.read_bytes()).hexdigest() if fp.exists() else None}
    (OUT/'living_vray_full4.json').write_text(json.dumps(info,indent=2))
    print('VRAY_VIEW_DONE', json.dumps(info), flush=True)
except Exception:
    traceback.print_exc()
finally:
    bpy.ops.wm.quit_blender()
