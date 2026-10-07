"""Owner-authorized sunroom study; existing chest freezer and laundry keep exact meshes/IDs."""
import bpy,json,math,sys,uuid,bmesh
from pathlib import Path
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import sha,object_state,bounds
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
source=r/'OPTION_A_R4_LONG_SIDE_CABINET_CHAISE_SOUTH_REVIEW_10.blend'
output=r/'OPTION_A_R4_BALCONY_SUNROOM_REVIEW_11.blend'
expected='70a36381a3f0131154e01fa19b1bf5b7ab63a2589995387dbaa108075970150f'
assert sha(source)==expected
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.view_layer.update()
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
freezer_names=['B11_Rectangle039_BODY','B11_Rectangle039_LID_SEAM']
laundry_names=['B11_Rectangle040_BODY_0','B11_Rectangle040_DOOR_0','B11_Rectangle040_BODY_1','B11_Rectangle040_DOOR_1']
before={n:bounds(bpy.data.objects[n]) for n in freezer_names+laundry_names}
f=bpy.data.objects[freezer_names[0]];a,b=bounds(f);pivot=Vector(((a[0]+b[0])/2,(a[1]+b[1])/2,0))
freezer_delta=Matrix.Translation((12.45,11.95,0))@Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Translation(-pivot)
for n in freezer_names:bpy.data.objects[n].matrix_world=freezer_delta@bpy.data.objects[n].matrix_world
washer=bpy.data.objects[laundry_names[0]];a,b=bounds(washer)
delta=Matrix.Translation((8.40-(a[0]+b[0])/2,11.47-(a[1]+b[1])/2,0))
for n in laundry_names:bpy.data.objects[n].matrix_world=delta@bpy.data.objects[n].matrix_world
bpy.context.view_layer.update()
after={n:bounds(bpy.data.objects[n]) for n in before}
allowed=set(before)
for n,state in prior.items():
    now=object_state(bpy.data.objects[n])
    if n not in allowed:assert now==state,n
    else:assert all(now[k]==state[k] for k in state if k!='matrix'),n
