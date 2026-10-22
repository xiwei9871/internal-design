"""Apply current user window facts and display corrections without changing frozen source geometry."""
import bpy
import hashlib
import json
import shutil
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
SOURCE=OUT/'B1_1_SITE_CORRECTED_V3.blend';MODEL=OUT/'B1_1_SITE_CORRECTED_V4.blend'
FREEZE=json.loads((ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
for key,expected in FREEZE['sha256'].items():assert hashlib.sha256((ROOT/FREEZE['files'][key]).read_bytes()).hexdigest()==expected
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update()
def signature(o):
    h=hashlib.sha256()
    if o.type=='MESH':
        for v in o.data.vertices:h.update((','.join(format(c,'.9g') for c in v.co)+';').encode())
        for f in o.data.polygons:h.update((','.join(str(v) for v in f.vertices)+';').encode())
    else:h.update(o.type.encode())
    return h.hexdigest()
def pose(o):return [list(o.location),list(o.rotation_euler),list(o.scale),o.parent.name if o.parent else None]
protected={o.name:dict(signature=signature(o),pose=pose(o)) for o in bpy.data.objects}
col=bpy.data.collections.new('COL_SITE_WINDOW_AND_BUFFET_V4');bpy.context.scene.collection.children.link(col)
col['geometry_authority']=False;col['physical_ground_truth']=False
M_BODY=bpy.data.materials['B11_REVIEW_BODY'];M_FRONT=bpy.data.materials['B11_REVIEW_FRONT']
M_METAL=bpy.data.materials['B11_REVIEW_METAL'];M_COUNTER=bpy.data.materials['B11_REVIEW_COUNTER'];M_GLASS=bpy.data.materials['B11_REVIEW_GLASS']
M_WALL=bpy.data.materials.new('SITE_REVIEW_CONTINUOUS_WALL');M_WALL.diffuse_color=(.85,.86,.84,1)
M_WALL.use_nodes=True;bsdf=M_WALL.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value=M_WALL.diffuse_color;bsdf.inputs['Roughness'].default_value=.72
def group(name):
    o=bpy.data.objects.new('B11_SITE_'+name,None);col.objects.link(o)
    o['physical_ground_truth']=False;o['review_status']='HUMAN_REVIEW';return o
def box(name,lo,hi,mat,parent,bevel=.0015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)])
    o=bpy.context.object;o.name='B11_SITE_'+name;o.dimensions=[hi[i]-lo[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);o.parent=parent;o.data.materials.append(mat);o.color=mat.diffuse_color
    if bevel:
        m=o.modifiers.new('Review edge','BEVEL');m.width=bevel;m.segments=2;o.modifiers.new('Review normals','WEIGHTED_NORMAL')
    o['physical_ground_truth']=False;return o
def suppress(root_name):
    root=bpy.data.objects.get(root_name)
    if not root:return
    for o in [root,*root.children_recursive]:o.hide_render=True;o.hide_viewport=True
    root['site_status']='INACTIVE_FROZEN_OR_PRIOR_REVIEW_GEOMETRY; NEW_B1_VISUAL_DETAIL_OVERRIDE'

for key in ['W-KIT-S','W-LBALC-S']:
    suppress('GLZ_'+key);suppress('B11_OPENING_'+key)

def window(name,x0,x1,y0,y1,sill,head,panes=2):
    r=group(name);r['sill_mm']=sill*1000;r['head_mm']=head*1000;r['span_mm']=(x1-x0)*1000
    mid=(y0+y1)/2;t=.035
    for n,x in enumerate([x0,x1-t]):box(name+f'_JAMB_{n}',[x,mid-.023,sill],[x+t,mid+.023,head],M_METAL,r)
    for n,z in enumerate([sill,head-t]):box(name+f'_RAIL_{n}',[x0,mid-.023,z],[x1,mid+.023,z+t],M_METAL,r)
    for n in range(panes):
        a=x0+(x1-x0)*n/panes;b=x0+(x1-x0)*(n+1)/panes
        box(name+f'_GLASS_{n}',[a+t,mid-.004,sill+t],[b-t,mid+.004,head-t],M_GLASS,r,0)
        if n:box(name+f'_MULLION_{n}',[a-t/2,mid-.023,sill],[a+t/2,mid+.023,head],M_METAL,r)
    return r
small=window('KITCHEN_WINDOW',6.100,7.100,-.200,0,1.020,2.400)
small['authority']='HUMAN_CONFIRMED: COUNTERTOP820 + WALL200 = WINDOW_SILL1020'
large=window('BALCONY_WINDOW',2.100,5.100,.500,.700,1.050,2.400)
large['authority']='LATEST_USER_CONFIRMED_WINDOW_OVERLAY; BLUE_SEGMENT_approximately_X2100_TO5100'
large['old_span_mm']=4500;large['wall_length_is_not_window_length']=True

small_wall=group('KITCHEN_WINDOW_SURROUND')
box('KITCHEN_WINDOW_UNDER_WALL',[6.100,-.200,0],[7.100,0,1.020],M_WALL,small_wall,0)
box('KITCHEN_WINDOW_HEAD_WALL',[6.100,-.200,2.400],[7.100,0,2.800],M_WALL,small_wall,0)

# The red-marked strip was inherited parapet W_wall_md_0042 clipped to 450 mm,
# not a cabinet. Retain its complete 1050 mm height and give it a continuous-wall finish.
parapet=bpy.data.objects['W_wall_md_0042']
parapet.data=parapet.data.copy();parapet.data.materials.clear();parapet.data.materials.append(M_WALL)
for f in parapet.data.polygons:f.material_index=0
parapet.color=M_WALL.diffuse_color;parapet['review_keep_full_height']=True
parapet['semantic_role']='WINDOW_UNDER_WALL; NOT_CABINET'
large_wall=group('BALCONY_WINDOW_SURROUND')
box('BALCONY_WINDOW_LEFT_RETURN',[1.500,.500,1.050],[2.100,.700,2.800],M_WALL,large_wall,0)
box('BALCONY_WINDOW_RIGHT_RETURN',[5.100,.500,1.050],[5.500,.700,2.800],M_WALL,large_wall,0)
box('BALCONY_WINDOW_HEAD',[2.100,.500,2.400],[5.100,.700,2.800],M_WALL,large_wall,0)

# Photo 5 = existing west-side dining/balcony storage at the guide's Rectangle029 footprint.
# Preserve its footprint and facing; replace the generic 850 mm review proxy with visible PDF/PHOTO organization.
suppress('B11_Rectangle029')
buffet=group('PHOTO5_BUFFET_R029');buffet['source_name']='Rectangle029'
buffet['authority']='SITE_PHOTO5_RELATIONSHIPS + CABINET_PDF_PAGE6; GUIDE_XY_RETAINED'
buffet['PDF_dimension_chain_mm']=[50,805,25,180,40,450,910,250]
buffet['height_mm']=2710;buffet['counter_top_mm']=1100;buffet['facing']='EAST'
buffet['review_footprint_mm']=[1500,500];buffet['pdf_nominal_width_mm']=1580
buffet['footprint_policy']='RETAIN_GUIDE1500x500; PDF1580x600 remains shop-drawing reference, not silently moved'
x0=1.5205;x1=2.0205;y0=.74021875;y1=2.24021875;t=.018
box('BUFFET_SIDE_S',[x0,y0,.05],[x1,y0+t,2.710],M_BODY,buffet)
box('BUFFET_SIDE_N',[x0,y1-t,.05],[x1,y1,2.710],M_BODY,buffet)
box('BUFFET_BACK',[x0,y0,.05],[x0+t,y1,2.710],M_FRONT,buffet)
box('BUFFET_PLINTH',[x0+.03,y0,0],[x1-.03,y1,.05],M_METAL,buffet)
box('BUFFET_BASE',[x0,y0,.05],[x1,y1,.068],M_BODY,buffet)
box('BUFFET_COUNTER',[x0,y0,1.060],[x1,y1,1.100],M_COUNTER,buffet)
box('BUFFET_UPPER_BASE',[x0,y0,1.532],[x1,y1,1.550],M_BODY,buffet)
box('BUFFET_UPPER_TOP',[x0,y0,2.442],[x1,y1,2.460],M_BODY,buffet)
box('BUFFET_TOP_CLOSING',[x1-t,y0,2.460],[x1,y1,2.710],M_FRONT,buffet)
for n in range(4):
    a=y0+(y1-y0)*n/4;b=y0+(y1-y0)*(n+1)/4
    box(f'BUFFET_LOWER_DOOR_{n}',[x1-t,a+.002,.052],[x1,b-.002,.855],M_FRONT,buffet)
    box(f'BUFFET_UPPER_DOOR_{n}',[x1-t,a+.002,1.552],[x1,b-.002,2.458],M_FRONT,buffet)
for n in range(2):
    a=y0+(y1-y0)*n/2;b=y0+(y1-y0)*(n+1)/2
    box(f'BUFFET_DRAWER_{n}',[x1-t,a+.002,.880],[x1,b-.002,1.060],M_FRONT,buffet)
box('BUFFET_RECESSED_PULL_SLOT',[x1-.03,y0,.855],[x1-.015,y1,.880],M_METAL,buffet)

bpy.context.view_layer.update()
for name,record in protected.items():
    o=bpy.data.objects[name]
    assert signature(o)==record['signature'],'Protected source geometry changed: '+name
    assert pose(o)==record['pose'],'Protected source pose changed: '+name
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
for key,expected in FREEZE['sha256'].items():assert hashlib.sha256((ROOT/FREEZE['files'][key]).read_bytes()).hexdigest()==expected
scene=bpy.context.scene;scene['B1_SITE_CORRECTION']='HUMAN_REVIEW'
scene['latest_user_facts']='KITCHEN_SILL1020; BALCONY_WINDOW3000_FROM_APPROVED_DIAGRAM; NO_PHANTOM_CAB; PHOTO5_BUFFET_VIEW'
scene['B0_geometry_policy']='FROZEN_SOURCE_DATA_RETAINED_UNCHANGED; ACTIVE_B1_SITE_DETAIL_OVERRIDES'
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))
records=dict(status='HUMAN_REVIEW',source_v3_sha256=source_hash,model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),
    B0_INTEGRITY='PASS',all_previous_objects_geometry_and_pose_preserved=len(protected),
    kitchen_window=dict(span_mm=1000,sill_mm=1020,head_mm=2400,height_mm=1380,countertop_mm=820,wall_above_counter_mm=200),
    balcony_window=dict(span_mm=3000,x_mm=[2100,5100],sill_mm=1050,head_mm=2400,height_unchanged=True,
        authority='USER_CONFIRMED_OVERLAY; APPROX_DIAGRAM_AXIS_READ_NOT_WALL_SPAN'),
    red_region=dict(object='W_wall_md_0042',cause='450mm review cut made 1050mm window wall appear as a low cabinet',
        correction='retain full window-under-wall height in renders; continuous wall material; no cabinet there'),
    photo5_cabinet=dict(object=buffet.name,footprint_unchanged_mm=[1500,500],upper_doors=4,lower_doors=4,drawers=2,
        counter_top_mm=1100,open_middle_height_mm=450,overall_review_height_mm=2710,
        authority='photo presence/order; PDF page6 dimension chain; guide footprint retained'),
    narrow_four_panel_refinement='RETAINED_FROM_V3',review_state='HUMAN_REVIEW')
(OUT/'WINDOW_AND_BUFFET_SITE_REGISTER_V04.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
reference=Path('/private/var/folders/ch/yf284jsj7f7_b0tgqkpxhwq00000gn/T/codex-clipboard-cc2b9e1f-74b6-4ee6-b441-ba748f565cf2.png')
dest=OUT/'originals/USER_APPROVED_WINDOW_OVERLAY_V04.png'
if not dest.exists():shutil.copy2(reference,dest)
print(json.dumps(records,ensure_ascii=False,indent=2))
