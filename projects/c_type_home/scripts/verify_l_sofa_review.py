import bpy,json,sys,hashlib,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent));from restore_kitchen_divider_pier import object_state,bounds
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006')
src=r/'OPTION_A_R4_WAVE35_HANDRAIL_REVIEW_3.blend';dst=r/'OPTION_A_R4_L_SOFA_REVIEW_4.blend'
bpy.ops.wm.open_mainfile(filepath=str(src));prior={o.name:object_state(o) for o in bpy.context.scene.objects}
bpy.ops.wm.open_mainfile(filepath=str(dst))
changed={'B11_Rectangle046_CATALOG_00_00','B11_Rectangle047_CATALOG_00_00','B11_Rectangle049_CATALOG_00_00','B11_Circle_CATALOG_00_00'}
assert all(object_state(bpy.data.objects[n])==v for n,v in prior.items() if n not in changed)
sofa=bpy.data.objects['B11_Rectangle046_CATALOG_00_00']
bm=bmesh.new();bm.from_mesh(sofa.data);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free();assert nonmanifold==0
def tree(o):return BVHTree.FromPolygons([tuple(o.matrix_world@v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-6)
st=tree(sofa);collisions=[]
index=json.loads((r.parent/'wall_identity_r4_review/WALL_PART_INDEX.json').read_text())
for part in index['parts']:
    lo,hi=part['world_bounds']
    if hi[0]<3.4 or lo[0]>5.2 or hi[1]<8.95 or lo[1]>12.25 or lo[2]>.70:continue
    o=bpy.data.objects[part['native_id']]
    if st.overlap(tree(o)):collisions.append(o.name)
assert not collisions,collisions
# Both tables/retained chaise have actual mesh separation from the L, not just enclosing bounds.
for n in ['B11_Rectangle049_CATALOG_00_00','B11_Circle_CATALOG_00_00','B11_Rectangle048_CATALOG_00_00']:
    assert not st.overlap(tree(bpy.data.objects[n])),n
floor=bpy.data.objects['FLOOR_LOWER']
for n in ['B11_Circle_CATALOG_00_00','B11_Rectangle049_CATALOG_00_00']:
    lo,hi=bounds(bpy.data.objects[n]);start=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,1))
    hit,p,normal,face=floor.ray_cast(floor.matrix_world.inverted()@start,Vector((0,0,-1)))
    assert hit and abs(p.z)<1e-5,n
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert hashlib.sha256(frozen.read_bytes()).hexdigest()=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='fd0f603b433bde0cdf14d9b3f17357c07ff2ab8a6575e89c77dc0f2e148cffe2'
before=bounds(sofa)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(r/'proxy_l_sofa_4/interaction_proxy.glb'))
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(entities)==1000 and 'B11_Rectangle047_CATALOG_00_00' not in entities
assert entities['B11_Rectangle046_CATALOG_00_00']['global_id']=='ent_d25c02916e634c6b810c2d13e29a9a62'
actual=bounds(entities['B11_Rectangle046_CATALOG_00_00'])
assert all(abs(actual[j][i]-before[j][i])<1e-4 for i in range(3) for j in range(2))
report={'fresh_import_entity_count':len(entities),'stable_sofa_id_retained':True,'two_seat_retired_from_proxy':True,'ottoman_added':False,'unrelated_objects_unchanged':True,'sofa_manifold':nonmanifold==0,'no_sofa_wall_or_furniture_surface_collisions':True,'both_tables_on_lower_floor':True,'frozen_r4_and_review3_unchanged':True}
(r/'L_SOFA_FINAL_QA.json').write_text(json.dumps(report,indent=2));print('L_SOFA_FINAL_QA_PASS',json.dumps(report))
