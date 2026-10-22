import bpy,json,hashlib,struct,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'design/platform_bath_fitness_v14';a=json.loads((D/'BUILD_AUDIT.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();S=Path(a['output']);O=D/'WHOLE_HOUSE_PLATFORM_BATH_FITNESS_REVIEW_V14.blend';assert sha(S)==a['sha256'] and not O.exists();bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
root=bpy.data.objects['HOUSE_V1_V14_CONCEPT2_ROWErg_PLACEHOLDER'];T=Matrix.Translation(Vector((4.32,12.41,0)))@Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Translation(Vector((-3.71,-11.42,0)));root.matrix_world=T@root.matrix_world
outline=bpy.data.objects['HOUSE_V1_V14_ROWER_2740x1220_USE_ZONE'];outline.matrix_world=T@outline.matrix_world;bpy.context.view_layer.update()
def geometry(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];fs=[list(f.vertices) for f in me.polygons];e.to_mesh_clear();return vs,fs
def bounds(o):
 vs,_=geometry(o);return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
def bh(o):
 vs,fs=geometry(o);return BVHTree.FromPolygons(vs,fs),[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
artparts=[o for o in bpy.data.objects['HOUSE_V1_STUDY_GAP_ART'].children_recursive if o.type=='MESH'];artback=max(bounds(o)[1][0] for o in artparts);artbottom=min(bounds(o)[0][2] for o in artparts);assert abs(16.1999-artback-.002)<1e-4
hinge=bpy.data.objects['V14_SHOWER_DOOR_HINGE'];door=bpy.data.objects['HOUSE_V1_V14_SHOWER_INWARD_DOOR'];angles=[]
obstacles=[o for o in s.objects if o.type=='MESH' and not o.hide_render and (o.name.startswith(('R3_VANITY','R3_WC','CBM_SECONDARY','VIEW_WALL')) or o.name.startswith('HOUSE_V1_V14_SHOWER') and o!=door and 'FRAME' not in o.name and 'POST' not in o.name and 'HANDLE' not in o.name)]
for deg in [0,15,30,45,60,75,90]:
 hinge.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();tree,b=bh(door);hits=[]
 for q in obstacles:
  qb=bounds(q)
  if all(b[1][k]>qb[0][k]+.003 and b[0][k]<qb[1][k]-.003 for k in range(3)):
   qt,_=bh(q)
   if tree.overlap(qt):hits.append(q.name)
 angles.append({'degrees':deg,'hits':hits})
hinge.rotation_euler.z=0;bpy.context.view_layer.update()
parts=[o for o in root.children_recursive if o.type=='MESH'];rv=[v for o in parts for v in geometry(o)[0]];rb=[[min(v[i] for v in rv) for i in range(3)],[max(v[i] for v in rv) for i in range(3)]]
rowhits=[]
for p in parts:
 pt,pb=bh(p)
 for q in s.objects:
  if q.type!='MESH' or q.hide_render or q in parts or q.name.startswith(('FLOOR','PRESENTATION','V14_')):continue
  vs=[q.matrix_world@Vector(v) for v in q.bound_box];qb=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
  if all(pb[1][k]>qb[0][k]+.003 and pb[0][k]<qb[1][k]-.003 for k in range(3)):
   qt,_=bh(q)
   if pt.overlap(qt):rowhits.append([p.name,q.name])
a['pre_fitness_reorientation']={'output':str(S),'sha256':a['sha256']};a['rower_use_bounds_xy_m']=[2.95,11.80,5.69,13.02];a['rower_measured_body_bounds_m']=rb;a['rower_body_obstacle_intersections']=rowhits;a['rower_use_overlap_chaise_mm']=150;a['rower_use_fit']='FAIL_IN_PLACE_WITH_CHAISE: physical proxy fits but manufacturer full use zone overlaps chaise and window ledge. Shorter machine or rearrangement needed.';a['door_swing_samples']=angles;a['art_actual_frame_bottom_absolute_m']=artbottom;a['art_actual_frame_bottom_above_FFL_mm']=(artbottom-.45)*1000;a['art_center_above_FFL_mm']=1650;a['status']='HUMAN_REVIEW'
bpy.context.window.view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN'];bpy.ops.wm.save_as_mainfile(filepath=str(O));a['output']=str(O);a['sha256']=sha(O);(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');print('V14_REVIEW',a['sha256'],'artbottom',artbottom,'rowerhits',rowhits,'doorangles',angles)

