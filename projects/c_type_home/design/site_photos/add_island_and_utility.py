"""Add the omitted original PDF island and the human-confirmed adjacent tall cabinet/AC."""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
SOURCE=OUT/'B1_1_SITE_CORRECTED_V1.blend'
MODEL=OUT/'B1_1_SITE_CORRECTED_V2.blend'
manifest=json.loads((ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
for key,expected in manifest['sha256'].items():
    assert hashlib.sha256((ROOT/manifest['files'][key]).read_bytes()).hexdigest()==expected
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.view_layer.update()
def bounds(objects):
    p=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
protected={n:bounds([o for o in bpy.data.objects[n].children_recursive if o.type=='MESH'])
           for n in ['B11_K-FRIDGE','B11_K-FRIDGE-OVERHEAD','B11_K-TALL-L','B11_K-NARROW-OUTER-320']}
col=bpy.data.collections.new('COL_SITE_KITCHEN_ISLAND_AND_UTILITY');bpy.context.scene.collection.children.link(col)
col['geometry_authority']=False;col['physical_ground_truth']=False
M_BODY=bpy.data.materials['B11_REVIEW_BODY'];M_FRONT=bpy.data.materials['B11_REVIEW_FRONT']
M_METAL=bpy.data.materials['B11_REVIEW_METAL'];M_COUNTER=bpy.data.materials['B11_REVIEW_COUNTER']
M_AC=bpy.data.materials['B11_REVIEW_CERAMIC']
def group(name):
    root=bpy.data.objects.new('B11_'+name,None);col.objects.link(root)
    root['physical_ground_truth']=False;root['review_status']='HUMAN_REVIEW';return root
def box(label,lo,hi,mat,parent,bevel=.0015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)])
    o=bpy.context.object;o.name='B11_'+label;o.dimensions=[hi[i]-lo[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);o.parent=parent;o.data.materials.append(mat);o.color=mat.diffuse_color
    if bevel:
        b=o.modifiers.new('Review edges','BEVEL');b.width=bevel;b.segments=2
        o.modifiers.new('Review normals','WEIGHTED_NORMAL')
    o['physical_ground_truth']=False;return o

island=group('K-ISLAND-PDF-C')
island['authority']='ORIGINAL_CABINET_PDF_PAGE_1_AND_4_ELEVATION_C'
island['source_confirmed_dims_mm']=[800,467,960]
island['drawer_module_width_mm']=700;island['counter_thickness_mm']=40
island['placement_basis']='Retained north-run reference front 3750 minus PDF 1520 gap gives island north end 2230; original cabinet 800 length.'
island['placement_status']='SHOP_DRAWING_TO_B1_REVIEW_ALIGNMENT'
# Drawer island lies beyond the pillar; bridge wraps along its kitchen face.
x0=5.700;x1=x0+.467;y0=1.430;y1=2.230;z_top=.960;t=.018
bx0=x0+.020;bx1=x1-.020;by0=y0+.050;by1=y1-.050
box('K-ISLAND_L',[bx0,by0,.05],[bx1,by0+t,.92],M_BODY,island)
box('K-ISLAND_R',[bx0,by1-t,.05],[bx1,by1,.92],M_BODY,island)
box('K-ISLAND_BACK',[bx0,by0,.05],[bx0+t,by1,.92],M_BODY,island)
box('K-ISLAND_BASE',[bx0,by0,.05],[bx1,by1,.05+t],M_BODY,island)
box('K-ISLAND_TOP_SUPPORT',[bx0,by0,.902],[bx1,by1,.920],M_BODY,island)
box('K-ISLAND_PLINTH',[bx0+.02,by0,0],[bx1-.03,by1,.05],M_METAL,island)
for n,(a,b) in enumerate([(.05,.36),(.385,.695),(.720,.920)]):
    box(f'K-ISLAND_DRAWER_{n}',[bx1-t,by0+.002,a+.002],[bx1,by1-.002,b-.002],M_FRONT,island)
    box(f'K-ISLAND_DRAWER_PULL_{n}',[bx1-.004,by0+.035,b-.024],[bx1+.002,by1-.035,b-.016],M_METAL,island)

# Counter has an explicitly rounded free end as called out in PDF C.
r=.040;points=[(x0,y0),(x1,y0)]
for n in range(9):
    a=(math.pi/2)*n/8;points.append((x1-r+r*math.cos(a),y1-r+r*math.sin(a)))
points.append((x0+r,y1))
for n in range(1,9):
    a=math.pi/2+(math.pi/2)*n/8;points.append((x0+r+r*math.cos(a),y1-r+r*math.sin(a)))
count=len(points);vertices=[(x,y,z) for z in [.920,.960] for x,y in points]
faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
faces.extend((n,(n+1)%count,(n+1)%count+count,n+count) for n in range(count))
mesh=bpy.data.meshes.new('K-ISLAND_ROUNDED_COUNTER_MESH');mesh.from_pydata(vertices,[],faces);mesh.update()
counter=bpy.data.objects.new('B11_K-ISLAND_ROUNDED_COUNTER',mesh);col.objects.link(counter);counter.parent=island
mesh.materials.append(M_COUNTER);counter.color=M_COUNTER.diffuse_color
counter['radius_authority']='GENERIC_REVIEW_RADIUS_40mm; rounded presence PDF_CONFIRMED'

bridge=group('K-ISLAND-CONNECTOR')
bridge['authority']='PDF_C: 890 connector / 270 narrow cabinet, no backboard'
box('K-ISLAND_CONNECTOR_COUNTER',[5.900,.540,.920],[6.170,1.430,.960],M_COUNTER,bridge)
# Stop solid body at the sink cabinet front to avoid a duplicate corner body.
box('K-ISLAND_CONNECTOR_SIDE_S',[5.910,.600,.05],[6.155,.618,.920],M_BODY,bridge)
box('K-ISLAND_CONNECTOR_SIDE_N',[5.910,1.412,.05],[6.155,1.430,.920],M_BODY,bridge)
box('K-ISLAND_CONNECTOR_BOTTOM',[5.910,.618,.05],[6.155,1.412,.068],M_BODY,bridge)
box('K-ISLAND_CONNECTOR_FRONT',[6.137,.618,.05],[6.155,1.412,.920],M_FRONT,bridge)
box('K-ISLAND_CONNECTOR_PLINTH',[5.930,.600,0],[6.125,1.430,.05],M_METAL,bridge)

# Existing unresolved balcony-counter proxy overlaps the photo-confirmed new utility cabinet.
# Retain it as hidden evidence rather than presenting two bodies in the same location.
proxy=bpy.data.objects.get('B11_Rectangle032')
if proxy:
    proxy['site_status']='HIDDEN_UNRESOLVED_PROXY_IN_UTILITY_AREA'
    for o in proxy.children_recursive:
        o.hide_render=True;o.hide_viewport=True

utility=group('K-UTILITY-TALL-600')
utility['authority']='CURRENT_USER: NEW, WIDTH600_HEIGHT2000, NEXT_TO_ORIGINAL_ISLAND'
utility['confirmed_width_mm']=600;utility['confirmed_height_mm']=2000
utility['review_depth_mm']=500;utility['depth_authority']='RETAINED_ADJACENT_CABINET_REVIEW_DEPTH_NOT_SITE_MEASURED'
utility['facing']='NORTH_TOWARD_ADJACENT_ROOM; PHOTO_RELATIONSHIP_REVIEW'
ux1=5.522375;ux0=ux1-.600;uy0=.71534375;uy1=uy0+.500;h=2.0
box('K-UTILITY_L',[ux0,uy0,.08],[ux0+t,uy1,h],M_BODY,utility)
box('K-UTILITY_R',[ux1-t,uy0,.08],[ux1,uy1,h],M_BODY,utility)
box('K-UTILITY_TOP',[ux0,uy0,h-t],[ux1,uy1,h],M_BODY,utility)
box('K-UTILITY_BACK',[ux0,uy0,.08],[ux1,uy0+t,h-t],M_BODY,utility)
box('K-UTILITY_BASE',[ux0,uy0,.08],[ux1,uy1,.08+t],M_BODY,utility)
box('K-UTILITY_PLINTH',[ux0,uy0+.025,0],[ux1,uy1-.035,.08],M_METAL,utility)
for n in range(4):
    a=.08+.82*n/4;b=.08+.82*(n+1)/4
    box(f'K-UTILITY_DRAWER_{n}',[ux0+.002,uy1-t,a+.002],[ux1-.002,uy1,b-.002],M_FRONT,utility)
    box(f'K-UTILITY_DRAWER_PULL_{n}',[ux0+.025,uy1-.005,b-.025],[ux1-.025,uy1+.001,b-.017],M_METAL,utility)
for n in range(2):
    a=ux0+.600*n/2;b=ux0+.600*(n+1)/2
    box(f'K-UTILITY_UPPER_DOOR_{n}',[a+.002,uy1-t,.902],[b-.002,uy1,h-t],M_FRONT,utility)

ac=group('K-UTILITY-WALL-AC')
ac['presence_authority']='HUMAN_CONFIRMED_AND_SITE_PHOTO_004'
ac['placement_relation']='ABOVE_K-UTILITY-TALL-600'
ac['review_size_mm']=[780,220,280];ac['dimensions_and_mount_height']='GENERIC_REVIEW_ONLY; SKU/SITE_HEIGHT_TO_VERIFY'
cx=(ux0+ux1)/2;az0=2.150;az1=2.430
box('K-UTILITY_AC_BODY',[cx-.390,uy0,az0],[cx+.390,uy0+.220,az1],M_AC,ac,.016)
box('K-UTILITY_AC_FACE',[cx-.368,uy0+.210,az0+.055],[cx+.368,uy0+.222,az1-.03],M_AC,ac,.009)
for n in range(3):
    zz=az0+.030+n*.014
    box(f'K-UTILITY_AC_LOUVER_{n}',[cx-.340,uy0+.210,zz],[cx+.340,uy0+.224,zz+.006],M_METAL,ac,.001)

bpy.context.view_layer.update()
for name,expected in protected.items():
    actual=bounds([o for o in bpy.data.objects[name].children_recursive if o.type=='MESH'])
    assert max(abs(actual[i][j]-expected[i][j]) for i in range(2) for j in range(3))<1e-7,'Accepted fridge area changed'

for name,loc,target,scale in [
    ('SITE_LOGIC_KITCHEN_COMPLETE',(2.0,-3.6,5.3),(6.4,2.15,1.1),7.4),
    ('SITE_LOGIC_ISLAND_UTILITY',(8.2,4.6,4.3),(5.70,1.20,1.15),4.4),
    ('SITE_LOGIC_KITCHEN_TOP',(6.1,2.25,10),(6.1,2.25,0),6.0)]:
    camera=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,camera);col.objects.link(o)
    o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    camera.type='ORTHO';camera.ortho_scale=scale

