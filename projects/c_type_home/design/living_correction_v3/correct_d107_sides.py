"""Apply the user's final RED50 / BLUE0 clarification to the actual D107 model."""
import json,math,runpy,sys,argparse
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
PRIOR=ROOT/'design/living_correction_v2';SOURCE=PRIOR/'B1_LIVING_CORRECTED_V2.blend'
MODEL=OUT/'B1_LIVING_CORRECTED_V3.blend'
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='freeze_helpers')
sha=H['sha'];snapshot=H['snapshot'];b0_check=H['b0_check']
ANGLE=math.radians(26.3);U=Vector((math.cos(ANGLE),math.sin(ANGLE),0));N=Vector((-math.sin(ANGLE),math.cos(ANGLE),0));HINGE=Vector((8.332,4.543,0))
BLUE_CASING=-.07;RED_CASING=.92;BLUE_CORNER=-.07;RED_CORNER=.97
VIEWS=[
 dict(id='01',name='用户标注相同轴测角度',camera='DOOR_V2_CAM_02'),
 dict(id='02',name='正面检查红侧50蓝侧0',camera='D107_V3_FRONT',pos=list(HINGE+U*.425+N*2.8+Vector((0,0,1.85))),target=list(HINGE+U*.425+Vector((0,0,1.85))),scale=3.9),
]

