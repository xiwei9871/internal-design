"""Relocate the complete existing reading rack to owner's exact selected west wall."""
import bpy,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'design/reading_wall_v10';S=R/'design/glass_visibility_v9/WHOLE_HOUSE_GLASS_VISIBILITY_V9.blend';O=D/'WHOLE_HOUSE_READING_WALL_V10.blend';assert not O.exists();assert hashlib.sha256(S.read_bytes()).hexdigest()=='42beee4cb51bce1487edbe0003b226951986ca073b2d2e3b4ffec9305c80f9cf'
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
hides={o.name:(o.hide_viewport,o.hide_get()) for o in bpy.data.objects}
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def meshhash(o):
 h=hashlib.sha256()
 if o.type=='MESH':
  for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
  for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
before={o.name:{'mesh':meshhash(o),'matrix':[list(r) for r in o.matrix_world],'hide_render':o.hide_render,'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else []} for o in bpy.data.objects}
# Only the proven whole reading assembly and its book root; do not move the selected background wall.
roots=[o for o in s.objects if (o.name.startswith(('READING_5015_','READING_DISPLAY_','HOUSE_V1_READING_WALL_CLEAT_')) or o.name=='HOUSE_V2_READING_BOOKS') and not o.hide_render]
assert bpy.data.objects['READING_5015_SHORT_SLIDING_CABINET'] in roots
moved={o.name for o in roots}
for o in roots:moved.update(q.name for q in o.children_recursive)
# Current rear-wall contact x7.75 -> target west face x9.059; avoid south doorway by center y5.30, not exact click y5.108.
delta=Vector((9.0499-7.75,5.30-8.60,.45))
for o in roots:o.location+=delta
bpy.context.view_layer.update()
def bounds(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();return [min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]
lo,hi=bounds(bpy.data.objects['READING_5015_SHORT_SLIDING_CABINET']);assert abs(hi[0]-lo[0]-.32)<1e-5 and abs(hi[1]-lo[1]-.82)<1e-5;assert lo[1]>4.82 and abs(lo[2]-.955)<1e-5
# Evaluate triangle intersections only for relocated assembly vs surrounding unchanged geometry.
def bvh(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];fs=[list(f.vertices) for f in me.polygons];e.to_mesh_clear();return BVHTree.FromPolygons(vs,fs),[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]
near=[]
for o in s.objects:
 if o.type=='MESH' and not o.hide_render and o.name not in moved:
  a,b=bounds(o)
  if all(b[i]>=lo[i]-.03 and a[i]<=hi[i]+(1.3 if i==2 else .07) for i in range(3)):near.append(o)
collisions=[];contacts=[]
for n in sorted(moved):
 o=bpy.data.objects[n]
 if o.type!='MESH':continue
 tree,a,b=bvh(o)
 for q in near:
  qa,qb=bounds(q)
  if not all(b[i]>qa[i]+.00005 and a[i]<qb[i]-.00005 for i in range(3)):continue
  qt,_,_=bvh(q);hits=tree.overlap(qt)
  if hits:collisions.append({'object':n,'obstacle':q.name,'triangles':len(hits)})
assert not collisions,collisions[:10]
for n,(hv,hg) in hides.items():bpy.data.objects[n].hide_viewport=hv;bpy.data.objects[n].hide_set(hg)
bpy.context.window.view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN'];bpy.ops.wm.save_as_mainfile(filepath=str(O))
record={'source':str(S),'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'output':str(O),'sha256':hashlib.sha256(O.read_bytes()).hexdigest(),'target_wall':'VIEW_WALL_R3_WEST_PARTITION','owner_hit_source_m':[9.059000015258787,5.108117921855653,1.5226244364137074],'assembly_translation_m':list(delta),'moved_objects':sorted(moved),'root_objects':[o.name for o in roots],'before':before,'cabinet_bounds_m':[lo,hi],'rack_envelope_m':[[8.6699,4.89,.955],[8.9899,5.71,2.495]],'wall_mount_rear_x_m':9.0499,'mount_face_note':'Selected derived wall face9.059 overlaps original wall whose visible westface9.0499; assembly placed at exterior-most source face to avoid9.1mm cleat embed' ,'floor_elevation_m':.45,'cabinet_bottom_above_floor_mm':505,'south_edge_to_room_door_trim_mm':(lo[1]-4.8390627)*1000,'corridor_clear_width_assuming_opposite_edge_x8_0_mm':(lo[0]-8.0)*1000,'corridor_note':'Local bounding estimate670mm if adjacent platform edge x8.0 controls; open-side span must be reviewed. Not comfort or elderly assistance certification.','relocation_obstacle_mesh_hits':collisions,'nearby_checked_objects':[o.name for o in near],'dimensions_and_materials_unchanged':True,'source_writeback':False,'image2_requests':0,'status':'HUMAN_REVIEW'}
(D/'BUILD_AUDIT.json').write_text(json.dumps(record,indent=2)+'\n');print('READING_WALL_V10',record['sha256'],'moved',len(moved),'bounds',record['cabinet_bounds_m'],'checked',len(near))
