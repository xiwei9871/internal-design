"""Appropriate first-layout gates; no plumbing/fabrication compliance assertion."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import sha,bounds,object_state
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
qa=json.loads((r/'SUNROOM_REVIEW11_QA.json').read_text())
bpy.ops.wm.open_mainfile(filepath=qa['source']);bpy.context.view_layer.update()
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
bpy.ops.wm.open_mainfile(filepath=qa['output']);bpy.context.view_layer.update()
changed=set(qa['moved_native_ids'])
assert all(object_state(bpy.data.objects[n])==s for n,s in prior.items() if n not in changed)
for n in changed:
    got=object_state(bpy.data.objects[n])
    assert all(got[k]==prior[n][k] for k in prior[n] if k!='matrix'),n
def tree(o):return BVHTree.FromPolygons([tuple(o.matrix_world@v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-7)
index=json.loads((r.parent/'wall_identity_r4_review/WALL_PART_INDEX.json').read_text())
wallnames=[p['native_id'] for p in index['parts'] if p['world_bounds'][1][0]>=8.03 and p['world_bounds'][0][0]<=12.9 and p['world_bounds'][1][1]>=11.13 and p['world_bounds'][0][1]<=13.37]
wallnames+=['NORTH_BALCONY_GLASS_NORTH_A','NORTH_BALCONY_GLASS_NORTH_B','NORTH_BALCONY_GLASS_EAST','DOOR_V2_NBALC_SINGLE_GLASS']
fixtures=[bpy.data.objects[n] for n in qa['new_objects']]
pairs=[]
for o in fixtures:
    for name in wallnames:
        if tree(o).overlap(tree(bpy.data.objects[name])):pairs.append([o.name,name])
# Appliances must not intersect cabinet finishes. Contained body/door detail within its
# own original appliance is intentional and is never read as a new physical relation.
for n in changed:
    o=bpy.data.objects[n]
    for other in fixtures:
        if tree(o).overlap(tree(other)):pairs.append([n,other.name])
assert not pairs,pairs
fa,fb=bounds(bpy.data.objects['B11_Rectangle039_BODY'])
fixed=[]
for o in fixtures:
    if 'PLANT_' in o.name and 'LEDGE' not in o.name:continue
    a,b=bounds(o)
    if min(b[0],fb[0])-max(a[0],fa[0])>1e-5 and min(b[1],fb[1])-max(a[1],fa[1])>1e-5 and b[2]>.85:fixed.append(o.name)
assert not fixed,fixed
assert qa['central_lane_seat_to_north_ledge_m']>=1.10
# Preserve a clear rectangle inward of the existing western balcony entry.
entry_min=[7.95,11.855,0];entry_max=[8.85,12.65,2.4]
entry_hits=[]
for o in fixtures+[bpy.data.objects[n] for n in changed]:
    a,b=bounds(o)
    if all(min(b[i],entry_max[i])-max(a[i],entry_min[i])>1e-5 for i in range(3)):entry_hits.append(o.name)
assert not entry_hits,entry_hits
manifest=json.loads((r/'proxy_review11/interaction_proxy.manifest.json').read_text())
assert sha(Path(qa['output']))==manifest['source_sha256']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(r/'proxy_review11/interaction_proxy.glb'))
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(entities)==manifest['entity_count']==1062
registry=json.loads((r/'spatial-canvas.bindings.review11.json').read_text())
assert all(entities[b['native_id']]['global_id']==b['entity_id'] for b in registry['bindings'])
for name,wanted in qa['after'].items():
    got=bounds(entities[name]);assert all(abs(got[j][i]-wanted[j][i])<1e-4 for j in range(2) for i in range(3)),name
assert sha(Path(qa['source']))==qa['source_sha256']
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
report={'revision':manifest['source_revision'],'fresh_glb_entities':len(entities),'all_stable_ids_retained':True,'moved_appliance_meshes_unchanged':True,'no_new_fixture_wall_window_or_appliance_surface_collisions':True,'freezer_top_has_no_fixed_obstruction':True,'entry_clear_rectangle_m':[.9,.795],'seat_ledge_central_lane_m':qa['central_lane_seat_to_north_ledge_m'],'review10_and_frozen_r4_unchanged':True,'utilities_and_manufacturer_clearances_verified':False}
(r/'REVIEW11_FINAL_QA.json').write_text(json.dumps(report,indent=2));print('REVIEW11_FINAL_QA_PASS',json.dumps(report))
