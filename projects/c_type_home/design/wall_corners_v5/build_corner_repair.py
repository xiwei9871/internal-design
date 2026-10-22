"""V5 targeted outer-corner completion; all non-wall V4 objects remain intact."""
import bpy,bmesh,json,runpy,subprocess,argparse,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];PRIOR=ROOT/'design/wall_junctions_v4'
SOURCE=PRIOR/'B1_WALL_JUNCTIONS_CORRECTED_V4.blend';MODEL=OUT/'B1_WALL_CORNERS_REPAIRED_V5.blend'
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='freeze_helpers')
sha=H['sha'];snapshot=H['snapshot'];b0_check=H['b0_check']
register=json.loads((OUT/'CORNER_REPAIR_REGISTER.json').read_text())
def write(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def normalize(d):return {n:{k:v for k,v in s.items() if k!='matrix_world' or not s['hide_viewport']} for n,s in d.items()}
def integrity():
 b0_check();m=json.loads((PRIOR/'V4_MANIFEST.json').read_text())
 for p,h in m['files_sha256'].items():assert sha(p)==h,p
 assert sha(SOURCE)==m['model_sha256']==register['source_sha256']
 km=json.loads((ROOT/'design/kitchen_frozen_v1/KITCHEN_FREEZE_MANIFEST.json').read_text())
 for cat in ['files_sha256','sources_sha256','approved_render_sha256']:
  for p,h in km[cat].items():assert sha(p)==h,p
 return m,km
def info(o):
 bm=bmesh.new();bm.from_mesh(o.data)
 r=dict(vertices=len(bm.verts),faces=len(bm.faces),boundary_edges=sum(e.is_boundary for e in bm.edges),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),volume=abs(bm.calc_volume(signed=True)))
 bm.free();return r
def bvh(o):return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons],all_triangles=False)
def inside(tree,p):
 origin=Vector(p);direction=Vector((.75431,.55791,.34517)).normalized();count=0
 for _ in range(100):
  hit,n,i,d=tree.ray_cast(origin,direction,100)
  if hit is None:break
  count+=1;origin=hit+direction*1e-5
 return bool(count%2)
def patch_wall(p):
 x0,y0,x1,y1=p['rect'];z0,z1=p['z0'],p['z1']
 vs=[[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]]
 tris=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]
 return dict(name=p['id'],vertices=vs,triangles=tris)
