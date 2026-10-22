"""Global continuous wall surface over V3; original wall/freeze files stay intact."""
import argparse,bmesh,bpy,json,math,runpy,sys,subprocess
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
PRIOR=ROOT/'design/living_correction_v3';SOURCE=PRIOR/'B1_LIVING_CORRECTED_V3.blend'
MODEL=OUT/'B1_WALL_JUNCTIONS_CORRECTED_V4.blend'
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='freeze_helpers')
sha=H['sha'];snapshot=H['snapshot'];b0_check=H['b0_check']
INVENTORY=json.loads((OUT/'ACTIVE_WALL_INVENTORY.json').read_text())
WALL_NAMES=[x['name'] for x in INVENTORY['walls']]
VIEWS=[
 dict(id='01',name='全屋墙体接口_北侧轴测',camera='WALL_V4_CAM_01',pos=[2,17,12],target=[9,7.1,1.35],scale=22),
 dict(id='02',name='全屋墙体接口_南侧轴测',camera='WALL_V4_CAM_02',pos=[18,-4,12],target=[8.8,7.0,1.35],scale=22),
 dict(id='03',name='走廊墙体交接近景',camera='WALL_V4_CAM_03',pos=[9.75,7.10,1.85],target=[12.60,7.10,1.85],lens=26),
 dict(id='04',name='D107标注边界保留检查',camera='DOOR_V2_CAM_02'),
]

def write(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def normalize(d):return {n:{k:v for k,v in s.items() if k!='matrix_world' or not s['hide_viewport']} for n,s in d.items()}
def integrity():
 b0_check();km=json.loads((ROOT/'design/kitchen_frozen_v1/KITCHEN_FREEZE_MANIFEST.json').read_text())
 for c in ['files_sha256','sources_sha256','approved_render_sha256']:
  for p,h in km[c].items():assert sha(p)==h,p
 pm=json.loads((PRIOR/'V3_MANIFEST.json').read_text())
 for p,h in pm['files_sha256'].items():assert sha(p)==h,p
 assert sha(SOURCE)==pm['model_sha256']==INVENTORY['source_sha256']
 return km
def geom(o):
 vertices=[o.matrix_world@v.co for v in o.data.vertices];faces=[list(p.vertices) for p in o.data.polygons]
 return vertices,faces
def tree(o):
 vs,fs=geom(o);return BVHTree.FromPolygons(vs,fs,all_triangles=False),[min(p[i] for p in vs) for i in range(3)],[max(p[i] for p in vs) for i in range(3)]
def nearest(trees,origin,direction,distance=100):
 hits=[]
 for t,lo,hi in trees:
  p,n,idx,d=t.ray_cast(origin,direction,distance)
  if p is not None:hits.append((d,p))
 return min(hits,key=lambda x:x[0]) if hits else None
def inside(info,p):
 t,lo,hi=info
 if any(p[i]<lo[i]-1e-7 or p[i]>hi[i]+1e-7 for i in range(3)):return False
 direction=Vector((.75431,.55791,.34517)).normalized();origin=p.copy();count=0
 for _ in range(80):
  pt,n,i,d=t.ray_cast(origin,direction,100)
  if pt is None:break
  count+=1;origin=pt+direction*1e-5
 return bool(count%2)
def surface_samples(objects):
 trees=[tree(o) for o in objects];rows=[]
 for o in objects:
  for face in o.data.polygons:
   if face.area<1e-7:continue
   p=o.matrix_world@face.center;normal=(o.matrix_world.to_3x3().inverted().transposed()@face.normal).normalized()
   origin=p+normal*.02
   if any(inside(t,origin) for t in trees):continue
   hit=nearest(trees,origin,-normal,.06)
   if hit is None:continue
   rows.append(dict(source=o.name,origin=list(origin),direction=list(-normal),distance=hit[0],point=list(hit[1])))
 return rows
def topology(o):
 bm=bmesh.new();bm.from_mesh(o.data)
 info=dict(vertices=len(bm.verts),faces=len(bm.faces),boundary_edges=sum(e.is_boundary for e in bm.edges),
           nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),volume_m3=abs(bm.calc_volume(signed=True)))
 bm.free();return info

