"""Review14: longitudinal east-wall freezer, restored ledge, integrated laundry upper storage."""
import bpy, json, hashlib, uuid, sys, math
from pathlib import Path
from mathutils import Vector, Matrix
R=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
SRC=R/'OPTION_A_R4_SUNROOM_CABINET_FREEZER_SWAP_REVIEW_13.blend'
OUT=R/'OPTION_A_R4_SUNROOM_INTEGRATED_LAUNDRY_REVIEW_14.blend'
REV='r4-sunroom-integrated-laundry-review-14'
FROZEN=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(SRC)=='ac9532d3a39ccd8dd6dd22d7a7b829f0113f2736c921a42637f5a27c506fa7f2'
assert sha(FROZEN)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import object_state
bpy.ops.wm.open_mainfile(filepath=str(SRC)); bpy.context.view_layer.update()
reg=json.loads((R/'spatial-canvas.bindings.review13.json').read_text())
before={o.name:object_state(o) for o in bpy.context.scene.objects}
old_names=set(before)
# Restore known, exact review12 appliances/ledge rather than rebuilding their geometry.
restore_names=['B11_Rectangle039_BODY','B11_Rectangle039_LID_SEAM',
 'SUNROOM_NORTH_PLANT_LEDGE_BASE','SUNROOM_NORTH_PLANT_LEDGE_TOP',
 'SUNROOM_COMPACT_TWO_SEAT_SOFA']
restore_names += [b['native_id'] for b in reg['bindings'] if b['native_id'].startswith('SUNROOM_PLANT_')]
with bpy.data.libraries.load(str(R/'OPTION_A_R4_SUNROOM_DOOR_CLEAR_SOFA_REVIEW_12.blend'),link=False) as (data_from,data_to):
 data_to.objects=list(restore_names)
for ref in data_to.objects:
 bpy.context.scene.collection.objects.link(ref)
bpy.context.view_layer.update()
for name,ref in zip(restore_names,data_to.objects):
 obj=bpy.data.objects[name]
 obj.matrix_world=ref.matrix_world.copy()
 # source mesh proportions are restored, including the full-length ledge.
 obj.data=ref.data.copy()
 bpy.data.objects.remove(ref,do_unlink=True)
# Long axis along source Y (east wall); no cover above the chest freezer.
for name in ['B11_Rectangle039_BODY','B11_Rectangle039_LID_SEAM']:
 obj=bpy.data.objects[name]; obj.matrix_world=Matrix.Translation((0,.60,0))@obj.matrix_world
# Keep low cabinet south of freezer with independent fixed counter.
for name in ['SUNROOM_EAST_LOW_STORAGE','SUNROOM_EAST_STORAGE_COUNTER']:
 bpy.data.objects[name].location.y-=.12
# Remove obsolete freezer enclosure trim. It should remain a free appliance bay.
retired=[b['native_id'] for b in reg['bindings'] if b['native_id'].startswith(
 ('SUNROOM_FREEZER_SIDE_FINISH_','SUNROOM_FREEZER_FRONT_PLINTH','SUNROOM_FREEZER_VENT_SLAT_'))]
for name in retired:
 obj=bpy.data.objects.get(name)
 if obj: bpy.data.objects.remove(obj,do_unlink=True)

warm=bpy.data.materials['BALCONY_WARM_WHITE']
wood=bpy.data.materials['BALCONY_PALE_ASH']
dark=bpy.data.materials['BALCONY_DARK_BRACKETS']
new=[]
def box(name,a,b,mat,bevel=.002):
 bpy.ops.mesh.primitive_cube_add(size=1,location=[(a[i]+b[i])/2 for i in range(3)])
 o=bpy.context.object; o.name=name; o.scale=[b[i]-a[i] for i in range(3)]
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('Edge finish','BEVEL');mod.width=bevel;mod.segments=3
  bpy.ops.object.modifier_apply(modifier=mod.name)
 o.data.materials.append(mat);return o
def cylinder(name,center,radius,depth,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=depth,location=center,rotation=(math.pi/2,0,0))
 o=bpy.context.object;o.name=name;o.data.materials.append(mat);return o
