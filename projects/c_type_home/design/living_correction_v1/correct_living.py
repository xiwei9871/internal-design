"""Reversible B1 corrections for the living bay, guest-bath wall and misplaced D107."""
import argparse
import hashlib
import json
import math
import runpy
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Matrix

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
KITCHEN=ROOT/'design/kitchen_frozen_v1'
SOURCE=KITCHEN/'KITCHEN_APPROVED_AS_IS_V1.blend'
MODEL=OUT/'B1_LIVING_CORRECTED_V1.blend'
HELPERS=runpy.run_path(str(KITCHEN/'freeze_kitchen.py'),run_name='kitchen_freeze_helpers')
sha=HELPERS['sha'];snapshot=HELPERS['snapshot'];b0_check=HELPERS['b0_check']
NAME='COL_B1_LIVING_SITE_CORRECTION_V1'
VIEWS=[
 dict(id='01',name='客厅正面飘窗',camera='LIVING_FIX_CAM_01',pos=[5.35,8.90,1.60],target=[5.35,13.65,1.45],lens=25,roi=[2.6,7.65,8.22,14.20]),
 dict(id='02',name='飘窗平台与侧窗',camera='LIVING_FIX_CAM_02',pos=[6.48,11.68,1.57],target=[4.98,13.65,1.27],lens=22,roi=[2.6,10.6,8.22,14.20]),
 dict(id='03',name='客厅与客卫完整分隔墙',camera='LIVING_FIX_CAM_03',pos=[3.75,11.05,1.68],target=[7.89,9.60,1.54],lens=22,roi=[2.6,7.50,10.15,14.20]),
 dict(id='04',name='全屋俯视_门扇与墙体定位',camera='LIVING_FIX_CAM_04',pos=[8.0,7.0,22],target=[8.0,7.0,0],projection='ORTHO',scale=23.2,roi=[1.0,-.8,16.8,15.4]),
 dict(id='05',name='客厅轴测_完整墙体',camera='LIVING_FIX_CAM_05',pos=[.40,4.15,9.50],target=[5.50,10.35,1.0],projection='ORTHO',scale=10.2,roi=[2.6,7.5,10.15,14.2]),
 dict(id='06',name='次主卧D107与绿框门洞',camera='LIVING_FIX_CAM_06',pos=[6.15,5.72,1.90],target=[8.62,4.83,1.53],lens=26,roi=[5.45,3.9,10.0,7.9]),
 dict(id='07',name='飘窗平台结构检查_家具暂隐',camera='LIVING_FIX_CAM_07',pos=[2.00,10.45,3.80],target=[5.35,13.40,1.40],projection='ORTHO',scale=5.1,roi=[3.40,12.70,7.30,14.20],isolated_bay=True),
]


def write(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def integrity():
    b0_check()
    m=json.loads((KITCHEN/'KITCHEN_FREEZE_MANIFEST.json').read_text())
    for cat in ['files_sha256','sources_sha256','approved_render_sha256']:
        for p,expected in m[cat].items():assert sha(p)==expected,'Frozen input changed: '+p
    return m


def bounds(obs):
    pts=[o.matrix_world@Vector(p) for o in obs if o.type=='MESH' for p in o.bound_box]
    return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]


def close(a,b,label,tol=1e-5):assert abs(a-b)<tol,f'{label}: {a} != {b}'


def material(name,color,alpha=1):
    m=bpy.data.materials.new('LIVING_REVIEW_'+name);m.diffuse_color=(*color,alpha);m.use_nodes=True
    node=m.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value=(*color,alpha)
    node.inputs['Roughness'].default_value=.6
    if alpha<1:
        node.inputs['Alpha'].default_value=alpha;node.inputs['Transmission Weight'].default_value=.65
        m.surface_render_method='DITHERED'
    return m


