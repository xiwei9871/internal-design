"""Reuse supplier upholstery components and native PBR shaders in a bounded derivative."""
import bpy,json,math,hashlib,struct,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/asset_model_v3';ASSETS=OUT/'assets'
INPUT=ROOT/'design/appearance_match_v2/LIVING_DINING_APPEARANCE_V2.blend'
assert hashlib.sha256(INPUT.read_bytes()).hexdigest()=='1b16fea0ad5e4079bab73e1fec9dc10a877198ed5dd997860f41a55ef08e441b'
bpy.ops.wm.open_mainfile(filepath=str(INPUT));scene=bpy.context.scene
original=[o for o in scene.objects if o.type=='MESH']
visibility={o.name:(o.hide_render,o.hide_viewport,o.hide_get()) for o in original}
for o in original:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def fingerprint(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 return h.hexdigest(),[float(v) for row in o.matrix_world for v in row]
before={o.name:fingerprint(o) for o in original}
def bounds(o):
 pts=[o.matrix_world@v.co for v in o.data.vertices]
 return [[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]
col=bpy.data.collections.new('V3_LIBRARY_ADAPTED_SELECTED_FURNITURE');scene.collection.children.link(col)
native={}
for id in ['linen','ash']:
 p=ASSETS/f'{id}_native_1k'/('rough_linen_1k.blend' if id=='linen' else 'ash_veneer_1k.blend')
 with bpy.data.libraries.load(str(p),link=False) as (a,b):b.materials=a.materials
 m=b.materials[0];m.name='V3_SUPPLIER_NATIVE_'+id.upper();native[id]=m
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image:
   n.image.filepath=str(p.parent/'textures'/Path(n.image.filepath).name);n.image.reload()
 # Original supplier UV map remains in the unmodified test file.
 ns=m.node_tree.nodes;ls=m.node_tree.links
 uv=ns.new('ShaderNodeUVMap');uv.name='Physical surface coordinates';uv.uv_map='V3_SurfaceMeters'
 mapping=next(n for n in ns if n.type=='MAPPING');ls.new(uv.outputs[0],mapping.inputs['Vector'])
 mapping.inputs['Scale'].default_value=(1/.3,1/.3,1) if id=='linen' else (1,1,1)
 for n in ns:
  if n.type in ['NORMAL_MAP','TANGENT']:n.uv_map='V3_SurfaceMeters'
 if hasattr(m,'displacement_method'):m.displacement_method='BUMP'
wood=native['ash'].copy();wood.name='V3_WHITE_ASH_NATIVE_OWNER_COLOR'
cloth=native['linen'].copy();cloth.name='V3_OATMEAL_LINEN_NATIVE_OWNER_COLOR'
ns=cloth.node_tree.nodes;ls=cloth.node_tree.links;p=next(n for n in ns if n.type=='BSDF_PRINCIPLED')
# One color adaptation only; retain supplier measured roughness, IOR, anisotropy, normal and sheen.
source=p.inputs['Base Color'].links[0].from_socket;bw=ns.new('ShaderNodeRGBToBW');ls.new(source,bw.inputs[0]);normalize=ns.new('ShaderNodeMath');normalize.operation='DIVIDE';normalize.inputs[1].default_value=.41;ls.new(bw.outputs[0],normalize.inputs[0]);tint=ns.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(.48,.418,.334,1);ls.new(normalize.outputs[0],tint.inputs[1]);ls.new(tint.outputs[0],p.inputs['Base Color'])
# Native material upgraded with verified 4K maps, preserving its node wiring.
manifest=json.loads((ASSETS/'linen_4k_complete/complete-material-manifest.json').read_text())
maps={f['map']:f['path'] for f in manifest['files']}
name_map={'diff':'diffuse','rough':'roughness','nor_gl':'normal','disp':'displacement','spec_ior':'spec_ior','anisotropy_rotation':'anisotropy_rotation','anisotropy_strength':'anisotropy_strength'}
for n in cloth.node_tree.nodes:
 if n.type=='TEX_IMAGE' and n.name in name_map:
  n.image=bpy.data.images.load(maps[name_map[n.name]],check_existing=True);n.image.colorspace_settings.name='sRGB' if n.name=='diff' else 'Non-Color'
ashfiles=json.loads((ROOT/'renders/whole_house_final_study_v1/assets/ash/asset-manifest.json').read_text())['files']
for n in wood.node_tree.nodes:
 if n.type=='TEX_IMAGE' and n.image:
  filename=n.image.filepath
  key='diffuse' if '_diff_' in filename else 'roughness' if '_rough_' in filename else 'normal' if '_nor_gl_' in filename else None
  if key:
   f=next(f for f in ashfiles if f['map']==key);n.image=bpy.data.images.load(f['path'],check_existing=True);n.image.colorspace_settings.name='sRGB' if key=='diffuse' else 'Non-Color'
def uvmeters(o):
 me=o.data;uv=me.uv_layers.get('V3_SurfaceMeters') or me.uv_layers.new(name='V3_SurfaceMeters');me.uv_layers.active=uv;uv.active_render=True
 dims=[max(v.co[i] for v in me.vertices)-min(v.co[i] for v in me.vertices) for i in range(3)];long=max(range(3),key=lambda i:dims[i]);offset=(int(hashlib.sha256(o.name.encode()).hexdigest()[:5],16)%73)/11
 for poly in me.polygons:
  normalaxis=max(range(3),key=lambda i:abs(poly.normal[i]));axes=[i for i in range(3) if i!=normalaxis]
  if long in axes:axes=[long]+[i for i in axes if i!=long]
  for li in poly.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]+offset,v[axes[1]]+offset*.27)
