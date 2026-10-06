"""Packet-selected two/three-seat replacement; L sofa only, no ottoman."""
import bpy,bmesh,json,sys,uuid,math
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import sha,object_state,bounds
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006')
source=r/'OPTION_A_R4_WAVE35_HANDRAIL_REVIEW_3.blend'
output=r/'OPTION_A_R4_L_SOFA_REVIEW_4.blend'
assert sha(source)=='fd0f603b433bde0cdf14d9b3f17357c07ff2ab8a6575e89c77dc0f2e148cffe2'
bpy.ops.wm.open_mainfile(filepath=str(source))
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
sofa=bpy.data.objects['B11_Rectangle046_CATALOG_00_00'];retired=bpy.data.objects['B11_Rectangle047_CATALOG_00_00'];coffee=bpy.data.objects['B11_Rectangle049_CATALOG_00_00']
side=bpy.data.objects['B11_Circle_CATALOG_00_00']
before={o.name:bounds(o) for o in [sofa,retired,coffee,side]}
fabric=bpy.data.materials.new('L_SOFA_WARM_GREY_FABRIC');fabric.diffuse_color=(.37,.36,.32,1);fabric.use_nodes=True
bs=fabric.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=fabric.diffuse_color;bs.inputs['Roughness'].default_value=.9
legmat=bpy.data.materials.new('L_SOFA_DARK_FEET');legmat.diffuse_color=(.09,.075,.055,1)
parts=[]
def rounded(name,lo,hi,bevel,material):
    center=Vector([(lo[i]+hi[i])/2 for i in range(3)]);size=Vector([hi[i]-lo[i] for i in range(3)])
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=o.modifiers.new('Soft upholstered edge','BEVEL');mod.width=bevel;mod.segments=6
    bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(material)
    for f in o.data.polygons:f.use_smooth=True
    mod=o.modifiers.new('Face normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    parts.append(o);return o
def foot(x,y):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.033,depth=.09,location=(x,y,.045))
    o=bpy.context.object;o.data.materials.append(legmat);parts.append(o)
# Source coordinates: west-backed sofa faces east; chaise at south end.
# Owner reference modules:1190mm chaise +920mm armless +1190mm armed.
x0=3.40;y0=8.95
rounded('CHAISE_BASE',(x0,y0,.09),(x0+1.80,y0+1.19,.285),.035,fabric)
rounded('ARMLESS_BASE',(x0,y0+1.19,.09),(x0+1.00,y0+2.11,.285),.035,fabric)
rounded('ARMED_BASE',(x0,y0+2.11,.09),(x0+1.00,y0+3.30,.285),.035,fabric)
rounded('CHAISE_CUSHION',(x0+.245,y0+.14,.285),(x0+1.73,y0+1.15,.425),.055,fabric)
rounded('MIDDLE_CUSHION',(x0+.245,y0+1.22,.285),(x0+.94,y0+2.08,.425),.050,fabric)
rounded('NORTH_CUSHION',(x0+.245,y0+2.14,.285),(x0+.94,y0+3.15,.425),.050,fabric)
rounded('SOUTH_ARM',(x0,y0,.285),(x0+1.10,y0+.14,.58),.045,fabric)
rounded('NORTH_ARM',(x0,y0+3.16,.285),(x0+1.00,y0+3.30,.58),.045,fabric)
rounded('BACK_STRUCTURE',(x0,y0+.14,.24),(x0+.21,y0+3.16,.61),.045,fabric)
for a,b in [(.16,1.14),(1.23,2.08),(2.15,3.14)]:
    rounded('BACK_PILLOW',(x0+.055,y0+a,.405),(x0+.285,y0+b,.70),.060,fabric)
