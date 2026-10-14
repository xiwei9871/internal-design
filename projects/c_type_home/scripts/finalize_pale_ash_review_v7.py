"""Normalize outward normals on new ceiling solids and save final review state."""
import bpy,bmesh,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/pale_ash_review_v7';a=json.loads((D/'BUILD_AUDIT.json').read_text())
src=Path(a['output']);dst=D/'WHOLE_HOUSE_PALE_ASH_REVIEW_V7_FINAL.blend';assert not dst.exists()
assert hashlib.sha256(src.read_bytes()).hexdigest()==a['sha256']
bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene
for n in a['new_ceiling_objects'][:2]:
 o=bpy.data.objects[n];bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 top=max(v.co.z for v in o.data.vertices);assert all(f.normal.z>.99 for f in o.data.polygons if all(abs(o.data.vertices[i].co.z-top)<1e-5 for i in f.vertices))
s.view_layers['OVERVIEW_CEILING_HIDDEN'].use=False;s.view_layers['INTERIOR_CLOSED_CEILING'].use=True
bpy.context.window.view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN']
bpy.ops.wm.save_as_mainfile(filepath=str(dst))
a['pre_normals_candidate']={'path':str(src),'sha256':a['sha256']};a['output']=str(dst);a['sha256']=hashlib.sha256(dst.read_bytes()).hexdigest();a['ceiling_normals_outward']=True
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');print('FINAL_V7',a['sha256'])
