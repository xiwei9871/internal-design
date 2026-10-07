"""Packet-targeted furniture refinement:1200x350x450 cabinet and900mm south chaise shift."""
import bpy,json,sys
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import sha,object_state,bounds
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
source=r/'OPTION_A_R4_UPPER_BOOKCASE_SIDE_CABINET_CHAISE_REVIEW_9.blend'
output=r/'OPTION_A_R4_LONG_SIDE_CABINET_CHAISE_SOUTH_REVIEW_10.blend'
expected='804e38e122995bc2aa1793ba5071fa2a7202e24d7f921747fe5ee40e543cc34d'
assert sha(source)==expected
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.view_layer.update()
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
chaise_name='B11_Rectangle048_CATALOG_00_00';cab_name='L_SOFA_5015_SHALLOW_SIDE_CABINET'
chaise=bpy.data.objects[chaise_name];cab=bpy.data.objects[cab_name]
before={o.name:bounds(o) for o in [chaise,cab]}
chaise.matrix_world=Matrix.Translation((0,-.9,0))@chaise.matrix_world
# Cabinet becomes a deliberately proportioned long low study, not a manufacturer SKU.
lo=[4.0,7.55,0];hi=[5.2,7.90,.45]
material=cab.data.materials[0];vertices=[];faces=[]
def box(a,b):
    x0,y0,z0=a;x1,y1,z1=b;offset=len(vertices)
    vertices.extend([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)])
    faces.extend([tuple(offset+i for i in f) for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
box((4.,7.55,0),(5.2,7.9,.025))
box((4.,7.55,.425),(5.2,7.9,.45))
for x in [4.,5.18]:box((x,7.55,.025),(x+.02,7.9,.425))
box((4.02,7.884,.025),(5.18,7.9,.425))
box((4.59,7.568,.025),(4.61,7.884,.425))
box((4.02,7.555,.032),(4.63,7.570,.418))
box((4.63,7.575,.032),(5.18,7.590,.418))
inverse=cab.matrix_world.inverted();mesh=bpy.data.meshes.new('LONG_SOFA_SIDE_CABINET_REVIEW10')
mesh.from_pydata([inverse@Vector(p) for p in vertices],[],faces);mesh.update();mesh.materials.append(material);cab.data=mesh
bpy.context.view_layer.update()
after={o.name:bounds(o) for o in [chaise,cab]}
for name,state in prior.items():
    now=object_state(bpy.data.objects[name])
    if name not in [cab_name,chaise_name]:assert now==state,name
    elif name==chaise_name:
        assert all(now[k]==state[k] for k in state if k!='matrix')
        for j in range(2):
            for i in range(3):assert abs(after[name][j][i]-before[name][j][i]-([0,-.9,0][i]))<1e-5
    else:assert all(now[k]==state[k] for k in state if k!='mesh')
for j in range(2):
    for i in range(3):assert abs(after[cab_name][j][i]-[lo,hi][j][i])<1e-5
floor=bpy.data.objects['FLOOR_LOWER']
for obj in [cab,chaise]:
    a,b=bounds(obj)
    for x in [a[0]+.015,b[0]-.015]:
        for y in [a[1]+.015,b[1]-.015]:
            hit,p,n,f=floor.ray_cast(floor.matrix_world.inverted()@Vector((x,y,1)),Vector((0,0,-1)))
            assert hit and abs(p.z)<1e-5,(obj.name,x,y)
def tree(o):return BVHTree.FromPolygons([tuple(o.matrix_world@v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-7)
checks=['B11_Rectangle046_CATALOG_00_00','B11_Rectangle049_CATALOG_00_00','B11_Circle_CATALOG_00_00','STEP_0','STEP_1','STEP_2','READING_5015_SHORT_SLIDING_CABINET','READING_3205A_PADDED_BENCH']
idx=json.loads((r.parent/'wall_identity_r4_review/WALL_PART_INDEX.json').read_text())
for part in idx['parts']:
    a,b=part['world_bounds']
    if b[0]>=4 and a[0]<=6.4 and b[1]>=7.55 and a[1]<=11.96 and a[2]<.85:checks.append(part['native_id'])
collisions=[]
for o in [cab,chaise]:
    for name in set(checks):
        if tree(o).overlap(tree(bpy.data.objects[name])):collisions.append([o.name,name])
assert not collisions,collisions
assert not tree(cab).overlap(tree(chaise))
registry=json.loads((r/'spatial-canvas.bindings.review9.json').read_text())
registry.update(registry_revision='20-long-side-cabinet-chaise-south',source_revision='r4-long-side-cabinet-chaise-south-review-10',source_locator=str(output))
bpy.ops.wm.save_as_mainfile(filepath=str(output));registry['source_sha256']=sha(output)
(r/'spatial-canvas.bindings.review10.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
saved={o.name:object_state(o) for o in bpy.context.scene.objects}
bpy.ops.wm.open_mainfile(filepath=str(output));assert all(object_state(bpy.data.objects[n])==state for n,state in saved.items())
assert sha(source)==expected
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
coffee=after[chaise_name][0][1]-bounds(bpy.data.objects['B11_Rectangle049_CATALOG_00_00'])[1][1]
report={'status':'HUMAN_REVIEW','output':str(output),'source':str(source),'output_sha256':sha(output),'before':before,'after':after,'cabinet_size_m':[1.2,.35,.45],'cabinet_is_custom_study_not_catalog5015_SKU':True,'chaise_source_translation_m':[0,-.9,0],'cabinet_to_sofa_gap_m':.05,'chaise_to_coffee_north_south_gap_m':coffee,'north_space_gain_m':.9,'no_surface_intersections':True,'all_other_object_states_unchanged':True,'balcony_geometry_and_appliances_unchanged':True,'actual_floor_below_both_furniture':True,'fresh_reopen_verified':True,'review9_and_frozen_r4_unchanged':True}
(r/'LONG_CABINET_CHAISE_REVIEW10_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['before','after']},ensure_ascii=False))
