"""Fresh-open whole-house architecture, history, fitting and actual-contact gates."""
import bpy,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/whole_house_model_v1';RUN=OUT/'assembly';a=json.loads((RUN/'BUILD_AUDIT.json').read_text())
protected=json.loads((OUT/'PRESERVATION.json').read_text())['files']
for f in protected:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==a['output_sha256']
bpy.ops.wm.open_mainfile(filepath=a['output']);visibility={o.name:o.hide_render for o in bpy.data.objects}
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def meshhash(me):
 h=hashlib.sha256()
 for v in me.vertices:h.update(struct.pack('<fff',*v.co))
 for f in me.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
allowed_pose={c['object'] for c in a['material_changes'] if c['kind']=='rigid_relocation'}
unexpected=[]
for n,s in a['original_states'].items():
 o=bpy.data.objects.get(n)
 if o is None:unexpected.append([n,'deleted']);continue
 if o.type=='MESH' and meshhash(o.data)!=s['geometry']:unexpected.append([n,'original_geometry_changed'])
 if o.type!='CAMERA' and n not in allowed_pose:
  vals=[v for row in o.matrix_world for v in row]
  if max(abs(x-y) for x,y in zip(vals,s['matrix']))>1e-5:unexpected.append([n,'transform_changed'])
assert not unexpected,unexpected[:20]
def g(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();pts=[e.matrix_world@v.co for v in me.vertices];faces=[tuple(f.vertices) for f in me.polygons];e.to_mesh_clear();return pts,BVHTree.FromPolygons(pts,faces)
def bounds(n):
 p=g(bpy.data.objects[n])[0];return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
upper=bounds('SUNROOM_SOFA_REAR_HIGH_CABINET');lower=bounds('SUNROOM_INTEGRATED_UNDERSIDE')
assert abs(upper[0][2]-2.1)<1e-5 and abs(upper[1][2]-2.6)<1e-5 and abs(upper[1][1]-upper[0][1]-.6)<1e-5
assert abs(lower[0][2]-1.8)<1e-5 and abs(lower[1][1]-lower[0][1]-.35)<1e-5
steps=[bounds('STEP_'+str(i)) for i in range(3)];assert all(abs(b[1][2]-.15*(i+1))<1e-5 for i,b in enumerate(steps))
reading=[bounds('READING_5015_SHORT_SLIDING_CABINET'),bounds('READING_5015_SHORT_SHELF_2')];assert reading[0][0][1]>8 and reading[0][1][0]<7.75
assert abs(reading[0][0][2]-.505)<1e-5
console_names=[n for n in bpy.data.objects.keys() if n.startswith('V4_Console_') and not visibility[n]]
reading_names=[n for n in bpy.data.objects.keys() if n.startswith(('READING_5015_','READING_DISPLAY_','READING_BOOK_')) and bpy.data.objects[n].type=='MESH' and not visibility[n]]
reading_collisions=[]
for n in reading_names:
 for other in console_names:
  overlap=g(bpy.data.objects[n])[1].overlap(g(bpy.data.objects[other])[1])
  if overlap:reading_collisions.append([n,other,len(overlap)])
assert not reading_collisions,reading_collisions
assert not bpy.data.objects['V3_KITCHEN_DAYLIGHT_THROUGH_SOUTH_WINDOW'].visible_transmission
assert not bpy.data.objects['V3_KITCHEN_DAYLIGHT_THROUGH_SOUTH_WINDOW'].visible_glossy
reg=json.loads((ROOT/'renders/whole_house_final_study_v1/00_MANIFEST/CAMERA_REGISTER_REVIEW_V3.json').read_text())
for c in reg['cameras']:
 o=bpy.data.objects[c['camera_name']]
 assert max(abs(o.matrix_world[i][j]-c['matrix_world'][i][j]) for i in range(4) for j in range(4))<1e-5
 assert abs(o.data.lens-c['lens_mm'])<1e-4
mirror_names=['B11_SITE_KITCHEN_WINDOW_GLASS_0','B11_SITE_KITCHEN_WINDOW_GLASS_1','B11_SITE_KITCHEN_WINDOW_MULLION_1'];windows=[bounds(n) for n in mirror_names]
assert len(windows)==3 and abs(windows[0][0][2]-1.055)<1e-4
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()];assert not missing,missing
# Only genuinely new product surfaces/contact relationships need new mesh gates.
intersections=[];contacts=[]
for j in [1,2]:
 sn='HOUSE_V1_SOFA_'+str(j)+'_V10_SEAT_COMPLETE_COVER';bn='HOUSE_V1_SOFA_'+str(j)+'_V10_BACK_COMPLETE_COVER'
 sp,st=g(bpy.data.objects[sn]);bp,bt=g(bpy.data.objects[bn]);overlap=st.overlap(bt)
 if overlap:intersections.append([sn,bn,len(overlap)])
 gaps=[]
 for p in bp:
  if p.z<.56:
   hit=st.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)))
   if hit[0] is not None:gaps.append(p.z-hit[0].z)
 contacts.append({'seat':sn,'back':bn,'min_back_vertex_gap_mm':min(gaps)*1000 if gaps else None,'seat_bottom_mm':min(p.z for p in sp)*1000})
 for rail in ['V4_Sofa_back_top_rail','V4_Sofa_back_lower_rail']:
  if bt.overlap(g(bpy.data.objects[rail])[1]):intersections.append([bn,rail])
