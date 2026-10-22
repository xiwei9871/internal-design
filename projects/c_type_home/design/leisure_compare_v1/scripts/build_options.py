"""R4-local authorized platform study, immutable original and all nonlocal architecture."""
import bpy,bmesh,json,sys,math,hashlib,runpy
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[1];SRC=ROOT/'design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend';SHA='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
sys.path.insert(0,'/Users/xiwei/interior_design/.venv/lib/python3.13/site-packages')
# Host-generated polygon contract needs no Shapely binary modules inside Blender.
G=json.loads((OUT/'reports/OPTION_GEOMETRY.json').read_text());H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='helpers');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def states():return {n:{k:v for k,v in d.items() if k in ['type','geometry_sha256','authored_transform','parent','modifiers']} for n,d in H['snapshot']().items()}
def simplemat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=.7;return m
def polygons(geo):
 if geo['type']=='Polygon':return [geo['coordinates']]
 if geo['type']=='MultiPolygon':return geo['coordinates']
 raise ValueError(geo['type'])
def slab(name,geo,z,col,mat,bottom=0):
 result=[]
 for pi,coords in enumerate(polygons(geo)):
  loops=[r[:-1] if r[0]==r[-1] else r for r in coords];verts=[];flatloops=[]
  for loop in loops:
   indices=[]
   for x,y in loop:indices.append(len(verts));verts.append((x,y,z))
   flatloops.append(indices)
  tri_contract=json.loads((OUT/'reports/GEOMETRY_TOP_TRIANGLES.json').read_text());poly_geo=dict(type='Polygon',coordinates=coords)
  alltri=tri_contract[json.dumps(geo,sort_keys=True)];tris=[t for t in alltri if all(any(abs(x-v[0])<1e-7 and abs(y-v[1])<1e-7 for v in verts) for x,y in t)];lookup={(round(v[0],7),round(v[1],7)):i for i,v in enumerate(verts)};faces=[]
  for tri in tris:
   ids=tuple(lookup[(round(x,7),round(y,7))] for x,y in tri)
   # Enforce upper face orientation.
   a,b,c=[Vector(verts[i]) for i in ids]
   if (b-a).cross(c-a).z<0:ids=tuple(reversed(ids))
   faces.append(ids)
  n=len(verts);verts += [(x,y,bottom) for x,y,_ in list(verts)];faces += [tuple(i+n for i in reversed(f)) for f in list(faces)]
  for loop in flatloops:
   for i,a in enumerate(loop):b=loop[(i+1)%len(loop)];faces.append((a,b,b+n,a+n))
  me=bpy.data.meshes.new(name+'_'+str(pi)+'_closed');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name+'_'+str(pi),me);col.objects.link(o);me.materials.append(mat);bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();o['authorized_research_geometry']=True;o['top_z_m']=z;result.append(o)
 return result
def cube(name,loc,size,col,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(mat);return o
def camera(name,pos,target,lens,col,ortho=None):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);col.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=.02;d.clip_end=150
 if ortho:d.type='ORTHO';d.ortho_scale=ortho
 return o
