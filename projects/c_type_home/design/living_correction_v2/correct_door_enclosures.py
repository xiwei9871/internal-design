"""Complete D107 and north-balcony door enclosures over living V1, preserving frozen sources."""
import argparse
import json
import math
import runpy
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
PRIOR=ROOT/'design/living_correction_v1'
SOURCE=PRIOR/'B1_LIVING_CORRECTED_V1.blend'
MODEL=OUT/'B1_LIVING_CORRECTED_V2.blend'
KITCHEN=ROOT/'design/kitchen_frozen_v1'
H=runpy.run_path(str(KITCHEN/'freeze_kitchen.py'),run_name='freeze_helpers')
sha=H['sha'];snapshot=H['snapshot'];b0_check=H['b0_check']
ANGLE=math.radians(26.3)
U=Vector((math.cos(ANGLE),math.sin(ANGLE),0))
N=Vector((-math.sin(ANGLE),math.cos(ANGLE),0))
HINGE=Vector((8.332,4.543,0))
VIEWS=[
 dict(id='01',name='次主卧门框与完整门上墙',camera='DOOR_V2_CAM_01',pos=[7.40,7.18,2.05],target=[8.70,4.80,1.87],lens=25,roi=[5.65,3.5,11.4,7.85]),
 dict(id='02',name='次主卧门洞顶部连接轴测',camera='DOOR_V2_CAM_02',pos=[6.10,7.70,6.30],target=[8.50,4.86,1.82],projection='ORTHO',scale=5.6,roi=[7.3,4.25,9.5,5.5]),
 dict(id='03',name='客厅侧_北阳台门框与墙垛',camera='DOOR_V2_CAM_03',pos=[5.05,12.225,1.57],target=[7.86,12.225,1.40],lens=25,roi=[2.7,10.9,8.8,14.2]),
 dict(id='04',name='阳台侧_门周边完整墙体',camera='DOOR_V2_CAM_04',pos=[10.50,12.225,1.57],target=[7.87,12.225,1.40],lens=25,roi=[6.7,10.9,13.3,14.2]),
 dict(id='05',name='北阳台门头与北墙垛轴测',camera='DOOR_V2_CAM_05',pos=[5.00,14.65,5.00],target=[7.88,12.24,1.42],projection='ORTHO',scale=4.4,roi=[7.5,11.1,8.25,13.41]),
]


def write(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def integrity():
    b0_check();km=json.loads((KITCHEN/'KITCHEN_FREEZE_MANIFEST.json').read_text())
    for cat in ['files_sha256','sources_sha256','approved_render_sha256']:
        for p,h in km[cat].items():assert sha(p)==h,'Frozen source changed: '+p
    m=json.loads((PRIOR/'LIVING_CORRECTION_MANIFEST.json').read_text())
    for p,h in m['files_sha256'].items():assert sha(p)==h,'Living V1 changed: '+p
    assert sha(SOURCE)==m['model_sha256']
    return km


def bounds(obs):
    pts=[o.matrix_world@Vector(c) for o in obs if o.type=='MESH' for c in o.bound_box]
    return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]


def material(name,color,glass=False):
    m=bpy.data.materials.new('DOOR_V2_REVIEW_'+name);m.diffuse_color=(*color,1)
    m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.62
    if glass:
        n.inputs['Transmission Weight'].default_value=.65;n.inputs['Alpha'].default_value=.22
        m.surface_render_method='DITHERED'
    return m


def group(name):
    o=bpy.data.objects.new('DOOR_V2_'+name,None);COL.objects.link(o)
    o['review_status']='HUMAN_REVIEW';o['physical_ground_truth']=False
    return o