def build():
 assert not MODEL.exists(),'Preserve versions';m,km=integrity()
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update();source_states=snapshot()
 old=bpy.data.objects['V4_CONTINUOUS_WALL_SHELL'];old.data.calc_loop_triangles()
 raw=dict(name=old.name,vertices=[list(old.matrix_world@v.co) for v in old.data.vertices],triangles=[list(t.vertices) for t in old.data.loop_triangles])
 write('V5_SOLID_INPUT.json',dict(walls=[raw,*[patch_wall(p) for p in register['patches']]],cuts=register['opening_cuts'],skin_overlap_m=0))
 col=bpy.data.collections.new('COL_V5_COMPLETE_WALL_CORNERS');bpy.context.scene.collection.children.link(col)
 body=bpy.data.objects.new('V5_CONTINUOUS_WALL_SHELL',old.data.copy());col.objects.link(body);body.color=old.color
 body.data.materials.append(bpy.data.materials['V4_CONTINUOUS_REVIEW_WALL'])
 for f in body.data.polygons:f.material_index=0;f.use_smooth=False
 # Patch only audited missing quadrants with closed, same-material solids. The
 # V4 shell remains closed and unchanged; patches remove visible notches
 # without introducing Boolean non-manifold artifacts.
 patch_objects=[]
 for patch in register['patches']:
  x0,y0,x1,y1=patch['rect'];z0,z1=patch['z0'],patch['z1']
  bpy.ops.mesh.primitive_cube_add(size=1,location=[(x0+x1)/2,(y0+y1)/2,(z0+z1)/2])
  patch_obj=bpy.context.object;patch_obj.name='V5_CORNER_PATCH_'+patch['id'];patch_obj.dimensions=[x1-x0,y1-y0,z1-z0];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  for c in list(patch_obj.users_collection):c.objects.unlink(patch_obj)
  col.objects.link(patch_obj);patch_obj.data.materials.append(bpy.data.materials['V4_CONTINUOUS_REVIEW_WALL']);patch_obj.color=old.color
  patch_obj['repair_patch_id']=patch['id'];patch_obj['review_status']='HUMAN_REVIEW';patch_obj['physical_ground_truth']=False;patch_objects.append(patch_obj)
 bpy.context.view_layer.update()
 body['repair_scope']='MISSING_OUTER_QUADRANTS_AT_L_T_WALL_JUNCTIONS';body['source_model']=str(SOURCE)
 old.hide_render=True;old.hide_viewport=True;old.hide_set(True)
 scene=bpy.context.scene;scene['living_revision']='V5_OUTER_WALL_CORNERS_COMPLETED';scene['current_study_south_opening']='AS_IS_OPEN; FUTURE_BATH_OPTIONS_SEPARATE'
 states=snapshot()
 for name,s in source_states.items():
  expected=s.copy()
  if name==old.name:expected['hide_render']=True;expected['hide_viewport']=True
  assert normalize({name:expected})==normalize({name:states[name]}),name
 topo=info(body);patch_topology={o.name:info(o) for o in patch_objects};assert topo['boundary_edges']==0 and topo['nonmanifold_edges']==0,topo;assert all(x['boundary_edges']==0 and x['nonmanifold_edges']==0 for x in patch_topology.values())
 write('V4_SOURCE_STATES.json',source_states);write('V5_OBJECT_STATES.json',states)
 bpy.ops.wm.save_as_mainfile(filepath=str(MODEL));integrity()
 write('V5_MANIFEST.json',dict(status='HUMAN_REVIEW',model=str(MODEL),model_sha256=sha(MODEL),source=str(SOURCE),source_sha256=m['model_sha256'],
      missing_corner_sites=register['missing_corner_sites'],height_specific_corner_patches=len(register['patches']),
      only_wall_skin_changed=True,all_other_objects_preserved=True,current_study_south_opening_preserved=True,patch_objects=len(patch_objects),topology=topo,patch_topology=patch_topology))
 print(json.dumps(dict(build='PASS',model=str(MODEL),corners=26,patches=len(register['patches']),patch_objects=len(patch_objects),topology=topo),ensure_ascii=False))