def replace_box(name,a,b,mat):
 o=bpy.data.objects[name];tmp=box('TEMP_'+name,a,b,mat)
 o.data=tmp.data.copy();o.matrix_world=tmp.matrix_world.copy()
 bpy.data.objects.remove(tmp,do_unlink=True); return o
def replace_join(name,parts):
 bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join()
 tmp=bpy.context.object
 o=bpy.data.objects[name];o.data=tmp.data.copy();o.matrix_world=tmp.matrix_world.copy()
 bpy.data.objects.remove(tmp,do_unlink=True);return o
def carcass(name,x0,x1,y0,y1,z0,z1):
 t=.018
 parts=[box('TEMP_bottom',(x0,y0,z0),(x1,y1,z0+t),warm),
 box('TEMP_top',(x0,y0,z1-t),(x1,y1,z1),warm),
 box('TEMP_left',(x0,y0,z0+t),(x0+t,y1,z1-t),warm),
 box('TEMP_right',(x1-t,y0,z0+t),(x1,y1,z1-t),warm),
 box('TEMP_back',(x0+t,y0,z0+t),(x1-t,y0+.012,z1-t),wood),
 box('TEMP_shelf',(x0+t,y0+.012,(z0+z1)/2),(x1-t,y1-.018,(z0+z1)/2+.018),warm)]
 return replace_join(name,parts)
# Kitchen-style continuous upper cabinets. The laundry tower remains open below.
# Matching 700mm depth, 2600mm top datum, 1800mm cabinet bottom and flat ash doors.
replace_box('SUNROOM_LAUNDRY_WEST_PANEL',(8.035,11.135,.015),(8.075,11.835,2.60),warm)
replace_box('SUNROOM_LAUNDRY_EAST_PANEL',(8.725,11.135,.015),(8.765,11.835,1.80),warm)
replace_box('SUNROOM_LAUNDRY_HEADER',(8.075,11.135,1.775),(8.725,11.835,1.80),wood)
over=carcass('SUNROOM_LAUNDRY_OVERHEAD',8.035,8.765,11.135,11.835,1.80,2.60)
upper=carcass('SUNROOM_SOFA_REAR_HIGH_CABINET',8.765,10.32,11.135,11.835,1.80,2.60)
upper['design_status']='HUMAN_REVIEW'
upper['door_mode']='hinged_upper_fronts'
upper['depth_m']=.70
upper['clearance_note']='Upper storage above sofa, bottom at1.80m; continuous with laundry cabinet.'
over['design_status']='HUMAN_REVIEW'
# Individual functional fronts keep readable seams and selectable object identities.
for i,(x0,x1) in enumerate([(8.055,8.397),(8.401,8.745),(8.785,9.281),(9.285,9.781),(9.785,10.30)]):
 o=box('SUNROOM_INTEGRATED_UPPER_DOOR_'+str(i),(x0,11.838,1.820),(x1,11.856,2.578),wood,.004)
 o['design_status']='HUMAN_REVIEW';o['opening_mode']='hinged_upper_front';new.append((o,'cabinet_door'))
 # A recessed finger-pull profile reads as kitchen cabinetry.
 h=box('SUNROOM_INTEGRATED_UPPER_PULL_'+str(i),(x0+.07,11.857,1.829),(x1-.07,11.862,1.838),dark,.001)
 new.append((h,'cabinet_handle'))
# Continuous crown and underside trim provide one visual datum.
for name,a,b in [
 ('SUNROOM_INTEGRATED_CROWN',(8.035,11.135,2.60),(10.32,11.856,2.64)),
 ('SUNROOM_INTEGRATED_UNDERSIDE',(8.765,11.135,1.775),(10.32,11.835,1.80))]:
 o=box(name,a,b,warm);new.append((o,'cabinet'))
# Wall mounting rails are within carcass depth; appliance loads never support cabinetry.
for name,x0,x1 in [('SUNROOM_INTEGRATED_WALL_RAIL_A',8.06,8.74),('SUNROOM_INTEGRATED_WALL_RAIL_B',8.79,10.29)]:
 o=box(name,(x0,11.147,2.49),(x1,11.161,2.54),dark)
 new.append((o,'cabinet_hardware'))
