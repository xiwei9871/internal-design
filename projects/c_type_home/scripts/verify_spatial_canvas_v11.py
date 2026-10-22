"""Read-only fresh-import verification, including source-linked identity and portable images."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];APP=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas');D=APP/'task-output/c_type_v11';F=D/'full'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
reg=json.loads((D/'spatial-canvas.bindings.json').read_text());m=json.loads((F/'interaction_proxy.manifest.json').read_text());old=json.loads((APP/'task-output/c_type_v9/spatial-canvas.bindings.json').read_text());known={b['native_id']:b['entity_id'] for b in old['bindings']}
assert sha(reg['source_locator'])==reg['source_sha256']==m['source_sha256']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(F/'interaction_proxy.glb'),loglevel=2)
objects={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')};assert len(objects)==m['entity_count']==len(reg['bindings'])
for b in reg['bindings']:
    assert objects[b['native_id']]['global_id']==b['entity_id']
    if b['native_id'] in known:assert b['entity_id']==known[b['native_id']]
assert 'READING_3205A_PADDED_BENCH' not in objects
assert not any(n.startswith(('CEILING_','V7_CEILING_')) for n in objects)
for n in ['HUNYUAN_V3_COUPLE_BED','HUNYUAN_V3_COUPLE_TV_CONSOLE','HUNYUAN_V3_LIVING_L_SOFA','READING_5015_SHORT_SLIDING_CABINET']:assert n in objects
images={n.image.name for mat in bpy.data.materials if mat.use_nodes for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image};assert any('pale_ash_floor' in n for n in images) and any('owner_subtle_marble' in n for n in images)
floors={}
for n,o in objects.items():
    if n.startswith(('PRESENTATION_FLOOR_','PRESENTATION_TILE_')):
        assert o.data.uv_layers,n
        floors[n]=o.data.materials[0].name
r={'status':'PASS_EXPORTED_PROXY_REIMPORT','source':reg['source_locator'],'source_sha256':reg['source_sha256'],'entity_count':len(objects),'old_stable_ids_retained':sum(n in known for n in objects),'source_preserved':True,'ceilings_omitted_from_overview':True,'duplicate_bench_omitted':True,'native_ids_roundtrip':True,'portable_finish_images':sorted(images),'portable_floor_materials':floors,'proxy_bytes':(F/'interaction_proxy.glb').stat().st_size,'adapter_source_sha256':sha(APP/'adapters/blender/export_proxy.py'),'task_only_adapter_change':'export_texcoords=True and retain only V11 finish UVs'}
(F/'EXPORT_EVIDENCE.json').write_text(json.dumps(r,indent=2)+'\n');print('V11_PROXY_VERIFY',json.dumps(r))
