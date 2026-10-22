"""Read-only V13 Interaction Proxy using the established frozen-sidecar adapter."""
import bpy,json,hashlib,sys,uuid
from pathlib import Path
from argparse import Namespace
R=Path(__file__).resolve().parents[1];APP=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas');D=R/'design/fridge_finish_v13';OUT=APP/'task-output/c_type_v13/full';OUT.mkdir(parents=True,exist_ok=True)
a=json.loads((D/'BUILD_AUDIT.json').read_text());S=Path(a['output']);SHA=a['sha256'];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(S)==SHA
bpy.ops.wm.open_mainfile(filepath=str(S));sys.path.insert(0,str(APP/'adapters/blender'));import export_proxy
from common import eligible_objects
from bindings import validate_registry
old=json.loads((APP/'task-output/c_type_v12/spatial-canvas.bindings.json').read_text());known={b['native_id']:b for b in old['bindings']}
objects=eligible_objects();bindings=[];kept=0
for o in objects:
 if o.name in known:
  b=dict(known[o.name]);kept+=1
 else:b={'entity_id':'ent_'+uuid.uuid4().hex,'adapter':'blender','native_id':o.name,'semantic_type':'unassigned','room_id':'unassigned','authority_level':'DERIVED_DESIGN_MODEL'}
 # Model is a derived design, external frozen policy only protects the snapshot.
 b['authority_level']='DERIVED_DESIGN_MODEL';bindings.append(b)
reg={'schema':'spatial-canvas.bindings.v1','registry_id':'bindings_'+uuid.uuid4().hex,'registry_revision':'v13-spatial-export-1','design_id':old['design_id'],'source_resource_id':'c_type_fridge_finish_v13','source_revision':'fridge-finish-v13-review-1','source_sha256':SHA,'source_locator':str(S),'source_authority':'frozen','source_frame':old['source_frame'],'bindings':bindings}
registry=OUT.parent/'spatial-canvas.bindings.json';assert not registry.exists(),'Preserved registry exists';validate_registry(reg);registry.write_text(json.dumps(reg,indent=2)+'\n')
ordinary=export_proxy.assign_flat_colors
def simple_glass(mesh,entity,cache,owned,counts,mode,source):
 original=list(mesh.materials);indices=[f.material_index for f in mesh.polygons];glass_slots={i:m for i,m in enumerate(original) if m and m.name in ['V8_COLORLESS_CLEAR_ARCHITECTURAL_GLASS','V8_COLORLESS_PRIVACY_FROSTED_GLASS']}
 ordinary(mesh,entity,cache,owned,counts,mode,source)
 if not glass_slots:return
 for i,m in glass_slots.items():
  frost='FROSTED' in m.name;key=('v13_glass','frost' if frost else 'clear');mat=cache.get(key)
  if mat is None:
   mat=bpy.data.materials.new('SC_V13_'+('FROSTED_GLASS' if frost else 'CLEAR_GLASS'));mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');c=(.88,.9,.9,.68) if frost else (.91,.96,.98,.14);mat.diffuse_color=c;p.inputs['Base Color'].default_value=c;p.inputs['Alpha'].default_value=c[3];p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=.7 if frost else .18;mat.surface_render_method='DITHERED';mat.use_backface_culling=False;owned.append(mat);cache[key]=mat
  mesh.materials[i]=mat
 for f,idx in zip(mesh.polygons,indices):f.material_index=idx
 counts['proxy_privacy_glass' if any('FROSTED' in m.name for m in glass_slots.values()) else 'proxy_clear_glass']=counts.get('proxy_privacy_glass' if any('FROSTED' in m.name for m in glass_slots.values()) else 'proxy_clear_glass',0)+1
export_proxy.assign_flat_colors=simple_glass
m=export_proxy.export_proxy(Namespace(output=str(OUT),bindings=str(registry),scope='full',room_id=None,global_ids=None,collection=None,color_mode='source-flat',source_resource_id=reg['source_resource_id'],source_revision=reg['source_revision']))
m['extensions']['spatial_canvas.presentation'].update(opaque=False,profile='V9 simplified source colors / alpha glass',textures=False,note='Interaction Proxy, not Cycles material fidelity; clear14pct / frost68pct opacity for selection readability')
m['extensions']['spatial_canvas.review']={'status':'HUMAN_REVIEW','source_design_authority':'DERIVED_DESIGN_MODEL','source_version':'V13','default_ceiling_hidden':True,'old_stable_ids_retained':kept}
(OUT/'interaction_proxy.manifest.json').write_text(json.dumps(m,indent=2)+'\n');assert sha(S)==SHA
# Fresh import verifies source-linked identities and whole replacement objects.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(OUT/'interaction_proxy.glb'));entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')};assert len(entities)==m['entity_count']==len(bindings)
for b in bindings:assert entities[b['native_id']]['global_id']==b['entity_id']
for n in ['HUNYUAN_V3_COUPLE_BED','HUNYUAN_V3_COUPLE_TV_CONSOLE','HUNYUAN_V3_LIVING_L_SOFA','HUNYUAN_V12_MOTHER_BED','HOUSE_V1_V7_SLIDER_GLASS_PANE']:assert n in entities,n
assert not any(n.startswith(('CEILING_','V7_CEILING_')) for n in entities)
assert 'HOUSE_V1_MOTHER_bedcover' not in entities and 'READING_3205A_PADDED_BENCH' not in entities
evidence={'status':'PASS_EXPORTED_PROXY_REIMPORT','source':str(S),'source_sha256':SHA,'manifest':str(OUT/'interaction_proxy.manifest.json'),'glb':str(OUT/'interaction_proxy.glb'),'entity_count':len(entities),'old_stable_ids_retained':kept,'source_preserved':True,'ceilings_omitted_from_overview':True,'native_ids_roundtrip':True,'proxy_bytes':(OUT/'interaction_proxy.glb').stat().st_size}
(OUT/'EXPORT_EVIDENCE.json').write_text(json.dumps(evidence,indent=2)+'\n');print('SPATIAL_V13_EXPORT',json.dumps(evidence))