def write(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def world(u,n,z):
 p=HINGE+U*u+N*n;p.z=z;return p
def integrity():
 b0_check()
 km=json.loads((ROOT/'design/kitchen_frozen_v1/KITCHEN_FREEZE_MANIFEST.json').read_text())
 for c in ['files_sha256','sources_sha256','approved_render_sha256']:
  for p,h in km[c].items():assert sha(p)==h,p
 prior=json.loads((PRIOR/'V2_MANIFEST.json').read_text())
 for p,h in prior['files_sha256'].items():assert sha(p)==h,p
 assert sha(SOURCE)==prior['model_sha256']
 return km
def prism(name,poly,z0,z1,parent):
 n=len(poly);verts=[(*p,z) for z in [z0,z1] for p in poly]
 faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata(verts,[],faces);mesh.update()
 o=bpy.data.objects.new('D107_V3_'+name,mesh);COL.objects.link(o);o.parent=parent;mesh.materials.append(WALL);o.color=WALL.diffuse_color
 o['review_status']='HUMAN_REVIEW';o['physical_ground_truth']=False;return o
def angled(name,u0,u1,n0,n1,z0,z1,parent):
 poly=[world(u0,n0,0),world(u1,n0,0),world(u1,n1,0),world(u0,n1,0)]
 return prism(name,[(p.x,p.y) for p in poly],z0,z1,parent)
def normalize(state):
 return {n:{k:v for k,v in s.items() if k!='matrix_world' or not s['hide_viewport']} for n,s in state.items()}

def build():
 global COL,WALL
 assert not MODEL.exists(),'Use separate versions';km=integrity();source_hash=sha(SOURCE)
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update();base=snapshot();changed=[]
 COL=bpy.data.collections.new('COL_D107_FINAL_SIDE_CORRECTION_V3');bpy.context.scene.collection.children.link(COL)
 WALL=bpy.data.materials['LIVING_REVIEW_WALL'];root=bpy.data.objects.new('D107_V3_ENCLOSURE',None);COL.objects.link(root)
 root['red_side_visible_wall_mm']=50;root['blue_side_visible_wall_mm']=0
 root['authority']='LATEST_USER_ANNOTATED_RED_BLUE_CORRECTION; 200MM_WITHDRAWN'
 for name in ['DOOR_V2_D107_LEFT_RETURN_WALL','DOOR_V2_D107_RIGHT_RETURN_WALL',
              'DOOR_V2_D107_SOLID_ABOVE_OPENING','DOOR_V2_D107_TOP_BEAM_CONNECTION','DOOR_V2_D107_PLATFORM_BASE_CLOSURE','W_wall_md_0018']:
  o=bpy.data.objects[name];o.hide_render=True;o.hide_viewport=True;o.hide_set(True);changed.append(name)
 # RED in the supplied camera is +U. Keep exactly50mm beyond the outer casing.
 red=angled('RED_SIDE_50MM_WALL',.90,RED_CORNER,0,.2,.45,3.05,root)
 red['visible_from_casing_edge_mm']=50;red['marked_side']='RED'
 # BLUE has no front wall pier. Its return ends directly at the casing outer
 # edge, with wall backing only behind the existing timber reveal.
 bfront=world(BLUE_CORNER,.2,0);bback=world(-.05,0,0)
 blue=prism('BLUE_RETURN_FLUSH_WITH_CASING',[(7.7999,4.5002),(bback.x,bback.y),
             (bfront.x,bfront.y),(7.7999,4.7002)],.45,3.25,root)
 blue['marked_side']='BLUE';blue['visible_front_wall_pier_mm']=0
 r0=world(RED_CORNER,0,0);r1=world(RED_CORNER,.2,0)
 prism('RED_RETURN_JOIN',[(r0.x,r0.y),(9.1999,5.2302),(9.0499,5.2302),(r1.x,r1.y)],.45,3.25,root)
 # The inherited rectangular return projects in front of the new50mm face.
 # Keep it as an inactive source and retain its exact remainder north of the
 # new turn connection, which closes the removed overlap locally.
 prism('ADJACENT_RETURN_WALL_REMAINDER',[(9.0499,5.2302),(9.1999,5.2302),
       (9.1999,6.4502),(9.0499,6.4502)],.45,3.25,root)
 angled('FULL_ABOVE_DOOR',BLUE_CORNER,RED_CORNER,0,.2,2.60,3.05,root)
 angled('TOP_CONNECTION',BLUE_CORNER,RED_CORNER,-.025,.25,3.05,3.25,root)
 angled('PLATFORM_BASE_CLOSURE',BLUE_CORNER,RED_CORNER,0,.2,.40,.45,root)
 # New front inspection; the old user-facing axon camera is inherited unchanged.
 v=VIEWS[1];data=bpy.data.cameras.new(v['camera']);cam=bpy.data.objects.new(v['camera'],data);COL.objects.link(cam)
 cam.location=v['pos'];cam.rotation_euler=(Vector(v['target'])-cam.location).to_track_quat('-Z','Y').to_euler()
 data.type='ORTHO';data.ortho_scale=v['scale'];data.clip_start=.02;data.clip_end=100
 s=bpy.context.scene;s.camera=bpy.data.objects['DOOR_V2_CAM_02'];s['living_revision']='V3_RED50_BLUE0_FINAL_CLARIFICATION'
 actual=snapshot()
 for name,a in base.items():
  a=a.copy()
  if name in changed:a['hide_render']=True;a['hide_viewport']=True
  assert normalize({name:a})==normalize({name:actual[name]}),'Inherited object changed: '+name
 for name in km['protected_objects']:assert actual[name]==base[name],name
 write('V2_SOURCE_STATES.json',base);write('V3_OBJECT_STATES.json',actual)
 bpy.ops.wm.save_as_mainfile(filepath=str(MODEL));integrity();assert sha(SOURCE)==source_hash
 write('V3_MANIFEST.json',dict(status='HUMAN_REVIEW',model=str(MODEL),model_sha256=sha(MODEL),source=str(SOURCE),source_sha256=source_hash,
       old_enclosure_parts_inactive=changed,red_visible_wall_mm=50,blue_visible_wall_mm=0,
       withdrawn_value_mm=200,measurement_origin='OUTER_CASING_TO_TURN_CORNER_IN_USER_MARKED_CAMERA',
       side_axis=dict(red='+U, screen left',blue='-U, screen right'),
       casing_local_limits_m=[BLUE_CASING,RED_CASING],turn_corner_limits_m=[BLUE_CORNER,RED_CORNER],
       door_leaf_dimensions_mm=[850,40,2100],door_leaf_pose_preserved=True,door_dimensions_basis='INHERITED_REGISTER_NOT_NEW_SITE_MEASUREMENT'))
 print(json.dumps(dict(build='PASS',model=str(MODEL),red_mm=50,blue_mm=0,door_leaf_unchanged=True)))

def verify():
 km=integrity();m=json.loads((OUT/'V3_MANIFEST.json').read_text());assert sha(MODEL)==m['model_sha256']
 bpy.ops.wm.open_mainfile(filepath=str(MODEL));bpy.context.view_layer.update();actual=snapshot();expected=json.loads((OUT/'V3_OBJECT_STATES.json').read_text())
 assert normalize(actual)==normalize(expected),'Fresh-open mismatch'
 old=json.loads((OUT/'V2_SOURCE_STATES.json').read_text())
 for name in km['protected_objects']:assert actual[name]==old[name],name
 assert actual['LIVING_FIX_LEAF_D107']==old['LIVING_FIX_LEAF_D107']
 assert all(actual[n]==old[n] for n in old if n.startswith('DOOR_V2_NBALC_'))
 assert abs((RED_CORNER-RED_CASING)*1000-50)<1e-6 and BLUE_CORNER==BLUE_CASING
 blue=bpy.data.objects['D107_V3_BLUE_RETURN_FLUSH_WITH_CASING'];red=bpy.data.objects['D107_V3_RED_SIDE_50MM_WALL']
 # Check actual vertices and casing geometry rather than only stored metadata.
 bp=[((blue.matrix_world@v.co-HINGE).dot(U),(blue.matrix_world@v.co-HINGE).dot(N)) for v in blue.data.vertices]
 edge=[u for u,n in bp if abs(n-.2)<1e-5];assert edge and abs(edge[0]-BLUE_CASING)<1e-5
 rp=[(red.matrix_world@v.co-HINGE).dot(U) for v in red.data.vertices];assert abs(max(rp)-RED_CORNER)<1e-5
 cam=bpy.data.objects['DOOR_V2_CAM_02'];scene=bpy.context.scene
 bx=world_to_camera_view(scene,cam,world(BLUE_CASING,.22,1.5)).x
 rx=world_to_camera_view(scene,cam,world(RED_CASING,.22,1.5)).x
 assert bx>rx,'Marked red/blue sides swapped'
 hit,p,n,i,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),world(.945,.7,1.5),-N,distance=.75)
 assert hit and obj.name=='D107_V3_RED_SIDE_50MM_WALL'
 result=dict(status='PASS',fresh_open_states=len(actual),kitchen_objects_preserved=272,
       red_visible_wall_mm=50,blue_visible_wall_mm=0,side_projection='RED_LEFT_BLUE_RIGHT_IN_SUPPLIED_AXON',
       actual_vertices_and_casing_checked=True,red_pier_ray_checked=True,
       door_leaf_pose_and_dimensions_unchanged=True,north_balcony_door_unchanged=True,
       source_B0_and_frozen_hashes='PASS',model_sha256=sha(MODEL),blender_version=bpy.app.version_string)
 write('V3_QA.json',result);print(json.dumps(result,ensure_ascii=False))

