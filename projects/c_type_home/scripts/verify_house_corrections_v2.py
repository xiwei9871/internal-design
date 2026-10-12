"""Fresh-open final geometry, protected sources, door sweeps and substance assignment."""
import bpy,json,hashlib,struct,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'design/whole_house_model_v2';a=json.loads((D/'BUILD_AUDIT.json').read_text());base=json.loads((R/'design/whole_house_model_v1/assembly/BUILD_AUDIT.json').read_text())
protected=json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files']
for f in protected:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256']
assert hashlib.sha256(Path(a['source']).read_bytes()).hexdigest()==a['source_sha256']
assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==a['output_sha256']
bpy.ops.wm.open_mainfile(filepath=a['output']);vis={o.name:o.hide_render for o in bpy.data.objects}
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def hashmesh(me):
 h=hashlib.sha256()
 for v in me.vertices:h.update(struct.pack('<fff',*v.co))
 for f in me.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
assert all(hashmesh(bpy.data.objects[n].data)==v['geometry'] for n,v in base['original_states'].items() if v['type']=='MESH')
cache={}
def geo(o):
 if o.name not in cache:
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];fs=[tuple(f.vertices) for f in me.polygons];e.to_mesh_clear();cache[o.name]=(vs,fs,BVHTree.FromPolygons(vs,fs))
 return cache[o.name]
def bb(o):
 pts=geo(o)[0];return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
reg=json.loads((R/'renders/whole_house_final_study_v1/00_MANIFEST/CAMERA_REGISTER_REVIEW_V3.json').read_text())
for c in reg['cameras']:
 o=bpy.data.objects[c['camera_name']];assert max(abs(o.matrix_world[i][j]-c['matrix_world'][i][j]) for i in range(4) for j in range(4))<1e-5
assert all(abs(bb(bpy.data.objects['STEP_'+str(i)])[1][2]-(i+1)*.15)<1e-5 for i in range(3))
up=bb(bpy.data.objects['SUNROOM_SOFA_REAR_HIGH_CABINET']);low=bb(bpy.data.objects['SUNROOM_INTEGRATED_UNDERSIDE']);assert abs(up[0][2]-2.1)<1e-5 and abs(up[1][2]-2.6)<1e-5 and abs(up[1][1]-up[0][1]-.6)<1e-5 and abs(low[0][2]-1.8)<1e-5
for c in a['material_changes']:
 o=bpy.data.objects[c['object']];assert o.data.materials[0].name==c['material']
assert bpy.data.materials['HOUSE_V2_SECONDARY_FROSTED_GLASS'].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value>.4
new=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('HOUSE_V2_') and not vis[o.name]]
guest=[o for o in new if o.name.startswith('HOUSE_V2_GUEST_')];guest.extend([bpy.data.objects['BW1_GUEST_DESK_CHAIR']])
leaves=[o for o in bpy.data.objects if o.name.startswith('B11_Rectangle045_FRONT_') and not vis[o.name]];assert len(leaves)==3
hits=[]
for leaf in leaves:
 vs,fs,_=geo(leaf);b=bb(leaf)
 for side,y,sign in [('south',b[0][1],-1),('north',b[1][1],1)]:
  pivot=Vector((b[1][0],y,b[0][2]))
  for angle in range(0,91):
   M=Matrix.Translation(pivot)@Matrix.Rotation(sign*math.radians(angle),4,'Z')@Matrix.Translation(-pivot);tree=BVHTree.FromPolygons([M@v for v in vs],fs)
   for target in guest:
    if tree.overlap(geo(target)[2]):hits.append([leaf.name,side,angle,target.name])
assert not hits,hits[:10]
# Entry leaf opening, both potential hinges against all new guest parts.
entry=bpy.data.objects['V4_D-GUEST-ROOM_LEAF_0'];vs,fs,_=geo(entry);b=bb(entry);entryhits=[]
for x,sign in [(b[0][0],1),(b[1][0],-1)]:
 pivot=Vector((x,b[0][1],b[0][2]))
 for ang in range(0,91):
  M=Matrix.Translation(pivot)@Matrix.Rotation(sign*math.radians(ang),4,'Z')@Matrix.Translation(-pivot);t=BVHTree.FromPolygons([M@v for v in vs],fs)
  for target in guest:
   if t.overlap(geo(target)[2]):entryhits.append([ang,target.name])
# Entry remains an explicit owner-directed guest placement issue.
# Continue independent contact diagnosis; never mark this gate passed.

contacts=[];problems=[]
for room in ['COUPLE','GUEST']:
 m=next(o for o in bpy.data.objects if o.name.startswith('HOUSE_V2_'+room+'_mattress') and 'seam' not in o.name);dv=bpy.data.objects['HOUSE_V2_'+room+'_duvet'];mp,_,mt=geo(m);dp,_,_=geo(dv);gaps=[]
 for p in dp:
  h=mt.ray_cast(Vector((p.x,p.y,3.5)),Vector((0,0,-1)))
  if h[0] is not None:gaps.append(p.z-h[0].z)
 contacts.append({'room':room,'cover_min_gap_mm':min(gaps)*1000,'mattress_min_z_m':min(p.z for p in mp)})
 if min(gaps)<-.001:problems.append([room,'cover penetration',min(gaps)])
 for target in new:
  if target.name.startswith('HOUSE_V2_'+room+'_') and 'pillow' in target.name:
   if geo(target)[2].overlap(mt):problems.append([target.name,'pillow/mattress'])
north=[]
for j in [0,1]:
 seat=bpy.data.objects['HOUSE_V2_North_seat_'+str(j)];back=bpy.data.objects['HOUSE_V2_North_back_'+str(j)]
 overlap=geo(seat)[2].overlap(geo(back)[2]);gaps=[]
 for p in geo(back)[0]:
  if p.z<.52:
   h=geo(seat)[2].ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)))
   if h[0] is not None:gaps.append(p.z-h[0].z)
 north.append({'pair':j,'overlaps':len(overlap),'min_back_vertex_gap_mm':min(gaps)*1000 if gaps else None,'seat_bounds':bb(seat),'back_bounds':bb(back)})
 if overlap:problems.append(['north',j,'seat/back'])
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()];assert not missing
report={'status':'PASS' if not problems and not entryhits else 'CORRECTION_REQUIRED','candidate_sha256':a['output_sha256'],'protected_hashes':len(protected),'original_meshes_preserved':True,'registered_cameras':75,'material_assignments_checked':len(a['material_changes']),'north_upper_bounds':up,'north_lower_bounds':low,'guest_wardrobe_leaf_count':len(leaves),'guest_wardrobe_0to90_both_hinge_sweep_hits':hits,'guest_entry_0to90_hits':entryhits,'guest_gate_status':'PENDING_OWNER_PLACEMENT_AND_HINGE_DECISION' if entryhits else 'PASS_GEOMETRY_SWEEPS','bed_contacts':contacts,'north_contacts':north,'contact_problems':problems,'new_mesh_count':len(new),'missing_images':missing,'accepted_visual':False,'limits':['product back/hidden joinery inferred','selective collision tests','dynamic comfort/body clearances not certified','procurement and hinges still need site verification']}
(D/'VERIFICATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('V2_VERIFICATION',json.dumps({k:report[k] for k in ['status','guest_wardrobe_leaf_count','guest_wardrobe_0to90_both_hinge_sweep_hits','contact_problems','new_mesh_count']}))