def cloth_uv(o):
 """Unwrap existing supplier seams and normalize to physical density after each fit."""
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 uv=o.data.uv_layers.new(name='V3_SurfaceMeters');o.data.uv_layers.active=uv;uv.active_render=True
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004);bpy.ops.object.mode_set(mode='OBJECT')
 o.data.update();uv=o.data.uv_layers.get('V3_SurfaceMeters')
 area_uv=0
 for poly in o.data.polygons:
  coords=[uv.data[li].uv for li in poly.loop_indices]
  area_uv+=abs(sum(coords[j].x*coords[(j+1)%len(coords)].y-coords[(j+1)%len(coords)].x*coords[j].y for j in range(len(coords)))*.5)
 area_mesh=sum(p.area for p in o.data.polygons);scale=math.sqrt(area_mesh/max(area_uv,1e-9))
 for data in uv.data:data.uv*=scale
oexisting={o.name for o in bpy.data.objects}
bpy.ops.wm.obj_import(filepath=str(ASSETS/'fly_sc2/3D_Fly_SC2/3D_Fly_SC2/obj/SC2_medium.obj'))
supplier=next(o for o in bpy.context.scene.objects if o.name not in oexisting and o.type=='MESH')
parts=json.loads((OUT/'SUPPLIER_COMPONENTS.json').read_text())[0]['parts']
def partmesh(index):
 indices=parts[index]['indices'];selected=set(indices);remap={v:i for i,v in enumerate(indices)}
 vertices=[Vector((supplier.data.vertices[i].co.x*.001,supplier.data.vertices[i].co.z*.001,-supplier.data.vertices[i].co.y*.001)) for i in indices]
 faces=[tuple(remap[i] for i in p.vertices) for p in supplier.data.polygons if all(i in selected for i in p.vertices)]
 return vertices,faces
def fitcoordinate(value,low,high,targetlow,targethigh,edge=.07):
 source=high-low;target=targethigh-targetlow
 if target/source>1.25:
  edge=min(edge,source*.25,target*.25)
  if value-low<edge:return targetlow+value-low
  if high-value<edge:return targethigh-(high-value)
  return targetlow+edge+(value-low-edge)/(source-2*edge)*(target-2*edge)
 return targetlow+(value-low)/source*target
adaptations=[]
def adapt(n,index,targetlo,targethi,axes):
 vertices,faces=partmesh(index)
 # Component-wise construction morph. Preserve edge radii when stretching longer seating modules.
 sourcev=[Vector(tuple(v[i] for i in axes)) for v in vertices];lo=[min(v[i] for v in sourcev) for i in range(3)];hi=[max(v[i] for v in sourcev) for i in range(3)]
 center=Vector(tuple((targetlo[i]+targethi[i])/2 for i in range(3)));size=[targethi[i]-targetlo[i] for i in range(3)]
 coords=[tuple(fitcoordinate(v[i],lo[i],hi[i],-size[i]/2,size[i]/2) for i in range(3)) for v in sourcev]
 me=bpy.data.meshes.new(n);me.from_pydata(coords,[],faces);me.update();o=bpy.data.objects.new('V3_'+n,me);col.objects.link(o);o.location=center;me.materials.append(cloth)
 for p in me.polygons:p.use_smooth=True
 cloth_uv(o);o['supplier']='AndTradition Fly SC2 component';o['source_component_index']=index;o['dimension_authority']='original owner envelope'
 adaptations.append({'object':o.name,'source_part_index':index,'source_axes':axes,'source_dimensions_m':[hi[i]-lo[i] for i in range(3)],'target_bounds_m':[list(targetlo),list(targethi)],'target_dimensions_m':size,'stretch_method':'interior panel extension with edge zones retained for large modules'})
 return o
