import bpy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import bounds,sha
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
qa=json.loads((r/'SIDE_CABINET_CHAISE_REVIEW9_QA.json').read_text())
book=json.loads((r/'BOOKCASE_UPPER_WALL_REVIEW8_QA.json').read_text())
bpy.ops.wm.open_mainfile(filepath=qa['output'])
chaise=bpy.data.objects['B11_Rectangle048_CATALOG_00_00']
original=json.loads((r.parent/'living_furniture_review_20261006'/'LIVING_FURNITURE_QA.json').read_text())['after'][chaise.name]
actual=bounds(chaise)
assert all(abs(actual[j][i]-original[j][i])<1e-4 for i in range(3) for j in range(2)),[actual,original]
assert chaise.visible_get()
assert abs(bounds(bpy.data.objects['READING_5015_SHORT_SLIDING_CABINET'])[0][2]-.45)<1e-5
manifest=json.loads((r/'proxy_review9/interaction_proxy.manifest.json').read_text())
assert sha(Path(manifest['source_resource']))==manifest['source_sha256']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(r/'proxy_review9/interaction_proxy.glb'))
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(entities)==1012
registry=json.loads((r/'spatial-canvas.bindings.review9.json').read_text())
assert all(entities[b['native_id']]['global_id']==b['entity_id'] for b in registry['bindings'])
for name,wanted in {**book['after'],qa['side_cabinet_native_id']:qa['side_cabinet_bounds'],qa['chaise_restored_native_id']:original}.items():
    got=bounds(entities[name]);assert all(abs(got[j][i]-wanted[j][i])<1e-4 for j in range(2) for i in range(3)),name
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
report={'revision':manifest['source_revision'],'fresh_glb_entities':len(entities),'all_ids_retained':True,'chaise_visible_at_original_accepted_north_station':True,'bookcase_on_actual_upper_platform':True,'extra_side_cabinet_bounds_match':True,'frozen_r4_unchanged':True,'fitness_machine_fit_verified':False}
(r/'REVIEW9_FINAL_QA.json').write_text(json.dumps(report,indent=2));print('REVIEW9_FINAL_QA_PASS',json.dumps(report))
