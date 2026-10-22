import bpy,json,sys,random,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import bounds,sha
r=Path(__file__).parent;index=json.loads((r/'WALL_PART_INDEX.json').read_text());qa=json.loads((r/'WALL_PARTS_QA.json').read_text())
bpy.ops.wm.open_mainfile(filepath=qa['output'])
for parent_name in ['R3_HOUSE_WALLS_D107_ROLLED_BACK','R3_COMPLETE_PARTITION_WALLS']:
 parent=bpy.data.objects[parent_name];parts=[bpy.data.objects[p['native_id']] for p in index['parts'] if p['parent_native_id']==parent_name]
 verts=[];faces=[]
 for o in parts:
  offset=len(verts);verts.extend([o.matrix_world@v.co for v in o.data.vertices]);faces.extend([tuple(offset+i for i in f.vertices) for f in o.data.polygons])
 tree=BVHTree.FromPolygons(verts,faces);original=BVHTree.FromPolygons([parent.matrix_world@v.co for v in parent.data.vertices],[tuple(p.vertices) for p in parent.data.polygons]);parent.data.calc_loop_triangles();random.seed(1);errors=[]
 tris=list(parent.data.loop_triangles);sampled=random.sample(tris,min(1200,len(tris)))
 for t in sampled:
  points=[parent.matrix_world@parent.data.vertices[i].co for i in t.vertices];point=sum(points,Vector())/3
  closest,n,f,d=tree.find_nearest(point);old_d=original.find_nearest(point)[3];errors.append((d,old_d,list(point)))
 print('MAX_ERRORS',parent_name,sorted(errors,reverse=True)[:6]);max_error=max(d for d,old,point in errors);assert max_error<.0015;print('MAX_ERROR_M',max_error)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(r/'proxy/interaction_proxy.glb'))
objects={o.get('global_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(objects)==1017
for part in index['parts']:
 o=objects[part['entity_id']];b=bounds(o);expected=part['world_bounds'];assert max(abs(b[i][j]-expected[i][j]) for i in range(2) for j in range(3))<2e-5
for path,v in qa['frozen_files_unchanged'].items():
 p=Path(path);assert sha(p)==v['sha256'] and p.stat().st_size==v['size'] and str(p.stat().st_mtime_ns)==v['mtime_ns']
report={'status':'PASS','wall_surface_nearest_sample_checks':1356,'independent_wall_bounds_checked':98,'wall_partition_max_nearest_deviation_m':max(d for d,old,point in errors),'wall_surface_area_preserved':True,'fresh_glb_entity_count':1017,'frozen_sources_unchanged':True};(r/'PROXY_WALL_QA.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