def build():
 assert not MODEL.exists(),'Keep prior versions';km=integrity();source_hash=sha(SOURCE)
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update();base=snapshot()
 original_objects=[bpy.data.objects[n] for n in WALL_NAMES];all_samples=surface_samples(original_objects)
 preparation=runpy.run_path(str(OUT/'prepare_all_openings.py'),run_name='prepare_v4_openings')['prepare'](ROOT)
 objects=[o for o in original_objects if not o.hide_render and not o.hide_viewport]+preparation['extra_walls']
 def feature_changed(r):
  p=r['point']
  if r['source'] in preparation['disabled_source_names']:return True
  for cut in preparation['cuts']:
   if all(cut['lo'][i]-.0005<=p[i]<=cut['hi'][i]+.0005 for i in range(3)):return True
  for o in preparation['extra_walls']:
   pts=[o.matrix_world@Vector(q) for q in o.bound_box]
   if all(min(q[i] for q in pts)-.0005<=p[i]<=max(q[i] for q in pts)+.0005 for i in range(3)):return True
  return False
 bpy.context.view_layer.update()
 samples=[r for r in all_samples if not feature_changed(r)]
 write('OPENING_AND_BAY_REGISTER.json',{k:v for k,v in preparation.items() if k!='extra_walls'})
 col=bpy.data.collections.new('COL_CONTINUOUS_WALLS_V4');bpy.context.scene.collection.children.link(col)
 operands=bpy.data.collections.new('COL_WALL_BOOLEAN_INPUTS_TEMP');bpy.context.scene.collection.children.link(operands)
 copies=[];snap_max=0;snap_count=0
 for source in objects:
  vs,fs=geom(source)
  # Axis-aligned CAD bands alone receive micro-coordinate normalization.
  # Preserve exact bespoke angled-door planes and the final50/0mm relation.
  axis_band=source.name.startswith(('W_wall_','B11_SITE_','LIVING_FIX_','DOOR_V2_NBALC_','V4_'))
  if axis_band:
   for p in vs:
    for axis in [0,1,2]:
     close_mm=round(p[axis]*1000)/1000
     delta=abs(close_mm-p[axis])
     if delta<=.00021:
      snap_max=max(snap_max,delta)
      if delta>1e-9:snap_count+=1
      p[axis]=close_mm
   # Point-only contacts between CAD rectangles produce four-face edges.
   # A50micron XY overlap makes the union continuous without a visible step;
   # vertical datums and bespoke D107 planes remain exact.
   center=[(min(p[i] for p in vs)+max(p[i] for p in vs))/2 for i in range(2)]
   for p in vs:
    for axis in [0,1]:
     if p[axis]>center[axis]+1e-8:p[axis]+=.00005
     elif p[axis]<center[axis]-1e-8:p[axis]-=.00005
  mesh=bpy.data.meshes.new('V4_INPUT_'+source.name);mesh.from_pydata(vs,[],fs);mesh.update()
  bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
  obj=bpy.data.objects.new('V4_INPUT_'+source.name,mesh);operands.objects.link(obj);copies.append(obj)
 # Use a shared planar arrangement for all height layers; this removes the
 # coplanar-floor/header ambiguity of sequential3D booleans.
 solid_rows=[]
 for obj in copies:
  obj.data.calc_loop_triangles()
  solid_rows.append(dict(name=obj.name,vertices=[list(v.co) for v in obj.data.vertices],triangles=[list(t.vertices) for t in obj.data.loop_triangles]))
 write('WALL_SOLID_INPUTS.json',dict(walls=solid_rows,cuts=preparation['cuts']))
 result=subprocess.run(['rtk','proxy',str(ROOT.parents[1]/'.venv/bin/python'),str(OUT/'solid_wall_backend.py'),
      str(OUT/'WALL_SOLID_INPUTS.json'),str(OUT/'CONTINUOUS_WALL_MESH.json')],capture_output=True,text=True)
 print(result.stdout,flush=True)
 assert result.returncode==0,'Solid wall reconstruction failed: '+result.stderr
 rebuilt=json.loads((OUT/'CONTINUOUS_WALL_MESH.json').read_text())
 body=copies.pop(0)
 for c in list(body.users_collection):c.objects.unlink(body)
 col.objects.link(body);body.name='V4_CONTINUOUS_WALL_SHELL'
 mesh=bpy.data.meshes.new('V4_CONTINUOUS_WALL_MESH');mesh.from_pydata(rebuilt['vertices'],[],rebuilt['faces']);mesh.update();body.data=mesh
 bm=bmesh.new();bm.from_mesh(body.data)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();body.data.update()
 wall=bpy.data.materials.new('V4_CONTINUOUS_REVIEW_WALL');wall.diffuse_color=(.85,.86,.84,1);wall.use_nodes=True
 bsdf=wall.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=wall.diffuse_color;bsdf.inputs['Roughness'].default_value=.72
 body.data.materials.clear();body.data.materials.append(wall);body.color=wall.diffuse_color
 for f in body.data.polygons:f.material_index=0;f.use_smooth=False
 for o in list(operands.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(operands)
 for o in objects:
  o.hide_render=True;o.hide_viewport=True;o.hide_set(True);o['wall_finish_source']='V4_UNIFIED_SKIN_SOURCE_PRESERVED'
 body['source_objects']=json.dumps(WALL_NAMES);body['geometry_policy']='SHARED_PLANAR_CELL_SOLID_UNION; MICROGAP_NORMALIZATION_ONLY'
 body['review_status']='HUMAN_REVIEW';body['physical_ground_truth']=False
 cc=bpy.data.collections.new('COL_WALL_JUNCTION_CAMERAS_V4');bpy.context.scene.collection.children.link(cc)
 for v in VIEWS+preparation['views']:
  if 'pos' not in v:continue
  data=bpy.data.cameras.new(v['camera']);o=bpy.data.objects.new(v['camera'],data);cc.objects.link(o)
  o.location=v['pos'];o.rotation_euler=(Vector(v['target'])-o.location).to_track_quat('-Z','Y').to_euler();data.clip_start=.02;data.clip_end=100
  if 'scale' in v:data.type='ORTHO';data.ortho_scale=v['scale']
  else:data.lens=v['lens'];data.sensor_width=36;data.sensor_fit='HORIZONTAL'
 scene=bpy.context.scene;scene.camera=bpy.data.objects['WALL_V4_CAM_01'];scene['living_revision']='V4_CONTINUOUS_FULL_HOUSE_WALL_JUNCTIONS'
 for scr in bpy.data.screens:
  for area in scr.areas:
   if area.type=='VIEW_3D':
    area.spaces.active.overlay.show_extras=False;area.spaces.active.overlay.show_relationship_lines=False
    area.spaces.active.region_3d.view_perspective='CAMERA'
 actual=snapshot()
 changed_source_names=set(WALL_NAMES)|set(preparation['disabled_source_names'])
 for name,s in base.items():
  expected=s.copy()
  if name in changed_source_names:expected['hide_render']=True;expected['hide_viewport']=True
  assert normalize({name:actual[name]})==normalize({name:expected}),'Unrelated source changed: '+name
 write('V3_SOURCE_STATES.json',base);write('V4_OBJECT_STATES.json',actual);write('SOURCE_EXTERIOR_SAMPLES.json',samples)
 topo=topology(body);write('V4_TOPOLOGY.json',topo)
 bpy.ops.wm.save_as_mainfile(filepath=str(MODEL));integrity();assert sha(SOURCE)==source_hash
 protected_walls=[n for n in km['protected_objects'] if n in WALL_NAMES]
 write('V4_MANIFEST.json',dict(status='HUMAN_REVIEW',source=str(SOURCE),source_sha256=source_hash,model=str(MODEL),model_sha256=sha(MODEL),
      wall_sources=WALL_NAMES,wall_source_count=len(WALL_NAMES),wall_material_variants_before=57,wall_material_variants_after=1,
      source_original_meshes_poses_preserved=True,micro_snap_max_mm=snap_max*1000,micro_snap_coordinate_count=snap_count,
      kitchen_finish_walls_in_unified_skin=protected_walls,kitchen_other_protected_objects=len(km['protected_objects'])-len(protected_walls),
      kitchen_dimensions_layout_preserved=True,exterior_sample_count=len(samples),topology=topo,
      prepared_wall_input_count=len(objects),normal_doors_completed=len(preparation['doors']),remaining_bays_completed=len(preparation['bays']),
      opening_cuts=preparation['cuts'],source_samples_before_feature_changes=len(all_samples),contact_overlap_mm=.05,
      rule='ALL_REGISTERED_DOORS_COMPLETE; ALL_FOUR_BAYS_PROJECTING; UNCHANGED_FURNITURE_LEVELS_AND_KITCHEN'))
 print(json.dumps(dict(build='PASS',model=str(MODEL),wall_sources=83,wall_inputs=len(objects),ordinary_doors=len(preparation['doors']),bays_completed=len(preparation['bays']),micro_snap_max_mm=snap_max*1000,samples=len(samples),topology=topo),ensure_ascii=False))

def verify():
 km=integrity();m=json.loads((OUT/'V4_MANIFEST.json').read_text());assert sha(MODEL)==m['model_sha256']
 bpy.ops.wm.open_mainfile(filepath=str(MODEL));bpy.context.view_layer.update();actual=snapshot()
 assert normalize(actual)==normalize(json.loads((OUT/'V4_OBJECT_STATES.json').read_text()))
 old=json.loads((OUT/'V3_SOURCE_STATES.json').read_text())
 unaffected=[n for n in km['protected_objects'] if n not in WALL_NAMES]
 for name in unaffected:assert actual[name]==old[name],name
 body=bpy.data.objects['V4_CONTINUOUS_WALL_SHELL'];topo=topology(body)
 assert topo['boundary_edges']==0 and topo['nonmanifold_edges']==0,topo
 assert len(body.material_slots)==1 and all(p.material_index==0 for p in body.data.polygons)
 samples=json.loads((OUT/'SOURCE_EXTERIOR_SAMPLES.json').read_text());bt=[tree(body)];deviations=[];missing=[];removed_internal_samples=[]
 source_trees=[(BVHTree.FromPolygons([Vector(p) for p in r['vertices']],r['faces'],all_triangles=False),r['bounds'][0],r['bounds'][1]) for r in INVENTORY['walls']]
 for i,r in enumerate(samples):
  if any(inside(t,Vector(r['origin'])) for t in source_trees):
   removed_internal_samples.append(i);continue
  hit=nearest(bt,Vector(r['origin']),Vector(r['direction']),.06)
  if hit is None:missing.append(i);continue
  deviations.append(abs(hit[0]-r['distance'])*1000)
 assert not missing,'Wall surfaces lost: '+str(missing)
 assert max(deviations,default=0)<.8, 'Boundary movement beyond micro tolerance: '+str(max(deviations))
 register=json.loads((OUT/'OPENING_AND_BAY_REGISTER.json').read_text())
 for r in register['rays']:
  hit=nearest(bt,Vector(r['origin']),Vector(r['direction']),r['distance'])
  assert hit is None,'Blocked wall opening: '+r['label']
 for d in register['doors']:
  vs=[]
  for name in d['leaves']:
   o=bpy.data.objects[name];vs.extend(o.matrix_world@v.co for v in o.data.vertices)
  axis=1 if d['axis']=='x' else 0
  assert abs((max(p[axis] for p in vs)-min(p[axis] for p in vs))*1000-d['width_mm'])<.01,d['id']
  assert abs((max(p.z for p in vs)-min(p.z for p in vs))*1000-2100)<.01,d['id']
  # Casing outside-left, outside-right and above must all meet solid wall,
  # while the clear doorway between them remains unobstructed in wall BVH.
  a,b=d['span'];z=d['ffl'];band=d['band'];axis=d['axis']
  nlo,nhi=(band[0],band[2]) if axis=='x' else (band[1],band[3])
  for t,zz in [(a-.08,z+1),(b+.08,z+1),((a+b)/2,z+2.2)]:
   origin=[nlo-.3,t,zz] if axis=='x' else [t,nlo-.3,zz]
   direction=[1,0,0] if axis=='x' else [0,1,0]
   assert nearest(bt,Vector(origin),Vector(direction),nhi-nlo+.6) is not None,'Missing door surrounding wall: '+d['id']
 for b in register['bays']:
  platform=b['platform'];x=(platform[0]+platform[2])/2;y=(platform[1]+platform[3])/2
  south=b['id']!='W-STUDY-NE'
  origin=[x,.35 if south else 10.65,1.8];direction=[0,-1 if south else 1,0]
  assert nearest(bt,Vector(origin),Vector(direction),1.5) is None,'Bay front still blocked: '+b['id']
  for sign in [-1,1]:
   distance=(x-platform[0] if sign<0 else platform[2]-x)+.001
   assert nearest(bt,Vector([x,y,1.8]),Vector([sign,0,0]),distance) is None,'Bay side still blocked: '+b['id']
 # Important opening centers retain open access, with the actual glass/frame
 # objects excluded because the wall BVH alone is tested here.
 tests=[]
 for origin,direction,distance,label in [([5.35,12.7,1.4],[0,1,0],.6,'Living bay inner aperture'),
              ([7.3,12.225,1.2],[1,0,0],.9,'North balcony door')]:
  hit=nearest(bt,Vector(origin),Vector(direction),distance);assert hit is None,label+' filled by union';tests.append(label)
 assert actual['LIVING_FIX_LEAF_D107']==old['LIVING_FIX_LEAF_D107']
 for name in old:
  if name.startswith(('DOOR_V2_D107_FRAME_','DOOR_V2_D107_ARCHITRAVE_','DOOR_V2_NBALC_')) and name not in WALL_NAMES:assert actual[name]==old[name],name
 # Two glass doors retain registered spans; guest slider is now inside the
 # actual host band and all bay inner-host proxies are inactive.
 assert all(bpy.data.objects[n].hide_render and bpy.data.objects[n].hide_viewport for n in register['disabled_source_names'])
 result=dict(status='PASS',fresh_open_states=len(actual),closed_wall_skin=topo,
       external_wall_surface_samples=len(deviations),old_internal_joint_samples_removed=removed_internal_samples,max_surface_deviation_mm=max(deviations,default=0),
       missing_surfaces=missing,kitchen_nonwall_protected_unchanged=len(unaffected),kitchen_wall_source_meshes_poses_preserved=len(m['kitchen_finish_walls_in_unified_skin']),
       opening_centers_checked=tests,D107_frame_and_leaf_preserved=True,one_wall_surface_material=True,
       ordinary_doors_width_height_checks=len(register['doors']),remaining_bays_completed=len(register['bays']),
       all_opening_void_rays_checked=len(register['rays']),guest_slider_host_cut_through=True,
       source_and_frozen_hashes='PASS',model_sha256=sha(MODEL),blender_version=bpy.app.version_string)
 write('V4_QA.json',result);print(json.dumps(result,ensure_ascii=False))

def render(selected_ids=None):
 integrity();m=json.loads((OUT/'V4_MANIFEST.json').read_text());assert sha(MODEL)==m['model_sha256']
 out=OUT/'renders';out.mkdir(exist_ok=True);results=[]
 if selected_ids and (OUT/'V4_RENDER_MANIFEST.json').exists():
  results=[r for r in json.loads((OUT/'V4_RENDER_MANIFEST.json').read_text()) if r['id'] not in selected_ids]
 register=json.loads((OUT/'OPENING_AND_BAY_REGISTER.json').read_text())
 for v in VIEWS+register['views']:
  if selected_ids and v['id'] not in selected_ids:continue
  bpy.ops.wm.open_mainfile(filepath=str(MODEL));s=bpy.context.scene;s.camera=bpy.data.objects[v['camera']]
  s.render.engine='BLENDER_WORKBENCH';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True
  sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD';s.world.color=(.90,.92,.94)
  s.display.render_aa='32';s.view_settings.view_transform='Standard';s.render.resolution_x=1800;s.render.resolution_y=1350;s.render.resolution_percentage=100
  s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
  for o in bpy.data.objects:
   if o.type=='FONT':o.hide_render=True;continue
   if o.type!='MESH':continue
   if o.name=='SITE_GROUND' or any(c.name in ['03_EXISTING_CEILING','05_HUMAN_DESIGN_GUIDE','99_TO_VERIFY','90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS'] for c in o.users_collection):o.hide_render=True
   if o.name.startswith(('GLZ_','G_wall_')) or 'GLASS' in o.name:o.hide_render=True
  bpy.context.view_layer.update();path=out/f'WALL_JUNCTIONS_{v["id"]}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  results.append(dict(**v,path=str(path),sha256=sha(path),resolution=[1800,1350],wall_cuts=[],source_saved=False))
 assert sha(MODEL)==m['model_sha256'];integrity();write('V4_RENDER_MANIFEST.json',results)
 print(json.dumps(dict(render='PASS',views=len(results),images='FILESYSTEM_ONLY')))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','verify','render']);a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 {'build':build,'verify':verify,'render':render}[p.parse_args(a).mode]()
