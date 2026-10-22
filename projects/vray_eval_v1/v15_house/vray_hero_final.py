import bpy, json, time
from pathlib import Path
from vray_blender.engine.zmq_process import ZMQ
root = Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/vray-living-20261015')
TEX = root/'textures'
out = root/'B_vray'
s = bpy.context.scene

def mk_tex(nt, fn):
    tex = nt.nodes.new('VRayNodeMetaImageTexture')
    uvw = nt.nodes.new('VRayNodeUVWMapping')
    if 'Mapping' in uvw.outputs and 'Mapping' in tex.inputs:
        nt.links.new(uvw.outputs['Mapping'], tex.inputs['Mapping'])
    tex.texture.image = bpy.data.images.load(str(TEX/fn), check_existing=True)
    tout = next((o for o in tex.outputs if o.name in ('Color','Tex','Texture','Out')), tex.outputs[0] if tex.outputs else None)
    return tex, tout

LINEN = 'linen_warm.png'
def override_mat(m):
    nt = m.node_tree
    if not nt: return
    brdfs=[n for n in nt.nodes if n.bl_idname=='VRayNodeBRDFVRayMtl']
    if not brdfs: return
    name=m.name.upper()
    if any(k in name for k in ['GLASS','WINDOW','MIRROR','CHROME','STAINLESS','METAL','SCREEN','LED']): return
    rules=[
        (['MARBLE','QUARTZ','STONE','GRANITE'], 'owner_subtle_marble_1200x600.jpg'),
        (['RUG','CARPET'], 'geometric_rug_woven.jpg'),
        (['FLOOR','PALE_ASH_FLOOR'], 'pale_ash_floor_1200x1080.jpg'),
        (['ART_','ARTWORK','PICTURE','PAINTING'], 'selected_art_rectified.jpg'),
        (['ASH','WOOD','OAK','VENEER','WALNUT','TIMBER'], 'ash_veneer_diffuse_2k.jpg'),
        (['LINEN','FLAX','COTTON','SOFA','BEDDING','FABRIC','CURTAIN','DRAPE','SHEER','UPHOLST','PILLOW'], LINEN),
    ]
    imgf=next((i for keys,i in rules if any(k in name for k in keys)),None)
    if not imgf: return
    outp=next((n for n in nt.nodes if n.bl_idname=='VRayNodeOutputMaterial'),None)
    brdf=brdfs[0]
    if outp and outp.inputs['Material'].links:
        c=outp.inputs['Material'].links[0].from_node
        if c.bl_idname=='VRayNodeBRDFVRayMtl': brdf=c
    tex,tout=mk_tex(nt,imgf)
    targets=[brdf] if brdf.bl_idname=='VRayNodeBRDFVRayMtl' else brdfs
    for b in targets:
        dc=b.inputs.get('Diffuse Color')
        if dc is None: continue
        for l in list(dc.links): nt.links.remove(l)
        if tout: nt.links.new(tout,dc)

s.render.engine='VRAY_RENDER_RT'
for op in ['convert_materials','convert_world','convert_lights']:
    print(op, getattr(bpy.ops.vray,op)(), flush=True)
for m in bpy.data.materials: override_mat(m)

sam=s.vray.SettingsImageSampler
sam.type='3'; sam.progressive_maxSubdivs=48; sam.progressive_threshold=0.005; sam.progressive_maxTime=14.0
s.vray.SettingsGI.on=True; s.vray.SettingsOptions.light_doDefaultLights=False
s.render.resolution_x=1280; s.render.resolution_y=720; s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
ZMQ.ensureRunning()
t0=time.monotonic()
while not ZMQ.isRunning() and time.monotonic()-t0<120: time.sleep(0.5)
print('ZMQ_RUNNING:',ZMQ.isRunning(),flush=True)
for cam,fn in [('CAM_living_VIEW_01','B_hero_final'),('HOUSE_V1_LIVING_SOFA_DETAIL','B_closeup_final')]:
    s.camera=bpy.data.objects[cam]
    s.render.filepath=str(out/(fn+'.png'))
    st=time.monotonic()
    bpy.ops.render.render(write_still=True)
    print('FINAL_RENDER',fn,round(time.monotonic()-st,1),'exists',Path(s.render.filepath).exists(),flush=True)
bpy.ops.wm.quit_blender()
