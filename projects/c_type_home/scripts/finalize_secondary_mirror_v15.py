"""V15: move only mirror+trim; hide selected leftover accessories; preserve all source visibility."""
import bpy,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/secondary_mirror_v15';S=R/'design/platform_bath_fitness_v14/WHOLE_HOUSE_PLATFORM_BATH_FITNESS_FINAL_V14.blend';O=D/'WHOLE_HOUSE_SECONDARY_MIRROR_FINAL_V15.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();SHA='0ef86d31de4ab8afb4befcb6ac639054c955e970f85bd4007f04dc3252055144';assert sha(S)==SHA and not O.exists()
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
moved=['CBM_SECONDARY_MIRROR','CBM_SECONDARY_MIRROR_FRAME'];hidden=['CBM_secondary_BOTTLE_0','CBM_secondary_BOTTLE_1','HOUSE_V1_secondary_bath_soap_body','HOUSE_V1_secondary_bath_soap_neck','HOUSE_V1_secondary_bath_towel']
for n in moved:bpy.data.objects[n].location.x-=.190
for n in hidden:
 o=bpy.data.objects[n];o.hide_render=True;o.hide_viewport=True
 for l in s.view_layers:o.hide_set(True,view_layer=l)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(O))
# Fresh-open compared in identical evaluation state; capture saved visibility before unhiding.
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene
 state={'active_layer':bpy.context.window.view_layer.name,'collections':{c.name:(c.hide_viewport,c.hide_render) for c in bpy.data.collections},'objects':{o.name:{'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'layer_hide':{l.name:o.hide_get(view_layer=l) for l in s.view_layers}} for o in bpy.data.objects}}
 for c in bpy.data.collections:c.hide_viewport=False
 for o in bpy.data.objects:
  o.hide_viewport=False
  for l in s.view_layers:o.hide_set(False,view_layer=l)
 bpy.context.view_layer.update()
 for o in bpy.data.objects:
  h=hashlib.sha256()
  if o.type=='MESH':
   for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
   for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
  b=state['objects'][o.name];b.update({'mesh':h.hexdigest(),'matrix':[list(r) for r in o.matrix_world],'materials':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else []})
  if o.type=='MESH' and o.name in moved+['CBM_SECONDARY_UPPER_STORAGE','R3_VANITY_TOP','HOUSE_V1_V14_SHOWER_WEST_FIXED','VIEW_WALL_R3_WEST_PARTITION']:
   e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();b['bounds']=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
 return state
before=snapshot(S);after=snapshot(O);assert before['objects'].keys()==after['objects'].keys();assert before['collections']==after['collections'];assert before['active_layer']==after['active_layer'];issues=[]
for n,b in before['objects'].items():
 c=after['objects'][n]
 for key in ['mesh','materials']:
  if b[key]!=c[key]:issues.append((n,key))
 if n not in moved and b['matrix']!=c['matrix']:issues.append((n,'matrix'))
 if n not in hidden:
  for key in ['hide_render','hide_viewport','layer_hide']:
   if b[key]!=c[key]:issues.append((n,key))
 else:assert c['hide_render'] and c['hide_viewport'] and all(c['layer_hide'].values())
for n in moved:
 b=before['objects'][n]['matrix'];c=after['objects'][n]['matrix'];assert abs(c[0][3]-b[0][3]+.190)<1e-5;assert b[1:]==c[1:]
assert not issues,issues
frame=after['objects']['CBM_SECONDARY_MIRROR_FRAME']['bounds'];cab=after['objects']['CBM_SECONDARY_UPPER_STORAGE']['bounds'];wall=after['objects']['VIEW_WALL_R3_WEST_PARTITION']['bounds'];vg=after['objects']['R3_VANITY_TOP']['bounds'];sh=after['objects']['HOUSE_V1_V14_SHOWER_WEST_FIXED']['bounds']
assert frame[0][0]>wall[1][0]+.003;assert cab[0][0]-frame[1][0]>.12
sources=json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files']
for f in sources:assert sha(f['path'])==f['sha256']
a={'source':str(S),'source_sha256':SHA,'output':str(O),'sha256':sha(O),'moved_objects':moved,'west_translation_mm':190,'requested_translation_mm':200,'fit_adjustment':'200mm moves frame about6mm into west wall;190mm leaves4mm nominal wall-side clearance','hidden_accessories':hidden,'upper_storage_unchanged':True,'all_original_meshes_and_materials_unchanged':len(before['objects']),'unrelated_visibility_preserved':True,'protected_sources':16,'unexpected_changes':issues,'mirror_frame_bounds_m':frame,'mirror_frame_to_west_wall_mm':(frame[0][0]-wall[1][0])*1000,'mirror_frame_to_upper_storage_mm':(cab[0][0]-frame[1][0])*1000,'vanity_to_shower_fixed_glass_mm':(sh[0][0]-vg[1][0])*1000,'shower_dimensions_and_geometry_unchanged':True,'status':'PASS_TECHNICAL_CHECKS_HUMAN_REVIEW'}
(D/'FINAL_AUDIT.json').write_text(json.dumps(a,indent=2)+chr(10));print('V15_FINAL_VERIFY',json.dumps(a))