replacement=[]
for name in ['LD_Sofa_upholstery_03','LD_Sofa_upholstery_04','LD_Sofa_upholstery_05','LD_Sofa_upholstery_09','LD_Sofa_upholstery_10','LD_Sofa_upholstery_11','LD_Chaise_seat_pad']:
 old=bpy.data.objects[name];lo,hi=bounds(old);isback=int(name.rsplit('_',1)[-1])>=9 if 'Sofa' in name else False
 o=adapt(name,43 if isback else 41,lo,hi,(1,0,2) if isback else (0,1,2));o.parent=old.parent
 old.hide_render=True;old.hide_viewport=True;old.hide_set(True);replacement.append(name)
 for sibling in list(bpy.data.objects):
  if sibling.name==name+'_piping':sibling.hide_render=True;sibling.hide_viewport=True;sibling.hide_set(True)
old=bpy.data.objects['LD_Chaise_back_pad'];size=[max(v.co[i] for v in old.data.vertices)-min(v.co[i] for v in old.data.vertices) for i in range(3)]
o=adapt('Chaise_back_soft_from_supplier',43,[-v/2 for v in size],[v/2 for v in size],(2,0,1));o.matrix_world=old.matrix_world.copy();o.parent=old.parent
bpy.context.view_layer.update()
wanted=bounds(old);actual=bounds(o);inv=o.matrix_world.inverted()
# Rotation changes the extremal contour; fit only overflowing world components to the old padded envelope.
for axis in range(3):
 if actual[0][axis]<wanted[0][axis] or actual[1][axis]>wanted[1][axis]:
  for vertex in o.data.vertices:
   world=o.matrix_world@vertex.co;world[axis]=wanted[0][axis]+(world[axis]-actual[0][axis])/(actual[1][axis]-actual[0][axis])*(wanted[1][axis]-wanted[0][axis]);vertex.co=inv@world
o.data.update();cloth_uv(o)
old.hide_render=True;old.hide_viewport=True;old.hide_set(True);replacement.append(old.name)
if 'LD_Chaise_back_pad_piping' in bpy.data.objects:bpy.data.objects['LD_Chaise_back_pad_piping'].hide_render=True
supplier.hide_render=True;supplier.hide_viewport=True;supplier.hide_set(True);supplier.name='V3_SUPPLIER_SOURCE_RETAINED'
material_assignments=[]
for o in original:
 if o.hide_render or not o.data.materials:continue
 inliving=o.name.startswith(('LD_Sofa_','LD_Chaise_','LD_Coffee_','LD_Console_','LD_Art_ash_'))
 inkitchen=o.name.startswith('B11_K-')
 if not (inliving or inkitchen):continue
 mats=[]
 for m in o.data.materials:
  if 'ASH' in m.name and not 'FRAME' in m.name:mats.append(wood)
  elif 'LINEN' in m.name and 'CURTAIN' not in m.name:mats.append(cloth)
  elif inkitchen and 'ASH' not in m.name and m.name.startswith('AM2_WHITE_ASH'):mats.append(wood)
  else:mats.append(m)
 if mats!=list(o.data.materials):
  o.data=o.data.copy();o.data.materials.clear()
  for m in mats:o.data.materials.append(m)
  uvmeters(o);material_assignments.append(o.name)
# Kitchen: direct reuse of existing measured-layout cabinetry with native ash, restrained finish details.
def mat(n,c,rough=.4,metal=0):
 m=bpy.data.materials.new('V3_'+n);m.use_nodes=True;m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
