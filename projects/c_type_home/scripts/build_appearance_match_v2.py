"""Material fidelity repair over preserved V1; geometry and architecture immutable."""
import bpy, json, hashlib, math, struct, time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design/appearance_match_v2';OUT.mkdir(exist_ok=True)
INPUT=ROOT/'design/living_dining_detail_v1/LIVING_DINING_DETAIL_V1.blend'
INPUT_HASH='8fec1e2169f715c5901f3abacd6885834c6c5b7a4e3baa66bd4baae4417892ab'
assert hashlib.sha256(INPUT.read_bytes()).hexdigest()==INPUT_HASH
bpy.ops.wm.open_mainfile(filepath=str(INPUT));scene=bpy.context.scene
source_objects=[o for o in scene.objects if o.type=='MESH']
viewport_hidden={o.name:(o.hide_viewport,o.hide_get()) for o in source_objects}
for o in source_objects:
 o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def geom(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 return h.hexdigest(),[float(x) for row in o.matrix_world for x in row]
before={o.name:geom(o) for o in source_objects}
hidden={o.name:o.hide_render for o in source_objects}
assets=ROOT/'renders/whole_house_final_study_v1/assets'
def material(name,color,roughness):
 m=bpy.data.materials.new('AM2_'+name);m.use_nodes=True;m.diffuse_color=(*color,1)
 n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');m.node_tree.links.new(p.outputs[0],out.inputs['Surface']);p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=roughness;return m,p
def image_nodes(m,folder,repeat,uv='AM2_SurfaceMeters'):
 ns=m.node_tree.nodes;ls=m.node_tree.links;c=ns.new('ShaderNodeUVMap');c.uv_map=uv
 mult=ns.new('ShaderNodeVectorMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=(repeat,repeat,1);ls.new(c.outputs[0],mult.inputs[0])
 result={}
 for f in json.loads((assets/folder/'asset-manifest.json').read_text())['files']:
  t=ns.new('ShaderNodeTexImage');t.image=bpy.data.images.load(f['path'],check_existing=True);t.image.colorspace_settings.name='sRGB' if f['map']=='diffuse' else 'Non-Color';ls.new(mult.outputs[0],t.inputs['Vector']);result[f['map']]=t
 return result,c
wood,p=material('WHITE_ASH_HONEY_MATTE',(.38,.285,.16),.4)
ns=wood.node_tree.nodes;ls=wood.node_tree.links;tex,coords=image_nodes(wood,'ash',1)
mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(1.10,1.00,.86,1);ls.new(tex['diffuse'].outputs['Color'],mix.inputs[1]);ls.new(mix.outputs[0],p.inputs['Base Color'])
r=ns.new('ShaderNodeMapRange');r.inputs['To Min'].default_value=.31;r.inputs['To Max'].default_value=.53;ls.new(tex['roughness'].outputs[0],r.inputs['Value']);ls.new(r.outputs[0],p.inputs['Roughness'])
normal=ns.new('ShaderNodeNormalMap');normal.uv_map='AM2_SurfaceMeters';normal.inputs['Strength'].default_value=.3;ls.new(tex['normal'].outputs[0],normal.inputs['Color']);ls.new(normal.outputs[0],p.inputs['Normal'])
p.inputs['Coat Weight'].default_value=.055;p.inputs['Coat Roughness'].default_value=.36
def textile(name,color,repeat,translucency=0):
 m,p=material(name,color,.9);ns=m.node_tree.nodes;ls=m.node_tree.links;tex,coord=image_nodes(m,'linen',repeat)
 bw=ns.new('ShaderNodeRGBToBW');ls.new(tex['diffuse'].outputs[0],bw.inputs[0])
 field=ns.new('ShaderNodeMapRange');field.clamp=True;field.inputs['From Min'].default_value=.24;field.inputs['From Max'].default_value=.56;field.inputs['To Min'].default_value=.68;field.inputs['To Max'].default_value=1.18;ls.new(bw.outputs[0],field.inputs['Value'])
 tint=ns.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(*color,1);ls.new(field.outputs[0],tint.inputs[1]);ls.new(tint.outputs[0],p.inputs['Base Color'])
 p.inputs['Specular IOR Level'].default_value=.23;p.inputs['Sheen Weight'].default_value=.3;p.inputs['Sheen Roughness'].default_value=.75
 normal=ns.new('ShaderNodeNormalMap');normal.uv_map='AM2_SurfaceMeters';normal.inputs['Strength'].default_value=.8;ls.new(tex['normal'].outputs[0],normal.inputs['Color'])
 bump=ns.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.00035;bump.inputs['Strength'].default_value=.32;ls.new(bw.outputs[0],bump.inputs['Height']);ls.new(bump.outputs[0],p.inputs['Normal'])
 if translucency:
  output=next(n for n in ns if n.type=='OUTPUT_MATERIAL');trans=ns.new('ShaderNodeBsdfTranslucent');ls.new(tint.outputs[0],trans.inputs['Color']);mix=ns.new('ShaderNodeMixShader');mix.inputs[0].default_value=translucency;ls.new(p.outputs[0],mix.inputs[1]);ls.new(trans.outputs[0],mix.inputs[2]);ls.new(mix.outputs[0],output.inputs['Surface'])
 return m
cloth=textile('SOFA_OATMEAL_LINEN',(.48,.418,.334),1.8)
curtain=textile('CURTAIN_LIGHT_FLAX',(.61,.554,.46),3.8,.18)
seam,_=material('LINEN_SEAM',(.35,.30,.24),.92)
wall,p=material('WARM_IVORY_WALL',(.70,.656,.584),.86)
ns=wall.node_tree.nodes;ls=wall.node_tree.links;c=ns.new('ShaderNodeTexCoord');noise=ns.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=150;noise.inputs['Detail'].default_value=2;ls.new(c.outputs['Object'],noise.inputs['Vector']);b=ns.new('ShaderNodeBump');b.inputs['Distance'].default_value=.00015;b.inputs['Strength'].default_value=.13;ls.new(noise.outputs['Fac'],b.inputs['Height']);ls.new(b.outputs[0],p.inputs['Normal'])
ceiling,_=material('WARM_WHITE_CEILING',(.82,.805,.758),.9)
dark,p=material('CHARCOAL_BRONZE_WINDOW',(.064,.059,.049),.32);p.inputs['Metallic'].default_value=.72
floor=wood.copy();floor.name='AM2_WOOD_FLOOR_BOARDS'
ns=floor.node_tree.nodes;ls=floor.node_tree.links;p=next(n for n in ns if n.type=='BSDF_PRINCIPLED')
brick=ns.new('ShaderNodeTexBrick');c=ns.new('ShaderNodeUVMap');c.uv_map='AM2_SurfaceMeters';ls.new(c.outputs[0],brick.inputs['Vector'])
brick.inputs['Scale'].default_value=1;brick.inputs['Brick Width'].default_value=1.20;brick.inputs['Row Height'].default_value=.18;brick.inputs['Mortar Size'].default_value=.001;brick.inputs['Mortar Smooth'].default_value=.0003;brick.inputs['Color1'].default_value=(1,1,1,1);brick.inputs['Color2'].default_value=(.87,.87,.87,1);brick.inputs['Mortar'].default_value=(.37,.37,.37,1)
base=p.inputs['Base Color'].links[0].from_socket;mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;ls.new(base,mix.inputs[1]);ls.new(brick.outputs['Color'],mix.inputs[2]);ls.new(mix.outputs[0],p.inputs['Base Color'])
b=ns.new('ShaderNodeBump');b.inputs['Distance'].default_value=.0012;b.inputs['Strength'].default_value=.25;ls.new(p.inputs['Normal'].links[0].from_socket,b.inputs['Normal']);ls.new(brick.outputs['Fac'],b.inputs['Height']);ls.new(b.outputs[0],p.inputs['Normal'])
def uv_surface(o):
 """Grain follows each board/rail long axis; cloth panels use continuous dominant plane."""
 me=o.data;layer=me.uv_layers.get('AM2_SurfaceMeters') or me.uv_layers.new(name='AM2_SurfaceMeters')
 layer.active_render=True;me.uv_layers.active=layer
 dims=[max(v.co[i] for v in me.vertices)-min(v.co[i] for v in me.vertices) for i in range(3)]
 grain=max(range(3),key=lambda i:dims[i]);offset=(int(hashlib.sha256(o.name.encode()).hexdigest()[:6],16)%1000)/173
 # Side panels need their own projection; flattening all panels on the top plane causes bands.
 for poly in me.polygons:
  axis=max(range(3),key=lambda i:abs(poly.normal[i]));axes=[i for i in range(3) if i!=axis]
  if grain in axes:axes=[grain]+[i for i in axes if i!=grain]
  for li in poly.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co
   layer.data[li].uv=(v[axes[0]]+offset,v[axes[1]]+offset*.31)
changed=[]
soft_refinements=[]
for o in source_objects:
 if o.hide_render:continue
 mats=[m for m in o.data.materials]
 replace=[]
 for m in mats:
  if m.name=='LD_PALE_ASH_SATIN':replace.append(wood)
  elif m.name=='LD_OATMEAL_WOVEN':replace.append(cloth)
  elif m.name=='LD_LIGHT_FLAX_CURTAIN':replace.append(curtain)
  elif m.name=='LD_SEAM_LINEN':replace.append(seam)
  elif m.name=='RENDER_WARM_OFF_WHITE':replace.append(ceiling if o.name.startswith('CEILING') else wall)
  else:replace.append(m)
 if o.name=='FLOOR_LOWER':replace=[floor]
 if o.name.startswith('LIVING_FIX_BAY_') and any(s in o.name for s in ['JAMB','RAIL','MULLION']):replace=[dark]
 if o.name.startswith('DOOR_V2_NBALC_') and not any(s in o.name for s in ['GLASS','HINGE','HANDLE','TRIM','THRESHOLD']):replace=[dark]
 if replace!=mats:
  o.data=o.data.copy();o.data.materials.clear()
  for m in replace:o.data.materials.append(m)
  for poly in o.data.polygons:poly.material_index=min(poly.material_index,len(replace)-1)
  uv_surface(o);changed.append(o.name)
# Cushion cloth has support compression and localized seam tucks, retaining exact envelope.
for o in source_objects:
 if not (o.name.startswith('LD_Sofa_upholstery_') or o.name=='LD_Chaise_seat_pad'):continue
 lo=[min(v.co[i] for v in o.data.vertices) for i in range(3)];hi=[max(v.co[i] for v in o.data.vertices) for i in range(3)]
 size=[hi[i]-lo[i] for i in range(3)];mid=[(hi[i]+lo[i])/2 for i in range(3)]
 primary=0 if 'upholstery_09' in o.name or 'upholstery_10' in o.name or 'upholstery_11' in o.name else 2
 planar=[i for i in range(3) if i!=primary]
 bpy.context.view_layer.objects.active=o;sub=o.modifiers.new('Fabric fold sampling','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=2;bpy.ops.object.modifier_apply(modifier=sub.name)
 phase=(int(hashlib.sha256(o.name.encode()).hexdigest()[:4],16)%11)/11
 for v in o.data.vertices:
  p=(v.co[primary]-mid[primary])/(size[primary]*.5)
  if p<.35:continue
  u=(v.co[planar[0]]-mid[planar[0]])/(size[planar[0]]*.5);w=(v.co[planar[1]]-mid[planar[1]])/(size[planar[1]]*.5)
  weight=max(0,min(1,(p-.35)/.6));crown=.010*(max(0,1-u*u)**1.7)*(max(0,1-w*w)**1.7)
  folds=0
  for edge,along,side in [(.89,.35+phase*.1,1),(-.90,-.42+phase*.12,-1),(.84,-.65+phase*.08,1)]:
   # Individual tapered compression creases at the sewn edges, no periodic broad ripples.
   d=(u-edge)/.13;alongdist=(w-along-side*(u-edge)*.8)/.065
   folds+=.0035*(1-2*alongdist*alongdist)*math.exp(-d*d-alongdist*alongdist)
  v.co[primary]+=weight*(crown+folds)
 for i in range(3):
  mn=min(v.co[i] for v in o.data.vertices);mx=max(v.co[i] for v in o.data.vertices)
  for v in o.data.vertices:v.co[i]=lo[i]+(v.co[i]-mn)/(mx-mn)*size[i]
 o.data.update();uv_surface(o);soft_refinements.append(o.name)
# Curves have no UV layer; tailored seam uses its own constant fabric material.
for o in scene.objects:
 if o.type=='CURVE' and o.name.startswith('LD_') and 'piping' in o.name:o.data.materials.clear();o.data.materials.append(seam)
data=bpy.data.cameras.new('AM2_CAM_SOFA_MATERIAL');camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera);camera.location=(4.95,9.38,.82);camera.rotation_euler=(Vector((4.06,9.64,.35))-camera.location).to_track_quat('-Z','Y').to_euler();data.lens=55;data.sensor_width=36;data.clip_start=.025
scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.denoiser='OPENIMAGEDENOISE';scene.cycles.denoising_use_gpu=True;scene.cycles.denoising_quality='HIGH'
scene.render.engine='CYCLES';scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=60
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='METAL'
scene.cycles.device='GPU'
def render(n,stage,suffix=''):
 dest=OUT/stage;dest.mkdir(exist_ok=True);scene.camera=bpy.data.objects[n];p=dest/(n+suffix+'.png');scene.render.filepath=str(p);t=time.time();bpy.ops.render.render(write_still=True);return {'camera':n,'path':str(p),'seconds':round(time.time()-t,2)}
# Material-only test retains inherited V1 light to separate color correction from illumination.
test1=[render('CAM_living_VIEW_01','material_test'),render('LD_CAM_living_DETAIL','material_test')]
# Lower morning sun is geometrically verified through existing north window, no wall hiding.
for o in scene.objects:
 if o.type=='LIGHT':
  if o.name.startswith('LIGHT_'):o.data.energy*=.30;o.data.color=(1,.94,.85)
  elif o.name.startswith('DAYLIGHT_'):o.data.energy*=.72;o.data.color=(.94,.97,1)
sun=bpy.data.objects['LD_Sun_through_actual_windows'];sun.data.energy=2.5;sun.data.angle=math.radians(1.1);sun.data.color=(1,.93,.82);sun.rotation_euler=Vector((-.26,-1,-.33)).to_track_quat('-Z','Y').to_euler()
# Thin architectural glass: preserve camera Fresnel, allow direct solar shadow throughput.
glass_materials={m for o in source_objects if not o.hide_render for m in o.data.materials if m and m.use_nodes and 'CLEAR_GLASS' in m.name}
for m in glass_materials:
 ns=m.node_tree.nodes;ls=m.node_tree.links;out=next(n for n in ns if n.type=='OUTPUT_MATERIAL');old=out.inputs['Surface'].links[0].from_socket
 ray=ns.new('ShaderNodeLightPath');trans=ns.new('ShaderNodeBsdfTransparent');trans.inputs[0].default_value=(.94,.94,.94,1)
 mix=ns.new('ShaderNodeMixShader');ls.new(ray.outputs['Is Shadow Ray'],mix.inputs[0]);ls.new(old,mix.inputs[1]);ls.new(trans.outputs[0],mix.inputs[2]);ls.new(mix.outputs[0],out.inputs['Surface'])
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.15
scene['appearance_authority']='OWNER_1_TO_1_COLOR_MATERIAL_MATCH';scene['V1_visual_status']='REJECTED_BY_OWNER';scene['source_candidate_sha256']=INPUT_HASH
test2=[render('CAM_living_VIEW_01','light_test'),render('AM2_CAM_SOFA_MATERIAL','light_test'),render('LD_CAM_dining_DETAIL','light_test')]
for n,f in before.items():
 if n not in soft_refinements:assert geom(bpy.data.objects[n])==f,n
for n,state in hidden.items():assert bpy.data.objects[n].hide_render==state,n
assert hashlib.sha256(INPUT.read_bytes()).hexdigest()==INPUT_HASH
scene.render.resolution_percentage=100;scene.cycles.samples=128;scene.camera=bpy.data.objects['CAM_living_VIEW_01']
for n,(hidden_global,hidden_layer) in viewport_hidden.items():
 o=bpy.data.objects[n];o.hide_viewport=hidden_global;o.hide_set(hidden_layer)
# Default saved view uses material preview; user may switch to rendered camera view.
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='MATERIAL'
   area.spaces.active.shading.use_scene_world=True
   area.spaces.active.shading.use_scene_lights=True
bpy.ops.file.pack_all();destination=OUT/'LIVING_DINING_APPEARANCE_V2.blend';bpy.ops.wm.save_as_mainfile(filepath=str(destination))
manifest={'source':str(INPUT),'source_sha256':INPUT_HASH,'output':str(destination),'output_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'unchanged_meshes_and_world_matrices':len(before)-len(soft_refinements),'soft_refinements_with_locked_bounds':soft_refinements,'material_assignments_repaired':changed,'render_visibility_unchanged':True,'material_test':test1,'light_test':test2,'visual_acceptance':'PENDING_REFERENCE_COMPARISON','sun_ray_toward': [.26,1,.33],'texture_sources':['https://polyhaven.com/a/ash_veneer','https://polyhaven.com/a/rough_linen'],'color_management':{'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure}}
(OUT/'BUILD_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(OUT/'PRESERVED_MESHES.json').write_text(json.dumps(before))
print('APPEARANCE_V2_BUILT',len(changed),destination)
