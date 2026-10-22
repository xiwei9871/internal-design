"""Make the verified GLB compatible with Spatial Canvas's texture-free V0.1 contract.

Only presentation fields/unused texture coordinates are stripped. Geometry,
node transforms and stable IDs stay exactly as in the verified reimport.
"""
import json,struct,hashlib,shutil
from pathlib import Path
APP=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas');S=APP/'task-output/c_type_v11';O=APP/'task-output/c_type_v11_canvas';F=O/'full';F.mkdir(parents=True,exist_ok=True)
assert not (F/'interaction_proxy.glb').exists(),'Preserve existing exports'
src=S/'full/interaction_proxy.glb';raw=src.read_bytes();length,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a;j=json.loads(raw[20:20+length]);offset=20+length;binarylen,binarykind=struct.unpack_from('<II',raw,offset);assert binarykind==0x004e4942;binary=raw[offset+8:offset+8+binarylen]
materials=[]
for m in j.get('materials',[]):
    n=m.get('name','');p=m.setdefault('pbrMetallicRoughness',{})
    if 'UNIFIED_PALE_ASH_FLOOR' in n:p['baseColorFactor']=[.42,.325,.215,1];p['roughnessFactor']=.46
    elif 'OWNER_WHITE_SUBTLE_MARBLE' in n:p['baseColorFactor']=[.84,.83,.81,1];p['roughnessFactor']=.38
    elif 'WARM_WHITE_LATEX' in n:p['baseColorFactor']=[.78,.76,.71,1];p['roughnessFactor']=.86
    materials.append({'name':n,'base_color':p.get('baseColorFactor',[1,1,1,1])})
def clean(obj):
    if isinstance(obj,dict):
        for k in list(obj):
            if k=='extensions' or k.endswith('Texture') or k.startswith('TEXCOORD_'):del obj[k]
            else:clean(obj[k])
    elif isinstance(obj,list):
        for v in obj:clean(v)
clean(j)
for k in ['images','textures','samplers','extensionsUsed','extensionsRequired']:j.pop(k,None)
data=json.dumps(j,separators=(',',':')).encode();data+=b' '*((-len(data))%4);payload=struct.pack('<III',0x46546c67,2,12+8+len(data)+8+len(binary))+struct.pack('<II',len(data),0x4e4f534a)+data+struct.pack('<II',len(binary),0x004e4942)+binary
dest=F/'interaction_proxy.glb';dest.write_bytes(payload)
# Same binding snapshot and native IDs; locator in manifest points to its copied bytes.
regsrc=S/'spatial-canvas.bindings.json';regdst=O/regsrc.name;shutil.copyfile(regsrc,regdst)
m=json.loads((S/'full/interaction_proxy.manifest.json').read_text());m['extensions']['spatial_canvas.blender']['bindings']['locator']=str(regdst)
m['extensions']['spatial_canvas.presentation'].update(textures=False,profile='V11 unified source colors, V0.1 compatible',note='Texture-free interaction proxy. Full wood grain and owner marble texture remain in the linked Blender source and review renders.')
(F/'interaction_proxy.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
for n in ['spatial-canvas.project.json','spatial-canvas.spaces.json']:shutil.copyfile(S/'full'/n,F/n)
pose=json.loads((S/'owner-view-preset.json').read_text());pose['bindings']['locator']=str(regdst);(O/'owner-view-preset.json').write_text(json.dumps(pose,indent=2)+'\n')
verification=json.loads((S/'full/EXPORT_EVIDENCE.json').read_text());verification.update({'presentation':'texture-free V0.1 proxy; full textures in Blender','source_textured_glb':str(src),'source_textured_glb_sha256':hashlib.sha256(raw).hexdigest(),'proxy_sha256':hashlib.sha256(payload).hexdigest(),'proxy_bytes':len(payload),'geometry_binary_unchanged':True,'stable_node_identity_and_transform_json_unchanged':True,'materials':materials})
verification.pop('portable_finish_images',None)
(F/'EXPORT_EVIDENCE.json').write_text(json.dumps(verification,indent=2)+'\n')
dep=json.loads((S/'DEPLOYMENT.json').read_text());dep.update({'proxy':str(dest),'manifest':str(F/'interaction_proxy.manifest.json'),'bindings':str(regdst),'view_preset':str(O/'owner-view-preset.json'),'presentation':'V0.1 texture-free; Blender retains full finishes'})
(O/'DEPLOYMENT.json').write_text(json.dumps(dep,indent=2)+'\n');print('CANVAS_FLAT_V11',m['entity_count'],len(payload),'binary preserved',binarylen)
