"""Packet correction: clear the southern glazed door;compact sofa beside laundry;movable freezer worktop."""
import bpy,json,math,uuid,sys
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import sha,object_state,bounds
def plain(v):
    if hasattr(v,'to_list'):return [plain(x) for x in v.to_list()]
    if hasattr(v,'items'):return {str(k):plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [plain(x) for x in v]
    return v if isinstance(v,(str,int,float,bool,type(None))) else str(v)
def snapshot(o):
    d=object_state(o);d['properties']=json.dumps({k:plain(o[k]) for k in o.keys()},sort_keys=True,ensure_ascii=False)
    d['authored_basis']=[float(v) for row in o.matrix_basis for v in row]
    d['parent_inverse']=[float(v) for row in o.matrix_parent_inverse for v in row]
    # Disabled objects have unevaluated world caches after reopen;verify authored transform instead.
    if o.hide_viewport:d['matrix']=d['authored_basis']
    return d
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
source=r/'OPTION_A_R4_BALCONY_SUNROOM_REVIEW_11.blend'
output=r/'OPTION_A_R4_SUNROOM_DOOR_CLEAR_SOFA_REVIEW_12.blend'
expected='1ef817c99f894501127cbaf1a74e2ede1d5166bb1b9129f7fbba5006914cf1b2'
assert sha(source)==expected
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.view_layer.update()
prior={o.name:snapshot(o) for o in bpy.context.scene.objects}
retired={o.name for o in bpy.context.scene.objects if o.name.startswith(('SUNROOM_SUN_SEAT_','SUNROOM_LAUNDRY_FOLDING_','SUNROOM_LAUNDRY_SHALLOW_UPPER','SUNROOM_MOVABLE_COFFEE_TABLE'))}
for name in retired:
    o=bpy.data.objects[name];o.hide_viewport=True;o.hide_render=True;o.hide_set(True)
wood=bpy.data.materials['BALCONY_PALE_ASH'];cloth=bpy.data.materials['BALCONY_SEAT_WARM_GREY'];warm=bpy.data.materials['BALCONY_WARM_WHITE'];dark=bpy.data.materials['BALCONY_DARK_BRACKETS']
top=bpy.data.materials.new('SUNROOM_LIGHTWEIGHT_WORKTOP');top.use_nodes=True;top.diffuse_color=(.63,.66,.64,1)
top.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=top.diffuse_color
top.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.65
new=[]
def box(name,a,b,m,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(a[i]+b[i])/2 for i in range(3)])
    o=bpy.context.object;o.name='SUNROOM_'+name;o.scale=[b[i]-a[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Soft edge','BEVEL');mod.width=bevel;mod.segments=5;bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(m);new.append(o);return o
# User steering: freezer,its finishes and neighboring east cabinet stay at review11 transforms/meshes.
extra_changed=set()
parts=[]
# Compact1450x750x800mm two-seat body;ends before measured southern door jamb.
x0,x1=8.89,10.34;y0,y1=11.14,11.89
parts.append(box('COMPACT_SOFA_BASE',(x0,y0,.10),(x1,y1,.29),wood,.014))
for x in [x0+.08,x1-.12]:
    for y in [y0+.08,y1-.12]:parts.append(box('COMPACT_SOFA_LEG',(x,y,0),(x+.04,y+.04,.10),wood,.005))
parts.append(box('COMPACT_SOFA_BACK',(x0,y0,.29),(x1,y0+.12,.72),wood,.020))
for x in [x0,x1-.08]:parts.append(box('COMPACT_SOFA_ARM',(x,y0+.06,.29),(x+.08,y1,.60),wood,.018))
mid=(x0+x1)/2
for a,b in [(x0+.09,mid-.014),(mid+.014,x1-.09)]:
    parts.append(box('COMPACT_SOFA_SEAT_CUSHION',(a,y0+.15,.29),(b,y1-.035,.45),cloth,.042))
    parts.append(box('COMPACT_SOFA_BACK_CUSHION',(a,y0+.12,.43),(b,y0+.26,.80),cloth,.045))
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();sofa=bpy.context.object;sofa.name='SUNROOM_COMPACT_TWO_SEAT_SOFA'
new=[o for o in new if o not in parts];new.append(sofa)
sofa['design_status']='1450x750x800 compact draft;laundry-east wall,clear ofguest-balconydoor'
# Lightweight two-leaf flip-up worktop;hinge on east/back edge,never a permanently sealed top.
worktops=[]
for k,(a,b) in enumerate([(11.30,11.95),(11.954,12.637)]):
    o=box('FREEZER_FLIP_WORKTOP_'+str(k),(12.13,a,.87),(12.76,b,.89),top,.002)
    o['opening_mode']='flip_up_for_chest_freezer'
    o['hinge_axis_source_xyz']='Y'
    o['hinge_point_source_xyz']=[12.76,(a+b)/2,.87]
    o['design_note']='Lightweight removable/flip-up study;freezer manual and actual lid sweep not verified'
    worktops.append(o)
    box('FREEZER_WORKTOP_HINGE_'+str(k),(12.765,a+.06,.865),(12.78,b-.06,.88),dark,.002)
# A narrowfiller connects to the neighboring cabinet so the visible top reads continuously.
# Last flip leaf meets the existing cabinet counter atY12.64;do not add a coplanar overlay strip.
bpy.context.view_layer.update()
for name,state in prior.items():
    now=snapshot(bpy.data.objects[name])
    if name in retired:assert all(now[k]==state[k] for k in state if k not in ['hide_viewport','hide_render','hidden'])
    elif name not in extra_changed:assert now==state,name
    elif name.startswith(('B11_Rectangle039','SUNROOM_FREEZER_VENT_SLAT')):
        assert all(now[k]==state[k] for k in state if k!='matrix'),name
    else:assert all(now[k]==state[k] for k in state if k!='mesh'),name
floor=bpy.data.objects['FLOOR_LOWER']
for x in [x0+.01,x1-.01]:
    for y in [y0+.01,y1-.01]:
        hit,p,n,i=floor.ray_cast(floor.matrix_world.inverted()@Vector((x,y,1)),Vector((0,0,-1)));assert hit and abs(p.z)<1e-5
# Door names selected in packet reveal what previous wall-based check missed.
door_names=['V4_GUEST_B11_G-GB-BALC_HOST_GLASS0','V4_GUEST_B11_G-GB-BALC_HOST_GLASS1','V4_GUEST_B11_G-GB-BALC_HOST_JAMB','V4_GUEST_B11_G-GB-BALC_HOST_JAMB.001']
door_lo=[min(bounds(bpy.data.objects[n])[0][i] for n in door_names) for i in range(3)]
door_hi=[max(bounds(bpy.data.objects[n])[1][i] for n in door_names) for i in range(3)]
front_rect=[(door_lo[0],11.10,0),(12.10,12.10,2.0)]
# Eastern freezer overlap explicitly accepted by owner;verify the remaining unobstructed opening.
accepted_east_overlap_m=max(0,door_hi[0]-12.10)
blocked=[]
for o in bpy.context.scene.objects:
    if o.type!='MESH' or not o.visible_get() or o.hide_render or o.name in door_names:continue
    if o.name.startswith('VIEW_WALL_') or o.name.startswith('V4_GUEST_') or 'FLOOR' in o.name:continue
    a,b=bounds(o)
    if all(min(b[i],front_rect[1][i])-max(a[i],front_rect[0][i])>1e-5 for i in range(3)):blocked.append(o.name)
assert not blocked,blocked
registry=json.loads((r/'spatial-canvas.bindings.review11.json').read_text())
registry['bindings']=[b for b in registry['bindings'] if b['native_id'] not in retired]
for o in new:
    typ='sofa' if o==sofa else 'countertop'
    registry['bindings'].append({'entity_id':'ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:sunroom:v2:'+o.name).hex,'adapter':'blender','native_id':o.name,'semantic_type':typ,'room_id':'unassigned','authority_level':'HUMAN_DESIGN_GUIDE'})
registry.update(registry_revision='22-sunroom-door-clearance-sofa',source_revision='r4-sunroom-door-clear-sofa-review-12',source_locator=str(output))
bpy.ops.wm.save_as_mainfile(filepath=str(output));registry['source_sha256']=sha(output)
(r/'spatial-canvas.bindings.review12.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
saved={o.name:snapshot(o) for o in bpy.context.scene.objects}
new_names=[o.name for o in new]
bpy.ops.wm.open_mainfile(filepath=str(output));bpy.context.view_layer.update()
differences={}
for n,old_state in saved.items():
    now=snapshot(bpy.data.objects[n])
    if now!=old_state:differences[n]={k:[old_state[k],now[k]] for k in old_state if old_state[k]!=now[k]}
assert not differences,json.dumps(differences,ensure_ascii=False)
assert sha(source)==expected
report={'status':'HUMAN_REVIEW','source':str(source),'source_sha256':expected,'output':str(output),'output_sha256':sha(output),'retired_native_ids':sorted(retired),'new_native_ids':new_names,'extra_changed_native_ids':sorted(extra_changed),'sofa_bounds':[[x0,y0,0],[x1,y1,.80]],'sofa_size_m':[1.45,.75,.80],'southern_glazed_door_clear_rectangle_source_xyz':front_rect,'sofa_to_door_x_gap_m':door_lo[0]-x1,'central_lane_sofa_to_plantledge_m':13.055-y1,'worktop_height_m':.89,'freezer_top_is_movable':True,'freezer_north_shift_m':0,'appliance_meshes_unchanged':True,'east_storage_and_freezer_unchanged':True,'owner_accepted_east_overlap_m':accepted_east_overlap_m,'all_other_existing_object_states_unchanged':True,'fresh_reopen_verified':True,'review11_source_unchanged':True,'freezer_lid_hardware_and_manufacturer_install_clearance_verified':False}
(r/'SUNROOM_DOOR_SOFA_REVIEW12_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['retired_native_ids','new_native_ids']},ensure_ascii=False))
