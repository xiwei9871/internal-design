"""Correct measured mattress support and cloth collision, retain all prior versions."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'design/whole_house_model_v1/assembly'
a=json.loads((RUN/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dest=RUN/'WHOLE_HOUSE_REVIEW_SUPPORTED_V2.blend'
if dest.exists():raise SystemExit('Preserved output exists.')
bpy.ops.wm.open_mainfile(filepath=str(src));visibility={o.name:(o.hide_viewport,o.hide_get()) for o in bpy.data.objects};cv={c.name:c.hide_viewport for c in bpy.data.collections}
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def mesh(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();vs=[e.matrix_world@v.co for v in m.vertices];fs=[tuple(f.vertices) for f in m.polygons];e.to_mesh_clear();return vs,BVHTree.FromPolygons(vs,fs)
def support_height(tree,p):
 hit=tree.ray_cast(Vector((p.x,p.y,3.5)),Vector((0,0,-1)));return hit[0].z if hit[0] is not None else None
records=[]
for room in ['MOTHER','COUPLE']:
 pre='HOUSE_V1_'+room+'_';m=bpy.data.objects[pre+'mattress'];pts,_=mesh(m);platform,_=mesh(bpy.data.objects[pre+'platform']);gap=min(p.z for p in pts)-max(p.z for p in platform)
 m.location.z-=gap;bpy.context.view_layer.update();_,tree=mesh(m)
 cover=bpy.data.objects[pre+'bedcover'];count=0
 # The first coarse-control projection failed after subdivision near the
 # rounded mattress rim. Bake that final surface, then test/project the final
 # evaluated vertices; do not validate just the unsmoothed control cage.
 for mod in list(cover.modifiers):
  if mod.type=='SOLIDIFY':cover.modifiers.remove(mod)
 bpy.context.view_layer.update()
 e=cover.evaluated_get(bpy.context.evaluated_depsgraph_get());baked=bpy.data.meshes.new_from_object(e);cover.modifiers.clear();cover.data=baked
 # Project to real final mattress surface where supported. The cloth outside
 # the mattress footprint keeps its explicit side drop; no whole-box flattening.
 for vertex in cover.data.vertices:
  p=cover.matrix_world@vertex.co;z=support_height(tree,p)
  if z is not None:p.z=max(p.z,z+.0055);vertex.co=cover.matrix_world.inverted()@p;count+=1
 so=cover.modifiers.new('Outward fabric thickness','SOLIDIFY');so.thickness=.002;so.offset=1
 bpy.context.view_layer.update();_,ct=mesh(cover);props=[]
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name.startswith(pre) and any(t in o.name for t in ['_pillow','_sage_runner']):
   pts,_=mesh(o);gaps=[]
   for p in pts:
    z=support_height(ct,p)
    if z is not None:gaps.append(p.z-z)
   if gaps:
    dz=min(gaps)-.001;o.location.z-=dz;props.append({'object':o.name,'vertical_correction_m':-dz})
 records.append({'room':room,'mattress_support_correction_m':-gap,'cover_projected_vertices':count,'supported_props':props})
for n,(hv,hs) in visibility.items():o=bpy.data.objects[n];o.hide_viewport=hv;o.hide_set(hs)
for n,h in cv.items():bpy.data.collections[n].hide_viewport=h
bpy.ops.wm.save_as_mainfile(filepath=str(dest));a['pre_bed_support_repair']={'path':str(src),'sha256':a['output_sha256']};a['output']=str(dest);a['output_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();a['bed_support_repairs']=records
(RUN/'BUILD_AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print('BED_SUPPORT_REPAIR',a['output_sha256'])
