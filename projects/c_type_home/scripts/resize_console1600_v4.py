"""Extend generated console length only; retain height/depth and prop proportions."""
import bpy,json,hashlib,struct,time
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'design/console1600_v4';D.mkdir(exist_ok=True);src=R/'design/hunyuan_asset_v3/WHOLE_HOUSE_HUNYUAN_MATERIAL_REVIEW_V3.blend';dest=D/'WHOLE_HOUSE_CONSOLE1600_V4.blend'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='8ce341da085e6a3c29b8fdc4ca4b8aa84117f6df19e4686a1be043d94e4fd609'
if dest.exists():raise SystemExit('Preserved candidate exists')
bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;name='HUNYUAN_V3_COUPLE_TV_CONSOLE';o=bpy.data.objects[name];orig={p.name:hashlib.sha256(bytes(str([(tuple(v.co)) for v in p.data.vertices]),'utf8')).hexdigest() for p in s.objects if p.type=='MESH' and p.name!=name}
o.data=o.data.copy();points=[v.co.copy() for v in o.data.vertices];center=2.087;tabletop=.696
# The generated GLB has table+some decorativeparts connected. Above tabletop,
# classify actual neighbouring geometry into connected prop groups with a
# coordinate seam map; translated groups keep their real shape and UV.
index={};adj={};eligible=set()
for i,p in enumerate(points):
 if p.z>tabletop+.001:eligible.add(i);index.setdefault(tuple(round(x,5) for x in p),[]).append(i)
for face in o.data.polygons:
 ids=[i for i in face.vertices if i in eligible]
 for i in ids:adj.setdefault(i,set()).update(ids)
for ids in index.values():
 for i in ids:adj.setdefault(i,set()).update(ids)
seen=set();groups=[];offsets={}
for i in eligible:
 if i in seen:continue
 stack=[i];seen.add(i);g=[]
 while stack:
  j=stack.pop();g.append(j)
  for k in adj.get(j,[]):
   if k not in seen:seen.add(k);stack.append(k)
 cy=(min(points[j].y for j in g)+max(points[j].y for j in g))/2;delta=(cy-center)/3
 for j in g:offsets[j]=delta
 groups.append({'vertices':len(g),'original_y_center':cy,'translation_y_m':delta})
for i,v in enumerate(o.data.vertices):
 p=points[i];v.co.y=p.y+offsets[i] if i in offsets else center+(p.y-center)*4/3
o.data.update();s['console_v4_length_mm']=1600
bpy.ops.wm.save_as_mainfile(filepath=str(dest));sha=hashlib.sha256(dest.read_bytes()).hexdigest()
for c in bpy.data.collections:c.hide_viewport=False
for p in s.objects:p.hide_viewport=False;p.hide_set(False)
bpy.context.view_layer.update()
def geo(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();vs=[e.matrix_world@v.co for v in m.vertices];fs=[list(f.vertices) for f in m.polygons];e.to_mesh_clear();return vs,BVHTree.FromPolygons(vs,fs)
vs,tree=geo(o);lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)];assert abs(hi[1]-lo[1]-1.6)<1e-5
bed=bpy.data.objects['HUNYUAN_V3_COUPLE_BED'];bv,bt=geo(bed);hits=tree.overlap(bt);assert not hits
for p in s.objects:
 if p.type=='MESH' and p.name!=name:assert hashlib.sha256(bytes(str([tuple(v.co) for v in p.data.vertices]),'utf8')).hexdigest()==orig[p.name]
protected=json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files']
for f in protected:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256']
a={'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output':str(dest),'sha256':sha,'length_mm':1600,'depth_mm':(hi[0]-lo[0])*1000,'total_height_with_props_mm':(hi[2]-lo[2])*1000,'bounds_m':[lo,hi],'bedfoot_clearance_mm':(min(p.x for p in bv)-hi[0])*1000,'bed_console_intersections':len(hits),'prop_groups':groups,'method':'lengthwise tableextension and above-table connected decorativegroups rigidtranslation, UVunchanged; hiddengeneratedconstruction not manufacturerexact','other_meshes_unchanged':len(orig),'protected_files':len(protected),'guest_unchanged':True,'image2_requests':0,'status':'HUMAN_REVIEW'}
(D/'AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print('CONSOLE1600',json.dumps({k:a[k] for k in ['sha256','length_mm','depth_mm','bedfoot_clearance_mm','other_meshes_unchanged']}))