def add_box(name,lo,hi,mat,parent,bevel=.0015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)])
    o=bpy.context.object;o.name='LIVING_FIX_'+name;o.dimensions=[hi[i]-lo[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    COL.objects.link(o);o.parent=parent;o.data.materials.append(mat);o.color=mat.diffuse_color
    if bevel:
        mod=o.modifiers.new('Review edge','BEVEL');mod.width=bevel;mod.segments=2
        o.modifiers.new('Review normals','WEIGHTED_NORMAL')
    o['authority']='USER_SITE_RELATIONSHIP + INHERITED_CAD_XY_Z_DATUM'
    o['review_status']='HUMAN_REVIEW';o['physical_ground_truth']=False
    return o


def group(name):
    o=bpy.data.objects.new('LIVING_FIX_'+name,None);COL.objects.link(o)
    o['review_status']='HUMAN_REVIEW';return o


def disable(name,changed):
    root=bpy.data.objects[name]
    for o in [root,*root.children_recursive]:
        o.hide_render=True;o.hide_viewport=True;o.hide_set(True)
        o['living_site_status']='INACTIVE_PRIOR_PROXY; B1_SITE_DETAIL_OVERRIDE'
        changed.add(o.name)


def framed(name,a,b,sill,head,panels,parent):
    # Arbitrary horizontal segment supports front and side-return glazing.
    a,b=Vector((*a,0)),Vector((*b,0));d=b-a;length=d.length
    axis=d.normalized();normal=Vector((-axis.y,axis.x,0));t=.035
    def part(label,cx,z0,z1,width,depth,mat):
        c=a+axis*cx;midz=(z0+z1)/2
        o=add_box(name+'_'+label,[-width/2,-depth/2,z0],[width/2,depth/2,z1],mat,parent,0)
        # The cube is local to its center on Z; rotate only local geometry about its own center.
        o.location=(c.x,c.y,midz);o.rotation_euler.z=math.atan2(axis.y,axis.x)
        return o
    for n,pos in enumerate([t/2,length-t/2]):part(f'JAMB_{n}',pos,sill,head,t,.046,METAL)
    part('BOTTOM_RAIL',length/2,sill,sill+t,length,.046,METAL)
    part('TOP_RAIL',length/2,head-t,head,length,.046,METAL)
    # Breaks are normalized review proportions, not surveyed sash widths.
    cuts=[0]
    for ratio in panels:cuts.append(cuts[-1]+length*ratio)
    for n,(x0,x1) in enumerate(zip(cuts,cuts[1:])):
        part(f'GLASS_{n}',(x0+x1)/2,sill+t,head-t,x1-x0-2*t,.008,GLASS)
        if n:part(f'MULLION_{n}',x0,sill,head,t,.046,METAL)


def build():
    global COL,WALL,STONE,METAL,GLASS,DOOR
    assert not MODEL.exists(),'Preserve V1; use a new correction version'
    km=integrity();source_sha=sha(SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));base=snapshot();changed=set()
    COL=bpy.data.collections.new(NAME);bpy.context.scene.collection.children.link(COL)
    COL['authority']='CURRENT_USER_SITE_CORRECTIONS; NEW_B1_BRANCH'
    COL['physical_ground_truth']=False
    WALL=material('WALL',(.84,.85,.82));STONE=material('SILL',(.72,.69,.61))
    METAL=material('WINDOW_FRAME',(.22,.28,.29));GLASS=material('GLASS',(.62,.75,.79),.22)
    DOOR=material('SOLID_DOOR',(.48,.46,.40))
    # One outer glazed bay; the inner portal remains open to its projecting sill.
    for name in ['GLZ_W-LIV-N','B11_OPENING_W-LIV-N','B11_BAY_W-LIV-N',
                 'W_wall_md_0008','W_wall_md_0011','W_wall_md_0063']:
        disable(name,changed)
    bay=group('BAY_W_LIV_N')
    bay['inner_aperture_mm']=[3800,13000,6900,13200]
    bay['bay_xy_basis']='PRESERVED_CAD_BANDS; REGISTER_PROJECTION900; NOT_PHOTO_METRICS'
    bay['sill_z_mm']=450;bay['head_z_mm']=2400
    bay['side_return_glazing']='USER_SITE_PHOTOS';bay['no_inner_window']=True
    # Portal lower wall and head preserve the actual source aperture.
    add_box('BAY_INNER_UNDER_WALL',[3.8,13.0002,0],[6.9,13.2002,.425],WALL,bay,0)
    add_box('BAY_INNER_HEAD',[3.8,13.0002,2.4],[6.9,13.2002,2.8],WALL,bay,0)
    # Use exact inherited side/front outlines as low plinths and head bands.
    for name,label in [('W_wall_md_0008','LEFT'),('W_wall_md_0011','RIGHT'),('W_wall_md_0063','FRONT')]:
        lo,hi=bounds([bpy.data.objects[name]])
        add_box('BAY_'+label+'_UNDER_WALL',[lo[0],lo[1],0],[hi[0],hi[1],.425],WALL,bay,0)
        add_box('BAY_'+label+'_HEAD',[lo[0],lo[1],2.4],[hi[0],hi[1],2.8],WALL,bay,0)
    add_box('BAY_SOLID_PLATFORM_CORE',[3.6999,13.2002,0],[6.9999,13.7902,.425],WALL,bay,0)
    add_box('BAY_SILL_PLATFORM',[3.6499,12.9502,.425],[7.0499,13.8732,.45],STONE,bay,.002)
    add_box('BAY_SOFFIT',[3.5999,13.2002,2.775],[7.0999,13.9002,2.8],WALL,bay,0)
    framed('BAY_FRONT',[3.5999,13.8452],[7.0999,13.8452],.45,2.4,[.18,.64,.18],bay)
    framed('BAY_LEFT_RETURN',[3.6499,13.2002],[3.6499,13.8452],.45,2.4,[1],bay)
    framed('BAY_RIGHT_RETURN',[7.0499,13.2002],[7.0499,13.8452],.45,2.4,[1],bay)
    # The guest-bath partition was wrongly treated as a parapet; keep CAD XY.
    disable('W_wall_md_0013',changed)
    partition=group('GUEST_BATH_PARTITION')
    lo,hi=bounds([bpy.data.objects['W_wall_md_0013']])
    wall=add_box('GUEST_BATH_FULL_WALL',[lo[0],lo[1],0],[hi[0],hi[1],3.25],WALL,partition,0)
    wall['source_object']='W_wall_md_0013';wall['semantic_role']='FULL_HEIGHT_INTERIOR_SPLIT_LEVEL_PARTITION'
    wall['review_keep_full_height']=True
    # Close only the thickness of the north wall connection, preserving room XY.
    add_box('GUEST_BATH_NORTH_JUNCTION',[7.75,10.9002,0],[8.0,11.1002,3.25],WALL,partition,0)['review_keep_full_height']=True
    # The existing TV/balcony return was also mislabeled parapet: same XY, registered door retained.
    disable('W_wall_md_0014',changed)
    add_box('TV_NORTH_SOLID_WALL',[7.75,11.1002,0],[8.0,11.8,2.8],WALL,partition,0)['review_keep_full_height']=True
    add_box('BALCONY_DOOR_HEAD',[7.75,11.8,2.4],[8.0,12.65,2.8],WALL,partition,0)
    # Door is already a baked world mesh rotated about the origin. Translate the
    # same orientation and hardware to the intended center; no angle redecision.
    door=group('D107_SECONDARY_BEDROOM')
    leaf=bpy.data.objects['LEAF_D107'];angle=leaf.rotation_euler.z
    intended=Vector((8.332+.425*math.cos(angle),4.543+.425*math.sin(angle),1.5))
    lo,hi=bounds([leaf]);actual=Vector([(lo[i]+hi[i])/2 for i in range(3)])
    delta=intended-actual
    moving=[leaf,*bpy.data.objects['B11_D107_DETAIL'].children_recursive]
    for old in moving:
        if old.type!='MESH':continue
        new=old.copy();new.data=old.data.copy();COL.objects.link(new)
        authored=old.matrix_world.copy();new.parent=door;new.matrix_world=authored
        new.matrix_world.translation+=delta;new.name='LIVING_FIX_'+old.name
        if old==leaf:
            new.data.materials.clear();new.data.materials.append(DOOR);new.color=DOOR.diffuse_color
        new['review_status']='HUMAN_REVIEW';new['source_object']=old.name
        new['correction']='ORIGIN_ROTATION_TRANSLATION_BUG_REPAIRED_WITH_ORIGINAL_HINGE_AND_ANGLE'
    door['source_name']='D-107 = D-SM';door['hinge_mm']=[8332,4543,450]
    door['angle_deg']=math.degrees(angle);door['translation_fix_m']=list(delta)
    door['glass_door']=False
    disable('LEAF_D107',changed);disable('B11_D107_DETAIL',changed)
    cameras=bpy.data.collections.new('COL_LIVING_CORRECTION_CAMERAS_V1');bpy.context.scene.collection.children.link(cameras)
    for v in VIEWS:
        data=bpy.data.cameras.new(v['camera']);o=bpy.data.objects.new(v['camera'],data);cameras.objects.link(o)
        o.location=v['pos'];o.rotation_euler=(Vector(v['target'])-o.location).to_track_quat('-Z','Y').to_euler()
        data.type=v.get('projection','PERSP');data.clip_start=.02;data.clip_end=100
        if data.type=='ORTHO':data.ortho_scale=v['scale']
        else:data.lens=v['lens'];data.sensor_width=36;data.sensor_fit='HORIZONTAL'
    # Make the new file open to a legible overall scene with overlays disabled.
    scene=bpy.context.scene;scene.camera=bpy.data.objects['LIVING_FIX_CAM_05']
    scene['living_correction_status']='HUMAN_REVIEW'
    scene['kitchen_freeze_inherited']='V1_UNCHANGED'
    scene['living_correction_scope']='BAY_PHYSICAL_LOGIC; GUEST_BATH_PARTITION; D107_ORIGIN_ROTATION_BUG'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.overlay.show_extras=False
                area.spaces.active.region_3d.view_perspective='CAMERA'
    actual=snapshot()
    for name,s in base.items():
        a=actual[name]
        if name in changed:
            s=s.copy();s['hide_render']=True;s['hide_viewport']=True
        assert a==s,'Unexpected source object edit: '+name
    for name in km['protected_objects']:
        assert actual[name]==base[name],'Frozen kitchen changed: '+name
    write('SOURCE_OBJECT_STATES.json',base)
    write('LIVING_CORRECTED_OBJECT_STATES.json',actual)
    write('LIVING_CAMERA_REGISTER.json',VIEWS)
    bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))
    integrity();assert sha(SOURCE)==source_sha
    changes=dict(status='HUMAN_REVIEW',source=str(SOURCE),source_sha256=source_sha,
                 model=str(MODEL),model_sha256=sha(MODEL),B0_INTEGRITY='PASS',
                 kitchen_protected_objects_unchanged=len(km['protected_objects']),
                 inherited_objects=len(base),prior_proxies_hidden=sorted(changed),
                 active_bay='ONE_OUTER_FRONT_PLUS_SIDE_RETURNS; INNER_APERTURE_OPEN',
                 bay_dimensions_basis='INHERITED_REGISTER_AND_CAD; PHOTO_RELATIONSHIPS_ONLY',
                 guest_bath_wall_top_mm=3250,D107=dict(object='LEAF_D107',identity='D-SM_SECONDARY_BEDROOM',
                 source_bug='BAKED_WORLD_VERTICES_ROTATED_AROUND_ORIGIN',correction_translation_m=list(delta),
                 correct_hinge_mm=[8332,4543,450],preserved_angle_deg=math.degrees(angle)),
                 references={str(p):sha(p) for p in (OUT/'references').iterdir() if p.is_file()})
    write('LIVING_CORRECTION_MANIFEST.json',changes)
    print(json.dumps({k:changes[k] for k in ['status','model','model_sha256','B0_INTEGRITY',
                                             'kitchen_protected_objects_unchanged','inherited_objects','D107']},ensure_ascii=False))