new=[]
def mat(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Roughness'].default_value=.7
    return m
warm=mat('BALCONY_WARM_WHITE',(.76,.77,.73));oak=mat('BALCONY_PALE_ASH',(.60,.44,.28));stone=mat('BALCONY_COUNTER_LIGHT_GREY',(.63,.66,.64));fabric=mat('BALCONY_SEAT_WARM_GREY',(.41,.44,.40));metal=mat('BALCONY_DARK_BRACKETS',(.09,.12,.12));leaf=mat('BALCONY_REAL_PLANT_LEAF',(.13,.31,.17));soil=mat('BALCONY_PLANT_SOIL',(.09,.065,.04))
def box(name,lo,hi,m,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)]);o=bpy.context.object;o.name='SUNROOM_'+name;o.scale=[hi[i]-lo[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Edge finish','BEVEL');mod.width=bevel;mod.segments=4;bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(m);new.append(o);return o
def cylinder(name,center,rad,depth,m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=rad,depth=depth,location=center);o=bpy.context.object;o.name='SUNROOM_'+name;o.data.materials.append(m);new.append(o);return o
def join(name,parts):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name='SUNROOM_'+name
    new[:]=[x for x in new if x not in parts];new.append(o);return o
def carcass(name,x0,x1,y0,y1,z0,z1,orientation='north',material=warm):
    # Hollow unit with clear door regions, not a solid mass masquerading as cabinet construction.
    t=.018;p=[]
    p.append(box(name+'_BOTTOM',(x0,y0,z0),(x1,y1,z0+t),material))
    p.append(box(name+'_TOP',(x0,y0,z1-t),(x1,y1,z1),material))
    if orientation=='north':
        for x in [x0,x1-t]:p.append(box(name+'_SIDE',(x,y0,z0+t),(x+t,y1,z1-t),material))
        p.append(box(name+'_BACK',(x0+t,y0,z0+t),(x1-t,y0+.012,z1-t),material))
        mid=(x0+x1)/2
        for a,b in [(x0+t,mid-.002),(mid+.002,x1-t)]:p.append(box(name+'_FRONT',(a,y1-.018,z0+t+.004),(b,y1,z1-t-.004),material,.002))
    else:
        for y in [y0,y1-t]:p.append(box(name+'_SIDE',(x0,y,z0+t),(x1,y+t,z1-t),material))
        p.append(box(name+'_BACK',(x1-.012,y0+t,z0+t),(x1,y1-t,z1-t),material))
        mid=(y0+y1)/2
        for a,b in [(y0+t,mid-.002),(mid+.002,y1-t)]:p.append(box(name+'_FRONT',(x0,a,z0+t+.004),(x0+.018,b,z1-t-.004),material,.002))
    return join(name,p)
# SW laundry: original600x600x1700mm tower, unsealed front/serviceable cabinet surround.
box('LAUNDRY_WEST_PANEL',(8.035,11.135,.015),(8.075,11.835,2.15),warm,.004)
box('LAUNDRY_EAST_PANEL',(8.725,11.135,.015),(8.765,11.835,2.15),warm,.004)
carcass('LAUNDRY_OVERHEAD',8.035,8.765,11.135,11.835,1.80,2.15)
box('LAUNDRY_HEADER',(8.075,11.135,1.775),(8.725,11.835,1.80),oak,.003)
carcass('LAUNDRY_FOLDING_BASE',8.83,9.53,11.14,11.79,.08,.87)
box('LAUNDRY_FOLDING_COUNTER',(8.82,11.13,.87),(9.54,11.81,.90),stone,.008)
carcass('LAUNDRY_SHALLOW_UPPER',8.86,9.53,11.14,11.42,1.36,1.94)
# Chest freezer at east: visible lid/open top, independent rear airspace, no countertop over appliance.
# Model gives1200x600x850mm; clearance figures are review defaults, pending manufacturer data.
carcass('EAST_LOW_STORAGE',12.14,12.74,12.65,13.30,.08,.855,'west')
box('EAST_STORAGE_COUNTER',(12.13,12.64,.855),(12.76,13.32,.89),stone,.008)
box('FREEZER_SIDE_FINISH_SOUTH',(12.14,11.245,.02),(12.74,11.265,.87),warm,.002)
box('FREEZER_SIDE_FINISH_NORTH',(12.14,12.635,.02),(12.74,12.655,.85),warm,.002)
box('FREEZER_FRONT_PLINTH',(12.11,11.265,.01),(12.13,12.635,.07),oak,.002)
# Low side panels have ventilation slots at the open front and leave150mm behind actual freezer.
for k in range(5):box('FREEZER_VENT_SLAT_'+str(k),(12.127,11.30+k*.12,.09),(12.147,11.37+k*.12,.12),metal)
# South wall sunlight seat, separate from wet utility work, backed against opaque span0055.
carcass('SUN_SEAT_BASE',10.04,11.54,11.14,11.76,.06,.40,material=oak)
box('SUN_SEAT_CUSHION',(10.04,11.16,.40),(11.54,11.76,.46),fabric,.026)
box('SUN_SEAT_BACK',(10.05,11.145,.46),(11.53,11.285,.80),fabric,.035)
for a,b in [(10.09,10.56),(10.58,11.05),(11.07,11.49)]:
    box('SUN_SEAT_BACK_PAD',(a,11.275,.48),(b,11.355,.77),fabric,.023)
tableparts=[box('MOVABLE_TABLE_TOP',(11.64,11.26,.47),(12.04,11.66,.50),oak,.015)]
for x,y in [(11.68,11.30),(11.96,11.30),(11.68,11.58),(11.96,11.58)]:tableparts.append(box('MOVABLE_TABLE_LEG',(x,y,0),(x+.025,y+.025,.47),metal,.002))
join('MOVABLE_COFFEE_TABLE',tableparts)
# North plants ledge:300mm deep, independent shallow storage below parapet, no glass anchors.
carcass('NORTH_PLANT_LEDGE_BASE',9.15,12.04,13.055,13.355,.10,.65)
box('NORTH_PLANT_LEDGE_TOP',(9.13,13.04,.65),(12.06,13.37,.675),stone,.006)
for k,x in enumerate([9.48,10.45,11.45]):
    potmat=mat('BALCONY_POT_'+str(k),[(.40,.46,.43),(.66,.69,.64),(.31,.38,.35)][k])
    cylinder('PLANT_POT_'+str(k),(x,13.20,.755),.085,.16,potmat)
    cylinder('PLANT_SOIL_'+str(k),(x,13.20,.836),.070,.008,soil)
    cylinder('PLANT_STEM_'+str(k),(x,13.20,.955),.004,.24,leaf)
    for j in range(5):
        angle=j*2.399+k
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=1,location=(x+.042*math.cos(angle),13.20+.042*math.sin(angle),.88+j*.042))
        o=bpy.context.object;o.name='SUNROOM_PLANT_LEAF_'+str(k)+'_'+str(j);o.scale=(.075,.025,.016);o.rotation_euler=(.3,j*.2,angle);o.data.materials.append(leaf);new.append(o)
# Clearance evidence and physical supports only; utility links remain unverified.
bpy.context.view_layer.update()
floor=bpy.data.objects['FLOOR_LOWER']
for x,y in [(8.10,11.20),(8.70,11.70),(12.20,11.40),(12.70,12.50),(10.10,11.20),(11.50,11.70),(9.20,13.10),(12.0,13.30)]:
    hit,p,n,i=floor.ray_cast(floor.matrix_world.inverted()@Vector((x,y,1)),Vector((0,0,-1)))
    assert hit and abs(p.z)<1e-5,(x,y)
fa,fb=bounds(bpy.data.objects[freezer_names[0]])
assert abs(fb[0]-fa[0]-.6)<1e-5 and abs(fb[1]-fa[1]-1.2)<1e-5 and abs(fb[2]-.85)<1e-5
registry=json.loads((r/'spatial-canvas.bindings.review10.json').read_text())
for o in new:
    typ='plant' if 'PLANT_' in o.name and 'LEDGE' not in o.name else 'bench' if 'SUN_SEAT' in o.name else 'cabinet'
    registry['bindings'].append({'entity_id':'ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:sunroom:v1:'+o.name).hex,'adapter':'blender','native_id':o.name,'semantic_type':typ,'room_id':'unassigned','authority_level':'HUMAN_DESIGN_GUIDE'})
