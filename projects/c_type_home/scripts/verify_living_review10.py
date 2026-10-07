import bpy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from restore_kitchen_divider_pier import bounds,sha
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
qa=json.loads((r/'LONG_CABINET_CHAISE_REVIEW10_QA.json').read_text());manifest=json.loads((r/'proxy_review10/interaction_proxy.manifest.json').read_text())
assert sha(Path(qa['output']))==manifest['source_sha256']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(r/'proxy_review10/interaction_proxy.glb'))
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(entities)==1012
registry=json.loads((r/'spatial-canvas.bindings.review10.json').read_text())
assert all(entities[b['native_id']]['global_id']==b['entity_id'] for b in registry['bindings'])
for name,wanted in qa['after'].items():
    got=bounds(entities[name]);assert all(abs(got[j][i]-wanted[j][i])<1e-4 for i in range(3) for j in range(2)),name
assert sha(Path(qa['source']))=='804e38e122995bc2aa1793ba5071fa2a7202e24d7f921747fe5ee40e543cc34d'
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
report={'revision':manifest['source_revision'],'fresh_glb_entities':len(entities),'all_stable_ids_retained':True,'cabinet_and_chaise_bounds_match':True,'chaise_shift_m':.9,'cabinet_dimensions_m':[1.2,.35,.45],'review9_and_frozen_r4_unchanged':True}
(r/'REVIEW10_FINAL_QA.json').write_text(json.dumps(report,indent=2));print('REVIEW10_FINAL_QA_PASS')