def verify():
    km=integrity();m=json.loads((OUT/'LIVING_CORRECTION_MANIFEST.json').read_text())
    assert sha(MODEL)==m['model_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(MODEL));state=snapshot()
    expected=json.loads((OUT/'LIVING_CORRECTED_OBJECT_STATES.json').read_text())
    # Blender does not evaluate matrix_world for hidden proxies on fresh load.
    # Their mesh, authored transform, parent and all other state are still checked;
    # active geometry keeps exact world-matrix comparison.
    for name,a in state.items():
        e=expected[name]
        if name in m['prior_proxies_hidden']:
            a={k:v for k,v in a.items() if k!='matrix_world'}
            e={k:v for k,v in e.items() if k!='matrix_world'}
        assert a==e,'Fresh-open state changed: '+name
    assert set(state)==set(expected),'Object inventory changed'
    old=json.loads((OUT/'SOURCE_OBJECT_STATES.json').read_text())
    for name in km['protected_objects']:assert state[name]==old[name],name
    for name in m['prior_proxies_hidden']:
        assert bpy.data.objects[name].hide_render and bpy.data.objects[name].hide_viewport
    leaf=bpy.data.objects['LIVING_FIX_LEAF_D107'];angle=leaf.rotation_euler.z
    lo,hi=bounds([leaf]);mid=Vector([(lo[i]+hi[i])/2 for i in range(3)])
    intended=Vector((8.332+.425*math.cos(angle),4.543+.425*math.sin(angle),1.5))
    assert (mid-intended).length<1e-5
    close(math.degrees(angle),26.3,'D107 angle',1e-4)
    # The hinge is on the fixed angled doorway, not in the living furniture zone.
    assert lo[0]>8.3 and hi[1]<5.0 and lo[2]>.44999
    wall=bpy.data.objects['LIVING_FIX_GUEST_BATH_FULL_WALL'];wl,wh=bounds([wall])
    src=bounds([bpy.data.objects['W_wall_md_0013']])
    for i in [0,1]:close(wl[i],src[0][i],'partition lower XY');close(wh[i],src[1][i],'partition upper XY')
    close(wh[2],3.25,'partition head');assert not wall.hide_render and not wall.hide_viewport
    # Actual ray tests through the bay volume must reach outer glass; the
    # portal must not hit an inner glass proxy or an outside full-height wall.
    dg=bpy.context.evaluated_depsgraph_get()
    def ray(origin,direction):
        hit,pt,norm,idx,obj,matrix=bpy.context.scene.ray_cast(dg,Vector(origin),Vector(direction))
        assert hit,'Missing bay enclosure'
        assert obj.name.startswith('LIVING_FIX_BAY_') and 'GLASS' in obj.name, 'Blocked ray: '+obj.name
        return dict(object=obj.name,point=list(pt))
    hits={
        'forward_through_inner_portal':ray([5.35,12.55,1.35],[0,1,0]),
        'left_side_return':ray([5.35,13.48,1.35],[-1,0,0]),
        'right_side_return':ray([5.35,13.48,1.35],[1,0,0]),
    }
    platform=bounds([bpy.data.objects['LIVING_FIX_BAY_SILL_PLATFORM']])
    close(platform[1][2],.45,'platform top')
    assert platform[1][1]-platform[0][1]>.85
    result=dict(status='PASS',source_hashes='PASS',B0_INTEGRITY='PASS',
                frozen_kitchen_objects_preserved=len(km['protected_objects']),
                fresh_open_object_states_match=len(state),
                three_bay_glazing_rays=hits,duplicate_inner_window='INACTIVE',
                guest_bath_partition_top_mm=wh[2]*1000,
                guest_bath_partition_XY='EXACT_SOURCE_BOUNDS',
                D107_centroid_error_mm=(mid-intended).length*1000,
                D107_no_longer_in_living=True,D107_angle_deg=math.degrees(angle),
                blender_version=bpy.app.version_string,model_sha256=sha(MODEL))
    write('LIVING_CORRECTION_QA.json',result);print(json.dumps(result,ensure_ascii=False))


def render():
    integrity();m=json.loads((OUT/'LIVING_CORRECTION_MANIFEST.json').read_text())
    assert sha(MODEL)==m['model_sha256'];out=OUT/'renders';out.mkdir(exist_ok=True)
    results=[]
    for v in VIEWS:
        bpy.ops.wm.open_mainfile(filepath=str(MODEL));s=bpy.context.scene
        s.camera=bpy.data.objects[v['camera']];s.render.engine='BLENDER_WORKBENCH'
        sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL'
        sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH'
        sh.show_specular_highlight=True;sh.background_type='WORLD';s.world.color=(.90,.92,.94)
        s.display.render_aa='32';s.view_settings.view_transform='Standard'
        s.render.resolution_x=1600;s.render.resolution_y=1200;s.render.resolution_percentage=100
        s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
        roi=v['roi'];hidden=[]
        for o in bpy.data.objects:
            if o.type=='FONT':o.hide_render=True;continue
            if o.type!='MESH':continue
            if v.get('isolated_bay') and not (o.name.startswith('LIVING_FIX_BAY_') or
                                               o.name in ['W_wall_md_0059','W_wall_md_0060']):
                o.hide_render=True;hidden.append(o.name);continue
            lo,hi=bounds([o])
            if hi[0]<roi[0] or lo[0]>roi[2] or hi[1]<roi[1] or lo[1]>roi[3]:
                o.hide_render=True;hidden.append(o.name);continue
            if o.name=='SITE_GROUND' or any(c.name in ['03_EXISTING_CEILING','05_HUMAN_DESIGN_GUIDE',
                   '99_TO_VERIFY','91_ACCESSIBILITY_OPTIONS','90_FUTURE_DESIGN_OPTIONS'] for c in o.users_collection):
                o.hide_render=True;hidden.append(o.name);continue
            # Transparent glass in Workbench is opaque; hide only the pane meshes,
            # leaving all physical frames and walls intact to expose relationships.
            if 'GLASS' in o.name or o.name.startswith(('GLZ_','G_wall_')):
                o.hide_render=True;hidden.append(o.name)
        bpy.context.view_layer.update()
        path=out/f"LIVING_{v['id']}.png";s.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        results.append(dict(**v,path=str(path),sha256=sha(path),resolution=[1600,1200],
                            engine='WORKBENCH',samples=32,color_management='Standard',
                            wall_cuts=[],hidden_for_review=hidden,source_saved=False,
                            note='Panes/ceiling temporarily hidden for geometry review; full walls kept'))
    assert sha(MODEL)==m['model_sha256'];integrity()
    write('LIVING_RENDER_MANIFEST.json',results)
    print(json.dumps(dict(render='PASS',views=len(results),images='FILESYSTEM_ONLY',model_unchanged=True)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','verify','render'])
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    {'build':build,'verify':verify,'render':render}[p.parse_args(args).mode]()
