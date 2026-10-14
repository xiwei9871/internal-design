"""Fresh-open material-only regression and exact privacy selection checks."""
import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/glass_privacy_v8';a=json.loads((D/'BUILD_AUDIT.json').read_text())
assert hashlib.sha256(Path(a['source']).read_bytes()).hexdigest()==a['source_sha256']
assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==a['sha256']
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
view={'active':bpy.context.window.view_layer.name,'roof_hidden':all(bpy.data.objects[n].hide_get(view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN']) for n in ['V7_CEILING_LOW','V7_CEILING_HIGH','V7_CEILING_450MM_TRANSITION'])}
for col in bpy.data.collections:col.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def h(o):
 v=hashlib.sha256()
 if o.type=='MESH':
  for p in o.data.vertices:v.update(struct.pack('<fff',*p.co))
  for f in o.data.polygons:v.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return v.hexdigest()
changed={c['object'] for c in a['changes']};issues=[]
assert set(a['baseline'])=={o.name for o in bpy.data.objects}
for n,b in a['baseline'].items():
 o=bpy.data.objects[n]
 if h(o)!=b['mesh'] or [list(v) for v in o.matrix_world]!=b['matrix'] or o.hide_render!=b['hide_render']:issues.append(n)
 if o.type=='MESH' and n not in changed:assert [m.name if m else None for m in o.data.materials]==b['materials'],n
assert not issues,issues[:10]
for name in ['V8_COLORLESS_CLEAR_ARCHITECTURAL_GLASS','V8_COLORLESS_PRIVACY_FROSTED_GLASS']:
 m=bpy.data.materials[name];p=m.node_tree.nodes.get('Principled BSDF');assert list(p.inputs['Base Color'].default_value)==[1,1,1,1];assert p.inputs['Transmission Weight'].default_value==1 and p.inputs['Metallic'].default_value==0;assert not any(n.type=='VOLUME_ABSORPTION' for n in m.node_tree.nodes)
for n in a['privacy_objects']:assert any(m.name=='V8_COLORLESS_PRIVACY_FROSTED_GLASS' for m in bpy.data.objects[n].data.materials if m)
for n in a['bathroom_timber_doors']:assert bpy.data.objects[n].data.materials[0].name=='V7_CATALOG_PALE_NATURAL_ASH'
protected=json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files']
for f in protected:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256']
r={'status':'PASS_MATERIAL_SELECTION_AND_PRESERVATION','sha256':a['sha256'],'source_objects_unchanged':len(a['baseline']),'geometry_pose_visibility_changes':issues,'clear_glass_objects':len(a['clear_objects']),'privacy_glass_objects':len(a['privacy_objects']),'unrelated_material_slots_unchanged':True,'wood_bathroom_doors_unchanged':a['bathroom_timber_doors'],'protected_sources':len(protected),'saved_view':view,'privacy_guarantee_certified':False,'owner_visual_accepted':False}
(D/'VERIFICATION.json').write_text(json.dumps(r,indent=2)+'\n');print('VERIFY_GLASS_V8',json.dumps(r))
