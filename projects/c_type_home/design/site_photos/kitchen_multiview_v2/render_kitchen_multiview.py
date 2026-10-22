"""Nine reproducible Blender review angles from immutable kitchen V2."""
import bpy
import bmesh
import hashlib
import json
import sys
import time
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
SITE=OUT.parent
ROOT=SITE.parents[1]
SOURCE=SITE/'B1_1_SITE_CORRECTED_V2.blend'
CAMERA_FILE=OUT/'KITCHEN_REVIEW_CAMERA_SET.blend'
FULL=(2000,1500)
PREVIEW=(960,720)
VIEWS=[
 dict(id='01',name='整体_西南轴测',slug='overall_southwest',camera='KITCHEN_REVIEW_CAM_01',
      pos=[2.0,-3.6,5.3],target=[6.4,2.15,1.1],projection='ORTHO',scale=7.4,cut=0.45),
 dict(id='02',name='整体_东北轴测',slug='overall_northeast',camera='KITCHEN_REVIEW_CAM_02',
      pos=[9.0,6.0,5.7],target=[6.2,2.2,1.0],projection='ORTHO',scale=7.0,cut=0.45),
 dict(id='03',name='冰箱与两侧柜列',slug='fridge_columns',camera='KITCHEN_REVIEW_CAM_03',
      pos=[6.60,.85,1.60],target=[6.66,4.05,1.205],projection='PERSP',lens=28,cut=.45),
 dict(id='04',name='灶台与长边柜体',slug='cooking_run',camera='KITCHEN_REVIEW_CAM_04',
      pos=[5.10,2.20,1.60],target=[7.5,2.10,1.20],projection='PERSP',lens=22,cut=.45),
 dict(id='05',name='水槽与转角',slug='sink_corner',camera='KITCHEN_REVIEW_CAM_05',
      pos=[6.75,2.60,1.60],target=[6.7,.22,1.20],projection='PERSP',lens=24,cut=.45),
 dict(id='06',name='岛台与旁柜_室内视点',slug='island_interior',camera='KITCHEN_REVIEW_CAM_06',
      pos=[6.75,3.20,1.60],target=[5.25,1.30,1.20],projection='PERSP',lens=24,cut=.45),
 dict(id='07',name='岛台抽屉与圆角',slug='island_drawers',camera='KITCHEN_REVIEW_CAM_07',
      pos=[7.15,1.90,1.10],target=[5.95,1.85,.50],projection='PERSP',lens=28,cut=.45),
 dict(id='08',name='600高柜与上方挂机',slug='utility_and_ac',camera='KITCHEN_REVIEW_CAM_08',
      pos=[5.20,3.80,1.60],target=[5.20,1.00,1.25],projection='PERSP',lens=27,cut=.45),
 dict(id='09',name='厨房俯视布局',slug='top_layout',camera='KITCHEN_REVIEW_CAM_09',
      pos=[6.15,2.30,10.0],target=[6.15,2.30,0],projection='ORTHO',scale=7.0,cut=1.2)]