def entry(root,id_,authority):
    objects=[o for o in root.children_recursive if o.type=='MESH']
    return dict(id=id_,assembly=root.name,authority=authority,body_objects=[o.name for o in objects],
                bounds_m=bounds(objects),review_status='HUMAN_REVIEW')
register=dict(register='KITCHEN_ISLAND_AND_UTILITY_REGISTER_V01',
    original_island_pdf=dict(source='source/世纪欣园3-1-901_cabinet_plan.pdf',pages=[1,4],
      countertop=[800,467,960],drawer_width=700,counter_thickness=40,overall_return_span=1690,connector=890),
    current_user_confirmed=dict(utility_width=600,utility_height=2000,AC_above_utility=True),
    review_assumptions=dict(utility_depth=500,AC_dimensions=[780,220,280],AC_base=2150,counter_round_radius=40),
    accepted_fridge_area='PRESERVED_WITH_IDENTICAL_WORLD_BOUNDS',protected_fridge_bounds=protected,
    replaced_proxy='B11_Rectangle032 kept hidden, identity not silently reassigned',
    items=[entry(island,'K-ISLAND-PDF-C','ORIGINAL_PDF + HUMAN_EXISTING_ISLAND_CONFIRMATION'),
           entry(bridge,'K-ISLAND-CONNECTOR','ORIGINAL_PDF_C'),
           entry(utility,'K-UTILITY-TALL-600','HUMAN_CONFIRMED_WIDTH_HEIGHT_AND_ADJACENCY'),
           entry(ac,'K-UTILITY-WALL-AC','HUMAN_CONFIRMED_PRESENCE_AND_ABOVE_RELATIONSHIP')])
(OUT/'KITCHEN_ISLAND_AND_UTILITY_REGISTER_V01.json').write_text(json.dumps(register,ensure_ascii=False,indent=2))
scene=bpy.context.scene;scene['B1_SITE_CORRECTION']='HUMAN_REVIEW'
scene['site_correction_scope']='ACCEPTED_FRIDGE_LOGIC + ORIGINAL_PDF_ISLAND + NEW_600x2000_UTILITY + WALL_AC'
scene.camera=bpy.data.objects['SITE_LOGIC_KITCHEN_COMPLETE']
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))
print(json.dumps({'model':str(MODEL),'fridge_area_unchanged':True,'island_pdf_counter':[800,467,960],
                  'new_cabinet':[600,500,2000],'AC_above':True},ensure_ascii=False,indent=2))