registry.update(registry_revision='21-balcony-sunroom-study',source_revision='r4-balcony-sunroom-review-11',source_locator=str(output))
bpy.ops.wm.save_as_mainfile(filepath=str(output));registry['source_sha256']=sha(output)
(r/'spatial-canvas.bindings.review11.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
saved={o.name:object_state(o) for o in bpy.context.scene.objects}
new_names=[o.name for o in new]
bpy.ops.wm.open_mainfile(filepath=str(output));assert all(object_state(bpy.data.objects[n])==s for n,s in saved.items())
assert sha(source)==expected
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
report={'status':'HUMAN_REVIEW','source':str(source),'source_sha256':expected,'output':str(output),'output_sha256':sha(output),'moved_native_ids':freezer_names+laundry_names,'before':before,'after':after,'existing_other_object_states_unchanged':True,'freezer_size_m':[1.2,.6,.85],'freezer_back_gap_m':12.899900436401367-fb[0],'freezer_fixed_counter_above_lid':False,'laundry_tower_original_meshes_retained':True,'sun_seat_size_m':[1.5,.62,.80],'north_ledge_depth_m':.30,'central_lane_seat_to_north_ledge_m':13.055-11.76,'west_balcony_door_unchanged':True,'utilities_and_manufacturer_clearances_unverified':True,'new_objects':new_names,'source_and_frozen_r4_unchanged':True,'fresh_reopen_verified':True}
(r/'SUNROOM_REVIEW11_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['before','after','new_objects']},ensure_ascii=False))