def checksum(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source_hash=checksum(SOURCE)
qa=json.loads((SITE/'KITCHEN_COMPLETION_QA.json').read_text())
assert source_hash==qa['model_sha256'],'Source V2 differs from approved delivery record'
freeze=json.loads((ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
for key,expected in freeze['sha256'].items():assert checksum(ROOT/freeze['files'][key])==expected
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
mode=args[0] if args else 'preview'
selected=set(args[1:]) if len(args)>1 else {v['id'] for v in VIEWS}
jobs=[v for v in VIEWS if v['id'] in selected]

def settings():
    s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH'
    s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL'
    s.display.shading.show_shadows=False;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
    s.display.shading.show_specular_highlight=True;s.display.shading.background_type='WORLD'
    s.world.color=(.94,.95,.96);s.view_settings.view_transform='Standard'
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
    s.render.film_transparent=False;s.render.resolution_percentage=100
    s.display.render_aa='32'
    return s

def build_camera_file():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    c=bpy.data.collections.new('COL_KITCHEN_REVIEW_CAMERAS');bpy.context.scene.collection.children.link(c)
    for view in VIEWS:
        data=bpy.data.cameras.new(view['camera']);obj=bpy.data.objects.new(view['camera'],data);c.objects.link(obj)
        obj.location=view['pos'];obj.rotation_euler=(Vector(view['target'])-obj.location).to_track_quat('-Z','Y').to_euler()
        data.type=view['projection'];data.clip_start=.025;data.clip_end=100
        if data.type=='ORTHO':data.ortho_scale=view['scale']
        else:data.lens=view['lens'];data.sensor_fit='HORIZONTAL';data.sensor_width=36
        obj['review_view']=view['name'];obj['local_ffl_m']=0;obj['geometry_authority']=False
    s=settings();s.camera=bpy.data.objects[VIEWS[0]['camera']]
    s['review_source_sha256']=source_hash;s['review_intent']='Kitchen geometry inspection; simple materials; no design mutation'
    bpy.ops.wm.save_as_mainfile(filepath=str(CAMERA_FILE))
    (OUT/'CAMERA_DEFINITIONS.json').write_text(json.dumps(VIEWS,ensure_ascii=False,indent=2))

if mode=='preview' or not CAMERA_FILE.exists():build_camera_file()
manifest_path=OUT/f'RENDER_MANIFEST_{mode.upper()}.json'
evidence=[e for e in json.loads(manifest_path.read_text()) if e['id'] not in selected] if manifest_path.exists() else []
for view in jobs:
    bpy.ops.wm.open_mainfile(filepath=str(CAMERA_FILE));s=settings()
    s.camera=bpy.data.objects[view['camera']]
    width,height=PREVIEW if mode=='preview' else FULL
    s.render.resolution_x=width;s.render.resolution_y=height
    # Hide unrelated scene areas, glass faces and ceiling for this inspection set.
    # All wall cuts are in memory; CAMERA_FILE and SOURCE keep original geometry.
    hidden=[];cuts=[]
    for o in list(bpy.data.objects):
        if o.type=='FONT':o.hide_render=True;continue
        if o.type!='MESH':continue
        points=[o.matrix_world@Vector(v) for v in o.bound_box]
        lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
        if hi[0]<4.65 or lo[0]>8.10 or hi[1]<-.30 or lo[1]>4.75:
            o.hide_render=True;hidden.append(o.name);continue
        if o.name=='SITE_GROUND' or o.name.startswith(('GLZ_','G_wall_')) or 'GLASS' in o.name:
            o.hide_render=True;hidden.append(o.name);continue
        if any(c.name in ['03_EXISTING_CEILING','05_HUMAN_DESIGN_GUIDE','99_TO_VERIFY','91_ACCESSIBILITY_OPTIONS'] for c in o.users_collection):
            o.hide_render=True;hidden.append(o.name);continue
        if o.name.startswith('W_wall_'):
            o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
            cut_z=(.45 if lo[2]>.30 else 0)+view['cut']
            point=o.matrix_world.inverted()@Vector([0,0,cut_z])
            normal=(o.matrix_world.to_3x3().inverted()@Vector([0,0,1])).normalized()
            bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=point,plane_no=normal,
                clear_outer=True,clear_inner=False,dist=1e-6)
            boundary=[e for e in bm.edges if e.is_boundary and all(abs((o.matrix_world@v.co).z-cut_z)<1e-4 for v in e.verts)]
            if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
            bm.to_mesh(o.data);bm.free();cuts.append(dict(object=o.name,cut_top_m=cut_z))
    bpy.context.view_layer.update()
    dest=OUT/f"{mode.upper()}_{view['id']}_{view['slug']}.png"
    s.render.filepath=str(dest);start=time.perf_counter();bpy.ops.render.render(write_still=True)
    evidence.append(dict(**view,path=dest.name,resolution=[width,height],engine='BLENDER_WORKBENCH',
        blender_version=bpy.app.version_string,color_management='Standard',anti_alias_samples=32,
        denoising='not_applicable_workbench',duration_seconds=round(time.perf_counter()-start,3),
        source_sha256=source_hash,temporary_wall_cuts=cuts,hidden_for_review=hidden,source_saved=False))
    print(f"REVIEW_RENDER_DONE {view['id']} {view['name']}",flush=True)
manifest_path.write_text(json.dumps(sorted(evidence,key=lambda v:v['id']),ensure_ascii=False,indent=2))
assert checksum(SOURCE)==source_hash
for key,expected in freeze['sha256'].items():assert checksum(ROOT/freeze['files'][key])==expected
print('SOURCE_AND_B0_INTEGRITY_PASS',flush=True)
