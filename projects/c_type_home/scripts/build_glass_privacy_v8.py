"""Owner-confirmed clear/frosted architectural glass; exclude appliances and lamps."""
import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/glass_privacy_v8';D.mkdir(exist_ok=True)
S=R/'design/pale_ash_review_v7/WHOLE_HOUSE_PALE_ASH_DELIVERY_V7.blend';O=D/'WHOLE_HOUSE_CLEAR_PRIVACY_GLASS_V8.blend'
assert hashlib.sha256(S.read_bytes()).hexdigest()=='e325b355d94a7d6d7cb88ca06e18f0eeeab5a96493a33266cf1e57a73f0cecf5';assert not O.exists()
bpy.ops.wm.open_mainfile(filepath=str(S));scene=bpy.context.scene
hidden={o.name:(o.hide_viewport,o.hide_get()) for o in bpy.data.objects}
for col in bpy.data.collections:col.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def fingerprint(o):
 h=hashlib.sha256()
 if o.type=='MESH':
  for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
  for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return {'type':o.type,'mesh':h.hexdigest(),'matrix':[list(row) for row in o.matrix_world],'hide_render':o.hide_render,'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else []}
baseline={o.name:fingerprint(o) for o in bpy.data.objects}
for n,(hv,hg) in hidden.items():bpy.data.objects[n].hide_viewport=hv;bpy.data.objects[n].hide_set(hg)
def glass(name,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(1,1,1,1);p=m.node_tree.nodes.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(1,1,1,1);p.inputs['Metallic'].default_value=0;p.inputs['Transmission Weight'].default_value=1;p.inputs['Roughness'].default_value=rough;p.inputs['IOR'].default_value=1.45;p.inputs['Alpha'].default_value=1
 m['role']='colorless architectural glazing; no absorption nodes';return m
clear=glass('V8_COLORLESS_CLEAR_ARCHITECTURAL_GLASS',.015)
frost=glass('V8_COLORLESS_PRIVACY_FROSTED_GLASS',.68)
# Exact privacy selections from room records/world bounds; ordinary windows remain clear.
privacy=set(['R3_SHOWER_GLASS_0','R3_SHOWER_GLASS_1','R3_SHOWER_GLASS_2','G_wall_gf_0007','G_wall_gs_0007','G_wall_gf_0033','G_wall_gs_0033','HOUSE_V1_V7_SLIDER_GLASS_PANE','V4_GUEST_B11_G-GB-BALC_HOST_GLASS0','V4_GUEST_B11_G-GB-BALC_HOST_GLASS1']+[f'B11_Rectangle007_GLASS_{i}' for i in range(3)]+[f'B11_Rectangle033_GLASS_{i}' for i in range(3)])
old_glass={'RENDER_CLEAR_GLASS','V4_CLEAN_ARCHITECTURAL_GLASS','V7_SLIDING_CLEAR_GLASS','HOUSE_V2_SECONDARY_FROSTED_GLASS'}
changes=[]
for o in scene.objects:
 if o.type!='MESH' or o.hide_render:continue
 for slot in o.material_slots:
  if slot.material and slot.material.name in old_glass:
   old=slot.material.name;slot.material=frost if o.name in privacy else clear
   changes.append({'object':o.name,'before':old,'after':slot.material.name,'privacy':o.name in privacy})
assert privacy=={c['object'] for c in changes if c['privacy']},privacy-{c['object'] for c in changes}
wood_doors=['V4_D-BATHM_LEAF_0','V4_D-GUEST-BATH_LEAF_0']
for n in wood_doors:assert bpy.data.objects[n].data.materials[0].name=='V7_CATALOG_PALE_NATURAL_ASH'
scene['V8_GLASS_RULE']='Clear colorless nonprivate glazing; frosted shower partitions, secondary bathroom slider, guest-bedroom to north-balcony double slider. Master/guest bathroom entry doors remain timber. Appliance hatch/lamp glass unchanged.'
# Preserve the default open-ceiling viewport mode.
for n in ['V7_CEILING_LOW','V7_CEILING_HIGH','V7_CEILING_450MM_TRANSITION']:
 bpy.data.objects[n].hide_set(True,view_layer=scene.view_layers['OVERVIEW_CEILING_HIDDEN'])
bpy.context.window.view_layer=scene.view_layers['OVERVIEW_CEILING_HIDDEN']
bpy.ops.wm.save_as_mainfile(filepath=str(O))
a={'source':str(S),'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'output':str(O),'sha256':hashlib.sha256(O.read_bytes()).hexdigest(),'baseline':baseline,'changes':changes,'privacy_objects':sorted(privacy),'clear_objects':sorted({c['object'] for c in changes if not c['privacy']}),'bathroom_timber_doors':wood_doors,'material_parameters':{'base_color':[1,1,1,1],'metallic':0,'transmission':1,'ior':1.45,'clear_roughness':.015,'frosted_roughness':.68,'no_volume_absorption':True},'user_correction':'Guest-bedroom double slider to north-balcony, NOT a nonexistent guest-bathroom exit','privacy_note':'Frosted surface scatters light; no unconditional privacy guarantee for skin/objects very close to pane or nighttime backlighting. Supplier sample check needed.','image2_requests':0,'status':'BUILT_PENDING_VISUAL_REVIEW'}
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');print('GLASS_V8',a['sha256'],'clear',len(a['clear_objects']),'frost',len(a['privacy_objects']))
