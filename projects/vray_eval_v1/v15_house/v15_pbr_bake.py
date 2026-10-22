import bpy, json, time
from pathlib import Path
root = Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
TEX = root/'textures'
s = bpy.context.scene

bpy.ops.file.unpack_all(method='WRITE_LOCAL')

def mk_tex(nt, fn):
    tex = nt.nodes.new('VRayNodeMetaImageTexture')
    uvw = nt.nodes.new('VRayNodeUVWMapping')
    if 'Mapping' in uvw.outputs and 'Mapping' in tex.inputs:
        nt.links.new(uvw.outputs['Mapping'], tex.inputs['Mapping'])
    tex.texture.image = bpy.data.images.load(str(TEX/fn), check_existing=True)
    tout = next((o for o in tex.outputs if o.name in ('Color','Tex','Texture','Out')), tex.outputs[0] if tex.outputs else None)
    return tex, tout

def wire_pbr(nt, brdf, diff_fn, nrm_fn=None, rough_fn=None):
    tex,tout = mk_tex(nt, diff_fn)
    dc = brdf.inputs.get('Diffuse Color')
    if dc is not None and tout:
        for l in list(dc.links): nt.links.remove(l)
        nt.links.new(tout, dc)
    if nrm_fn:
        ntex,ntout = mk_tex(nt, nrm_fn)
        bump = nt.nodes.new('VRayNodeTexNormalBump')
        nmap_out = next((o for o in ntex.outputs if o.name=='Color'), ntout)
        if 'Map' in bump.inputs and nmap_out:
            nt.links.new(nmap_out, bump.inputs['Map'])
        bout = next((o for o in bump.outputs if o.name in ('Color','Bump','Out')), bump.outputs[0] if bump.outputs else None)
        binp = brdf.inputs.get('Bump Map')
        if binp is not None and bout:
            for l in list(binp.links): nt.links.remove(l)
            nt.links.new(bout, binp)
    if rough_fn:
        rtex,rout = mk_tex(nt, rough_fn)
        comb = nt.nodes.new('VRayNodeTexCombineFloat')
        inten = next((o for o in rtex.outputs if o.name=='Intensity'), rout)
        if 'Texture' in comb.inputs and inten:
            nt.links.new(inten, comb.inputs['Texture'])
        cout = next((o for o in comb.outputs if o.name in ('Float','Out','Result')), comb.outputs[0] if comb.outputs else None)
        ginp = brdf.inputs.get('Reflection Glossiness')
        if ginp is not None and cout:
            for l in list(ginp.links): nt.links.remove(l)
            nt.links.new(cout, ginp)

s.render.engine='VRAY_RENDER_RT'
from vray_blender.engine.zmq_process import ZMQ
ZMQ.ensureRunning()
t0=time.monotonic()
while not ZMQ.isRunning() and time.monotonic()-t0<120: time.sleep(0.5)
print('ZMQ',ZMQ.isRunning(),flush=True)
for op in ['convert_materials','convert_world','convert_lights']:
    print(op, getattr(bpy.ops.vray,op)(), flush=True)

LINEN=('linen_warm.png','rough_linen_normal_4k.png','rough_linen_roughness_4k.png')
ASH=('ash_veneer_diffuse_2k.jpg','ash_veneer_normal_2k.png','ash_veneer_roughness_2k.png')
FLOOR=('pale_ash_floor_1200x1080.jpg','normal.png','roughness.png')
count={'pbr':0,'diff':0}
wired=[]
for m in bpy.data.materials:
    nt=m.node_tree
    if not nt: continue
    brdfs=[n for n in nt.nodes if n.bl_idname=='VRayNodeBRDFVRayMtl']
    if not brdfs: continue
    name=m.name.upper()
    if any(k in name for k in ['GLASS','WINDOW','MIRROR','CHROME','STAINLESS','METAL','SCREEN','LED']): continue
    rules=[(['MARBLE','QUARTZ','STONE','GRANITE'], ('owner_subtle_marble_1200x600.jpg',None,None)),
        (['RUG','CARPET'], ('geometric_rug_woven.jpg',None,None)),
        (['FLOOR','PALE_ASH_FLOOR'], FLOOR),
        (['ART_','ARTWORK','PICTURE','PAINTING'], ('selected_art_rectified.jpg',None,None)),
        (['ASH','WOOD','OAK','VENEER','WALNUT','TIMBER'], ASH),
        (['LINEN','FLAX','COTTON','SOFA','BEDDING','FABRIC','CURTAIN','DRAPE','SHEER','UPHOLST','PILLOW'], LINEN)]
    pick=next((p for keys,p in rules if any(k in name for k in keys)),None)
    if not pick: continue
    outp=next((n for n in nt.nodes if n.bl_idname=='VRayNodeOutputMaterial'),None)
    brdf=brdfs[0]
    if outp and outp.inputs['Material'].links:
        c=outp.inputs['Material'].links[0].from_node
        if c.bl_idname=='VRayNodeBRDFVRayMtl': brdf=c
    targets=[brdf] if brdf.bl_idname=='VRayNodeBRDFVRayMtl' else brdfs
    for b in targets:
        wire_pbr(nt, b, *pick)
    count['pbr' if pick[1] else 'diff']+=1
    wired.append(m.name)
print('PBR_COUNT',json.dumps(count),flush=True)
print('WIRED',len(wired),wired[:20],flush=True)
out = root/'V15_PBR.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(out))
print('SAVED', out, flush=True)
bpy.ops.wm.quit_blender()
