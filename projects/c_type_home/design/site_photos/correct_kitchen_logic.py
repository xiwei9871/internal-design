"""Apply the user's explicit cabinet-order correction; retain frozen B0 geometry."""
import bpy
import copy
import hashlib
import json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
SOURCE=ROOT/'design/blender_b1_1/B1_1_DESIGN_MODEL_V1.blend'
MODEL=OUT/'B1_1_SITE_CORRECTED_V1.blend'
manifest=json.loads((ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
for key,expected in manifest['sha256'].items():
    assert hashlib.sha256((ROOT/manifest['files'][key]).read_bytes()).hexdigest()==expected,'B0 integrity failure'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
source_register=json.loads((ROOT/'design/blender_b1_1/B1_1_ASSET_REGISTER.json').read_text())

WALL_BACK=4.500
SOCKET_GAP=.055
FRIDGE_DEPTH=.710
FRONT=WALL_BACK-SOCKET_GAP-FRIDGE_DEPTH
NARROW_WIDTH=.320
NARROW_DEPTH=FRIDGE_DEPTH+SOCKET_GAP
OUTER_START=5.900
FRIDGE_WIDTH=.905
INNER_START=OUTER_START+FRIDGE_WIDTH
INNER_WIDTH=.935
REVIEW_HEIGHT=2.410

changes=[]
def move(name,offset,role):
    o=bpy.data.objects[name];o.location+=Vector(offset)
    o['site_correction_authority']='HUMAN_CONFIRMED_KITCHEN_LOGIC_2026-10-01'
    o['column_role']=role
    changes.append(dict(object=name,translation_m=offset,role=role))

# Outer refrigerator and its overhead cabinet move together; the niche goes inside.
move('B11_K-FRIDGE',[-.935,FRONT-3.750,0],'OUTER_REFRIGERATOR_COLUMN')
move('B11_K-FRIDGE-OVERHEAD',[-.935,FRONT-3.750,0],'OUTER_REFRIGERATOR_OVERHEAD')
move('B11_K-TALL-L',[.905,0,0],'INNER_HIGH_CABINET_AND_NICHE_COLUMN')

col=bpy.data.collections.get('COL_B11_KITCHEN')
root=bpy.data.objects.new('B11_K-NARROW-OUTER-320',None);col.objects.link(root)
root.empty_display_type='PLAIN_AXES';root.empty_display_size=.05
root['source_name']='K-NARROW-OUTER-320';root['column_role']='OUTERMOST_NEXT_TO_DOOR'
root['width_mm']=320;root['depth_range_mm']=[760,770];root['review_depth_mm']=765
root['front_alignment']='FRIDGE_FRONT';root['socket_clearance_range_mm']=[50,60]
root['authority']='HUMAN_CONFIRMED_CURRENT_SITE_DIMENSION_AND_RELATIONSHIP'
root['height_authority']='EXISTING_REVIEW_HEIGHT_2410; TOP_JOIN_TO_VERIFY'
root['physical_ground_truth']=False;root['review_status']='HUMAN_REVIEW'
body=[]
x0=OUTER_START-NARROW_WIDTH;x1=OUTER_START;y0=FRONT;y1=WALL_BACK;t=.018
M_BODY=bpy.data.materials['B11_REVIEW_BODY']
M_FRONT=bpy.data.materials['B11_REVIEW_FRONT']
M_METAL=bpy.data.materials['B11_REVIEW_METAL']
def box(label,lo,hi,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)])
    o=bpy.context.object;o.name='B11_K-NARROW-OUTER-320_'+label
    o.dimensions=[hi[i]-lo[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);o.parent=root;o.data.materials.append(mat);o.color=mat.diffuse_color
    mod=o.modifiers.new('Review panel edges','BEVEL');mod.width=.0015;mod.segments=2
    o.modifiers.new('Review normals','WEIGHTED_NORMAL')
    o['physical_ground_truth']=False;o['bas_role']='human_confirmed_dimensional_cabinet_review'
    body.append(o);return o
box('L',[x0,y0,.08],[x0+t,y1,REVIEW_HEIGHT],M_BODY)
box('R',[x1-t,y0,.08],[x1,y1,REVIEW_HEIGHT],M_BODY)
box('TOP',[x0,y0,REVIEW_HEIGHT-t],[x1,y1,REVIEW_HEIGHT],M_BODY)
box('BASE',[x0,y0,.08],[x1,y1,.08+t],M_BODY)
box('BACK',[x0,y1-t,.08],[x1,y1,REVIEW_HEIGHT-t],M_BODY)
box('PLINTH',[x0,y0+.04,0],[x1,y1-.03,.08],M_METAL)
levels=[.08,.50,1.30,REVIEW_HEIGHT-t]
for n,(a,b) in enumerate(zip(levels,levels[1:])):
    box(f'FRONT_{n}',[x0+.002,y0,a+.002],[x1-.002,y0+t,b-.002],M_FRONT)
    box(f'RECESSED_PULL_{n}',[x0+.025,y0+.001,a+.025],[x1-.025,y0+.004,a+.035],M_METAL)
    if n:box(f'SHELF_{n}',[x0+t,y0+t,a],[x1-t,y1-t,a+t],M_BODY)

# Socket clearance is semantic installation space, not a guessed socket model.
gap=bpy.data.objects.new('B11_K-FRIDGE_REAR_SOCKET_ALLOWANCE',None);col.objects.link(gap)
gap.empty_display_type='CUBE';gap.empty_display_size=.03
gap.location=[(OUTER_START+INNER_START)/2,WALL_BACK-SOCKET_GAP/2,1.0]
gap['depth_range_mm']=[50,60];gap['review_depth_mm']=55
gap['geometry_authority']=False;gap['physical_ground_truth']=False
gap['purpose']='socket/plug installation clearance only; exact socket position not modeled'

bpy.context.view_layer.update()
def bounds(objects):
    points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    return [[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]

register=copy.deepcopy(source_register)
for item in register['items']:
    if item['source_name'] not in ['K-FRIDGE','K-FRIDGE-OVERHEAD','K-TALL-L']:continue
    objects=[bpy.data.objects[n] for n in item['body_objects']];b=bounds(objects)
    item['previous_target_bounds_m']=item['target_bounds_m'];item['target_bounds_m']=b
    item['rect_mm']=[b[0][0]*1000,b[0][1]*1000,b[1][0]*1000,b[1][1]*1000]
    item['placement_authority']='CURRENT_HUMAN_CONFIRMED_OUTER_INNER_LOGIC'
    item['column_role']=bpy.data.objects[item['assembly']]['column_role']
register['items'].append(dict(source_name='K-NARROW-OUTER-320',label='门边新增窄柜',semantic_type='NARROW_TALL_CABINET',
    room='R-KITCHEN_DOOR_SIDE',assembly=root.name,body_objects=[o.name for o in body],verify_envelope=True,
    rect_mm=[x0*1000,y0*1000,x1*1000,y1*1000],target_bounds_m=[[x0,y0,0],[x1,y1,REVIEW_HEIGHT]],
    height_mm=2410,height_authority='RETAINED_REVIEW_HEIGHT_TO_VERIFY',
    width_mm=320,depth_range_mm=[760,770],depth_mm=765,local_ffl_mm=0,facing_deg=270,
    modeling_mode='HUMAN_CONFIRMED_SITE_REVIEW',review_status='HUMAN_REVIEW',
    placement_authority='HUMAN_CONFIRMED_NEXT_TO_DOOR_OUTSIDE_FRIDGE',front_plane_m=FRONT))
register['register']='B1_1_SITE_CORRECTED_ASSET_REGISTER'
register['human_confirmed_kitchen_order']=['K-NARROW-OUTER-320','K-FRIDGE_WITH_OVERHEAD','K-TALL-L_INNER_NICHE']
register['site_correction_scope']='NORTH_ROW_LOGIC_ONLY; OTHER_PHOTO_DETAILS_PENDING'
register['photo_registration_gate_override']='User directs simple logical correction from explicit human facts; do not block this on camera fitting.'
(OUT/'B1_1_SITE_ASSET_REGISTER.json').write_text(json.dumps(register,ensure_ascii=False,indent=2))

logic=dict(authority='DIRECT_USER_CONFIRMATION',status='HUMAN_REVIEW',
    order_from_door=['320 mm narrow cabinet','refrigerator plus overhead','inner high cabinet / open niche'],
    confirmed_dimensions_mm=dict(narrow_width=320,fridge=[905,710,1700],narrow_depth_range=[760,770],rear_gap_range=[50,60]),
    representative_review_dimensions_mm=dict(narrow_depth=765,rear_gap=55),
    inherited_review_dimensions_mm=dict(inner_column_width=935,cabinet_top=2410,overhead_base=1930),
    front_plane_m=FRONT,back_wall_reference_m=WALL_BACK,
    confirmed_front_relation='NARROW_FRONT = FRIDGE_FRONT',
    old_column_order_error='High cabinet/niche outside; refrigerator inside; narrow extra cabinet omitted',
    changes=changes,source_blend_sha256=source_hash,
    uncertainties=['Narrow top/door segmentation uses simple inherited-height review geometry.',
                   'Inner column width/depth and upper cabinet profiles retain existing review sizes.'],
    no_new_photo_metric_estimates=True)
(OUT/'KITCHEN_COLUMN_LOGIC_V02.json').write_text(json.dumps(logic,ensure_ascii=False,indent=2))

for name,location,target,scale in [
 ('SITE_LOGIC_NORTH_FRONT',(6.66,1.0,1.205),(6.66,4.0,1.205),3.3),
 ('SITE_LOGIC_NORTH_TOP',(6.66,4.0,10),(6.66,4.0,0),2.7),
 ('SITE_LOGIC_NORTH_AXON',(3.8,1.5,3.9),(6.66,4.0,1.15),4.0)]:
    camera=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,camera);col.objects.link(o)
    o.location=location;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    camera.type='ORTHO';camera.ortho_scale=scale;camera.clip_end=100
scene['B1_SITE_CORRECTION']='HUMAN_REVIEW'
scene['site_model_geometry_correction']='APPLIED_HUMAN_CONFIRMED_KITCHEN_COLUMN_LOGIC'
scene['photo_metric_estimation_required_for_this_change']=False
scene['current_kitchen_pdf_role']='INITIAL_INSTALLATION; HUMAN_CONFIRMED_CURRENT_LOGIC_SUPERSEDES_COLUMN_MAPPING'
scene.camera=bpy.data.objects['SITE_LOGIC_NORTH_AXON']
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
for key,expected in manifest['sha256'].items():
    assert hashlib.sha256((ROOT/manifest['files'][key]).read_bytes()).hexdigest()==expected
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))
print(json.dumps({'model':str(MODEL),'order':logic['order_from_door'],'narrow_width_mm':320,
                  'narrow_depth_mm':765,'rear_gap_mm':55,'B0_INTEGRITY':'PASS'},ensure_ascii=False,indent=2))
