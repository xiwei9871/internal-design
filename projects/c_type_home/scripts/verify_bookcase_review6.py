import bpy,json,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import bounds,sha
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
qa=json.loads((r/'BOOKCASE_MOVE_REVIEW6_QA.json').read_text())
manifest=json.loads((r/'proxy_review6/interaction_proxy.manifest.json').read_text())
assert sha(Path(manifest['source_resource']))==manifest['source_sha256']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(r/'proxy_review6/interaction_proxy.glb'))
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(entities)==1010
for name,wanted in qa['after'].items():
    got=bounds(entities[name]);assert all(abs(got[j][i]-wanted[j][i])<1e-4 for j in range(2) for i in range(3)),name
registry=json.loads((r/'spatial-canvas.bindings.review6.json').read_text())
for b in registry['bindings']:
    assert entities[b['native_id']]['global_id']==b['entity_id'],b['native_id']
rail=entities['WAVE_WALL_HANDRAIL_900'];lo,hi=bounds(rail)
assert hi[0]-lo[0]<.95
assert qa['rail_extensions_m']==.1 and abs(qa['rail_horizontal_extent_m']-.9)<1e-7
for name,z in [('STEP_0',.15),('STEP_1',.30),('STEP_2',.45)]:
    assert abs(bounds(entities[name])[1][2]-z)<1e-5
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
(r/'REVIEW6_FINAL_QA.json').write_text(json.dumps({'revision':manifest['source_revision'],'fresh_glb_entities':len(entities),'all_stable_ids_retained':True,'bookcase_bounds_match_blender':True,'rail_span_m':qa['rail_horizontal_extent_m'],'rail_extensions_m':.1,'three_existing_steps_unchanged':True,'frozen_r4_unchanged':True},indent=2))
print('REVIEW6_FINAL_QA_PASS')
