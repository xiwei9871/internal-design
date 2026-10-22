import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
m=json.loads((R/'proxy_review14/interaction_proxy.manifest.json').read_text());r=json.loads((R/'spatial-canvas.bindings.review14.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'proxy_review14/interaction_proxy.glb'))
bpy.context.view_layer.update()
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(entities)==m['entity_count']==len(r['bindings'])
assert all(entities[b['native_id']]['global_id']==b['entity_id'] for b in r['bindings'])
f=entities['B11_Rectangle039_BODY'];coords=[f.matrix_world@Vector(v) for v in f.bound_box]
span=[max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)]
assert abs(span[0]-.60)<1e-4 and abs(span[1]-1.20)<1e-4,span
assert not any(n.startswith(('SUNROOM_FREEZER_FLIP','SUNROOM_FREEZER_WORKTOP')) for n in entities)
assert len([n for n in entities if n.startswith('SUNROOM_INTEGRATED_UPPER_DOOR_')])==5
assert hashlib.sha256(Path(m['source_resource']).read_bytes()).hexdigest()==m['source_sha256']
report={'fresh_glb_entities':len(entities),'all_stable_ids_match':True,'freezer_source_span_m':span,'no_extra_freezer_cover':True,'upper_fronts_count':5,'source_hash_matches':True}
(R/'REVIEW14_EXPORT_EVIDENCE.json').write_text(json.dumps(report,indent=2)+'\n')
print('FRESH_IMPORT',json.dumps(report))

