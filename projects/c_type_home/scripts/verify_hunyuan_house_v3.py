"""Measure owner metric candidate, preserve house/guest and diagnose real fits."""
import bpy,json,hashlib,struct,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'design/hunyuan_asset_v3';a=json.loads((D/'BUILD_AUDIT.json').read_text())
protected=json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files']
for f in protected:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256']
assert hashlib.sha256(Path(a['source']).read_bytes()).hexdigest()==a['source_sha256']
for f in json.loads((D/'IMPORT_REGISTER.json').read_text())['assets']:
 assert hashlib.sha256(Path(f['original']).read_bytes()).hexdigest()==f['sha256']
assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==a['output_sha256']
# Hidden source matrices can be unevaluated identity in a saved viewlayer.
# Compare both fresh scenes under the same evaluated visibility state.
bpy.ops.wm.open_mainfile(filepath=a['source'])
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();source_matrices={o.name:[list(row) for row in o.matrix_world] for o in bpy.data.objects}
bpy.ops.wm.open_mainfile(filepath=a['output']);visibility={o.name:o.hide_render for o in bpy.data.objects}
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def mh(me):
 h=hashlib.sha256()
 for v in me.vertices:h.update(struct.pack('<fff',*v.co))
 for f in me.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
unexpected=[];guest=[]
for n,rec in a['original_states'].items():
 o=bpy.data.objects.get(n)
 if not o:unexpected.append([n,'missing']);continue
 if o.type=='MESH' and mh(o.data)!=rec['geometry']:unexpected.append([n,'meshchanged'])
 if o.type not in ['CAMERA'] and max(abs(o.matrix_world[i][j]-source_matrices[n][i][j]) for i in range(4) for j in range(4))>1e-5:unexpected.append([n,'posechanged'])
 if n.startswith(('HOUSE_V2_GUEST_','BW1_GUEST_','B11_Rectangle045_')) and visibility[n]!=rec['hide_render']:guest.append(n)
assert not unexpected,unexpected[:20];assert not guest,guest
reg=json.loads((R/'renders/whole_house_final_study_v1/00_MANIFEST/CAMERA_REGISTER_REVIEW_V3.json').read_text())
for c in reg['cameras']:
 o=bpy.data.objects[c['camera_name']];assert max(abs(o.matrix_world[i][j]-c['matrix_world'][i][j]) for i in range(4) for j in range(4))<1e-5
cache={}
def geo(o):
 if o.name not in cache:
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];fs=[list(f.vertices) for f in me.polygons];e.to_mesh_clear();cache[o.name]=(vs,BVHTree.FromPolygons(vs,fs))
 return cache[o.name]
def bounds(o):
 vs=geo(o)[0];return [Vector(min(p[i] for p in vs) for i in range(3)),Vector(max(p[i] for p in vs) for i in range(3))]
checks=[];intersections=[]
for rec in a['assets']:
 o=bpy.data.objects[rec['object']];lo,hi=bounds(o);dims=hi-lo
 bm=bmesh.new();bm.from_mesh(o.data);before=sum(e.is_boundary for e in bm.edges);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);after=sum(e.is_boundary for e in bm.edges);bm.free()
 checks.append({'object':o.name,'dims_m':list(dims),'bounds_m':[list(lo),list(hi)],'floor_contact_m':lo.z,'triangles':len(o.data.polygons),'uv_layers':len(o.data.uv_layers),'raw_boundary_edges':before,'boundary_after_analysis_only_weld':after,'temporary_weld':'never applied to actual source UV mesh'})
 if rec['role']=='COUPLE_BED':assert max(abs(dims[i]-[2.13,1.91,1.07][i]) for i in range(3))<1e-4 and abs(lo.z-.45)<1e-5
 if rec['role']=='LIVING_L_SOFA':assert max(abs(dims[i]-[1.45,2.9,.9][i]) for i in range(3))<1e-4 and abs(lo.z)<1e-5
 if rec['role']=='COUPLE_TV_CONSOLE':assert abs(dims.y-1.2)<1e-5 and abs(lo.z-.45)<1e-5
 targets=[]
 if rec['role']=='COUPLE_BED':targets=[t for t in bpy.data.objects if t.type=='MESH' and not visibility[t.name] and (t.name.startswith(('HOUSE_V2_COUPLE_0_','HOUSE_V2_COUPLE_1_','VIEW_WALL_')))]
 if rec['role']=='LIVING_L_SOFA':targets=[t for t in bpy.data.objects if t.type=='MESH' and not visibility[t.name] and t.name.startswith(('V4_Coffee','V4_Window','VIEW_WALL_'))]
 if rec['role']=='COUPLE_TV_CONSOLE':targets=[bpy.data.objects['HUNYUAN_V3_COUPLE_BED']]+[t for t in bpy.data.objects if t.type=='MESH' and not visibility[t.name] and t.name.startswith('VIEW_WALL_')]
 for t in targets:
  tl,th=bounds(t)
  if all(hi[i]>=tl[i] and th[i]>=lo[i] for i in range(3)):
   hits=geo(o)[1].overlap(geo(t)[1])
   if hits:intersections.append([o.name,t.name,len(hits)])
bedlo,bedhi=bounds(bpy.data.objects['HUNYUAN_V3_COUPLE_BED']);clo,chi=bounds(bpy.data.objects['HUNYUAN_V3_COUPLE_TV_CONSOLE'])
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()];assert not missing
report={'status':'PASS_SELECTED_TECHNICAL_GATES' if not intersections else 'FIT_REPAIR_REQUIRED','candidate_sha256':a['output_sha256'],'protected_files':len(protected),'original_objects_preserved':len(a['original_states']),'original_geometry_pose_changes':unexpected,'guest_unchanged':not guest,'guest_previous_entry_issue':'unchanged and unresolved by ownerinstruction','registered_cameras':75,'asset_checks':checks,'selective_intersections':intersections,'bedfoot_to_console_front_m':bedlo.x-chi.x,'bedside_restored':len(a.get('bedside_restored',[])),'missing_textures':missing,'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'owner_appearance_accepted':False,'not_certified':['allfurniture mechanics','dynamicdoors/body envelopes','exactcataloginternalshapes','texturephysicalroughness','procurementdimensions beyond declared outer calibration']}
(D/'VERIFICATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('HUNYUAN_VERIFY',json.dumps({k:report[k] for k in ['status','guest_unchanged','selective_intersections','bedfoot_to_console_front_m']}))
