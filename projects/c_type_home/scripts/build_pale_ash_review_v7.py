"""Owner-requested pale ash, correct door substances and reviewable ceilings."""
import bpy,json,hashlib,struct,sys,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/pale_ash_review_v7';D.mkdir(exist_ok=True)
S=R/'design/console1310_v5/WHOLE_HOUSE_CONSOLE1310_REAL_V5.blend';O=D/'WHOLE_HOUSE_PALE_ASH_REVIEW_V7.blend'
source_sha=hashlib.sha256(S.read_bytes()).hexdigest()
assert source_sha=='3d75cbabe06a0bbace8fb95fb395bcc7f645ed5d26d6fed2d1fb094f0881f63a'
assert not O.exists(),'Preserve previous candidates'
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
def meshhash(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
 for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
# Evaluate uniformly before comparing parented matrices.
hidden={o.name:(o.hide_viewport,o.hide_get()) for o in bpy.data.objects}
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
before={o.name:{'mesh':meshhash(o) if o.type=='MESH' else None,'matrix':[list(v) for v in o.matrix_world],'hide_render':o.hide_render,'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else []} for o in bpy.data.objects}
for n,(hv,hg) in hidden.items():bpy.data.objects[n].hide_viewport=hv;bpy.data.objects[n].hide_set(hg)
sys.path.insert(0,str(R/'scripts'));from whole_house_finish_parts_v1 import Parts
wood=bpy.data.materials['V5_NATURAL_ASH_PLANKS_OIL'].copy();wood.name='V7_CATALOG_PALE_NATURAL_ASH'
nodes=wood.node_tree.nodes;links=wood.node_tree.links;p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
source=next(iter(p.inputs['Base Color'].links)).from_socket
hs=nodes.new('ShaderNodeHueSaturation');hs.name='Catalog ash lightness correction';hs.inputs['Saturation'].default_value=.78;hs.inputs['Value'].default_value=1.50
links.new(source,hs.inputs['Color']);links.new(hs.outputs['Color'],p.inputs['Base Color'])
wood.diffuse_color=(.465,.327,.198,1)
rough_src=next(iter(p.inputs['Roughness'].links)).from_socket
remap=nodes.new('ShaderNodeMapRange');remap.name='Matte oil finish roughness range';remap.inputs['From Min'].default_value=0;remap.inputs['From Max'].default_value=1;remap.inputs['To Min'].default_value=.36;remap.inputs['To Max'].default_value=.58
links.new(rough_src,remap.inputs['Value']);links.new(remap.outputs[0],p.inputs['Roughness'])
wood['reference']='Owner Desktop ash catalog p17; project-tested TextureCan ash atlas CC0, color correction retained grain and complete roughness/normal/height'
linen=bpy.data.materials['V5_NATURAL_FLAX_COTTON'].copy();linen.name='V7_IVORY_FLAX_NATIVE'
lp=next(n for n in linen.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
for sock,val in [('Metallic',0),('Sheen Weight',.28),('Subsurface Weight',0)]:
 for l in list(lp.inputs[sock].links):linen.node_tree.links.remove(l)
 lp.inputs[sock].default_value=val
for n in linen.node_tree.nodes:
 if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY':n.inputs[2].default_value=(.54,.48,.385,1)
linen.diffuse_color=(.54,.48,.385,1)
P=Parts(s.collection,wood,linen)
wood_family={'V5_NATURAL_ASH_PLANKS_OIL','V3_WHITE_ASH_NATIVE_OWNER_COLOR','V4_ASH_WAX_OIL_FROM_REAL_CATALOG','AM2_WHITE_ASH_HONEY_MATTE','R3_STUDY_WOOD','BW1_PALE_ASH','BALCONY_PALE_ASH','LD_PALE_ASH_SATIN','DOOR_V2_REVIEW_TIMBER_FRAME','R4_WAVE_STEP_PALE_WOOD'}
assignments=[]
for o in s.objects:
 if o.type!='MESH' or o.hide_render:continue
 changed=False
 for slot in o.material_slots:
  if slot.material and slot.material.name in wood_family:slot.material=wood;changed=True
  elif slot.material and slot.material.name in {'V5_NATURAL_FLAX_COTTON','AM2_SOFA_OATMEAL_LINEN','V3_OATMEAL_LINEN_NATIVE_OWNER_COLOR'}:slot.material=linen;changed=True
 if changed:
  if not o.data.uv_layers.get('ProductMeters'):
   o.data=o.data.copy();original=o.data.uv_layers.active_index;P.uv(o)
   if len(o.data.uv_layers)>1:o.data.uv_layers.active_index=original
  assignments.append(o.name)
# Whole generated bed: real wooden frame is below mattress; reject UV color classification.
bed=bpy.data.objects['HUNYUAN_V3_COUPLE_BED'];bed.data=bed.data.copy()
bed.data.materials.append(wood);woodslot=len(bed.data.materials)-1;bedwood=0
for f in bed.data.polygons:
 if max(bed.data.vertices[i].co.z for i in f.vertices)<.785:f.material_index=woodslot;bedwood+=1
native=bed.data.materials[0].copy();native.name='V7_BED_RETAINED_BEDDING_TEXTURE';bed.data.materials[0]=native
bp=next(n for n in native.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bp.inputs['Roughness'].default_value=.82;bp.inputs['Sheen Weight'].default_value=.24
# ProductMeters coexists with source GLB UV. Source texture still explicitly uses original UV.
orig=bed.data.uv_layers.active_index;P.uv(bed);bed.data.uv_layers.active_index=orig
for layer in bed.data.uv_layers:layer.active_render=False
bed.data.uv_layers[orig].active_render=True
console=bpy.data.objects['HUNYUAN_V3_COUPLE_TV_CONSOLE'];console.data=console.data.copy();console.data.materials.append(wood);ci=len(console.data.materials)-1
ca=json.loads((R/'design/console1310_v5/AUDIT.json').read_text());body=set(ca['body_vertex_indices']);consolewood=0
for f in console.data.polygons:
 if all(i in body for i in f.vertices):f.material_index=ci;consolewood+=1
orig=console.data.uv_layers.active_index;P.uv(console);console.data.uv_layers.active_index=orig
for layer in console.data.uv_layers:layer.active_render=False
console.data.uv_layers[orig].active_render=True
def material(name,color,roughness,metallic=0,transmission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
 n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=roughness;n.inputs['Metallic'].default_value=metallic;n.inputs['Transmission Weight'].default_value=transmission;n.inputs['IOR'].default_value=1.45
 return m
metal=material('V7_ENTRY_SATIN_METAL',(.18,.20,.22),.34,1)
glass=material('V7_SLIDING_CLEAR_GLASS',(.97,.98,.99),.035,0,1)
door_changes=[]
for name in ['V4_ENT-1_LEAF_0','V4_ENT-1_LEAF_1']:
 o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(metal);door_changes.append((name,metal.name))
o=bpy.data.objects['R3_SLIDING_LEAF'];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(glass);door_changes.append((o.name,glass.name))
# Replace coarse overlapping ceiling pieces with triangulated planar unions.
ceiling_col=bpy.data.collections.new('V7_CEILING_TOGGLE_FOR_OVERVIEW');s.collection.children.link(ceiling_col)
ceiling_mat=bpy.data.materials['AM2_WARM_WHITE_CEILING'];plan=json.loads((D/'CEILING_PLANAR_REPAIR.json').read_text())
old_ceiling=[o.name for o in s.objects if o.name.startswith('CEILING_')]
for n in old_ceiling:
 o=bpy.data.objects[n];o.hide_render=True;o.hide_viewport=True;o.hide_set(True)
created=[]
for key,group in plan['groups'].items():
 vertices=[];faces=[];index={}
 def vertex(x,y,z):
  co=(round(x,5),round(y,5),round(z,5))
  if co not in index:index[co]=len(vertices);vertices.append(co)
  return index[co]
 z=group['z'];top=z+group['thickness']
 for tri in group['triangles_xy']:
  ids=[vertex(x,y,z) for x,y in tri];faces.append(tuple(ids[::-1]))
  faces.append(tuple(vertex(x,y,top) for x,y in tri))
 for rings in group['rings_xy']:
  for ring in rings:
   for a,b in zip(ring,ring[1:]):faces.append((vertex(*a,z),vertex(*b,z),vertex(*b,top),vertex(*a,top)))
 me=bpy.data.meshes.new('V7_'+key+'_CEILING_MESH');me.from_pydata(vertices,[],faces);me.update();o=bpy.data.objects.new('V7_CEILING_'+key.upper(),me);ceiling_col.objects.link(o);me.materials.append(ceiling_mat);created.append(o.name)
# Vertical face at true 450mm ceiling transition, not a roof ridge.
vertices=[];faces=[]
for line in plan['shared_boundary_lines']:
 for a,b in zip(line,line[1:]):
  start=len(vertices);vertices.extend([(a[0],a[1],2.8),(b[0],b[1],2.8),(b[0],b[1],3.25),(a[0],a[1],3.25)]);faces.append(tuple(range(start,start+4)))
me=bpy.data.meshes.new('V7_450MM_CEILING_TRANSITION');me.from_pydata(vertices,[],faces);me.update();o=bpy.data.objects.new('V7_CEILING_450MM_TRANSITION',me);ceiling_col.objects.link(o);me.materials.append(ceiling_mat);created.append(o.name)
# Two named view layers: viewport-only ceiling hide keeps interior render occlusion.
interior=bpy.context.view_layer;interior.name='INTERIOR_CLOSED_CEILING'
overview=s.view_layers.new('OVERVIEW_CEILING_HIDDEN')
def copy_layer(src,dst):
 dst.exclude=src.exclude;dst.hide_viewport=src.hide_viewport
 srcs={c.name:c for c in src.children}
 for c in dst.children:
  if c.name in srcs:copy_layer(srcs[c.name],c)
copy_layer(interior.layer_collection,overview.layer_collection)
for n in created:bpy.data.objects[n].hide_set(True,view_layer=overview)
s.render.engine='CYCLES';s.cycles.samples=256;s.cycles.adaptive_threshold=.01;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE';s.cycles.preview_samples=128;s.cycles.use_preview_denoising=True
s.render.resolution_x=2560;s.render.resolution_y=1440;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
for dev in pref.devices:dev.use=dev.type=='METAL'
s.cycles.device='GPU'
if bpy.context.window:bpy.context.window.view_layer=overview
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;sp.shading.type='MATERIAL';sp.shading.use_scene_world=False;sp.shading.use_scene_lights=False;sp.shading.studiolight_rotate_z=.4
   sp.region_3d.view_location=(8.5,6.3,.7);sp.region_3d.view_distance=19;sp.region_3d.view_perspective='PERSP'
   from mathutils import Quaternion
   sp.region_3d.view_rotation=Vector((-.7,-1,1.2)).to_track_quat('Z','Y')
s['V7_REVIEW_HELP']='Default OVERVIEW layer hides ceiling in viewport; select INTERIOR_CLOSED_CEILING for room lighting. F12 uses closed ceiling. Material Preview is studio-lit; inspect actual Cycles renders for acceptance.'
s['V7_OWNER_REQUIREMENTS']='Pale natural ash catalog; entrance metal, interior swing leaves timber, sliding leaves glass; 450mm ceiling height difference retained.'
bpy.ops.wm.save_as_mainfile(filepath=str(O))
a={'source':str(S),'source_sha256':source_sha,'output':str(O),'sha256':hashlib.sha256(O.read_bytes()).hexdigest(),'before':before,'wood_family_reassigned':assignments,'bed_frame_wood_triangles':bedwood,'console_body_wood_triangles':consolewood,'door_changes':door_changes,'old_ceiling_hidden':old_ceiling,'new_ceiling_objects':created,'ceiling_gap_repair':{k:{n:g[n] for n in ['z','before_area','after_area','added_area_m2','removed_overlap_area_m2']} for k,g in plan['groups'].items()},'ceiling_height_difference_mm':450,'geometry_policy':'All original meshes/matrices preserved, including hidden old ceiling; only material slots/UVs and documented ceiling visibility change.','references':['/Users/xiwei/Desktop/木甲木乙-白蜡木系列.pdf p17','design_selections/review/LIVING_SELECTION_REFERENCES.jpg','lookdev_v5/assets/ash_furniture_atlas/manifest.json'],'no_image2':True,'status':'BUILT_PENDING_VISUAL_REVIEW'}
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');print('V7_BUILT',a['sha256'],len(assignments),bedwood,consolewood,a['door_changes'])
