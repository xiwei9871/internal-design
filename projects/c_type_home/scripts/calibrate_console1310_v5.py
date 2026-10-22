"""Catalog1310-2.0: body2000x460x400; decorative objects remain separate metrics."""
import bpy,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'design/console1310_v5';D.mkdir(exist_ok=True);src=R/'design/console1600_v4/WHOLE_HOUSE_CONSOLE1600_V4.blend';dest=D/'WHOLE_HOUSE_CONSOLE1310_REAL_V5.blend';name='HUNYUAN_V3_COUPLE_TV_CONSOLE'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='7ff55a69723783bf6a59af837a1afe53e42e8532a4e7d03bd922d1b1a855d2ac'
if dest.exists():raise SystemExit('Preserved real-size candidate exists')
def mh(me):
 h=hashlib.sha256()
 for v in me.vertices:h.update(struct.pack('<fff',*v.co))
 for f in me.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;o=bpy.data.objects[name];initial={q.name:mh(q.data) for q in s.objects if q.type=='MESH' and q!=o};o.data=o.data.copy();pts=[v.co.copy() for v in o.data.vertices]
lo=Vector(min(p[i] for p in pts) for i in range(3));hi=Vector(max(p[i] for p in pts) for i in range(3));cut=.683;underside=.649;floor=.45;newtop=.85;center=2.087
# Source horizontal area probe locates primarytabletop around677-680mm,
# underside649mm. Cut683 separates cabinet support from most loose decor.
# Upper-connected objects inferred by same coordinate-seam/component method
# used in V4; immutableGLB remains the source ofshape and UV.
eligible={i for i,p in enumerate(pts) if p.z>cut};index={};adj={};groups=[];seen=set();offset={}
for i in eligible:index.setdefault(tuple(round(v,5) for v in pts[i]),[]).append(i)
for f in o.data.polygons:
 ids=[i for i in f.vertices if i in eligible]
 for i in ids:adj.setdefault(i,set()).update(ids)
for ids in index.values():
 for i in ids:adj.setdefault(i,set()).update(ids)
for i in eligible:
 if i in seen:continue
 stack=[i];g=[];seen.add(i)
 while stack:
  j=stack.pop();g.append(j)
  for k in adj.get(j,[]):
   if k not in seen:seen.add(k);stack.append(k)
 cx=(min(pts[j].x for j in g)+max(pts[j].x for j in g))/2;cy=(min(pts[j].y for j in g)+max(pts[j].y for j in g))/2
 delta=Vector(((cx-lo.x)*(.46/(hi.x-lo.x)-1),(cy-center)*.25,newtop-cut))
 for j in g:offset[j]=delta
 groups.append({'vertices':len(g),'translation_m':list(delta)})
body=[]
for i,v in enumerate(o.data.vertices):
 p=pts[i]
 if i in offset:v.co=p+offset[i]
 else:
  x=lo.x+(p.x-lo.x)*.46/(hi.x-lo.x);y=center+(p.y-center)*1.25
  z=floor+(p.z-floor)*(.368/(underside-floor)) if p.z<underside else floor+.368+(p.z-underside)/(cut-underside)*.032
  v.co=Vector((x,y,z));body.append(i)
o.data.update();o['real_product']='1310-2.0 naturaledge body2000x460x400mm';o['body_top_elevation_m']=.85
bpy.ops.wm.save_as_mainfile(filepath=str(dest));sha=hashlib.sha256(dest.read_bytes()).hexdigest()
for q in s.objects:
 if q.type=='MESH' and q!=o:assert mh(q.data)==initial[q.name]
bpts=[o.data.vertices[i].co for i in body];bb=[[min(p[i] for p in bpts) for i in range(3)],[max(p[i] for p in bpts) for i in range(3)]]
assert abs(bb[1][0]-bb[0][0]-.46)<1e-5 and abs(bb[1][1]-bb[0][1]-2)<1e-5
assert abs(bb[1][2]-.85)<.003
for c in bpy.data.collections:c.hide_viewport=False
for q in s.objects:q.hide_viewport=False;q.hide_set(False)
bpy.context.view_layer.update()
def geo(q):
 e=q.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();vs=[e.matrix_world@v.co for v in m.vertices];fs=[list(f.vertices) for f in m.polygons];e.to_mesh_clear();return vs,BVHTree.FromPolygons(vs,fs)
cv,ct=geo(o);bed=bpy.data.objects['HUNYUAN_V3_COUPLE_BED'];bv,bt=geo(bed);hits=ct.overlap(bt);assert not hits
record={'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output':str(dest),'sha256':sha,'catalog_product':'1310-2.0 naturaledge','specified_body_l_d_h_mm':[2000,460,400],'floor_m':floor,'body_bounds_m':bb,'measured_body_l_d_h_mm':[(bb[1][1]-bb[0][1])*1000,(bb[1][0]-bb[0][0])*1000,(bb[1][2]-bb[0][2])*1000],'decor_groups':groups,'body_vertex_indices':body,'decor_vertex_indices':sorted(eligible),'body_top_nominal_elevation_m':newtop,'totalheight_including_decor_mm':(max(p.z for p in cv)-min(p.z for p in cv))*1000,'bedfoot_clearance_mm':(min(p.x for p in bv)-max(p.x for p in cv))*1000,'bed_console_intersections':len(hits),'other_meshes_unchanged':len(initial),'source_semantics':'tabletop area probe separatesbody/props; generatedmesh junctions inferred, notmanufacturerexact','image2_requests':0,'status':'HUMAN_REVIEW'}
(D/'AUDIT.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print('REAL_CONSOLE1310',json.dumps({k:record[k] for k in ['sha256','measured_body_l_d_h_mm','totalheight_including_decor_mm','bedfoot_clearance_mm']}))