nickel=mat('BRUSHED_STAINLESS',(.48,.49,.49),.30,1)
nickel.node_tree.nodes.get('Principled BSDF').inputs['Anisotropic'].default_value=.45
castiron=mat('CAST_IRON',(.02,.021,.022),.62,.35);blackglass=mat('APPLIANCE_BLACK_GLASS',(.014,.016,.017),.19,.1)
stone=mat('QUIET_WARM_QUARTZ_REUSED_FINISH',(.68,.65,.59),.38)
# Existing project stone material is retained as baseline because searched library stones were patterned tiles / weathered, unsuitable.
stone.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.46
nodes=stone.node_tree.nodes;links=stone.node_tree.links;t=nodes.new('ShaderNodeTexCoord');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=110;noise.inputs['Detail'].default_value=2;links.new(t.outputs['Object'],noise.inputs['Vector']);mix=nodes.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.12;mix.inputs[1].default_value=(.64,.60,.54,1);mix.inputs[2].default_value=(.76,.73,.67,1);links.new(noise.outputs['Fac'],mix.inputs[0]);links.new(mix.outputs[0],nodes.get('Principled BSDF').inputs['Base Color'])
for o in original:
 if not o.name.startswith('B11_K-') or o.hide_render:continue
 selected=None
 if any(w in o.name for w in ['COUNTER','WORKTOP']):selected=stone
 elif any(w in o.name for w in ['PULL','HANDLE','SINK_','FRIDGE_DOOR','FRIDGE_BODY','COOK_HOB','COOK_HOOD']):selected=nickel
 elif any(w in o.name for w in ['DISHW_APPLIANCE','DISHW_CONTROL']):selected=blackglass
 if selected:
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(selected);material_assignments.append(o.name)
 if '_FRONT_' in o.name or 'FRIDGE_DOOR' in o.name:
  b=o.modifiers.new('Fine manufactured edge highlight','BEVEL');b.width=.001;b.segments=3
  n=o.modifiers.new('Finish normals','WEIGHTED_NORMAL');n.keep_sharp=True
def box(n,pos,size,material,r=.001):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name='V3_'+n;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(material);b=o.modifiers.new('Edge radius','BEVEL');b.width=r;b.segments=3;return o
def cylinder(n,pos,r,depth,material):
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=depth,location=pos);o=bpy.context.object;o.name='V3_'+n
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 b=o.modifiers.new('Turned edge','BEVEL');b.width=.001;b.segments=3;return o
# Local functional appliance detail from pre-researched FOTILE photographs, footprint and centers preserved.
for i,(x,y) in enumerate([(7.5,2.64),(7.5,3.06)]):
 cylinder('Gas_burner_base_%d'%i,(x,y,.840),.081,.012,castiron)
 cylinder('Gas_burner_cap_%d'%i,(x,y,.855),.047,.014,castiron)
 bpy.ops.mesh.primitive_torus_add(major_segments=72,minor_segments=12,location=(x,y,.847),major_radius=.067,minor_radius=.004)
 o=bpy.context.object;o.name='V3_Gas_burner_ring_%d'%i
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(nickel)
 for j in range(4):
  a=j*math.pi/2;xx=x+.085*math.cos(a);yy=y+.085*math.sin(a);o=box('Pan_support_%d_%d'%(i,j),(xx,yy,.860),(.096,.012,.036),castiron,.002);o.rotation_euler.z=a
 for j in range(36):
  a=j*math.tau/36;cylinder('Burner_port_%d_%d'%(i,j),(x+.062*math.cos(a),y+.062*math.sin(a),.849),.002,.006,castiron)
 for n in ['B11_K-COOK_BURNER' if i==0 else 'B11_K-COOK_BURNER.001']:bpy.data.objects[n].hide_render=True;replacement.append(n)
 cylinder('Rotary_knob_%d'%i,(7.315,y,.845),.020,.026,nickel)
box('Hood_dark_control_strip',(7.421,2.85,1.680),(.005,.42,.035),blackglass,.002)
for y in [2.57,3.13]:
 cylinder('Hood_tasklight',(7.58,y,1.601),.026,.004,stone)
