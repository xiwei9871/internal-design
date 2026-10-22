import bpy,json,hashlib,sys,struct,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/fridge_finish_v13';a=json.loads((D/'BUILD_AUDIT.json').read_text());S=Path(a['output']);O=D/'WHOLE_HOUSE_FRIDGE_FINISH_DELIVERY_V13.blend';assert not O.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(S)==a['sha256'];bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
sys.path.insert(0,str(R/'scripts'));from whole_house_finish_parts_v1 import Parts
P=Parts(s.collection,bpy.data.materials[a['finish_material']],None)
for n in a['changed_cabinet_objects']:P.uv(bpy.data.objects[n])
bpy.ops.wm.save_as_mainfile(filepath=str(O));a['pre_uv_repair']={'output':str(S),'sha256':a['sha256']};a['output']=str(O);a['sha256']=sha(O)
a['shower_audit']={'outer_envelope_mm':[842.0,784.8],'shape':'five-sided chamfered corner; outer envelope is not a full rectangular clear area','rectangular_region_behind_chamfer_mm':[842.0,531.5],'glass_thickness_mm':8,'post_width_mm':18,'door_panel_width_mm':round(math.hypot(.332375,.253281)*1000,1),'max_nominal_clear_between_posts_mm':round(math.hypot(.332375,.253281)*1000-18,1),'door_hinges_or_slide_track_registered':False,'threshold_height_above_FFL_mm':20,'verdict':'Entry about400mm before hardware is too narrow for reliable basic daily use. Interior is also tight. Do not approve current shower as adequate; revise door/front geometry from an actual enclosure product before construction.','layout_changed':False}
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n')
# Fresh reopen compares source V12 vs final: geometry, poses, visibility and slots.
def snapshot():
 for c in bpy.data.collections:c.hide_viewport=False
 for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update();out={}
 for o in bpy.data.objects:
  h=hashlib.sha256()
  if o.type=='MESH':
   for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
   for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
  out[o.name]={'mesh':h.hexdigest(),'matrix':[list(r) for r in o.matrix_world],'render':o.hide_render,'mats':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else []}
 return out
bpy.ops.wm.open_mainfile(filepath=a['source']);before=snapshot();bpy.ops.wm.open_mainfile(filepath=str(O));after=snapshot();assert before.keys()==after.keys();issues=[]
for n,b in before.items():
 c=after[n]
 for key in ['mesh','matrix','render']:
  if b[key]!=c[key]:issues.append((n,key))
 if n not in a['changed_cabinet_objects'] and b['mats']!=c['mats']:issues.append((n,'mats'))
assert not issues,issues
for n in a['changed_cabinet_objects']:
 o=bpy.data.objects[n];assert o.data.materials[0].name==a['finish_material'];assert o.data.uv_layers.get('ProductMeters')
for f in json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files']:assert sha(f['path'])==f['sha256']
v={'status':'PASS_FRESH_OPEN_PRESERVATION','output_sha256':a['sha256'],'original_geometry_transforms_visibility_unchanged':len(before),'changed_wood_panels':a['changed_cabinet_objects'],'matching_material_and_metric_UV':True,'shower_layout_unchanged':True,'shower_audit':a['shower_audit'],'protected_sources':16};(D/'VERIFICATION.json').write_text(json.dumps(v,indent=2)+'\n');print('V13_FINAL_VERIFY',json.dumps(v))