pair_faces=[]
names=[n for n in bpy.data.objects.keys() if n.startswith('HOUSE_V1_SOFA_') and 'COMPLETE_COVER' in n and not n.endswith('_welt')]
for i,n in enumerate(names):
 for other in names[i+1:]:
  overlap=g(bpy.data.objects[n])[1].overlap(g(bpy.data.objects[other])[1])
  if overlap:pair_faces.append([n,other,len(overlap)])
report={'status':'PASS_ARCHITECTURE_AND_HISTORY_CONTACT_REVIEW' if not intersections and not pair_faces else 'PASS_ARCHITECTURE_CONTACT_REPAIR_REQUIRED','source_sha256':a['source_sha256'],'candidate_sha256':a['output_sha256'],'protected_files':len(protected),'original_geometry_unchanged':len(a['original_states']),'unexpected_geometry_pose_changes':unexpected,'allowed_reading_rigid_move':sorted(allowed_pose),'north_upper_bounds_m':upper,'north_lower_open_bounds_m':lower,'three_step_tops_m':[b[1][2] for b in steps],'reading_bounds_m':reading,'kitchen_window_bounds_m':windows,'sofa_contacts':contacts,'sofa_penetrating_pairs':intersections+pair_faces,'total_object_count':len(bpy.data.objects),'actual_new_geometry_count':a['created_count'],'missing_images':missing,'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'owner_visual_accepted':False,'dimension_approval':'source architecture fixed; new furniture follows recorded custom dimensions; procurement/site/human clearance pending'}
report.update({'registered_camera_count':len(reg['cameras']),'reading_console_penetrating_pairs':reading_collisions,'reading_console_clearance_mm':1000*(reading[0][0][2]-bounds('V4_Console_solid_ash_top')[1][2]),'helper_light_disc_visibility_corrected':True,'not_certified':['wall-mounted bookcase anchors/loading','dynamic north-cabinet head clearance','furniture SKU/procurement','seat height/comfort','pixelwise AI reference match']})
bed_support=[]
for room in ['MOTHER','COUPLE']:
 pre='HOUSE_V1_'+room+'_';mp,mt=g(bpy.data.objects[pre+'mattress']);pp,_=g(bpy.data.objects[pre+'platform']);cp,ct=g(bpy.data.objects[pre+'bedcover'])
 gap=min(p.z for p in mp)-max(p.z for p in pp);gaps=[]
 for p in cp:
  hit=mt.ray_cast(Vector((p.x,p.y,3.5)),Vector((0,0,-1)))
  if hit[0] is not None:gaps.append(p.z-hit[0].z)
 assert abs(gap)<.0001,(room,gap)
 assert min(gaps)>-.001,(room,min(gaps))
 bed_support.append({'room':room,'mattress_platform_gap_mm':gap*1000,'cover_min_gap_mm':min(gaps)*1000,'cover_vertices_checked':len(gaps)})
prop_support=[]
for rec in a['explicit_prop_supports']:
 points=[]
 for n in rec['objects']:points+=g(bpy.data.objects[n])[0]
 bb=bounds(rec['source_support']);lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
 gap=lo[2]-bb[1][2];inside=all(lo[i]>=bb[0][i]-.001 and hi[i]<=bb[1][i]+.001 for i in [0,1])
 assert abs(gap)<.002 and inside,(rec['objects'],gap,inside)
 prop_support.append({'objects':rec['objects'],'support':rec['source_support'],'bottom_gap_mm':gap*1000,'footprint_supported':inside})
report.update({'bed_supports':bed_support,'styling_supports':prop_support,'actual_added_meshes':sum(o.type=='MESH' and o.name not in a['original_states'] for o in bpy.data.objects)})
assert not intersections and not pair_faces
(RUN/'VERIFICATION_FINAL.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('HOUSE_VERIFICATION',json.dumps({k:report[k] for k in ['status','protected_files','original_geometry_unchanged','sofa_penetrating_pairs','actual_new_geometry_count','packed_images','reading_console_clearance_mm','registered_camera_count']}))