def render():
 integrity();m=json.loads((OUT/'V3_MANIFEST.json').read_text());assert sha(MODEL)==m['model_sha256']
 out=OUT/'renders';out.mkdir(exist_ok=True);result=[]
 for v in VIEWS:
  bpy.ops.wm.open_mainfile(filepath=str(MODEL));s=bpy.context.scene;s.camera=bpy.data.objects[v['camera']]
  s.render.engine='BLENDER_WORKBENCH';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL'
  sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD';s.world.color=(.90,.92,.94)
  s.display.render_aa='32';s.view_settings.view_transform='Standard';s.render.resolution_x=1600;s.render.resolution_y=1200;s.render.resolution_percentage=100
  s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
  for o in bpy.data.objects:
   if o.type=='FONT':o.hide_render=True;continue
   if o.type!='MESH':continue
   p=[o.matrix_world@Vector(c) for c in o.bound_box];lo=[min(q[i] for q in p) for i in range(3)];hi=[max(q[i] for q in p) for i in range(3)]
   if hi[0]<7.3 or lo[0]>9.5 or hi[1]<4.25 or lo[1]>5.5:o.hide_render=True;continue
   if o.name=='SITE_GROUND' or any(c.name in ['03_EXISTING_CEILING','05_HUMAN_DESIGN_GUIDE','99_TO_VERIFY','90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS'] for c in o.users_collection):o.hide_render=True
   if o.name.startswith(('GLZ_','G_wall_')) or 'GLASS' in o.name:o.hide_render=True
  bpy.context.view_layer.update();path=out/f'D107_SIDES_{v["id"]}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  result.append(dict(**v,path=str(path),sha256=sha(path),wall_cuts=[],source_saved=False,resolution=[1600,1200]))
 assert sha(MODEL)==m['model_sha256'];integrity();write('V3_RENDER_MANIFEST.json',result)
 print(json.dumps(dict(render='PASS',views=2,images='FILESYSTEM_ONLY')))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','verify','render']);a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 {'build':build,'verify':verify,'render':render}[p.parse_args(a).mode]()
