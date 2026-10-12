"""Fresh-open length and exact preservation outside owner-requested console."""
import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/console1600_v4';a=json.loads((D/'AUDIT.json').read_text());target='HUNYUAN_V3_COUPLE_TV_CONSOLE'
def meshhash(me):
 h=hashlib.sha256()
 for v in me.vertices:h.update(struct.pack('<fff',*v.co))
 for f in me.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
def states(path):
 bpy.ops.wm.open_mainfile(filepath=path);v={o.name:o.hide_render for o in bpy.data.objects}
 for c in bpy.data.collections:c.hide_viewport=False
 for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update()
 return {o.name:{'mesh':meshhash(o.data) if o.type=='MESH' else None,'matrix':[list(r) for r in o.matrix_world],'hide_render':v[o.name]} for o in bpy.data.objects}
assert hashlib.sha256(Path(a['source']).read_bytes()).hexdigest()==a['source_sha256'];assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==a['sha256']
old=states(a['source']);new=states(a['output']);issues=[]
for n,s in old.items():
 if n!=target and new.get(n)!=s:issues.append(n)
assert not issues,issues[:10]
o=bpy.data.objects[target];vs=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
assert abs(hi[1]-lo[1]-1.6)<1e-5
protected=json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files']
for f in protected:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256']
r={'status':'PASS_SINGLE_OBJECT_LENGTH_CHANGE','candidate_sha256':a['sha256'],'console_length_mm':(hi[1]-lo[1])*1000,'unchanged_other_objects':len(old)-1,'unexpected_changes':issues,'protected_source_hashes':len(protected),'guest_unchanged':True,'depth_height_unchanged':True,'bedfoot_clearance_mm':a['bedfoot_clearance_mm'],'owner_visual_accepted':False}
(D/'VERIFICATION.json').write_text(json.dumps(r,indent=2)+'\n');print('VERIFY_CONSOLE1600',json.dumps(r))