# Existing appliance windows were recessed inside the solid appliance boxes.
# Reveal those original doors and add a simple bezel/control face for readable
# generic washer/dryer placeholders, preserving their original stable IDs.
for i,z in enumerate([.425,1.275]):
 door=bpy.data.objects['B11_Rectangle040_DOOR_'+str(i)]
 door.location.y+=.03
 door.data=door.data.copy();door.data.materials.clear();door.data.materials.append(dark)
 rim=cylinder('SUNROOM_LAUNDRY_DOOR_BEZEL_'+str(i),(8.40,11.784,z),.205,.024,warm)
 new.append((rim,'appliance_part'))
 window=cylinder('SUNROOM_LAUNDRY_DOOR_WINDOW_'+str(i),(8.40,11.801,z),.166,.009,dark)
 new.append((window,'appliance_part'))
 panel=box('SUNROOM_LAUNDRY_CONTROL_'+str(i),(8.16,11.773,z+.279),(8.64,11.788,z+.342),warm,.005)
 new.append((panel,'appliance_part'))
 display=box('SUNROOM_LAUNDRY_DISPLAY_'+str(i),(8.18,11.789,z+.289),(8.30,11.794,z+.332),dark,.002)
 new.append((display,'appliance_part'))
bpy.context.view_layer.update()
changed=set(restore_names+['SUNROOM_EAST_LOW_STORAGE','SUNROOM_EAST_STORAGE_COUNTER',
 'SUNROOM_LAUNDRY_WEST_PANEL','SUNROOM_LAUNDRY_EAST_PANEL','SUNROOM_LAUNDRY_HEADER',
 'SUNROOM_LAUNDRY_OVERHEAD','SUNROOM_SOFA_REAR_HIGH_CABINET','B11_Rectangle040_DOOR_0','B11_Rectangle040_DOOR_1']+retired)
unrelated_diff=[n for n,s in before.items() if n not in changed and object_state(bpy.data.objects[n])!=s]
assert not unrelated_diff,unrelated_diff
def bounds(o):
 cs=[o.matrix_world@Vector(c) for c in o.bound_box]
 return [[min(v[i] for v in cs) for i in range(3)],[max(v[i] for v in cs) for i in range(3)]]
freezer=bounds(bpy.data.objects['B11_Rectangle039_BODY'])
print('FREEZER_MEASURED',freezer)
assert abs(freezer[1][0]-freezer[0][0]-.60)<1e-5
assert abs(freezer[1][1]-freezer[0][1]-1.20)<1e-5
sofa=bounds(bpy.data.objects['SUNROOM_COMPACT_TWO_SEAT_SOFA'])
assert 13.055-sofa[1][1]>1.16
reg['bindings']=[b for b in reg['bindings'] if b['native_id'] not in retired]
for o,typ in new:
 reg['bindings'].append({'entity_id':'ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:sunroom:v14:'+o.name).hex,
 'adapter':'blender','native_id':o.name,'semantic_type':typ,'room_id':'unassigned','authority_level':'HUMAN_DESIGN_GUIDE'})
reg.update(registry_revision='24-integrated-laundry-east-freezer',source_revision=REV,source_locator=str(OUT))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
reg['source_sha256']=sha(OUT)
(R/'spatial-canvas.bindings.review14.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
report={'status':'HUMAN_REVIEW','revision':REV,'source':str(SRC),'source_sha256':sha(SRC),'output':str(OUT),
 'output_sha256':sha(OUT),'freezer_source_bounds_m':freezer,'freezer_parallel_to_east_wall':True,
 'freezer_top_has_no_extra_cover':True,'flower_ledge_length_m':2.89,
 'integrated_cabinet_width_m':2.285,'integrated_cabinet_depth_m':.70,
 'upper_cabinet_bottom_m':1.80,'upper_cabinet_top_m':2.60,'fronts_count':5,
 'central_lane_m':13.055-sofa[1][1],'unrelated_existing_objects_unchanged':True,
 'retired_native_ids':retired,'modified_existing_native_ids':sorted(changed-set(retired)),
 'manufacturer_opening_clearance_verified':False}
(R/'SUNROOM_INTEGRATED_LAUNDRY_REVIEW14_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
assert sha(FROZEN)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
print('REVIEW14_SAVED',json.dumps(report,ensure_ascii=False))