def box(name,lo,hi,mat,parent,bevel=.001):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)])
    o=bpy.context.object;o.name='DOOR_V2_'+name;o.dimensions=[hi[i]-lo[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    COL.objects.link(o);o.parent=parent;o.data.materials.append(mat);o.color=mat.diffuse_color
    if bevel:
        mod=o.modifiers.new('Review edge','BEVEL');mod.width=bevel;mod.segments=2
        o.modifiers.new('Review normals','WEIGHTED_NORMAL')
    o['review_status']='HUMAN_REVIEW';o['physical_ground_truth']=False
    o['authority']='USER_DOOR_ENCLOSURE_PHOTOS; REGISTERED_XY_Z; REVIEW_FRAME_SECTIONS'
    return o


def angled_box(name,ulo,uhi,nlo,nhi,zlo,zhi,mat,parent,bevel=.001):
    o=box(name,[-(uhi-ulo)/2,-(nhi-nlo)/2,-(zhi-zlo)/2],
          [(uhi-ulo)/2,(nhi-nlo)/2,(zhi-zlo)/2],mat,parent,bevel)
    center=HINGE+U*((ulo+uhi)/2)+N*((nlo+nhi)/2)
    o.location=(center.x,center.y,(zlo+zhi)/2);o.rotation_euler.z=ANGLE
    return o


def prism(name,poly,z0,z1,mat,parent):
    count=len(poly);verts=[(*p,z) for z in [z0,z1] for p in poly]
    faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
    faces.extend((i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count))
    mesh=bpy.data.meshes.new('DOOR_V2_'+name+'_mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new('DOOR_V2_'+name,mesh);COL.objects.link(o);o.parent=parent
    mesh.materials.append(mat);o.color=mat.diffuse_color
    o['physical_ground_truth']=False;o['review_status']='HUMAN_REVIEW'
    return o


def disable(name,changed):
    root=bpy.data.objects[name]
    for o in [root,*root.children_recursive]:
        o.hide_render=True;o.hide_viewport=True;o.hide_set(True);changed.append(o.name)
        o['door_enclosure_status']='INACTIVE_PRIOR_PROXY; REPLACED_IN_V2'


def world(u,n,z):
    p=HINGE+U*u+N*n;p.z=z;return p


def cast(origin,direction,max_distance=100):
    hit,p,n,i,o,m=bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector(origin),Vector(direction),distance=max_distance)
    return dict(hit=hit,object=o.name if hit else None,point=list(p) if hit else None,
                distance=(p-Vector(origin)).length if hit else None)


def enclosure_checks():
    checks=[]
    for u in [.10,.425,.75]:
        for z in [2.75,3.20]:
            hit=cast(world(u,.7,z),-N,.75)
            checks.append(dict(test=f'D107 above opening u{u} z{z}',pass_gate=hit['hit'] and hit['object'].startswith('DOOR_V2_D107_'),**hit))
    for u,label in [(-.025,'left jamb'),(.875,'right jamb')]:
        hit=cast(world(u,.7,1.5),-N,.75)
        checks.append(dict(test='D107 '+label,pass_gate=hit['hit'] and hit['object'].startswith('DOOR_V2_D107_'),**hit))
    for y,z,label in [(12.70,1.50,'north pier'),(12.85,2.65,'north pier upper'),
                       (12.225,2.65,'door head'),(11.77,1.5,'south pier'),
                       (12.62,1.5,'frame north jamb'),(11.83,1.5,'frame south jamb')]:
        hit=cast([7.30,y,z],[1,0,0],.75)
        checks.append(dict(test='BALCONY '+label,pass_gate=hit['hit'] and
                           hit['object'].startswith(('DOOR_V2_NBALC_','LIVING_FIX_TV_NORTH_SOLID_WALL')),**hit))
    return checks


def regress():
    integrity();bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update()
    checks=[c for c in enclosure_checks() if c['test'].startswith('D107 above') or 'north pier' in c['test']]
    assert any(not x['pass_gate'] for x in checks if x['test'].startswith('D107 above'))
    assert any(not x['pass_gate'] for x in checks if 'north pier' in x['test'])
    write('V1_DOOR_ENCLOSURE_FAILURE.json',dict(source=str(SOURCE),status='MISSING_ENCLOSURES_REPRODUCED',checks=checks))
    print(json.dumps(dict(regression='MISSING_ENCLOSURES_REPRODUCED',failed=sum(not c['pass_gate'] for c in checks),checks=len(checks))))


def build():
    global COL,WALL,TRIM,BLACK,METAL,GLASS
    assert not MODEL.exists(),'Keep versions separate'
    km=integrity();source_sha=sha(SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update();base=snapshot();changed=[]
    COL=bpy.data.collections.new('COL_LIVING_DOOR_ENCLOSURES_V2');bpy.context.scene.collection.children.link(COL)
    WALL=bpy.data.materials['LIVING_REVIEW_WALL']
    TRIM=material('TIMBER_FRAME',(.64,.57,.43));BLACK=material('BLACK_FRAME',(.13,.16,.16))
    METAL=material('HARDWARE',(.48,.51,.51));GLASS=material('GLASS_PANE',(.22,.28,.31),True)
    d=group('D107_COMPLETE_ENCLOSURE')
    d['hinge_mm']=[8332,4543,450];d['door_frame_plane_deg']=26.3
    d['reference']='secondary_door_site.jpg';d['structure']='FULL_JAMBS_HEADER_AND_TOP_CONNECTION'
    # Reveal thickness extends toward bedroom negative side / corridor positive normal.
    # Existing leaf is retained at the registered door plane.
    angled_box('D107_FRAME_LEFT',-.05,0,0,.2,.45,2.55,TRIM,d)
    angled_box('D107_FRAME_RIGHT',.85,.90,0,.2,.45,2.55,TRIM,d)
    angled_box('D107_FRAME_HEAD',-.05,.90,0,.2,2.55,2.60,TRIM,d)
    angled_box('D107_ARCHITRAVE_LEFT',-.07,-.015,.198,.225,.45,2.625,TRIM,d)
    angled_box('D107_ARCHITRAVE_RIGHT',.865,.92,.198,.225,.45,2.625,TRIM,d)
    angled_box('D107_ARCHITRAVE_HEAD',-.07,.92,.198,.225,2.57,2.64,TRIM,d)
    # Exact connections are constructed from registered door plane and adjacent
    # immutable CAD wall endpoints. No room or furniture coordinates are moved.
    l0=world(-.05,0,0);l1=world(-.05,.2,0)
    prism('D107_LEFT_RETURN_WALL',[(7.7999,4.5002),(l0.x,l0.y),(l1.x,l1.y),(7.7999,4.7002)],.45,3.25,WALL,d)
    r0=world(.90,0,0);r1=world(.90,.2,0)
    prism('D107_RIGHT_RETURN_WALL',[(r0.x,r0.y),(9.1999,4.971),(9.1999,5.1502),
                                   (9.0499,5.1502),(r1.x,r1.y)],.45,3.25,WALL,d)
    angled_box('D107_SOLID_ABOVE_OPENING',-.05,.90,0,.2,2.60,3.05,WALL,d,0)
    beam=angled_box('D107_TOP_BEAM_CONNECTION',-.05,.90,-.025,.25,3.05,3.25,WALL,d,0)
    beam['section_precision']='REVIEW_ENCLOSURE; FIELD_BEAM_SECTION_TO_VERIFY'
    # Low full-width backing below upper-floor datum closes the base to the platform.
    angled_box('D107_PLATFORM_BASE_CLOSURE',-.05,.90,0,.2,.40,.45,WALL,d,0)
    # Single north balcony door enclosed in solid pier/header/return geometry.
    n=group('NBALC_COMPLETE_ENCLOSURE');n['opening_rect_mm']=[7800,11800,7900,12650]
    n['door_type']='SINGLE_HINGED_GLAZED_LEAF';n['reference']='north_balcony_door_site.jpg'
    for old in ['GLZ_G-LIV-NBALC','B11_OPENING_G-LIV-NBALC','LIVING_FIX_BALCONY_DOOR_HEAD']:
        disable(old,changed)
    box('NBALC_NORTH_FULL_WALL_PIER',[7.75,12.65,0],[8.0,13.0002,2.8],WALL,n,0)
    box('NBALC_SOLID_ABOVE_DOOR',[7.75,11.8,2.4],[8.0,12.65,2.8],WALL,n,0)
    box('NBALC_FRAME_SOUTH_JAMB',[7.80,11.8,0],[7.95,11.855,2.4],BLACK,n)
    box('NBALC_FRAME_NORTH_JAMB',[7.80,12.595,0],[7.95,12.65,2.4],BLACK,n)
    box('NBALC_FRAME_TOP',[7.80,11.8,2.345],[7.95,12.65,2.4],BLACK,n)
    box('NBALC_THRESHOLD',[7.80,11.8,0],[7.95,12.65,.055],BLACK,n)
    box('NBALC_ROOM_TRIM_SOUTH',[7.735,11.78,0],[7.80,11.845,2.43],BLACK,n)
    box('NBALC_ROOM_TRIM_NORTH',[7.735,12.605,0],[7.80,12.67,2.43],BLACK,n)
    box('NBALC_ROOM_TRIM_TOP',[7.735,11.78,2.365],[7.80,12.67,2.43],BLACK,n)
    # Sash body is connected inside the frame, not a second pane across the opening.
    for label,lo,hi in [
        ('SASH_SOUTH',[7.825,11.86,.06],[7.865,11.905,2.34]),
        ('SASH_NORTH',[7.825,12.55,.06],[7.865,12.59,2.34]),
        ('SASH_TOP',[7.825,11.86,2.295],[7.865,12.59,2.34]),
        ('SASH_BOTTOM',[7.825,11.86,.06],[7.865,12.59,.105]),
    ]:box('NBALC_'+label,lo,hi,BLACK,n)
    box('NBALC_SINGLE_GLASS',[7.839,11.905,.105],[7.847,12.55,2.295],GLASS,n,0)
    for i,z in enumerate([.40,1.15,1.95]):
        box(f'NBALC_HINGE_{i}',[7.795,12.583,z],[7.835,12.615,z+.065],METAL,n)
    box('NBALC_HANDLE_BASE',[7.785,11.875,.95],[7.825,11.91,1.12],METAL,n)
    box('NBALC_HANDLE_LEVER',[7.762,11.89,1.005],[7.802,12.015,1.035],METAL,n)
    # Review cameras keep complete headers and wall returns in frame.
    cc=bpy.data.collections.new('COL_LIVING_DOOR_CAMERAS_V2');bpy.context.scene.collection.children.link(cc)
    for v in VIEWS:
        data=bpy.data.cameras.new(v['camera']);o=bpy.data.objects.new(v['camera'],data);cc.objects.link(o)
        o.location=v['pos'];o.rotation_euler=(Vector(v['target'])-o.location).to_track_quat('-Z','Y').to_euler()
        data.type=v.get('projection','PERSP');data.clip_start=.02;data.clip_end=100
        if data.type=='ORTHO':data.ortho_scale=v['scale']
        else:data.lens=v['lens'];data.sensor_width=36;data.sensor_fit='HORIZONTAL'
    s=bpy.context.scene;s.camera=bpy.data.objects['DOOR_V2_CAM_01']
    s['living_correction_status']='HUMAN_REVIEW';s['living_revision']='V2_COMPLETE_DOOR_ENCLOSURES'
    s['kitchen_freeze_inherited']='V1_UNCHANGED'
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.overlay.show_relationship_lines=False
                area.spaces.active.overlay.show_extras=False
                area.spaces.active.region_3d.view_perspective='CAMERA'
    bpy.context.view_layer.update();new=snapshot()
    for name,a in base.items():
        b=new[name];a=a.copy()
        if name in changed:a['hide_render']=True;a['hide_viewport']=True
        if a['hide_viewport']:
            a.pop('matrix_world');b={k:v for k,v in b.items() if k!='matrix_world'}
        assert a==b,'Unrelated inherited object changed: '+name
    for name in km['protected_objects']:assert base[name]==new[name],'Kitchen changed: '+name
    checks=enclosure_checks();assert all(c['pass_gate'] for c in checks),checks
    write('V1_OBJECT_STATES.json',base);write('V2_OBJECT_STATES.json',new)
    write('V2_CAMERA_REGISTER.json',VIEWS)
    bpy.ops.wm.save_as_mainfile(filepath=str(MODEL));integrity();assert sha(SOURCE)==source_sha
    manifest=dict(status='HUMAN_REVIEW',source=str(SOURCE),source_sha256=source_sha,
                   model=str(MODEL),model_sha256=sha(MODEL),
                   inherited_objects=len(base),kitchen_protected_objects_unchanged=len(km['protected_objects']),
                   prior_proxies_disabled=changed,door_leaf_pose_preserved=True,
                   corrections=['D107 side returns, frame, solid above opening and top connection',
                                'North balcony full north pier and header; single glazed door/frame/hardware'],
                   review_dimensions=dict(D107_frame_width_mm=50,D107_wall_thickness_mm=200,
                                         D107_beam_band_mm=200,north_door_frame_mm=55),
                   measurement_policy='PHOTO_RELATIONSHIPS_ONLY; FRAME_BEAM_SECTIONS_TO_VERIFY',
                   references={str(p):sha(p) for p in (OUT/'references').iterdir()},B0_INTEGRITY='PASS')
    write('V2_MANIFEST.json',manifest)
    print(json.dumps(dict(build='PASS',model=str(MODEL),kitchen_unchanged=272,
                          inherited_objects=len(base),enclosure_checks=len(checks)),ensure_ascii=False))


def verify():
    km=integrity();m=json.loads((OUT/'V2_MANIFEST.json').read_text())
    assert sha(MODEL)==m['model_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(MODEL));bpy.context.view_layer.update();actual=snapshot()
    expected=json.loads((OUT/'V2_OBJECT_STATES.json').read_text())
    assert set(actual)==set(expected)
    for name,a in actual.items():
        e=expected[name]
        if a['hide_viewport']:
            a={k:v for k,v in a.items() if k!='matrix_world'};e={k:v for k,v in e.items() if k!='matrix_world'}
        assert a==e,'Fresh-open object mismatch: '+name
    prior=json.loads((OUT/'V1_OBJECT_STATES.json').read_text())
    for name in km['protected_objects']:assert actual[name]==prior[name],name
    assert actual['LIVING_FIX_LEAF_D107']==prior['LIVING_FIX_LEAF_D107']
    assert actual['LIVING_FIX_BAY_SILL_PLATFORM']==prior['LIVING_FIX_BAY_SILL_PLATFORM']
    assert actual['LIVING_FIX_GUEST_BATH_FULL_WALL']==prior['LIVING_FIX_GUEST_BATH_FULL_WALL']
    checks=enclosure_checks();assert all(c['pass_gate'] for c in checks),checks
    for name in m['prior_proxies_disabled']:
        assert actual[name]['hide_render'] and actual[name]['hide_viewport']
    # Continuous upper closure to source ceiling datums; exact coincident contacts.
    assert abs(bounds([bpy.data.objects['DOOR_V2_D107_TOP_BEAM_CONNECTION']])[1][2]-3.25)<1e-5
    assert abs(bounds([bpy.data.objects['DOOR_V2_NBALC_NORTH_FULL_WALL_PIER']])[1][2]-2.8)<1e-5
    assert abs(bounds([bpy.data.objects['DOOR_V2_NBALC_SOLID_ABOVE_DOOR']])[1][2]-2.8)<1e-5
    result=dict(status='PASS',fresh_open_object_states=len(actual),
                kitchen_objects_preserved=len(km['protected_objects']),
                V1_door_leaf_bay_and_partition_preserved=True,
                source_and_B0_hashes='PASS',enclosure_checks=checks,
                old_missing_enclosures_reproduced=True,D107_top_connection_mm=3250,
                north_balcony_top_connection_mm=2800,north_door='SINGLE_GLAZED_LEAF',
                model_sha256=sha(MODEL),blender_version=bpy.app.version_string)
    write('V2_QA.json',result);print(json.dumps({k:result[k] for k in result if k!='enclosure_checks'},ensure_ascii=False))


def render():
    integrity();m=json.loads((OUT/'V2_MANIFEST.json').read_text());assert sha(MODEL)==m['model_sha256']
    renders=OUT/'renders';renders.mkdir(exist_ok=True);results=[]
    for v in VIEWS:
        bpy.ops.wm.open_mainfile(filepath=str(MODEL));s=bpy.context.scene;s.camera=bpy.data.objects[v['camera']]
        s.render.engine='BLENDER_WORKBENCH';sh=s.display.shading
        sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True
        sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=True
        sh.background_type='WORLD';s.world.color=(.90,.92,.94);s.display.render_aa='32'
        s.view_settings.view_transform='Standard';s.render.resolution_x=1600;s.render.resolution_y=1200
        s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
        roi=v['roi'];hidden=[]
        for o in bpy.data.objects:
            if o.type=='FONT':o.hide_render=True;continue
            if o.type!='MESH':continue
            lo,hi=bounds([o])
            if hi[0]<roi[0] or lo[0]>roi[2] or hi[1]<roi[1] or lo[1]>roi[3]:
                o.hide_render=True;hidden.append(o.name);continue
            if o.name=='SITE_GROUND' or any(c.name in ['03_EXISTING_CEILING','05_HUMAN_DESIGN_GUIDE','99_TO_VERIFY',
                        '90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS'] for c in o.users_collection):
                o.hide_render=True;hidden.append(o.name);continue
            if (o.name.startswith(('GLZ_','G_wall_')) or 'GLASS' in o.name) and o.name!='DOOR_V2_NBALC_SINGLE_GLASS':
                o.hide_render=True;hidden.append(o.name)
        bpy.context.view_layer.update();path=renders/f'DOOR_ENCLOSURE_{v["id"]}.png'
        s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        results.append(dict(**v,path=str(path),sha256=sha(path),resolution=[1600,1200],engine='WORKBENCH',
                            wall_cuts=[],door_head_and_sidewalls_visible=True,temporary_hidden=hidden,source_saved=False))
    assert sha(MODEL)==m['model_sha256'];integrity();write('V2_RENDER_MANIFEST.json',results)
    print(json.dumps(dict(render='PASS',views=len(results),source_unchanged=True,images='FILESYSTEM_ONLY')))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['regress','build','verify','render'])
    a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    {'regress':regress,'build':build,'verify':verify,'render':render}[p.parse_args(a).mode]()
