"""Preserved architecture and prior candidate + evaluated new whole objects and real fit."""
import bpy,hashlib,json,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/product_rebuild_v4'
audit=json.loads((OUT/'BUILD_AUDIT.json').read_text())
assert hashlib.sha256(Path(audit['output']).read_bytes()).hexdigest()==audit['output_sha256'],'output differs from final build audit'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'LIVING_DINING_PRODUCT_REBUILD_V4.blend'))
for o in bpy.context.scene.objects:
 if o.type=='MESH':o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
def fingerprint(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 return h.hexdigest(),[float(x) for row in o.matrix_world for x in row]
baseline=json.loads((OUT/'PRESERVED_GEOMETRY.json').read_text())
for n,(hash,matrix) in baseline.items():
 actual=fingerprint(bpy.data.objects[n]);assert actual[0]==hash,n;assert max(abs(x-y) for x,y in zip(actual[1],matrix))<1e-6,n
def pts(o):
 e=o.evaluated_get(deps);me=e.to_mesh();points=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();return points
def objects(g):return [o for o in bpy.data.objects[g].children_recursive if o.type in ['MESH','CURVE'] and not o.hide_render]
def bounds(obs):
 p=[v for o in obs for v in pts(o)];return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
envelopes={
'V4_LIVING_SOFA_COMPLETE':[[3.4,7.95,0],[5.2,11.25,.7]],
'V4_WINDOW_CHAISE_COMPLETE':[[4.671625,11.05522,0],[6.371625,11.95522,.8]],
'V4_COFFEE_TABLE_COMPLETE':[[5.025,9.49,0],[5.575,10.49,.4]],
'V4_EAST_CONSOLE_COMPLETE':[[7.398,8.634937,0],[7.696875,11.523844,.48]],
'V4_DINING_TABLE_COMPLETE':[[3.027625,3.064406,0],[4.627625,3.864406,.75]]}
report={}
ceiling_rays=[]
for origin in [(5.3,9.5,2.6),(4.0,9.0,2.6)]:
 hit=bpy.context.scene.ray_cast(deps,Vector(origin),Vector((0,0,1)),distance=1)
 assert hit[0] and hit[4].name.startswith('CEILING_'),(origin,hit[4].name if hit[4] else None)
 ceiling_rays.append({'origin_m':origin,'hit':hit[4].name,'hit_z_m':hit[1].z})
for g,wanted in envelopes.items():
 actual=bounds(objects(g));within=all(actual[0][i]>=wanted[0][i]-.003 and actual[1][i]<=wanted[1][i]+.003 for i in range(3));report[g]={'actual_bounds_m':actual,'constraint_bounds_m':wanted,'within_3mm':within};assert within,(g,actual,wanted)
chair_bounds=[]
for i in range(4):
 g='V4_DINING_CHAIR_%d_COMPLETE'%i;b=bounds(objects(g));dims=[b[1][j]-b[0][j] for j in range(3)];chair_bounds.append({'group':g,'bounds_m':b,'dimensions_mm':[round(v*1000,1) for v in dims]});assert dims[0]<=.565 and dims[1]<=.565 and dims[2]<=.855,(g,dims)
# Surface intersection check for table and whole chair: geometric overlap is review-required,
# BVH overlap is an intersection candidate, not a physical occupied knee envelope certification.
def tree(o):
 e=o.evaluated_get(deps);me=e.to_mesh();verts=[e.matrix_world@v.co for v in me.vertices];faces=[tuple(p.vertices) for p in me.polygons];t=BVHTree.FromPolygons(verts,faces);e.to_mesh_clear();return t
table=[(o.name,tree(o)) for o in objects('V4_DINING_TABLE_COMPLETE')]
collisions=[]
for i in range(4):
 for o in objects('V4_DINING_CHAIR_%d_COMPLETE'%i):
  if o.type!='MESH':continue
  t=tree(o)
  for name,tt in table:
   if t.overlap(tt):collisions.append([o.name,name])
assert not collisions,collisions
arm_top=max(v.z for o in bpy.data.objects if o.name.startswith('V4_Chair_arm.') or o.name=='V4_Chair_arm' for v in pts(o))
table_under=.712
seat_names=['V4_Sofa_chaise_upholstery','V4_Sofa_seat_middle','V4_Sofa_seat_north'];back_names=['V4_Sofa_back_0','V4_Sofa_back_1','V4_Sofa_back_2']
gaps={}
for label,names in [('seat',seat_names),('back',back_names)]:
 bs=[bounds([bpy.data.objects[n]]) for n in names];gaps[label]=[(bs[j+1][0][1]-bs[j][1][1])*1000 for j in range(2)];assert all(0<=v<15 for v in gaps[label]),gaps
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()];assert not missing,missing
protected=json.loads((OUT/'PRESERVATION.json').read_text())['files']
for f in protected:
 assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
report={'status':'PASS','fresh_reopen':True,'output_sha256':audit['output_sha256'],'original_meshes_and_matrices_preserved':len(baseline),'envelopes':report,'closed_ceiling_actual_rays':ceiling_rays,'chair_actual_size_and_fit':chair_bounds,'chair_table_triangle_intersections':collisions,'armrest_top_mm':arm_top*1000,'table_underside_mm':table_under*1000,'arm_table_vertical_clearance_mm':(table_under-arm_top)*1000,'cushion_y_minimum_gaps_mm':gaps,'missing_images':missing,'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'protected_file_hashes_pass':True,'protected_file_count':len(protected),'not_certified':'SKU exact geometry, manufacture, dynamic pullout/access, human knee/foot envelope or installation safety'}
(OUT/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print('V4_VERIFY_PASS',len(baseline),json.dumps(gaps))
