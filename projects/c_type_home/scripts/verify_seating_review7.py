import bpy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import bounds,sha
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
qa=json.loads((r/'SEATING_SOUTH_REVIEW7_QA.json').read_text())
manifest=json.loads((r/'proxy_review7/interaction_proxy.manifest.json').read_text())
assert sha(Path(manifest['source_resource']))==manifest['source_sha256']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(r/'proxy_review7/interaction_proxy.glb'))
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(entities)==1010
for name,wanted in qa['after'].items():
    got=bounds(entities[name]);assert all(abs(got[j][i]-wanted[j][i])<1e-4 for j in range(2) for i in range(3)),name
    assert entities[name]['global_id']==qa['selected_native_global_ids'][name]
registry=json.loads((r/'spatial-canvas.bindings.review7.json').read_text())
assert all(entities[b['native_id']]['global_id']==b['entity_id'] for b in registry['bindings'])
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
report={'revision':manifest['source_revision'],'fresh_glb_entities':len(entities),'all_stable_ids_retained':True,'three_moved_bounds_match_blender':True,'source_delta_m':[0,-1,0],'only_selected_source_transforms_changed':qa['all_other_object_states_unchanged'],'frozen_r4_unchanged':True}
(r/'REVIEW7_FINAL_QA.json').write_text(json.dumps(report,indent=2));print('REVIEW7_FINAL_QA_PASS')