for i in range(18):box('Hood_filter_slot_%02d'%i,(7.60,2.50+i*.04,1.600),(.23,.009,.002),castiron,.0003)
# Under-cabinet tasklight is implemented as real recessed light, no additional cabinet volume.
diffuser=mat('LED_OPAL_DIFFUSER',(.8,.76,.67),.55);led=diffuser.node_tree.nodes.get('Principled BSDF');led.inputs['Emission Color'].default_value=(1,.82,.62,1);led.inputs['Emission Strength'].default_value=.8
box('Under_cabinet_LED_profile',(7.64,1.50,1.741),(.022,1.72,.005),nickel,.001)
box('Under_cabinet_LED_diffuser',(7.64,1.50,1.737),(.014,1.70,.002),diffuser,.0003)
d=bpy.data.lights.new('V3_KITCHEN_UNDERCABINET_3000K','AREA');d.energy=30;d.shape='RECTANGLE';d.size=1.7;d.size_y=.025;d.color=(1,.82,.62);o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=(7.64,1.50,1.735);o.rotation_euler=(0,0,math.pi/2);o.visible_camera=False
d=bpy.data.lights.new('V3_KITCHEN_DAYLIGHT_THROUGH_SOUTH_WINDOW','AREA');d.energy=350;d.shape='DISK';d.size=2;d.color=(.96,.98,1);o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=(6.60,-1.2,1.8);o.rotation_euler=(Vector((6.8,2.5,.7))-o.location).to_track_quat('-Z','Y').to_euler();o.visible_camera=False
PRES=ROOT/'renders/whole_house_final_study_v1/production_batch_v1/WHOLE_HOUSE_PRODUCTION_V1.blend'
with bpy.data.libraries.load(str(PRES),link=False) as (a,b):b.objects=[n for n in a.objects if n.startswith('CAM_kitchen_')]
for o in b.objects:
 if o and not o.users_collection:scene.collection.objects.link(o)
register=json.loads((ROOT/'renders/whole_house_final_study_v1/00_MANIFEST/CAMERA_REGISTER_REVIEW_V3.json').read_text())['cameras']
for c in register:
 if c['room_id']!='kitchen':continue
 o=bpy.data.objects[c['camera_name']];o.location=c['eye'];direction=Vector(c['target'])-o.location
 if c.get('controlled_verticals'):direction.z=0;o.data.shift_y=c['shift_y']
 o.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();o.data.lens=c['lens_mm'];o.data.dof.use_dof=False
scene['asset_method']='Supplier upholstery components + native PolyHaven shader graphs';scene['not_exact_supplier_SKU']='Original design layout retained, component morphs documented';scene['scope']='living+kitchen';scene['kitchen_equipment_detail']='appearance-only mechanism; SKU and fabrication clearance unconfirmed'
scene.render.engine='CYCLES';scene.cycles.samples=128;scene.cycles.use_denoising=True;scene.cycles.denoising_use_gpu=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100;scene.render.threads_mode='FIXED';scene.render.threads=2
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
for d in pref.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU';scene.camera=bpy.data.objects['CAM_living_VIEW_01']
for n,f in before.items():assert fingerprint(bpy.data.objects[n])==f,n
for n,(hide_render,hide_viewport,hide_layer) in visibility.items():
 if n in replacement:continue
 o=bpy.data.objects[n];o.hide_viewport=hide_viewport;o.hide_set(hide_layer)
bpy.ops.file.pack_all();dest=OUT/'LIVING_KITCHEN_LIBRARY_V3.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
report={'status':'BUILT_REQUIRES_VISUAL_REVIEW','source':str(INPUT),'output':str(dest),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'all_existing_meshes_and_matrices_unchanged':len(before),'retained_hidden_objects':replacement,'supplier_component_adaptations':adaptations,'native_shader_sources':{'wood':'Poly Haven ash_veneer .blend','fabric':'Poly Haven rough_linen .blend'},'physical_scan_repeat_per_m':{'fabric':1/.3,'wood':1},'material_reassignment_count':len(material_assignments),'supplier_package_sha256':'420578640e428da6144201e53c9bb1c881dc91722384b5aa88a56d118f329118','kitchen_shape_invariants':'cabinet/layout/window/FFL/installation points kept','kitchen_detail_departures':'burner mechanism extends schematic symbol from844 to878mm; not fabrication authority','missing_supplier_exact_match':'no exact MuJiaMuYi OBJ; supplier cushion components adapted to source design; custom quiet quartz retained because searched library stones unsuitable'}
(OUT/'BUILD_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(OUT/'EXISTING_GEOMETRY_FINGERPRINTS.json').write_text(json.dumps(before))
print('V3_ASSET_MODEL_BUILT',len(adaptations),dest)
