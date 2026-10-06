"""Only move the existing bookshelf assembly to the packet-selected partition."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import sha,object_state,bounds
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
source=r/'OPTION_A_R4_THREE_STEP_READING_FITNESS_REVIEW_5.blend'
output=r/'OPTION_A_R4_BOOKCASE_SHORT_RAIL_REVIEW_6.blend'
assert sha(source)=='c396497077bc564d06d3c8855c731d977ca7dbdfc7cce104456f6bba16e78b20'
bpy.ops.wm.open_mainfile(filepath=str(source))
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
group=[o for o in bpy.context.scene.objects if o.name.startswith(('READING_5015_','READING_DISPLAY_SIDE_POST','READING_BOOK_'))]
assert len(group)==10,len(group)
cab=bpy.data.objects['READING_5015_SHORT_SLIDING_CABINET'];lo,hi=bounds(cab)
target_name='B11_G-DIN-LIV_HOST_GLASS2'
target=bpy.data.objects[target_name];tlo,thi=bounds(target)
center=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,0))
stand_off=.25
destination=Vector(((tlo[0]+thi[0])/2,thi[1]+stand_off+(hi[0]-lo[0])/2,0))
delta=Matrix.Translation(destination)@Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Translation(-center)
before={o.name:bounds(o) for o in group}
for o in group:o.matrix_world=delta@o.matrix_world
bpy.context.view_layer.update()
after={o.name:bounds(o) for o in group}
# Owner steering: shorten only the existing rail/support assembly in addition to bookcase relocation.
rail_y=4.770099945068359;radius=.02;rise=.15;run=.35;angle=math.atan(rise/run)
geometry=json.loads((r/'THREE_STEP_GEOMETRY.json').read_text())
def interpolate(line,y):
    for (x0,y0),(x1,y1) in zip(line,line[1:]):
        if y0<=y<=y1:return x0+(x1-x0)*(y-y0)/(y1-y0)
first=interpolate(geometry['front_lines'][0],rail_y);last=first+2*run
low_z=1.05-radius*math.cos(angle);high_z=1.35-radius*math.cos(angle)
extension=.10
points=[(first-extension,rail_y,low_z),(first,rail_y,low_z),(last,rail_y,high_z),(last+extension,rail_y,high_z)]
rail=bpy.data.objects['WAVE_WALL_HANDRAIL_900'];rail_material=rail.data.materials[0]
curve=bpy.data.curves.new('SHORT_THREE_STEP_HANDRAIL_PATH','CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=5;curve.use_fill_caps=True
spline=curve.splines.new('POLY');spline.points.add(3)
for p,co in zip(spline.points,points):p.co=(*co,1)
temp=bpy.data.objects.new('TEMP_SHORT_HANDRAIL',curve);bpy.context.scene.collection.objects.link(temp)
bpy.ops.object.select_all(action='DESELECT');temp.select_set(True);bpy.context.view_layer.objects.active=temp;bpy.ops.object.convert(target='MESH')
rail.data=temp.data.copy();rail.data.materials.append(rail_material);bpy.data.objects.remove(temp,do_unlink=True)
rail_changes={rail.name}
def replace_cylinder(name,a,b,rad):
    o=bpy.data.objects[name];m=o.data.materials[0];a,b=Vector(a),Vector(b);v=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=rad,depth=v.length,location=(a+b)/2);temp=bpy.context.object
    o.data=temp.data.copy();o.matrix_world=temp.matrix_world;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(m);bpy.data.objects.remove(temp,do_unlink=True);rail_changes.add(name)
for tag,p in [('LOWER',points[0]),('UPPER',points[-1])]:
    replace_cylinder('WAVE_HANDRAIL_'+tag+'_RETURN',p,(p[0],p[1],p[2]-.10),radius)
post_x=first-.05
replace_cylinder('WAVE_HANDRAIL_LOWER_POST',(post_x,rail_y,.02),(post_x,rail_y,low_z-radius),.015)
base=bpy.data.objects['WAVE_HANDRAIL_LOWER_BASE'];base.location.x=post_x;rail_changes.add(base.name)
def rail_height(x):
    return low_z if x<first else high_z if x>last else low_z+(x-first)*rise/run
for i,x in enumerate([5.98,6.20,6.41]):
    z=rail_height(x)-radius-.035
    plate=bpy.data.objects['WAVE_HANDRAIL_WALL_PLATE_'+str(i)];plate.location=(x,4.70409994506836,z);rail_changes.add(plate.name)
    replace_cylinder('WAVE_HANDRAIL_BRACKET_ARM_'+str(i),(x,4.70809994506836,z),(x,rail_y,z),.007)
    replace_cylinder('WAVE_HANDRAIL_BRACKET_UP_'+str(i),(x,rail_y,z),(x,rail_y,rail_height(x)-radius),.007)
bpy.context.view_layer.update()
for name,state in prior.items():
    now=object_state(bpy.data.objects[name])
    if name not in after and name not in rail_changes:assert now==state,name
    elif name in after:assert all(now[k]==state[k] for k in state if k!='matrix'),name
newlo,newhi=bounds(cab)
assert abs(newlo[1]-(thi[1]+stand_off))<1e-5
assert newlo[0]>=tlo[0]-1e-5 and newhi[0]<=thi[0]+1e-5
floor=bpy.data.objects['FLOOR_LOWER']
for x in [newlo[0]+.01,newhi[0]-.01]:
    for y in [newlo[1]+.01,newhi[1]-.01]:
        hit,p,n,face=floor.ray_cast(floor.matrix_world.inverted()@Vector((x,y,1)),Vector((0,0,-1)))
        assert hit and abs(p.z)<1e-5,'Bookcase must stand on actual lower floor'
def tree(o):return BVHTree.FromPolygons([tuple(o.matrix_world@v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-7)
near_names=['B11_G-DIN-LIV_HOST_GLASS2','STEP_0','STEP_1','STEP_2','WAVE_WALL_HANDRAIL_900','WAVE_HANDRAIL_LOWER_POST','WAVE_HANDRAIL_LOWER_BASE','WAVE_HANDRAIL_LOWER_RETURN','READING_3205A_PADDED_BENCH']
pairs=[]
for o in group:
    for name in near_names:
        if tree(o).overlap(tree(bpy.data.objects[name])):pairs.append([o.name,name])
assert not pairs,pairs
registry=json.loads((r/'spatial-canvas.bindings.json').read_text())
registry.update(registry_revision='16-bookcase-short-rail-review',source_revision='r4-bookcase-short-rail-review-6',source_locator=str(output))
bpy.ops.wm.save_as_mainfile(filepath=str(output));registry['source_sha256']=sha(output)
(r/'spatial-canvas.bindings.review6.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
saved={o.name:object_state(o) for o in bpy.context.scene.objects}
bpy.ops.wm.open_mainfile(filepath=str(output))
assert all(object_state(bpy.data.objects[name])==s for name,s in saved.items())
assert sha(source)=='c396497077bc564d06d3c8855c731d977ca7dbdfc7cce104456f6bba16e78b20'
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
report={'status':'HUMAN_REVIEW','output':str(output),'source':str(source),'output_sha256':sha(output),'target_entity_id':'ent_689bedcf7fb7490d9358a8078ab4a0cc','target_native_id':target_name,'target_is_partition_panel_not_new_wall':True,'bookcase_stand_off_m':stand_off,'reason':'Clear existing handrail lower extension;freestanding,no anchors to glass','rotated_degrees':-90,'moved_native_ids':list(after),'before':before,'after':after,'rail_changed_native_ids':sorted(rail_changes),'rail_horizontal_extent_m':last-first+2*extension,'previous_rail_horizontal_extent_m':1.65,'rail_extensions_m':extension,'rail_slope_degrees':math.degrees(angle),'rail_top_over_nosings_m':.9,'rail_points_source_xyz':points,'rail_design_note':'Owner-requested short domestic trial;100mm horizontal ends deviate from300mm accessibility-reference ends;not accessibility compliance certification','all_other_object_states_unchanged':True,'no_intersections_with_target_steps_rail_bench':True,'actual_floor_under_four_corners':True,'fresh_reopen_verified':True,'source_review5_and_frozen_r4_unchanged':True}
(r/'BOOKCASE_MOVE_REVIEW6_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['before','after']},ensure_ascii=False))
