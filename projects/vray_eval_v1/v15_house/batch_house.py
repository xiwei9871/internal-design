import bpy, json, time, re
from pathlib import Path
from vray_blender.engine.zmq_process import ZMQ
root = Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
TEX = root/'textures'; TEX.mkdir(exist_ok=True)
OUT = root/'renders'; OUT.mkdir(exist_ok=True)
s = bpy.context.scene

bpy.ops.file.unpack_all(method='WRITE_LOCAL')

import numpy as np
src = bpy.data.images.load(str(TEX/'rough_linen_diffuse_4k.jpg'))
px = np.array(src.pixels[:]).reshape(-1,4)[:, :3]
scale = np.array([0.90,0.87,0.80]) / px.mean(axis=0)
rgba = np.ones((px.shape[0],4),dtype=np.float32); rgba[:,:3] = np.clip(px*scale,0,1)
img = bpy.data.images.new('linen_warm', width=src.size[0], height=src.size[1], alpha=False)
img.pixels = rgba.flatten(); img.filepath_raw=str(TEX/'linen_warm.png'); img.file_format='PNG'; img.save()
LINEN='linen_warm.png'

def mk_tex(nt, fn):
    tex = nt.nodes.new('VRayNodeMetaImageTexture')
    uvw = nt.nodes.new('VRayNodeUVWMapping')
    if 'Mapping' in uvw.outputs and 'Mapping' in tex.inputs:
        nt.links.new(uvw.outputs['Mapping'], tex.inputs['Mapping'])
    tex.texture.image = bpy.data.images.load(str(TEX/fn), check_existing=True)
    tout = next((o for o in tex.outputs if o.name in ('Color','Tex','Texture','Out')), tex.outputs[0] if tex.outputs else None)
    return tex, tout

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

cams=[o.name for o in bpy.data.objects if o.type=='CAMERA' and re.match(r'CAM_.+_VIEW_\d+', o.name)]
def keyf(n):
    g = re.match(r'CAM_(.+)_VIEW_(\d+)',n)
    return (int(g.group(2)), g.group(1))  # VIEW_01 of every room first
cams.sort(key=keyf)
print('CAM_QUEUE', len(cams), json.dumps(cams), flush=True)

manifest=[]
for cname in cams:
    room=re.match(r'CAM_(.+)_VIEW_(\d+)',cname)
    fn=f"{room.group(1)}_view{room.group(2)}"
    path=OUT/(fn+'.png')
    if path.exists():
        print('SKIP',fn,flush=True); continue
    s.camera=bpy.data.objects[cname]
    s.render.filepath=str(path)
    st=time.monotonic()
    try:
        bpy.ops.render.render(write_still=True)
        ok=path.exists()
    except Exception as e:
        ok=False; print('RENDER_FAIL',fn,repr(e)[:150],flush=True)
    rec={'cam':cname,'file':fn+'.png','seconds':round(time.monotonic()-st,1),'exists':ok}
    manifest.append(rec)
    print('DONE',json.dumps(rec),flush=True)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=1))
bpy.ops.wm.quit_blender()
