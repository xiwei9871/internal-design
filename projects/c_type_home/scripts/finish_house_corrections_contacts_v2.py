"""Bounded final-surface contact repair, original built candidate retained."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'design/whole_house_model_v2';a=json.loads((D/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dest=D/'WHOLE_HOUSE_CORRECTED_CONTACT_V2.blend'
if dest.exists():raise SystemExit('Preserved contact candidate exists')
bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene
ov={o.name:(o.hide_viewport,o.hide_get()) for o in s.objects};cv={c.name:c.hide_viewport for c in bpy.data.collections}
for c in bpy.data.collections:c.hide_viewport=False
for o in s.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
for room in ['COUPLE','GUEST']:
 m=next(o for o in s.objects if o.name.startswith('HOUSE_V2_'+room+'_mattress') and o.type=='MESH' and 'seam' not in o.name);e=m.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];fs=[list(f.vertices) for f in me.polygons];e.to_mesh_clear();tree=BVHTree.FromPolygons(vs,fs)
 o=bpy.data.objects['HOUSE_V2_'+room+'_duvet'];o.data=o.data.copy()
 for v in o.data.vertices:
  p=o.matrix_world@v.co;hit=tree.ray_cast(Vector((p.x,p.y,3.5)),Vector((0,0,-1)))
  if hit[0] is not None:p.z=max(p.z,hit[0].z+.0055);v.co=o.matrix_world.inverted()@p
for n,(hv,hs) in ov.items():o=bpy.data.objects[n];o.hide_viewport=hv;o.hide_set(hs)
for n,hv in cv.items():bpy.data.collections[n].hide_viewport=hv
bpy.ops.wm.save_as_mainfile(filepath=str(dest));a['pre_contact_candidate']={'path':str(src),'sha256':a['output_sha256']};a['output']=str(dest);a['output_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();a['contact_fix']='project actual final mattress surface; preserve drop outside supporting footprint'
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print('CONTACT_FINISH',a['output_sha256'])
