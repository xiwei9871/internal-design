"""Deterministic B1.1 additions over the unchanged authorized B1 branch."""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CATALOG = Path('/Users/xiwei/.pascal/runtime/1.0.3/apps/editor/public/items')
MODEL = OUT/'B1_1_DESIGN_MODEL_V1.blend'
SOURCE = ROOT/'design/blender_b0/B1_RENOVATION_DESIGN.blend'
DIM = ROOT/'design/b1_blockout/furniture_3d_dimension_register_v01.json'
ORI = ROOT/'design/b1_blockout/furniture_orientation_register_v01.json'
CAL = ROOT/'design/pascal_b1/FURNITURE_ASSET_CALIBRATION_V02.json'
GLASS_T = 0.008
PANEL_T = 0.018
UPPER_FFL = 0.45
LOWER_FFL = 0.0

def json_read(p):
    return json.loads(p.read_text())

def integrity():
    m=json_read(ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json')
    result=[]
    for k,expected in m['sha256'].items():
        actual=hashlib.sha256((ROOT/m['files'][k]).read_bytes()).hexdigest()
        result.append(dict(key=k,path=m['files'][k],actual=actual,expected=expected,match=actual==expected))
    if not all(r['match'] for r in result):
        raise RuntimeError('B0_INTEGRITY = FAIL; stop')
    return result

def collection(name):
    c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
    c['stage']='B1.1';c['physical_ground_truth']=False
    return c

def link(obj,col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj

def material(name,rgba):
    m=bpy.data.materials.new('B11_REVIEW_'+name);m.diffuse_color=rgba;m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=rgba
    bsdf.inputs['Roughness'].default_value=0.65
    if name=='GLASS':
        bsdf.inputs['Alpha'].default_value=0.18
        bsdf.inputs['Transmission Weight'].default_value=0.7
        m.surface_render_method='DITHERED'
    return m

def empty(name,col,src=None):
    o=bpy.data.objects.new('B11_'+name,None);col.objects.link(o)
    o.empty_display_type='PLAIN_AXES';o.empty_display_size=0.06
    o['bas_role']='assembly';o['stage']='B1.1';o['physical_ground_truth']=False
    if src:o['source_name']=src
    return o

def box(name,bounds,col,mat,parent=None,bevel=0.002):
    lo,hi=bounds
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)])
    o=bpy.context.object;o.name='B11_'+name;o.dimensions=[hi[i]-lo[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    link(o,col);o.data.materials.clear();o.data.materials.append(mat);o.color=mat.diffuse_color
    if bevel:
        mod=o.modifiers.new('Review edge radius','BEVEL');mod.width=min(bevel,min(o.dimensions)*0.16);mod.segments=2
        o.modifiers.new('Review normals','WEIGHTED_NORMAL')
    if parent:o.parent=parent
    o['bas_role']='review_part';o['physical_ground_truth']=False
    return o

def cylinder(name,location,radius,depth,col,mat,parent=None,rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=depth,location=location)
    o=bpy.context.object;o.name='B11_'+name;link(o,col);o.data.materials.append(mat)
    o.color=mat.diffuse_color
    if rotation:o.rotation_euler=rotation
    for p in o.data.polygons:p.use_smooth=True
    if parent:o.parent=parent
    o['bas_role']='review_hardware';o['physical_ground_truth']=False
    return o

def beam(name,a,b,width,col,mat,parent=None):
    d=Vector(b)-Vector(a);mid=(Vector(a)+Vector(b))/2
    o=box(name,([mid.x-width/2,mid.y-width/2,mid.z-d.length/2],
                [mid.x+width/2,mid.y+width/2,mid.z+d.length/2]),col,mat,parent)
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    return o

def world_bounds(objs):
    bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(v) for o in objs if o.type=='MESH' for v in o.bound_box]
    return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]