for option in ['A','B']:
 assert sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update();before=states()
 permitted=[n for n in before if n in ['R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD','FASCIA_PLATFORM_CURVE','STEP_0','STEP_1','STEP_2'] or n.startswith(('B11_LEISURE_CURVE_TRIM','B11_STEP_'))]
 col=bpy.data.collections.new('OPTION_'+option+('_RETAINED' if option=='A' else '_REMOVED'));bpy.context.scene.collection.children.link(col)
 clay=simplemat('STUDY_CLAY',(.84,.84,.81));white=simplemat('STUDY_WARM_WHITE',(.92,.92,.89));wood=simplemat('STUDY_LIGHT_WOOD',(.68,.58,.44));dark=simplemat('STUDY_DOOR_FRAME',(.27,.31,.31));glass=simplemat('STUDY_CLEAR_GLASS',(.78,.89,.91));lower=simplemat('STUDY_LOWER_FFL0',(.88,.83,.74));upper=simplemat('STUDY_UPPER450',(.72,.80,.70));red=simplemat('STUDY_RAMP_INFEASIBLE',(.82,.20,.12))
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  if o.name in permitted:o.hide_render=True;o.hide_set(True)
  if any(c.name in ['05_HUMAN_DESIGN_GUIDE','06_FUTURE_DESIGN_OPTIONS','90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS','COL_B11_REVIEW_MARKERS'] for c in o.users_collection):o.hide_render=True;o.hide_set(True);continue
  if o.hide_render or o.hide_viewport:continue
  o.data=o.data.copy()
  for i,m in enumerate(list(o.data.materials)):
   mn=m.name.upper() if m else '';n=o.name.upper();mat=glass if 'GLASS' in n or 'GLASS' in mn else dark if 'METAL' in mn or any(w in n for w in ['JAMB','MULLION','FRAME','TRACK']) else white if 'WALL' in n or 'CEILING' in n or 'WALL' in mn or 'CORNER_PATCH' in n else lower if n.startswith('FLOOR_LOWER') else upper if 'FLOOR' in n else wood if n.startswith(('B11_RECTANGLE004','B11_RECTANGLE049','B11_CIRCLE','R3_WARDROBE')) else clay;o.data.materials[i]=mat
  if not o.data.materials:o.data.materials.append(white)
 if option=='A':
  slab('A_PLATFORM450_RETAINED',G['A_full_upper'],.45,col,upper)
  # Only exposed tiers, avoiding coincident internal top surfaces.
  geometry=json.loads((OUT/'reports/A_EXPOSED_RINGS.json').read_text())
  slab('A_CONTINUOUS_TREAD300',geometry['ring300'],.30,col,wood);slab('A_CONTINUOUS_TREAD150',geometry['ring150'],.15,col,wood)
 else:
  slab('B_UPPER450_RETAINED',G['B_retained_upper'],.45,col,upper)
  slab('B_LOWER0_PLATFORM_REMOVAL_INFILL',G['B_lower_infill'],0,col,lower,bottom=-.10)
  for i,geo in enumerate(G['B_steps']):slab('B_STAIR_'+str(i+1)+'_RISE150_GOING300',geo,(i+1)*.15,col,wood)
 # Full scaled ramp and1525mm landings are a disabled red research collection, never adopted.
 rc=bpy.data.collections.new('RAMP_RESEARCH_NOT_ADOPTED_450_5400_1in12');bpy.context.scene.collection.children.link(rc)
 verts=[(1.8,5.0,0),(7.2,5.0,.45),(7.2,6.1,.45),(1.8,6.1,0),(1.8,5.0,-.06),(7.2,5.0,.39),(7.2,6.1,.39),(1.8,6.1,-.06)];faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)];me=bpy.data.meshes.new('RAMP_FULL_RUN');me.from_pydata(verts,[],faces);me.update();ro=bpy.data.objects.new('RAMP_INFEASIBLE_RUN_5400',me);rc.objects.link(ro);me.materials.append(red);ro['status']='INFEASIBLE_LOCAL_ENVIRONMENT';ro['slope_percent']=100/12;ro['run_m']=5.4;ro['rise_m']=.45
 cube('RAMP_BOTTOM_LANDING1525',[1.0375,5.55,-.03],[1.525,1.1,.06],rc,red);cube('RAMP_TOP_LANDING1525',[7.9625,5.55,.42],[1.525,1.1,.06],rc,red);rc.hide_render=True;rc.hide_viewport=True
 # Cameras are shared exactly across options. Roof/wall study cut is render-only and restored in branch.
 cc=bpy.data.collections.new('STUDY_CAMERAS');bpy.context.scene.collection.children.link(cc)
 cams=[dict(id='PLAN',camera='LEISURE_PLAN',pos=[5.4,7.45,20],target=[5.4,7.45,0],lens=35,ortho=13.5,cut='roof_hidden'),dict(id='AXON',camera='LEISURE_AXON',pos=[-3.0,18.0,15],target=[5.5,7.3,.25],lens=35,ortho=13.0,cut='roof_hidden_wall_height1150'),dict(id='VIEW_01',camera='LEISURE_FROM_LIVING',pos=[5.5,10.25,1.55],target=[6.65,5.85,.70],lens=28,ortho=None,cut='NONE'),dict(id='VIEW_02',camera='LEISURE_TO_LIVING',pos=[7.55,5.95,2.0],target=[4.80,10.60,.92],lens=28,ortho=None,cut='NONE'),dict(id='SECTION',camera='LEISURE_SECTION',pos=[6.80,3.0,1.0],target=[6.80,6.0,1.0],lens=35,ortho=4.7,cut='section_y5.55')]
 for c in cams:camera(c['camera'],c['pos'],c['target'],c['lens'],cc,c['ortho'])
 # Recorded physical samples and numerical mesh closure evidence.
 bpy.context.view_layer.update();after=states();protected=[n for n in before if n not in permitted]
 for n in protected:assert after[n]==before[n],('unexpected inherited geometry/pose',n)
 (OUT/'reports'/('OPTION_'+option+'_INHERITED_STATE_LOCK.json')).write_text(json.dumps(dict(source_sha256=SHA,protected_names=protected,protected_count=len(protected),permitted_local_geometry=permitted,all_protected_geometry_pose_parent_modifiers='PASS_UNCHANGED'),ensure_ascii=False)+'\n')
 samples=[]
 # Raycast hide all irrelevant furniture/guides temporarily for floor top lookup, preserve afterward.
 visible={o.name:o.hide_get() for o in bpy.data.objects}
 for o in bpy.data.objects:
  if o.type=='MESH' and any(c.name in ['COL_B11_CORE_FURNITURE','COL_B11_APPLIANCES','COL_B11_BATHROOMS','05_HUMAN_DESIGN_GUIDE'] for c in o.users_collection):o.hide_set(True)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 test=[(6.7,7.10),(6.7,7.40),(6.7,7.70),(6.45,5.6),(6.75,5.6),(7.05,5.6),(7.35,5.6),(5.8,5.8),(7.6,7.6)]
 for x,y in test:
  hit=bpy.context.scene.ray_cast(dg,Vector([x,y,1.2]),Vector([0,0,-1]),distance=2);samples.append(dict(x=x,y=y,z=round(hit[1].z,4) if hit[0] else None,object=hit[4].name if hit[0] else None))
 for n,v in visible.items():bpy.data.objects[n].hide_set(v)
 topology=[]
 for o in col.objects:
  if o.type=='MESH':bm=bmesh.new();bm.from_mesh(o.data);topology.append(dict(name=o.name,boundary_edges=sum(e.is_boundary for e in bm.edges),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),verts=len(o.data.vertices),faces=len(o.data.polygons)));bm.free()
 assert all(t['boundary_edges']==0 and t['nonmanifold_edges']==0 for t in topology),topology
 s=bpy.context.scene;s.camera=bpy.data.objects['LEISURE_FROM_LIVING'];s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1800;s.render.resolution_y=1400;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='Standard';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=False;s.display.render_aa='32';s['research_only']=True;s['authoritative_source_sha256']=SHA;s['option']=option;s['lower_ffl_m']=0;s['upper_ffl_m']=.45;s['construction_release']=False
 for obj in rc.objects:obj.hide_render=True;obj.hide_set(True)
 file=OUT/('LEISURE_COMPARE_OPTION_'+option+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));assert sha(SRC)==SHA
 (OUT/'reports'/('OPTION_'+option+'_BUILD_QA.json')).write_text(json.dumps(dict(source_sha256=SHA,branch=str(file),option=option,cameras=cams,samples=samples,topology=topology,source_unchanged=True,local_change_only=True,ramp_collection_disabled=True,physical_cut_applied=False),ensure_ascii=False,indent=2)+'\n');print('OPTION_BUILD_PASS '+option,flush=True)
print('BOTH_OPTIONS_SAVED')