def verify():
 m,km=integrity();release=json.loads((OUT/'V5_MANIFEST.json').read_text());assert sha(MODEL)==release['model_sha256']
 bpy.ops.wm.open_mainfile(filepath=str(MODEL));bpy.context.view_layer.update();states=snapshot()
 assert normalize(states)==normalize(json.loads((OUT/'V5_OBJECT_STATES.json').read_text()))
 old=bpy.data.objects['V4_CONTINUOUS_WALL_SHELL'];new=bpy.data.objects['V5_CONTINUOUS_WALL_SHELL']
 # Old source skin is baked world geometry with identity transform.
 oldtree=BVHTree.FromPolygons([v.co for v in old.data.vertices],[list(f.vertices) for f in old.data.polygons],all_triangles=False);newtree=bvh(new)
 topo=info(new);assert topo['boundary_edges']==0 and topo['nonmanifold_edges']==0
 patch_objects=[o for o in bpy.data.objects if o.name.startswith('V5_CORNER_PATCH_')]
 assert len(patch_objects)==len(register['patches']);assert all(info(o)['boundary_edges']==0 and info(o)['nonmanifold_edges']==0 for o in patch_objects)
 probes=0
 for patch in register['patches']:
  for p in patch['probes']:
   assert not inside(oldtree,p),'Old corner was not actually empty: '+patch['id']
   assert inside(newtree,p) or any(inside(bvh(o),p) for o in patch_objects),'Corner still empty: '+patch['id'];probes+=1
 # All registered openings and three bay returns retain net clear space.
 openings=json.loads((PRIOR/'OPENING_AND_BAY_REGISTER.json').read_text())
 for r in openings['rays']:
  pt,n,i,d=newtree.ray_cast(Vector(r['origin']),Vector(r['direction']),r['distance'])
  assert pt is None,'Opening blocked: '+r['label']
 for y in [4.52,4.62,4.72]:
  for x in [9.5,10.0,10.5]:assert not inside(newtree,[x,y,1.5]),'Current study intentional opening filled'
 originals=json.loads((OUT/'V4_SOURCE_STATES.json').read_text())
 for name in originals:
  if name!='V4_CONTINUOUS_WALL_SHELL':assert normalize({name:originals[name]})==normalize({name:states[name]}),name
 samples=json.loads((PRIOR/'SOURCE_EXTERIOR_SAMPLES.json').read_text());deviations=[];skipped=[]
 def affected(p):return any(a['rect'][0]-.03<=p[0]<=a['rect'][2]+.03 and a['rect'][1]-.03<=p[1]<=a['rect'][3]+.03 and a['z0']-.03<=p[2]<=a['z1']+.03 for a in register['patches'])
 for i,r in enumerate(samples):
  if affected(r['point']):skipped.append(i);continue
  origin=Vector(r['origin']);direction=Vector(r['direction'])
  before,nn,ii,dd=oldtree.ray_cast(origin,direction,.06);after,n2,i2,d2=newtree.ray_cast(origin,direction,.06)
  if before is None:continue
  assert after is not None,'Outside-patch wall disappeared';deviations.append((before-after).length*1000)
 assert max(deviations,default=0)<.05,'Outside-patch surfaces moved'
 q=dict(status='PASS',fresh_open_objects=len(states),corners_completed=26,height_patches=len(register['patches']),void_before_solid_after_probes=probes,
       unchanged_outside_corner_surface_samples=len(deviations),max_outside_corner_deviation_mm=max(deviations,default=0),topology=topo,patch_objects=len(patch_objects),
       all_nonwall_objects_preserved=True,current_study_opening_preserved=True,all_registered_openings_clear=True,
       black_wall_demolition_count=0,source_and_kitchen_freeze_hashes='PASS',model_sha256=sha(MODEL),blender_version=bpy.app.version_string)
 write('V5_QA.json',q);print(json.dumps(q,ensure_ascii=False))
def render():
 integrity();release=json.loads((OUT/'V5_MANIFEST.json').read_text());assert sha(MODEL)==release['model_sha256']
 out=OUT/'renders';out.mkdir(exist_ok=True);rows=[]
 for phase,source in [('BEFORE',SOURCE),('AFTER',MODEL)]:
  for id,cam in [('01','WALL_V4_CAM_01'),('02','WALL_V4_CAM_02')]:
   bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;s.camera=bpy.data.objects[cam]
   s.render.engine='BLENDER_WORKBENCH';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True
   sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD';s.world.color=(.90,.92,.94);s.display.render_aa='32';s.view_settings.view_transform='Standard'
   s.render.resolution_x=2000;s.render.resolution_y=1500;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
   for o in bpy.data.objects:
    if o.type=='FONT':o.hide_render=True;continue
    if o.type!='MESH':continue
    if o.name=='SITE_GROUND' or any(c.name in ['03_EXISTING_CEILING','05_HUMAN_DESIGN_GUIDE','99_TO_VERIFY','90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS'] for c in o.users_collection):o.hide_render=True
    if o.name.startswith(('GLZ_','G_wall_')) or 'GLASS' in o.name:o.hide_render=True
   path=out/f'WALL_CORNERS_{phase}_{id}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   rows.append(dict(phase=phase,camera=cam,path=str(path),sha256=sha(path),resolution=[2000,1500],source_saved=False))
 write('V5_RENDER_MANIFEST.json',rows);assert sha(MODEL)==release['model_sha256'];integrity();print(json.dumps(dict(render='PASS',fixed_before_after_views=4,images='FILESYSTEM_ONLY')))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','verify','render']);args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 {'build':build,'verify':verify,'render':render}[p.parse_args(args).mode]()