def import_calibrated(src,path,rect,h,z,yaw,col,mat,repeat=1):
    """Bake imported GLTF transforms before fitting; never rotate a world-space mesh about origin."""
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new=set(bpy.data.objects)-before
    meshes=[o for o in new if o.type=='MESH']
    bpy.context.view_layer.update()
    # Preserve material-region topology; use review category materials only.
    for o in meshes:
        transform=o.matrix_world.copy();o.data=o.data.copy()
        for v in o.data.vertices:v.co=transform@v.co
        o.data.update()
        o.parent=None;o.matrix_world=Matrix.Identity(4)
    for o in new:
        if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
    bpy.context.view_layer.update()
    native_points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    native=[[min(p[i] for p in native_points) for i in range(3)],
            [max(p[i] for p in native_points) for i in range(3)]]
    native_dims=[native[1][i]-native[0][i] for i in range(3)]
    x0,y0,x1,y1=[v/1000 for v in rect];target_w=x1-x0;target_d=y1-y0
    odd=round(yaw/90)%2
    local_width=(target_d if odd else target_w)/repeat
    local_depth=target_w if odd else target_d
    scale=[local_width/native_dims[0],local_depth/native_dims[1],h/native_dims[2]]
    center=Vector([(native[0][0]+native[1][0])/2,(native[0][1]+native[1][1])/2,native[0][2]])
    R=Matrix.Rotation(math.radians(yaw),3,'Z')
    target=Vector([(x0+x1)/2,(y0+y1)/2,z]);all_meshes=[]
    root=empty(src,col,src)
    for n in range(repeat):
        along=(n-(repeat-1)/2)*local_width
        for j,original in enumerate(meshes):
            # The first mesh is transformed only after the other copies have been made.
            o=original.copy();o.data=original.data.copy();col.objects.link(o)
            o.name=f'B11_{src}_CATALOG_{n:02d}_{j:02d}'
            for v in o.data.vertices:
                p=v.co-center
                p=Vector([p[i]*scale[i] for i in range(3)])+Vector([along,0,0])
                v.co=R@p+target
            o.data.update()
            o.data.materials.clear();o.data.materials.append(mat)
            for face in o.data.polygons:face.material_index=0
            o.color=mat.diffuse_color;o.parent=root
            # Keep bbox fit exact: bevels are internal and do not expand source bounds.
            # The single-bed's acute imported topology expands under an extra bevel.
            # Retain its native edge shape rather than changing the source envelope.
            if path.parent.name!='single-bed':
                mod=o.modifiers.new('Review edge rounding','BEVEL');mod.width=0.003;mod.segments=2
                o.modifiers.new('Review normals','WEIGHTED_NORMAL')
            o['native_asset_path']=str(path);o['bas_role']='calibrated_furniture';o['physical_ground_truth']=False
            all_meshes.append(o)
    for o in meshes:bpy.data.objects.remove(o,do_unlink=True)
    root['native_yaw_deg']=yaw
    front=R@Vector([0,-1,0])
    return root,all_meshes,dict(native_dims_blender_m=native_dims,scale_blender_xyz=scale,
                               actual_front_world=list(front),native_sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def carcass(src,rect,z,h,facing,col,mat,open_shelves=False,divisions=None):
    """Editable generic cabinet inside the registered world envelope."""
    x0,y0,x1,y1=[v/1000 for v in rect];root=empty(src,col,src);objects=[]
    # A cabinet's local front is -Y, then rotate to the registered semantic facing.
    yaw=(90+facing)%360;odd=round(yaw/90)%2
    w=(y1-y0) if odd else (x1-x0);d=(x1-x0) if odd else (y1-y0)
    R=Matrix.Rotation(math.radians(yaw),3,'Z');origin=Vector([(x0+x1)/2,(y0+y1)/2,z])
    def part(label,a,b,material=mat):
        o=box(src+'_'+label,(a,b),col,material,root)
        for v in o.data.vertices:
            v.co=R@(o.matrix_world@v.co)+origin
        o.matrix_world=Matrix.Identity(4);objects.append(o);return o
    t=PANEL_T;kick=min(0.08,h*0.1)
    part('L',[-w/2,-d/2,kick],[-w/2+t,d/2,h])
    part('R',[w/2-t,-d/2,kick],[w/2,d/2,h])
    part('TOP',[-w/2,-d/2,h-t],[w/2,d/2,h])
    part('BASE',[-w/2,-d/2,kick],[w/2,d/2,kick+t])
    part('BACK',[-w/2,d/2-t,kick],[w/2,d/2,h-t])
    part('PLINTH',[-w/2,-d/2+0.04,0],[w/2,d/2-0.03,kick])
    count=divisions or max(1,math.ceil(w/(0.52 if h>1.3 else 0.60)))
    if open_shelves:
        for n in range(1,count):
            q=-w/2+w*n/count;part(f'DIV_{n}',[q-t/2,-d/2,kick],[q+t/2,d/2,h-t])
        for n in range(1,max(2,round(h/0.34))):
            q=kick+(h-kick)*n/max(2,round(h/0.34));part(f'SHELF_{n}',[-w/2,-d/2,q],[w/2,d/2-t,q+t])
    else:
        for n in range(count):
            a=-w/2+w*n/count;b=-w/2+w*(n+1)/count
            part(f'FRONT_{n}',[a+0.002,-d/2,kick+0.002],[b-0.002,-d/2+t,h-t],MATS['FRONT'])
            handle_h=min(h-0.15,1.15) if h>1.3 else h-0.12
            part(f'PULL_{n}',[b-0.055,-d/2+0.001,handle_h-0.045],
                 [b-0.045,-d/2+t+0.003,handle_h+0.045],MATS['METAL'])
        part('SHELF',[-w/2+t,-d/2+t,h*0.5],[w/2-t,d/2-t,h*0.5+t])
    root['facing_deg']=facing;root['panel_thickness_mm']=18;root['generic_review_details']=True
    return root,objects,dict(actual_front_world=list(R@Vector([0,-1,0])))

def generic_furniture(i,o,cal,col):
    src=i['source_name'];rect=o['rect'];z=UPPER_FFL if i['level']=='upper' else 0
    x0,y0,x1,y1=[v/1000 for v in rect];h=i['height']/1000;kind=i['semantic_type'];f=o.get('semantic_facing_deg')
    root=empty(src,col,src);objs=[]
    def b(label,lo,hi,mat=None):
        ob=box(src+'_'+label,(lo,hi),col,mat or MATS['BODY'],root);objs.append(ob);return ob
    if kind=='HEADBOARD':
        b('PANEL',[x0,y0,z],[x1,y1,z+h],MATS['FRONT'])
        for n in range(1,5):
            yy=y0+(y1-y0)*n/5;b(f'RECESS_{n}',[x0+0.001,yy-0.002,z+0.12],[x0+0.004,yy+0.002,z+h-0.04],MATS['METAL'])
    elif kind in ['NARROW_DESK','BENCH']:
        thick=0.04;b('TOP',[x0,y0,z+h-thick],[x1,y1,z+h],MATS['FRONT'])
        inset=0.035
        for px in [x0+inset,x1-inset-0.04]:
            for py in [y0+inset,y1-inset-0.04]:
                b('LEG',[px,py,z],[px+0.04,py+0.04,z+h-thick],MATS['METAL'])
    elif kind=='STOOL':
        radius=min(x1-x0,y1-y0)/2
        objs.append(cylinder(src+'_SEAT',[(x0+x1)/2,(y0+y1)/2,z+h-0.025],radius,0.05,col,MATS['FRONT'],root))
        for sx in [-1,1]:
            for sy in [-1,1]:
                px=(x0+x1)/2+sx*radius*0.62;py=(y0+y1)/2+sy*radius*0.62
                b('LEG',[px-0.016,py-0.016,z],[px+0.016,py+0.016,z+h-0.05],MATS['METAL'])
    elif kind=='STACKED_WASHER_DRYER':
        for n in range(2):
            zz=z+n*h/2;b(f'BODY_{n}',[x0,y0,zz],[x1,y1,zz+h/2],MATS['APPLIANCE'])
            objs.append(cylinder(src+f'_DOOR_{n}',[(x0+x1)/2,y1-0.008,zz+h/4],min(x1-x0,h/2)*0.31,
                                  0.014,col,MATS['METAL'],root,rotation=(math.pi/2,0,0)))
    elif kind=='FREEZER':
        b('BODY',[x0,y0,z],[x1,y1,z+h],MATS['APPLIANCE'])
        b('LID_SEAM',[x0+0.006,y0+0.006,z+h-0.045],[x1-0.006,y1-0.006,z+h-0.042],MATS['METAL'])
    elif kind=='STUDY_ARMCHAIR':
        # Do not invent a back direction for a chair whose facing is unresolved.
        b('PENDING_DIRECTION',[x0,y0,z],[x1,y1,z+h],MATS['PENDING'])
    else:
        b('DIMENSIONAL_BODY',[x0,y0,z],[x1,y1,z+h],MATS['PENDING'])
    return root,objs,{}

integrity_before=integrity()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
for name in ['05_HUMAN_DESIGN_GUIDE','90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS','03_EXISTING_CEILING']:
    c=bpy.data.collections.get(name)
    if c:
        c.hide_render=True;c.hide_viewport=True

COL={k:collection(v) for k,v in {
    'core':'COL_B11_CORE_FURNITURE','storage':'COL_B11_STORAGE','bath':'COL_B11_BATHROOMS',
    'kitchen':'COL_B11_KITCHEN','openings':'COL_B11_OPENING_DETAILS','bay':'COL_B11_BAY_ASSEMBLIES',
    'edge':'COL_B11_SPLIT_FINISHING','pending':'COL_B11_PENDING_INSTALL','markers':'COL_B11_REVIEW_MARKERS',
    'camera':'COL_B11_REVIEW_CAMERAS'}.items()}
COL['pending'].hide_render=True;COL['pending'].hide_viewport=True
MATS={k:material(k,c) for k,c in {
    'BODY':(0.59,0.65,0.67,1),'FRONT':(0.70,0.69,0.64,1),'FABRIC':(0.53,0.63,0.64,1),
    'METAL':(0.20,0.25,0.28,1),'CERAMIC':(0.88,0.89,0.87,1),
    'APPLIANCE':(0.68,0.73,0.75,1),'GLASS':(0.42,0.72,0.79,0.18),
    'PENDING':(0.81,0.43,0.38,1),'COUNTER':(0.87,0.87,0.83,1)}.items()}
dimensions={i['source_name']:i for i in json_read(DIM)['items']}
orientations={i['source_name']:i for i in json_read(ORI)['items']}
calibrations={i['source_name']:i for i in json_read(CAL)['items']}
decisions=json_read(OUT/'B1_1_DECISIONS.json');allow_overrides=decisions['facing_overrides']['approved']
REGISTER=[];DECISIONS=[];BAYS=[];OPENINGS=[];KITCHEN=[]

def issue(id_,items,description,kind='DESIGN_DECISION_REQUIRED'):
    DECISIONS.append(dict(id=id_,items=items,status=kind,description=description))

issue('INHERITED_MUTABLE_GUIDE_TRANSFORMS',['05_HUMAN_DESIGN_GUIDE'],
      'Imported mutable guide assets have world-origin rotation and old Z-offset defects. Originals retained unchanged and hidden; B1 additions use source-register rectangles.',
      'REPORT_ONLY_SOURCE_DEFECT')
issue('INHERITED_VISUAL_OBSERVATIONS',['LEAF_D107','FASCIA_PLATFORM_CURVE','FLOOR_UPPER'],
      'LEISURE cutaway shows the confirmed D-107 leaf lower-edge offset relative to the adjacent lower-floor view, and surface striping on the inherited curved fascia/floor edge. Source geometry/pose remains unchanged; report the appearance only, do not re-decide the frozen datum or door.',
      'REPORT_ONLY_SOURCE_OBSERVATION')
if not allow_overrides:
    issue('THREE_FACING_CONFLICTS',['Rectangle032','Rectangle030','Rectangle035'],
          'V02 overrides are not human confirmed. Keep these three bodies nondirectional until their front orientation is approved.')
issue('MINI_WASHER_MOUNT_Z',['Rectangle041'],'Wall mounting height and MEP not provided; physical review body hidden; XY helper shown.')
issue('DEVICE_SUPPORT_Z',['Rectangle043','Rectangle044'],'Printer/NAS are intended on/in shelving; exact support level unprovided. Physical bodies hidden; XY helpers shown.')
issue('OWNER_CHAIR_FACING',['Circle007'],'Owner study-chair facing unresolved; nondirectional envelope retained.')
issue('MEDIA_CANDIDATE_DISTORTION',['Rectangle004'],'V02 tv-stand candidate remains SIZE_DISTORTION; native front assumption and final floor-standing/floating solution need review.')
issue('GENERIC_REVIEW_DETAILS',['B1_ALL_NEW_ASSEMBLIES'],'Panel, hardware, door trim and glass profiles are generic review details, not selected products or shop-drawing approval.')
issue('CEILING_COFFER_LIGHT_SLOT',['CEILING_LOWER','CEILING_UPPER'],'Inherited exact ceiling blockout retained. No confirmed coffer, beam, soffit or light-slot dimensions; do not invent.')
issue('BATHROOM_MEP_AND_PRODUCT',['Rectangle008','Rectangle034','Rectangle038','Rectangle030','Rectangle035','Rectangle037'],
      'Fixture envelopes and guide XY modeled; sanitary product SKUs, inlet/outlet/drain installation coordinates and mount heights need confirmation. No hidden plumbing routes inferred.')
issue('OTHER_INTERNAL_DOOR_DETAILS',['FINAL_OPENING_ACTIVE_REGISTER doors'],
      'Nine verified glazed openings and D-107 receive review detailing. Other internal-door entries contain plan symbol bounds; leaf swing/clear widths/hardware need verified dimensions before detailed leaves are installed.')

for src,i in dimensions.items():
    if src.startswith('K-'):continue
    ori=orientations[src];cal=calibrations.get(src,{});rect=ori['rect'];h=i['height']/1000
    kind=i['semantic_type'];z=UPPER_FFL if i['level']=='upper' else 0
    xy=[v/1000 for v in rect];target=[[xy[0],xy[1],z],[xy[2],xy[3],z+h]]
    f=ori.get('semantic_facing_deg');root=None;objs=[];extra={};mode='';verify=True
    is_conflict=src in ['Rectangle032','Rectangle030','Rectangle035'] and not allow_overrides
    if src in ['Rectangle041','Rectangle043','Rectangle044']:
        root,objs,extra=generic_furniture(i,ori,cal,COL['pending']);mode='PENDING_INSTALL_HIDDEN';verify=False
        box(src+'_XY_ONLY_HELPER',([xy[0],xy[1],z+0.002],[xy[2],xy[3],z+0.006]),COL['markers'],MATS['PENDING'])
    elif kind=='SHOWER_ZONE':
        root=empty(src,COL['bath'],src);x0,y0,x1,y1=xy
        # Keep approved wet-zone footprint and semantic access side. Door type remains provisional.
        if f==270: a=(x0,y0);b=(x1,y0)
        elif f==180:a=(x0,y0);b=(x0,y1)
        elif f==90:a=(x0,y1);b=(x1,y1)
        else:a=(x1,y0);b=(x1,y1)
        vector=Vector([b[0]-a[0],b[1]-a[1],0]);length=vector.length
        for n in range(3):
            p=Vector([a[0],a[1],z])+vector*(n/3);q=Vector([a[0],a[1],z])+vector*((n+1)/3)
            glass=beam(src+f'_GLASS_{n}',[p.x,p.y,z+h/2],[q.x,q.y,z+h/2],GLASS_T,COL['bath'],MATS['GLASS'],root)
            # Replace beam shape with proper full-height glass box, retaining world footprint.
            bpy.data.objects.remove(glass,do_unlink=True)
            lo=[min(p.x,q.x),min(p.y,q.y),z+0.025];hi=[max(p.x,q.x),max(p.y,q.y),z+h-0.025]
            if abs(p.x-q.x)<1e-6:lo[0]=p.x;hi[0]=p.x+GLASS_T
            else:lo[1]=p.y;hi[1]=p.y+GLASS_T
            objs.append(box(src+f'_GLASS_{n}',(lo,hi),COL['bath'],MATS['GLASS'],root,bevel=0))
        for n,p in enumerate([a,b]):
            objs.append(box(src+f'_JAMB_{n}',([p[0],p[1],z],[p[0]+0.018,p[1]+0.018,z+h]),COL['bath'],MATS['METAL'],root))
        for zz in [z+0.01,z+h-0.012]:
            objs.append(beam(src+'_TRACK',[a[0],a[1],zz],[b[0],b[1],zz],0.016,COL['bath'],MATS['METAL'],root))
        mid=(Vector([a[0],a[1],z])+Vector([b[0],b[1],z]))/2
        objs.append(beam(src+'_HANDLE',[mid.x,mid.y,z+0.92],[mid.x,mid.y,z+1.1],0.012,COL['bath'],MATS['METAL'],root))
        mode='GLASS_REVIEW_SCREEN';verify=False
        extra['wet_zone_bounds_m']=target;extra['glass_height_mm']=2000;extra['glass_thickness_mm']=8
        extra['opening_mechanism']='PROVISIONAL_3_PANEL_REVIEW; SKU_AND_DOOR_MECHANISM_TO_VERIFY'
        issue(src+'_SHOWER_DETAIL',[src],'2000 mm screen and generic glass hardware are review assumptions; exact enclosure/door mechanism and MEP require confirmation.')
    elif is_conflict:
        root,objs,extra=generic_furniture(i,ori,cal,COL['bath'] if kind=='VANITY' else COL['storage'])
        mode='NONDIRECTIONAL_REVIEW_BODY';verify=True
    elif kind in ['WARDROBE','GUEST_WARDROBE','TALL_BOOKCASE','LOW_BOOKCASE','SHOE_CABINET','CABINET']:
        root,objs,extra=carcass(src,rect,z,h,f,COL['storage'],MATS['BODY'],open_shelves='BOOKCASE' in kind)
        mode='DIMENSIONAL_EDITABLE_CARCASS';verify=True
        extra['V02_candidate_status']=cal.get('classification')
    elif kind=='VANITY':
        root,objs,extra=carcass(src,rect,z,h,f,COL['bath'],MATS['BODY'])
        mode='VANITY_CARCASS_REVIEW';verify=True
        # Countertop/basin mark lies within the dimensional envelope. No product model assumed.
        cx=(xy[0]+xy[2])/2;cy=(xy[1]+xy[3])/2
        objs.append(box(src+'_BASIN_REVIEW',([cx-0.20,cy-0.14,z+h-0.012],[cx+0.20,cy+0.14,z+h]),COL['bath'],MATS['CERAMIC'],root))
    elif cal.get('candidate_asset') and not cal['candidate_asset']['id'].startswith('PRIMITIVE') and kind not in ['STACKED_WASHER_DRYER']:
        asset=cal['candidate_asset'];path=CATALOG/asset['id']/'model.glb'
        mat=MATS['FABRIC'] if kind in ['SOFA_3S','SOFA_2S','CHAISE','BED_BASE'] else MATS['CERAMIC'] if kind=='WC' else MATS['FRONT']
        root,objs,extra=import_calibrated(src,path,rect,h,z,cal['final_yaw_deg'],COL['bath'] if kind=='WC' else COL['core'],mat,asset.get('repeat',1))
        mode='CALIBRATED_LOCAL_CATALOG';verify=True;extra['native_asset_id']=asset['id']
    else:
        root,objs,extra=generic_furniture(i,ori,cal,COL['core']);mode='CUSTOM_DIMENSIONAL_REVIEW'
    root['source_rect_mm']=rect;root['local_ffl_m']=z;root['height_mm']=i['height']
    root['dimension_source']=str(DIM.relative_to(ROOT));root['orientation_source']=str(ORI.relative_to(ROOT))
    root['review_status']='HUMAN_REVIEW';root['semantic_type']=kind
    orientation_status='REGISTER_MATCH' if f is not None and extra.get('actual_front_world') is not None else 'NOT_DIRECTIONAL_OR_PENDING'
    if kind=='CHAISE':
        orientation_status='V02_RECLINE_AXIS_WITH_NORTH_ENTRY';issue('CHAISE_RECLINE_AXIS',[src],'V02 uses east-west recline axis, back at west and open entry north; retain as review candidate, no layout change.')
    if f is not None and extra.get('actual_front_world') is not None and orientation_status=='REGISTER_MATCH':
        ang=math.degrees(math.atan2(extra['actual_front_world'][1],extra['actual_front_world'][0]))%360
        if abs((ang-f+180)%360-180)>0.1:orientation_status='V02_OVERRIDE_HUMAN_CONFIRMED' if allow_overrides else 'REGISTER_CONFLICT'
    REGISTER.append(dict(source_name=src,label=i['label'],semantic_type=kind,room=i['room'],
                         rect_mm=rect,local_ffl_mm=z*1000,height_mm=i['height'],facing_deg=f,
                         base_z_source=i['base_z'],vertical_authority='Z_DATUM_SPEC.json; old offsets superseded',
                         target_bounds_m=target,verify_envelope=verify,body_objects=[p.name for p in objs],
                         assembly=root.name,modeling_mode=mode,orientation_status=orientation_status,
                         calibration_status=cal.get('classification'),review_status='HUMAN_REVIEW',**extra))

# Kitchen: shop drawing owns dimensions; preserve registered XY topology.
kitchen_source=json_read(ROOT/'design/pascal_b1/KITCHEN_CABINET_3D_REGISTER_V01.json')
existing={c['id']:c for c in json_read(ROOT/'current_existing/kitchen_cabinet_register.json')['cabinets']}
for c in kitchen_source['cabinets']:
    c=dict(c);src=c['cabinet_id'];rect=c['rect'];x0,y0,x1,y1=[v/1000 for v in rect]
    prior=dict(height=c['height'],base_z=c['base_z'],depth=c['depth'])
    if src=='K-WALL-E':
        c.update(base_z=1670,height=740);c['pdf_override']='PDF p2: 620 front + 120 closing panel; overall top 2410'
    if src=='K-FRIDGE-OVERHEAD':
        c.update(base_z=1930,height=480);c['pdf_override']='PDF p5: 470 front + 10 top filler, bottom=1930; top=2410'
    z=c['base_z']/1000;h=c['height']/1000;f=180 if src in ['K-RUN-E','K-COOK','K-DISHW','K-BASKET','K-CORNER','K-WALL-E'] else 90 if src in ['K-RUN-S','K-SINK'] else 270
    mode='';verify=True;objects=[]
    if src in ['K-SINK','K-COOK','K-DISHW','K-BASKET']:
        # Subcomponents of the physical runs, never overlapping full solid cabinet boxes.
        root=empty(src,COL['kitchen'],src);verify=False;mode='NESTED_FUNCTIONAL_COMPONENT'
        if src=='K-SINK':
            cx=(x0+x1)/2;cy=(y0+y1)/2
            # Exact source sink 800x430x190, open bowl assembled from base and four sides.
            sx0=cx-0.4;sx1=cx+0.4;sy0=cy-0.215;sy1=cy+0.215;bottom=0.82-0.19
            for label,lo,hi in [
                ('BOTTOM',[sx0,sy0,bottom],[sx1,sy1,bottom+0.008]),
                ('L',[sx0,sy0,bottom],[sx0+0.008,sy1,0.82]),
                ('R',[sx1-0.008,sy0,bottom],[sx1,sy1,0.82]),
                ('S',[sx0,sy0,bottom],[sx1,sy0+0.008,0.82]),
                ('N',[sx0,sy1-0.008,bottom],[sx1,sy1,0.82])]:
                objects.append(box(src+'_'+label,(lo,hi),COL['kitchen'],MATS['METAL'],root))
            objects.append(beam(src+'_TAP_UP',[cx,cy-0.24,0.82],[cx,cy-0.24,1.10],0.018,COL['kitchen'],MATS['METAL'],root))
            objects.append(beam(src+'_TAP_SPOUT',[cx,cy-0.24,1.10],[cx,cy-0.03,1.10],0.018,COL['kitchen'],MATS['METAL'],root))
        elif src=='K-COOK':
            objects.append(box(src+'_HOB',([x0+0.08,y0+0.07,0.82],[x1-0.08,y1-0.07,0.832]),COL['kitchen'],MATS['METAL'],root))
            for py in [y0+0.24,y1-0.24]:objects.append(cylinder(src+'_BURNER',[(x0+x1)/2,py,0.838],0.085,0.012,COL['kitchen'],MATS['APPLIANCE'],root))
            objects.append(box(src+'_HOOD_REVIEW',([x1-0.38,y0,1.60],[x1,y1,1.73]),COL['kitchen'],MATS['METAL'],root))
        elif src=='K-DISHW':
            objects.append(box(src+'_APPLIANCE',([x0,y0+0.002,0.06],[x1-0.01,y1-0.002,0.80]),COL['kitchen'],MATS['APPLIANCE'],root))
            objects.append(box(src+'_CONTROL',([x0,y0+0.015,0.73],[x0+0.007,y1-0.015,0.775]),COL['kitchen'],MATS['METAL'],root))
        else:
            # The physical front already belongs to K-RUN-E_SEG2. Add only hardware,
            # avoiding a second coplanar cabinet front on the same physical module.
            objects.append(box(src+'_PULL_HANDLE',([x0-0.008,y0+0.08,0.69],[x0-0.002,y1-0.08,0.705]),COL['kitchen'],MATS['METAL'],root))
    elif src=='K-FRIDGE':
        # Width/depth is appliance size; register rect was a 700 mm niche placeholder.
        y1=y0+0.710;rect=[x0*1000,y0*1000,x1*1000,y1*1000];c['modeled_rect_mm']=rect
        root=empty(src,COL['kitchen'],src);mode='DIMENSIONAL_APPLIANCE_REVIEW'
        objects.append(box(src+'_BODY',([x0,y0+0.018,z],[x1,y1,z+h]),COL['kitchen'],MATS['APPLIANCE'],root))
        for n in range(2):
            xx=x0+(x1-x0)*n/2
            objects.append(box(src+f'_DOOR_{n}',([xx+0.002,y0,z+0.015],[xx+(x1-x0)/2-0.002,y0+0.018,z+h-0.012]),COL['kitchen'],MATS['BODY'],root))
        objects.append(box(src+'_PULL',([x0+(x1-x0)/2-0.013,y0+0.001,z+0.3],[x0+(x1-x0)/2+0.013,y0+0.005,z+1.35]),COL['kitchen'],MATS['METAL'],root))
    elif src=='K-TALL-L':
        root=empty(src,COL['kitchen'],src);mode='PDF_LOWER_NICHE_UPPER_ASSEMBLY'
        # Split within same registered envelope; exact lateral split is pending.
        sub,body,_=carcass(src+'_BASE',rect,0,0.82,f,COL['kitchen'],MATS['BODY']);sub.parent=root;objects.extend(body)
        sub,body,_=carcass(src+'_UPPER',rect,1.67,0.74,f,COL['kitchen'],MATS['BODY']);sub.parent=root;objects.extend(body)
        objects.append(box(src+'_BACK',([x0,y1-0.018,0.82],[x1,y1,1.67]),COL['kitchen'],MATS['BODY'],root))
        issue('K_TALL_INTERNAL_SPLIT',[src],'Registered XY retained. PDF shows appliance niche; the register full-height solid is replaced by lower/upper review bodies, while the internal lateral/corner split needs confirmation.')
    else:
        # K-RUN-E leaves a dishwasher bay instead of a second intersecting solid.
        if src=='K-RUN-E':
            root=empty(src,COL['kitchen'],src);mode='DISJOINT_EDITABLE_RUN'
            for n,rr in enumerate([[7200,535,7800,1800],[7200,2400,7800,3300],[7200,3300,7800,3750]]):
                sub,body,_=carcass(src+f'_SEG{n}',rr,z,0.80,f,COL['kitchen'],MATS['BODY']);sub.parent=root;objects.extend(body)
            objects.append(box(src+'_COUNTER',([x0,y0,0.80],[x1,y1,0.82]),COL['kitchen'],MATS['COUNTER'],root))
        elif src=='K-RUN-S':
            root=empty(src,COL['kitchen'],src);mode='SINK_COUNTER_ASSEMBLY'
            sub,body,_=carcass(src+'_BODY',rect,0,0.80,f,COL['kitchen'],MATS['BODY']);sub.parent=root;objects.extend(body)
            # The sink counter has its own open ring, so remove this generic full top.
            for ob in list(objects):
                if ob.name=='B11_K-RUN-S_BODY_TOP':
                    objects.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
            # Counter ring leaves the exact 800x430 sink cutout empty.
            cx=(6.1+7.09)/2;cy=0.30;sx0=cx-.4;sx1=cx+.4;sy0=cy-.215;sy1=cy+.215
            for n,rr in enumerate([[x0,y0,sx0,y1],[sx1,y0,x1,y1],[sx0,y0,sx1,sy0],[sx0,sy1,sx1,y1]]):
                objects.append(box(src+f'_COUNTER_{n}',([rr[0],rr[1],.80],[rr[2],rr[3],.82]),COL['kitchen'],MATS['COUNTER'],root))
        else:
            root,objects,_=carcass(src,rect,z,h,f,COL['kitchen'],MATS['BODY'])
            mode='DIMENSIONAL_EDITABLE_CARCASS'
    root['source_name']=src;root['source_rect_mm']=c.get('modeled_rect_mm',c['rect']);root['review_status']='HUMAN_REVIEW'
    target=[[x0,y0,z],[x1,y1,z+h]]
    ref=existing.get(src,{})
    c.update(prior_3d_values=prior,dimension_status=ref.get('dimension_status',c['confidence']),
             placement_status=ref.get('placement_status','TO_VERIFY'),review_status='HUMAN_REVIEW',
             body_objects=[p.name for p in objects],assembly=root.name,modeling_mode=mode,
             target_bounds_m=target,verify_envelope=verify)
    KITCHEN.append(c)
    REGISTER.append(dict(source_name=src,label=src,semantic_type=c['type'],room='R-KITCHEN',
                         rect_mm=c.get('modeled_rect_mm',c['rect']),local_ffl_mm=0,height_mm=c['height'],
                         target_bounds_m=target,verify_envelope=verify,body_objects=c['body_objects'],
                         assembly=root.name,modeling_mode=mode,orientation_status='PDF_REVIEW',facing_deg=f,
                         review_status='HUMAN_REVIEW'))
issue('KITCHEN_PLACEMENT_AND_NICHE',['K-COOK','K-DISHW','K-BASKET','K-FRIDGE','K-RUN-S','K-SINK'],
      'XY remains as registered. Appliance/corner module positions and south-leg origin are TO_VERIFY in existing cabinet register. Internal fridge/tall splits conflict with PDF chains; no automatic topology change.')
issue('KITCHEN_TOP_AND_DEPTH',['K-WALL-E','K-FRIDGE-OVERHEAD'],
      'PDF p2 and p5 explicit vertical dimensions supersede temporary approximations. Overhead depth remains provisional 600; module splits/installation require review.')

# Nine frozen openings: new review frames overlay existing envelopes without changing the existing meshes.
opening_register=json_read(ROOT/'design/pascal_b1/wall_audit/FINAL_OPENING_ACTIVE_REGISTER.json')['windows']
bay_ids={w['window_id'] for w in opening_register if w['type']=='BAY_WINDOW'}
def framed_panel(src,rect,z0,z1,parent,col,pieces=2):
    x0,y0,x1,y1=[v/1000 for v in rect];horizontal=(x1-x0)>(y1-y0);t=0.035
    obs=[]
    if horizontal:
        mid=(y0+y1)/2
        for px in [x0,x1-t]:obs.append(box(src+'_JAMB',([px,mid-.023,z0],[px+t,mid+.023,z1]),col,MATS['METAL'],parent))
        for zz in [z0,z1-t]:obs.append(box(src+'_RAIL',([x0,mid-.023,zz],[x1,mid+.023,zz+t]),col,MATS['METAL'],parent))
        for n in range(pieces):
            a=x0+(x1-x0)*n/pieces+t;b=x0+(x1-x0)*(n+1)/pieces-t
            obs.append(box(src+f'_GLASS{n}',([a,mid-GLASS_T/2,z0+t],[b,mid+GLASS_T/2,z1-t]),col,MATS['GLASS'],parent,bevel=0))
            if n:obs.append(box(src+'_MULLION',([a-t,mid-.023,z0],[a,mid+.023,z1]),col,MATS['METAL'],parent))
    else:
        mid=(x0+x1)/2
        for py in [y0,y1-t]:obs.append(box(src+'_JAMB',([mid-.023,py,z0],[mid+.023,py+t,z1]),col,MATS['METAL'],parent))
        for zz in [z0,z1-t]:obs.append(box(src+'_RAIL',([mid-.023,y0,zz],[mid+.023,y1,zz+t]),col,MATS['METAL'],parent))
        for n in range(pieces):
            a=y0+(y1-y0)*n/pieces+t;b=y0+(y1-y0)*(n+1)/pieces-t
            obs.append(box(src+f'_GLASS{n}',([mid-GLASS_T/2,a,z0+t],[mid+GLASS_T/2,b,z1-t]),col,MATS['GLASS'],parent,bevel=0))
    return obs

for w in opening_register:
    src=w['window_id'];original=bpy.data.objects['GLZ_'+src];z0,z1=world_bounds([original])[0][2],world_bounds([original])[1][2]
    root=empty('OPENING_'+src,COL['openings'],src)
    obs=framed_panel(src+'_HOST',w['opening_rect_mm'],z0,z1,root,COL['openings'],pieces=3 if src=='G-DIN-LIV' else 2)
    if src=='G-DIN-LIV':
        x0,y0,x1,y1=[v/1000 for v in w['opening_rect_mm']]
        for n in range(3):box(src+f'_SLIDING_TRACK_{n}',([x0,y0+0.04*n,z0],[x1,y0+0.04*n+0.018,z0+0.015]),COL['openings'],MATS['METAL'],root)
    OPENINGS.append(dict(id=src,inherited_object=original.name,inherited_geometry_preserved=True,
                         review_assembly=root.name,new_objects=[p.name for p in obs],z0_m=z0,z1_m=z1))
    if src in bay_ids:
        bay=w['bay'];front=bay['front'];jambs=bay['jambs'];br=empty('BAY_'+src,COL['bay'],src)
        # XY from finalized active register, Z inherited from the frozen opening.
        obs=framed_panel('BAY_'+src+'_FRONT',front,z0,z1,br,COL['bay'],pieces=3)
        x0=min(r[0] for r in jambs)/1000;x1=max(r[2] for r in jambs)/1000
        y0=min(r[1] for r in jambs)/1000;y1=max(r[3] for r in jambs)/1000
        platform=box('BAY_'+src+'_SILL_PLATFORM',([x0,y0,z0-.025],[x1,y1,z0]),COL['bay'],MATS['COUNTER'],br)
        br['geometry_authority']='FINAL_OPENING_ACTIVE_REGISTER bay XY + frozen GLZ Z';br['review_status']='HUMAN_REVIEW'
        BAYS.append(dict(id=src,projection_mm=w['projection_mm'],front_rect_mm=front,cheek_rects_mm=jambs,
                         sill_z_inherited_m=z0,head_z_inherited_m=z1,assembly=br.name,
                         body_objects=[p.name for p in obs]+[platform.name],
                         original_cheeks_preserved=True,front_interference_status='REPORT_ONLY_EXISTING_FULL_HEIGHT_BAND'))
issue('BAY_FRONT_SOURCE_INTERFERENCE',sorted(bay_ids),
      'Frozen bay outlines are retained. Existing front wall bands appear full height and overlap the new front glazing review assemblies. Existing flat host glazing also remains. Report only; no cut, movement or redesign of frozen walls/openings.')

# D-107 hardware uses the inherited leaf's local coordinate system and angle.
leaf=bpy.data.objects['LEAF_D107'];root=empty('D107_DETAIL',COL['openings'],'D-107');lb=[Vector(v) for v in leaf.bound_box]
lo=[min(v[i] for v in lb) for i in range(3)];hi=[max(v[i] for v in lb) for i in range(3)]
for n,zz in enumerate([lo[2]+0.25,(lo[2]+hi[2])/2,hi[2]-.25]):
    local=Vector([lo[0]+0.02,(lo[1]+hi[1])/2,zz]);p=leaf.matrix_world@local
    cylinder(f'D107_HINGE_{n}',p,0.009,0.07,COL['openings'],MATS['METAL'],root)
p=leaf.matrix_world@Vector([hi[0]-0.09,lo[1],lo[2]+0.95]);q=leaf.matrix_world@Vector([hi[0]-0.18,lo[1],lo[2]+0.95])
beam('D107_HANDLE',p,q,0.01,COL['openings'],MATS['METAL'],root)
root['angle_deg']=math.degrees(leaf.rotation_euler.z);root['leaf_authority']='LEAF_D107 unchanged'

# Stair finishing stays at approved top datums; no addition above FFL.
for n in range(3):
    step=bpy.data.objects[f'STEP_{n}'];lo,hi=world_bounds([step]);zz=hi[2]
    box(f'STEP_{n}_REVIEW_NOSING',([lo[0],lo[1],zz-.008],[lo[0]+.012,hi[1],zz]),COL['edge'],MATS['METAL'])
    for j in range(3):
        xx=lo[0]+.04+j*.04
        box(f'STEP_{n}_SLIP_GROOVE_{j}',([xx,lo[1]+.025,zz-.001],[xx+.003,hi[1]-.025,zz]),COL['edge'],MATS['METAL'],bevel=0)
fascia=bpy.data.objects['FASCIA_PLATFORM_CURVE'];root=empty('LEISURE_CURVE_FINISH',COL['edge'],'FASCIA_PLATFORM_CURVE')
points=sorted({(round((fascia.matrix_world@v.co).x,6),round((fascia.matrix_world@v.co).y,6)) for v in fascia.data.vertices})
# Trim follows existing mesh edges; never use raster or a new inferred outline.
edges=set()
for edge in fascia.data.edges:
    a=fascia.matrix_world@fascia.data.vertices[edge.vertices[0]].co;b=fascia.matrix_world@fascia.data.vertices[edge.vertices[1]].co
    if abs(a.z-.45)<1e-5 and abs(b.z-.45)<1e-5 and (a-b).length<.25:
        key=tuple(sorted([(round(a.x,6),round(a.y,6)),(round(b.x,6),round(b.y,6))]))
        if key in edges:continue
        edges.add(key);beam(f'LEISURE_CURVE_TRIM_{len(edges):03d}',[a.x,a.y,.444],[b.x,b.y,.444],.006,COL['edge'],MATS['METAL'],root)
issue('SPLIT_EDGE_PROFILE',['STEP_0','STEP_1','STEP_2','FASCIA_PLATFORM_CURVE'],'Generic nosing and in-datum edge strip only. No railing, ramp or leisure demolition; finish product and railing intent require review.')

scene=bpy.context.scene;scene['B1_1_DESIGN_MODEL']='HUMAN_REVIEW';scene['B0_INTEGRITY']='PASS'
scene['source_blend']=str(SOURCE);scene['source_manifest']='B0_FREEZE_MANIFEST.json'
scene['design_scope']='INHERITED_LAYOUT; REVIEW_MATERIALS_ONLY; NO_REDESIGN'
scene['pending_decisions_count']=len(DECISIONS)
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.studiolight_rotate_z=0.45
scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=False
scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
scene.display.shading.curvature_ridge_factor=1.2;scene.display.shading.curvature_valley_factor=1.0
scene.display.shading.show_specular_highlight=True
scene.display.shading.background_type='WORLD';scene.world.color=(.92,.93,.94)
scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard'
scene.render.film_transparent=False

# B1 review cameras; viewing cuts are applied only during evidence rendering.
camera_specs={
 'TOP':((8.9,6.6,30),(8.9,6.6,0),22.0),
 'AXON':((25,-21,25),(8.9,6.5,.6),24.0),
 'LIVING':((-.5,16.5,7.2),(5.25,10.4,.75),7.9),
 'KITCHEN':((2.0,-3.6,5.3),(6.85,2.25,1.0),6.9),
 'LEISURE':((2.0,2.7,5.6),(7.25,6.5,.65),5.8),
 'OWNER_BED':((6.7,-3.6,5.9),(9.75,2.4,.85),5.8),
 'MOTHER_BED':((10.7,-3.7,6.1),(13.75,2.4,.9),6.0),
 'STUDY':((10.0,12.8,7.0),(14.85,8.6,1.0),6.4),
 'GUEST_BED':((6.7,11.7,6.6),(11.45,9.35,.9),5.5),
 'BATH_OWNER':((7.7,2.5,4.5),(10.2,5.6,1.0),3.25),
 'BATH_MOTHER':((11.7,2.4,4.6),(14.65,5.5,1.0),3.9),
 'BATH_GUEST':((5.8,11.4,5.0),(8.95,9.5,1.0),4.0)}
camera_register=[]
for name,(location,target,scale) in camera_specs.items():
    data=bpy.data.cameras.new('B11_CAM_'+name);o=bpy.data.objects.new('B11_CAM_'+name,data);COL['camera'].objects.link(o)
    o.location=location;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO';data.ortho_scale=scale;data.lens=40;data.clip_end=100
    camera_register.append(dict(name=name,object=o.name,position_m=location,target_m=target,ortho_scale=scale,
                                purpose='DIMENSIONAL_CUTAWAY_REVIEW'))
scene.camera=bpy.data.objects['B11_CAM_AXON']
if bpy.context.screen:
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
integrity_after=integrity()
asset_register=dict(register='B1_1_ASSET_REGISTER',status='HUMAN_REVIEW',units='m/mm/deg as named',
                    source_priority=dict(geometry='FROZEN B0',placement=str(ORI.relative_to(ROOT)),
                    dimensions=str(DIM.relative_to(ROOT)),asset_calibration=str(CAL.relative_to(ROOT)),kitchen='source cabinet PDF'),
                    inherited_source_report='SOURCE_SCENE_SNAPSHOT.json',items=REGISTER,
                    bay_assemblies=BAYS,opening_details=OPENINGS,review_cameras=camera_register,
                    decisions_required=DECISIONS,
                    invariants=dict(split_level_ffl_mm=[0,450],ceiling_mm=[2800,3250],stairs_mm=[150,300,450],
                                    d107_deg=26.3,verified_openings=9,bay_count=4,no_redesign=True))
(OUT/'B1_1_ASSET_REGISTER.json').write_text(json.dumps(asset_register,ensure_ascii=False,indent=2))
(OUT/'KITCHEN_CABINET_3D_REGISTER_V01.json').write_text(json.dumps(dict(register='KITCHEN_CABINET_3D_REGISTER_V01',
    stage='B1.1',status='HUMAN_REVIEW',units='mm',authority='source/世纪欣园3-1-901_cabinet_plan.pdf',
    source_register='design/pascal_b1/KITCHEN_CABINET_3D_REGISTER_V01.json',
    confirmed_facts=dict(countertop_top=820,base_depth=600,wall_depth=380,overall_top=2410,fridge=[905,710,1700],
                         wall_front_height=620,wall_top_closing_panel=120,fridge_overhead_front_height=470,fridge_overhead_base=1930),
    cabinetry=KITCHEN,notes='Registered XY retained; installation, internal splits and unresolved depth/placements remain TO_VERIFY.'),ensure_ascii=False,indent=2))
(OUT/'B1_1_BUILD_INTEGRITY.json').write_text(json.dumps(dict(before=integrity_before,after=integrity_after),indent=2))
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))
print('B1_1_DESIGN_MODEL = HUMAN_REVIEW')
print(json.dumps(dict(model=str(MODEL),assemblies=len(REGISTER),bays=len(BAYS),pending_decisions=len(DECISIONS),
                      total_objects=len(bpy.data.objects)),indent=2))
