"""Updated review views, including two photo-5 storage-cabinet angles."""
import bpy
import bmesh
import hashlib
import json
import time
from pathlib import Path
from mathutils import Vector

SITE=Path(__file__).resolve().parent;ROOT=SITE.parents[1]
OUT=SITE/'kitchen_multiview_v4';OUT.mkdir(exist_ok=True)
SOURCE=SITE/'B1_1_SITE_CORRECTED_V4.blend'
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
views=json.loads((SITE/'kitchen_multiview_v2/CAMERA_DEFINITIONS.json').read_text())
for v in views:v['roi']=[4.65,-.30,8.10,4.75]
views.extend([
 dict(id='10',name='图5窗边储物柜_正面',slug='photo5_buffet_front',camera='KITCHEN_REVIEW_CAM_10',
      pos=[4.40,1.60,1.60],target=[1.78,1.50,1.35],projection='PERSP',lens=22,cut=.45,roi=[1.25,-.30,5.80,3.20]),
 dict(id='11',name='图5窗边储物柜_侧面',slug='photo5_buffet_oblique',camera='KITCHEN_REVIEW_CAM_11',
      pos=[3.80,2.90,1.60],target=[1.78,1.50,1.35],projection='PERSP',lens=22,cut=.45,roi=[1.25,-.30,5.80,3.20])])
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
cam_col=bpy.data.collections.new('COL_REVIEW_CAMERAS_V4');bpy.context.scene.collection.children.link(cam_col)
for v in views:
    data=bpy.data.cameras.new(v['camera']);o=bpy.data.objects.new(v['camera'],data);cam_col.objects.link(o)
    o.location=v['pos'];o.rotation_euler=(Vector(v['target'])-o.location).to_track_quat('-Z','Y').to_euler()
    data.type=v['projection'];data.clip_start=.025;data.clip_end=100
    if data.type=='ORTHO':data.ortho_scale=v['scale']
    else:data.lens=v['lens'];data.sensor_width=36;data.sensor_fit='HORIZONTAL'
bpy.context.scene.camera=bpy.data.objects['KITCHEN_REVIEW_CAM_05']
CAMFILE=OUT/'KITCHEN_REVIEW_CAMERA_SET_V4.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(CAMFILE))
manifest=[]
for v in views:
    bpy.ops.wm.open_mainfile(filepath=str(CAMFILE));s=bpy.context.scene;s.camera=bpy.data.objects[v['camera']]
    s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL'
    s.display.shading.show_shadows=False;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
    s.display.shading.show_specular_highlight=True;s.display.shading.background_type='WORLD'
    s.world.color=(.94,.95,.96);s.display.render_aa='32';s.view_settings.view_transform='Standard'
    s.render.resolution_x=2000;s.render.resolution_y=1500;s.render.resolution_percentage=100
    s.render.film_transparent=False;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
    roi=v['roi'];cuts=[]
    for o in list(bpy.data.objects):
        if o.type=='FONT':o.hide_render=True;continue
        if o.type!='MESH':continue
        points=[o.matrix_world@Vector(p) for p in o.bound_box]
        lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
        if hi[0]<roi[0] or lo[0]>roi[2] or hi[1]<roi[1] or lo[1]>roi[3]:o.hide_render=True;continue
        if o.name=='SITE_GROUND' or o.name.startswith(('GLZ_','G_wall_')) or 'GLASS' in o.name:o.hide_render=True;continue
        if any(c.name in ['03_EXISTING_CEILING','05_HUMAN_DESIGN_GUIDE','99_TO_VERIFY','91_ACCESSIBILITY_OPTIONS'] for c in o.users_collection):o.hide_render=True;continue
        if o.name.startswith('W_wall_') and not o.get('review_keep_full_height',False) and o.name!='W_wall_md_0004':
            o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
            z=(.45 if lo[2]>.30 else 0)+v['cut']
            p=o.matrix_world.inverted()@Vector([0,0,z]);n=(o.matrix_world.to_3x3().inverted()@Vector([0,0,1])).normalized()
            bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=p,plane_no=n,clear_outer=True,clear_inner=False,dist=1e-6)
            e=[e for e in bm.edges if e.is_boundary and all(abs((o.matrix_world@q.co).z-z)<1e-4 for q in e.verts)]
            if e:bmesh.ops.holes_fill(bm,edges=e,sides=0)
            bm.to_mesh(o.data);bm.free();cuts.append(o.name)
    bpy.context.view_layer.update();s.render.filepath=str(OUT/f"FULL_{v['id']}_{v['slug']}_V4.png")
    start=time.perf_counter();bpy.ops.render.render(write_still=True)
    manifest.append(dict(**v,path=Path(s.render.filepath).name,resolution=[2000,1500],engine='WORKBENCH',
        blender_version=bpy.app.version_string,duration_seconds=round(time.perf_counter()-start,3),
        window_under_wall_unclipped=True,temporary_cuts=cuts,source_saved=False,source_sha256=source_hash))
    print('V4_VIEW_DONE '+v['id'],flush=True)
(OUT/'RENDER_MANIFEST_V4.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
print('V4_RENDER_DONE_SOURCE_UNCHANGED')
