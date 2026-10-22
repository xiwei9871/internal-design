"""Established frozen-sidecar exporter; retain only owner finish UVs/textures for this export."""
import bpy,json,hashlib,sys,uuid,types
from pathlib import Path
from argparse import Namespace
R=Path(__file__).resolve().parents[1];APP=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas');D=R/'design/finishes_v11';OUT=APP/'task-output/c_type_v11/full';OUT.mkdir(parents=True,exist_ok=True)
a=json.loads((D/'BUILD_AUDIT.json').read_text());S=Path(a['output']);SHA=a['sha256'];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(S)==SHA
bpy.ops.wm.open_mainfile(filepath=str(S));sys.path.insert(0,str(APP/'adapters/blender'))
# Reuse the complete adapter, changing only this export's documented UV switch.
# Never patch the app's default texture-free exporter or its protocol contract.
module_path=APP/'adapters/blender/export_proxy.py';code=module_path.read_text();assert code.count('export_texcoords=False')==1
export_proxy=types.ModuleType('finish_v11_proxy');export_proxy.__file__=str(module_path)
exec(compile(code.replace('export_texcoords=False','export_texcoords=True'),str(module_path),'exec'),export_proxy.__dict__)
from common import eligible_objects
from bindings import validate_registry
old=json.loads((APP/'task-output/c_type_v9/spatial-canvas.bindings.json').read_text());known={b['native_id']:b for b in old['bindings']}
objects=eligible_objects();bindings=[];kept=0
for o in objects:
    if o.name in known:b=dict(known[o.name]);kept+=1
    else:b={'entity_id':'ent_'+uuid.uuid4().hex,'adapter':'blender','native_id':o.name,'semantic_type':'unassigned','room_id':'unassigned','authority_level':'DERIVED_DESIGN_MODEL'}
    b['authority_level']='DERIVED_DESIGN_MODEL';bindings.append(b)
assert 'READING_3205A_PADDED_BENCH' not in {b['native_id'] for b in bindings}
reg={'schema':'spatial-canvas.bindings.v1','registry_id':'bindings_'+uuid.uuid4().hex,'registry_revision':'v11-spatial-export-1','design_id':old['design_id'],'source_resource_id':'c_type_finishes_reading_v11','source_revision':'finishes-reading-v11-review-1','source_sha256':SHA,'source_locator':str(S),'source_authority':'frozen','source_frame':old['source_frame'],'bindings':bindings}
registry=OUT.parent/'spatial-canvas.bindings.json';assert not registry.exists(),'Preserve old registry';validate_registry(reg);registry.write_text(json.dumps(reg,indent=2)+'\n')
ordinary=export_proxy.assign_flat_colors
def finish_and_glass(mesh,entity,cache,owned,counts,mode,source):
    original=list(mesh.materials);indices=[f.material_index for f in mesh.polygons]
    finishes={i:m for i,m in enumerate(original) if m and m.name.startswith(('V11_UNIFIED_','V11_OWNER_WHITE_','V11_WARM_WHITE_'))}
    glasses={i:m for i,m in enumerate(original) if m and m.name in ['V8_COLORLESS_CLEAR_ARCHITECTURAL_GLASS','V8_COLORLESS_PRIVACY_FROSTED_GLASS']}
    ordinary(mesh,entity,cache,owned,counts,mode,source)
    for i,m in finishes.items():
        key=('owner_finish',m.name);mat=cache.get(key)
        if mat is None:
            mat=m.copy();mat.name='SC_'+m.name;owned.append(mat);cache[key]=mat
            # Portable PBR: retain image color and constant roughness, omit paint noise.
            p=mat.node_tree.nodes.get('Principled BSDF')
            for link in list(p.inputs['Normal'].links):mat.node_tree.links.remove(link)
        mesh.materials[i]=mat
    for i,m in glasses.items():
        frost='FROSTED' in m.name;key=('v11_glass',frost);mat=cache.get(key)
        if mat is None:
            mat=bpy.data.materials.new('SC_V11_'+('FROSTED_GLASS' if frost else 'CLEAR_GLASS'));mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');c=(.88,.9,.9,.68) if frost else (.91,.96,.98,.14);mat.diffuse_color=c;p.inputs['Base Color'].default_value=c;p.inputs['Alpha'].default_value=c[3];p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=.7 if frost else .18;mat.surface_render_method='DITHERED';mat.use_backface_culling=False;owned.append(mat);cache[key]=mat
        mesh.materials[i]=mat
    for f,idx in zip(mesh.polygons,indices):f.material_index=idx
    # Other entities remain cheap source-flat interaction geometry.
    for layer in list(mesh.uv_layers):
        if not finishes or layer.name!='V11_FinishUV':mesh.uv_layers.remove(layer)
    if finishes and mesh.uv_layers:
        mesh.uv_layers.active_index=0;mesh.uv_layers[0].active_render=True
    if finishes:counts['owner_finish_textured_entities']=counts.get('owner_finish_textured_entities',0)+1
export_proxy.assign_flat_colors=finish_and_glass
m=export_proxy.export_proxy(Namespace(output=str(OUT),bindings=str(registry),scope='full',room_id=None,global_ids=None,collection=None,color_mode='source-flat',source_resource_id=reg['source_resource_id'],source_revision=reg['source_revision']))
m['extensions']['spatial_canvas.presentation'].update(opaque=False,profile='V11 owner floor/wall finishes plus source-flat furnishings / alpha glass',textures=True,note='Only unified floor and600x1200 tile color images retained; other furnishings are interaction-proxy simplifications, not Cycles fidelity')
m['extensions']['spatial_canvas.review']={'status':'HUMAN_REVIEW','source_design_authority':'DERIVED_DESIGN_MODEL','source_version':'V11','default_ceiling_hidden':True,'old_stable_ids_retained':kept}
(OUT/'interaction_proxy.manifest.json').write_text(json.dumps(m,indent=2)+'\n');assert sha(S)==SHA
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(OUT/'interaction_proxy.glb'));entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')};assert len(entities)==m['entity_count']==len(bindings)
for b in bindings:assert entities[b['native_id']]['global_id']==b['entity_id']
assert 'READING_3205A_PADDED_BENCH' not in entities
assert not any(n.startswith(('CEILING_','V7_CEILING_')) for n in entities)
for n in ['HUNYUAN_V3_COUPLE_BED','HUNYUAN_V3_COUPLE_TV_CONSOLE','HUNYUAN_V3_LIVING_L_SOFA','READING_5015_SHORT_SLIDING_CABINET']:assert n in entities
images={n.image.name for mat in bpy.data.materials if mat.use_nodes for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image};assert any('pale_ash_floor' in n for n in images) and any('owner_subtle_marble' in n for n in images),images
e={'status':'PASS_EXPORTED_PROXY_REIMPORT','source':str(S),'source_sha256':SHA,'entity_count':len(entities),'old_stable_ids_retained':kept,'retired_duplicate_id':known.get('READING_3205A_PADDED_BENCH',{}).get('entity_id'),'source_preserved':True,'ceilings_omitted_from_overview':True,'native_ids_roundtrip':True,'portable_finish_images':sorted(images),'proxy_bytes':(OUT/'interaction_proxy.glb').stat().st_size,'adapter_source_sha256':sha(module_path),'task_only_adapter_change':'export_texcoords=True and retain only V11 finish UVs'}
(OUT/'EXPORT_EVIDENCE.json').write_text(json.dumps(e,indent=2)+'\n');print('SPATIAL_V11_EXPORT',json.dumps(e))