for x,y in [(x0+.11,y0+.12),(x0+1.69,y0+.12),(x0+.11,y0+1.07),(x0+1.69,y0+1.07),(x0+.11,y0+2.0),(x0+.89,y0+2.0),(x0+.11,y0+3.18),(x0+.89,y0+3.18)]:foot(x,y)
# Join in world space and retain selected three-seat native/global identity.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();joined=bpy.context.object
mesh=joined.data.copy();mesh.transform(sofa.matrix_world.inverted()@joined.matrix_world)
sofa.data=mesh
bpy.data.objects.remove(joined,do_unlink=True)
retired.hide_render=True;retired.hide_viewport=True;retired.hide_set(True)
sofa['review_status']='HUMAN_REVIEW'
sofa['design_reference']='Owner1028 modules:1190+920+1190 width,1800 chaise depth,700 height;L sofa only,no ottoman'
sofa['previous_native_asset_path']=sofa.get('native_asset_path','')
if 'native_asset_path' in sofa:del sofa['native_asset_path']
# Raise no furniture; translate coffee table into the seating opening to clear chaise foot.
lo,hi=bounds(coffee);center=Vector([(lo[i]+hi[i])/2 for i in range(3)])
coffee.matrix_world=Matrix.Translation((5.30-center.x,10.99-center.y,0))@coffee.matrix_world
side_lo,side_hi=bounds(side);side_center_y=(side_lo[1]+side_hi[1])/2
side.matrix_world=Matrix.Translation((0,12.59-side_center_y,0))@side.matrix_world
bpy.context.view_layer.update()
after={o.name:bounds(o) for o in [sofa,retired,coffee,side]}
lo,hi=after[sofa.name]
assert abs(hi[0]-lo[0]-1.80)<1e-5 and abs(hi[1]-lo[1]-3.30)<1e-5 and abs(hi[2]-lo[2]-.70)<1e-5
for name,state in prior.items():
    if name in [sofa.name,retired.name,coffee.name,side.name]:continue
    assert object_state(bpy.data.objects[name])==state,name
def overlap(a,b):
    aa,bb=bounds(a),bounds(b)
    return all(min(aa[1][i],bb[1][i])-max(aa[0][i],bb[0][i])>1e-5 for i in range(3))
# Check the actual L footprint; a single enclosing AABB includes its empty seating bay.
footprint_rects=[((x0,y0),(x0+1.8,y0+1.19)),((x0,y0+1.19),(x0+1.0,y0+3.3))]
def sofa_overlap(o):
    a,b=bounds(o)
    return any(min(b[0],hi[0])-max(a[0],lo[0])>1e-5 and min(b[1],hi[1])-max(a[1],lo[1])>1e-5 for lo,hi in footprint_rects)
assert not sofa_overlap(coffee)
assert not sofa_overlap(bpy.data.objects['B11_Rectangle048_CATALOG_00_00'])
assert not sofa_overlap(side)
assert not overlap(side,coffee)
assert not overlap(side,bpy.data.objects['B11_Rectangle048_CATALOG_00_00'])
assert not overlap(coffee,bpy.data.objects['B11_Rectangle048_CATALOG_00_00'])
# The L's occupied bounding envelope is conservative for the east primary aisle.
east_wall=bpy.data.objects['VIEW_WALL_LIVING_FIX_GUEST_BATH_FULL_WALL']
main_gap=bounds(east_wall)[0][0]-hi[0]
assert main_gap>=1.10
stair_y=max(bounds(bpy.data.objects[n])[1][1] for n in ['STEP_0','STEP_1','STEP_2','WAVE_STEP_3_ARRIVAL'])
south_gap=lo[1]-stair_y
assert south_gap>=1.10
registry=json.loads((r/'spatial-canvas.bindings.handrail-3.json').read_text())
registry['bindings']=[b for b in registry['bindings'] if b['native_id']!=retired.name]
for b in registry['bindings']:
    if b['native_id']==sofa.name:b['semantic_type']='sofa'
registry.update(registry_revision='14-l-sofa-no-ottoman-review',source_revision='r4-living-l-sofa-review-4',source_locator=str(output))
bpy.ops.wm.save_as_mainfile(filepath=str(output));registry['source_sha256']=sha(output)
(r/'spatial-canvas.bindings.l-sofa-4.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
report={'status':'HUMAN_REVIEW','source':str(source),'source_sha256':sha(source),'output':str(output),'output_sha256':sha(output),'revision':registry['source_revision'],'sofa_entity_id':'ent_d25c02916e634c6b810c2d13e29a9a62','retired_entity_id':'ent_d95e43b44132461ea84f3faee6684c67','reference_module_widths_m':[1.19,.92,1.19],'sofa_envelope_m':[1.80,3.30,.70],'ottoman_added':False,'window_chaise_unchanged':True,'before':before,'after':after,'east_aisle_conservative_clearance_m':main_gap,'south_stair_to_sofa_station_separation_m':south_gap,'coffee_translation_m':[5.30-center.x,10.99-center.y,0],'side_table_north_translation_m':12.59-side_center_y,'all_unrelated_object_states_unchanged':True}
(r/'L_SOFA_REVIEW_4_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
assert sha(source)=='fd0f603b433bde0cdf14d9b3f17357c07ff2ab8a6575e89c77dc0f2e148cffe2'
print(json.dumps(report,ensure_ascii=False))
