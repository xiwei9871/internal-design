"""Reproducible PRESENTATION successor over the user-designated immutable house."""
import bpy,json,hashlib,math,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/whole_house_final_study_v1';M=OUT/'00_MANIFEST'
plan=json.loads((M/'WHOLE_HOUSE_ROOM_MANIFEST_V1.json').read_text());SOURCE=Path(plan['source'])
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==plan['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update()
registry=json.loads((ROOT/'design/console_bath_mirrors_review/spatial-canvas.bindings.full.json').read_text())
allowed={b['native_id'] for b in registry['bindings']};sourcefingerprints={}
def geomhash(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
 for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest(),list(float(v) for row in o.matrix_world for v in row)
for n in allowed:sourcefingerprints[n]=geomhash(bpy.data.objects[n])
for c in bpy.data.collections:
 if 'CEILING' in c.name:c.hide_render=False;c.hide_viewport=False
col=bpy.data.collections.new('COL_PRESENTATION_WHOLE_HOUSE_RENDER');bpy.context.scene.collection.children.link(col)
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  visible=o.name in allowed or o.name.startswith('CEILING_')
  o.hide_render=not visible;o.hide_viewport=not visible;o.hide_set(not visible)
  if o.name in ['NORTH_WINDOW_FITNESS_RESERVE_NOT_EQUIPMENT','PLATE_AC_ZONE','PLATE_GAP20_TO_VERIFY','STUDY_V1_CONTEXT_FLOOR']:o.hide_render=True
 elif o.type=='LIGHT':o.hide_render=True
# Owner2026-10-07explicitlyapprovedrender-layeronlyhideofduplicatedlegacywindowwall.
bpy.data.objects['VIEW_WALL_W_wall_md_0036'].hide_render=True
def material(n,c,rough=.65,metal=0):
 m=bpy.data.materials.new('RENDER_'+n);m.use_nodes=True;m.diffuse_color=(*c,1)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
def scanned(n,c,folder,scale):
 m=material(n,c);ns=m.node_tree.nodes;ls=m.node_tree.links;p=ns.get('Principled BSDF')
 manifest=json.loads((OUT/'assets'/folder/'asset-manifest.json').read_text());coord=ns.new('ShaderNodeTexCoord');mapping=ns.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(scale,scale,scale);ls.new(coord.outputs['UV'],mapping.inputs[0])
 for f in manifest['files']:
  t=ns.new('ShaderNodeTexImage');t.image=bpy.data.images.load(f['path'],check_existing=True);t.image.colorspace_settings.name='sRGB' if f['map']=='diffuse' else 'Non-Color';ls.new(mapping.outputs[0],t.inputs['Vector'])
  if f['map']=='diffuse':
   mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.50;mix.inputs[2].default_value=(*c,1);ls.new(t.outputs['Color'],mix.inputs[1]);ls.new(mix.outputs[0],p.inputs['Base Color'])
  elif f['map']=='roughness':ls.new(t.outputs['Color'],p.inputs['Roughness'])
  elif f['map']=='normal':
   nn=ns.new('ShaderNodeNormalMap');nn.inputs['Strength'].default_value=.12 if folder=='ash' else .25;ls.new(t.outputs['Color'],nn.inputs['Color']);ls.new(nn.outputs['Normal'],p.inputs['Normal'])
 return m
wood=scanned('WHITE_ASH',(.63,.57,.47),'ash',1.3);fabric=scanned('IVORY_LINEN',(.75,.70,.61),'linen',5)
floorwood=wood.copy();floorwood.name='RENDER_PALE_WOOD_FLOOR'
sage=scanned('SAGE_LINEN',(.37,.45,.36),'linen',5);walls=material('WARM_OFF_WHITE',(.78,.75,.69),.83)
stone=material('QUIET_CREAM_STONE',(.71,.68,.60),.42);tile=material('WARM_GREIGE_TILE',(.55,.52,.46),.7)
nickel=material('BRUSHED_NICKEL',(.47,.46,.43),.3,.8);dark=material('DARK_APPLIANCE',(.06,.067,.068),.32,.3)
ceramic=material('CERAMIC',(.84,.83,.78),.24);glass=material('CLEAR_GLASS',(.95,.97,.98),.07)
glass.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=1;glass.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.45
mirrors=material('MIRROR',(.96,.97,.98),.045,1);leaf=material('SAGE_FOLIAGE',(.13,.24,.11),.65)
paper=material('WARM_PAPER',(.83,.79,.71),.83)
def uv(o):
 me=o.data;layer=me.uv_layers.get('RenderMeters') or me.uv_layers.new(name='RenderMeters');me.uv_layers.active=layer
 for poly in me.polygons:
  ax=max(range(3),key=lambda i:abs(poly.normal[i]));axes=[i for i in range(3) if i!=ax]
  for li in poly.loop_indices:
   v=o.matrix_world@me.vertices[me.loops[li].vertex_index].co;layer.data[li].uv=(v[axes[0]],v[axes[1]])
def choose(n,oldname):
 t=(n+' '+oldname).upper()
 if 'MIRROR' in t and 'LIGHT' not in t and 'FRAME' not in t:return mirrors
 if 'GLASS' in t or 'WINDOW_0' in t or 'WINDOW_1' in t or n.startswith('G_wall_g'):return glass
 if 'LEAF' in t and 'PLANT' in t:return leaf
 if 'FLOOR' in n:return floorwood
 if n.startswith(('VIEW_WALL','G_wall','CEILING')) or 'PIER_SITE' in t:return walls
 if any(s in oldname.upper() for s in ['ASH','TIMBER','WOOD','OAK']):return wood
 if any(s in t for s in ['TAP','PULL','HANDLE','RAIL','NICKEL','METAL','DARK_BRACKET','FRAME','HINGE','HANGER']):return nickel
 if any(s in t for s in ['BASIN','WC_','TOILET','CERAMIC']):return ceramic
 if any(s in t for s in ['COUNTER','WORKTOP','STONE','SILL_PLATFORM']):return stone
 if any(s in t for s in ['APPLIANCE','FRIDGE_BODY','BODY_0','BODY_1','B11_RECTANGLE039_BODY','CONTROL','BURNER','HOB']):return ceramic if '039' in t else dark
 if 'ART_PAPER' in t or 'ART_LOW' in t:return paper
 if any(s in t for s in ['CUSHION','FABRIC','LINEN','CLOTH','PADDED','SOFT','BED_RUNNER','DAILY_SEAT','RECTANGLE046','RECTANGLE048','RECTANGLE012','RECTANGLE013','RECTANGLE017']):return sage if any(s in t for s in ['GREEN','SAGE','RUNNER','BLUE']) else fabric
 if 'POT' in t or 'VASE' in t or 'BOTTLE' in t:return ceramic
 return wood
for o in list(bpy.context.scene.objects):
 if o.type!='MESH' or o.hide_render:continue
 oldm=[m.name if m else '' for m in o.data.materials];o.data=o.data.copy();uv(o)
 mats=[choose(o.name,n) for n in oldm] or [choose(o.name,'')];o.data.materials.clear()
 for m in mats:o.data.materials.append(m)
 for p in o.data.polygons:p.material_index=min(p.material_index,len(mats)-1)
 o['render_authority']='PRESENTATION'
 # Split bedframefromtextiles byactualfacecentres; count/location/dimensionsunchanged.
 if o.name.startswith(('B11_Rectangle012','B11_Rectangle013','B11_Rectangle017')):
  o.data.materials.append(wood)
  for p in o.data.polygons:
   z=(o.matrix_world@p.center).z
   if z<.74:p.material_index=len(o.data.materials)-1
# Closedroom floorfinish patches at modelFFL,exclude obsolete curved platform fromhiddenupperfootprint.
for room in plan['rooms']:
 if room['floor_z']!=.45:continue
 x0,y0,x1,y1=room['bounds_xy'];z=.4505
 me=bpy.data.meshes.new('finish_'+room['room_id']);me.from_pydata([(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)],[],[(0,1,2,3)]);me.update()
 o=bpy.data.objects.new('PRESENTATION_FLOOR_'+room['room_id'],me);col.objects.link(o);o.data.materials.append(tile if room['wet_area'] else floorwood);uv(o);o['authority']='PRESENTATION_FLOOR_FINISH_AT_EXISTING_FFL'
# Lowerfloorfinish:paintthetopbyshader masks,geometric mesh untouched.
floor=bpy.data.objects['FLOOR_LOWER'];floor.data.materials.clear();floor.data.materials.append(floorwood);floor.data.materials.append(tile)
for p in floor.data.polygons:
 v=floor.matrix_world@p.center
 if p.normal.z>.9 and ((v.x>5.7 and v.x<7.81 and v.y<4.5) or (v.y<2.5 and v.x<5.7) or (v.x>7.9 and v.y>10.9)):p.material_index=1
 # Largefloorpolygonscannotbereliablyclassifiedusingonecentre; regionaltilefinishsurfacesbelow.
for rid in ['kitchen','service_balcony','north_sunroom']:
 r=next(r for r in plan['rooms'] if r['room_id']==rid);x0,y0,x1,y1=r['bounds_xy'];z=.0006
 me=bpy.data.meshes.new('tile_finish_'+rid);me.from_pydata([(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)],[],[(0,1,2,3)]);me.update();o=bpy.data.objects.new('PRESENTATION_TILE_'+rid,me);col.objects.link(o);o.data.materials.append(tile);uv(o)
# Floorgrout/boardjoinsareprocedural surfacefinishing,notnewlayout.
for mat,scale,bw,rh in [(floorwood,1,.18,1.2),(tile,1,.6,.6)]:
 ns=mat.node_tree.nodes;ls=mat.node_tree.links;p=ns.get('Principled BSDF');t=ns.new('ShaderNodeTexCoord');brick=ns.new('ShaderNodeTexBrick');ls.new(t.outputs['UV'],brick.inputs['Vector']);brick.inputs['Scale'].default_value=scale;brick.inputs['Brick Width'].default_value=bw;brick.inputs['Row Height'].default_value=rh;brick.inputs['Mortar Size'].default_value=.001;brick.inputs['Mortar Smooth'].default_value=.002
 bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.10;bump.inputs['Distance'].default_value=.001;ls.new(brick.outputs['Fac'],bump.inputs['Height']);ls.new(bump.outputs[0],p.inputs['Normal'])
# Daylightworldandwarmpracticalillumination consistentacrossallrooms.
world=bpy.data.worlds.new('RENDER_DAYLIGHT_WORLD');world.use_nodes=True;bpy.context.scene.world=world
ns=world.node_tree.nodes;ls=world.node_tree.links;env=ns.new('ShaderNodeTexEnvironment');env.image=bpy.data.images.load(str(OUT/'assets/daylight/courtyard_hdri_2k.hdr'));ls.new(env.outputs[0],ns.get('Background').inputs[0]);ns.get('Background').inputs[1].default_value=.45
# Neutralcamera backdrop; HDRIstilldriveslighting/reflections,do notinventexternalhousegeometry.
lp=ns.new('ShaderNodeLightPath');bg=ns.new('ShaderNodeBackground');bg.inputs[0].default_value=(.8,.83,.85,1);bg.inputs[1].default_value=.6
mix=ns.new('ShaderNodeMixShader');ls.new(lp.outputs['Is Camera Ray'],mix.inputs[0]);ls.new(ns.get('Background').outputs[0],mix.inputs[1]);ls.new(bg.outputs[0],mix.inputs[2]);ls.new(mix.outputs[0],ns.get('World Output').inputs[0])
def area(n,pos,target,power,size,color):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(n,d);col.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler();o.visible_camera=False;o.visible_transmission=False;o.visible_glossy=False;return o
for r in plan['rooms']:
 x0,y0,x1,y1=r['bounds_xy'];cx,cy=(x0+x1)/2,(y0+y1)/2
 ceiling=r['floor_z']+2.72;power=130 if r['wet_area'] else 220 if (x1-x0)*(y1-y0)>10 else 110
 area('LIGHT_'+r['room_id']+'_2900K',(cx,cy,ceiling),(cx,cy,r['floor_z']),power,1.8,(1,.80,.61))
for n,pos,target,size,power in [('southbed',(11.6,-1,2.1),(11.5,2,1.2),4,900),('northliving',(5.4,14.3,2),(5.1,9.5,1),3,850),('northstudy',(14.6,12.2,2.2),(14.6,8.3,1.2),2,600),('northsunroom',(10.5,14.2,2),(10.5,12,1),3,550)]:area('DAYLIGHT_'+n,pos,target,power,size,(.86,.92,1))
cameras=[]
overrides={}
reviewed=M/'CAMERA_REGISTER_REVIEWED.json'
if reviewed.exists():overrides={(c['room_id'],c['view_id']):c for c in json.loads(reviewed.read_text())['cameras']}
for r in plan['rooms']:
 for v in r['views']:
  v={**v,**overrides.get((r['room_id'],v['view_id']),{})}
  n='CAM_'+r['room_id']+'_'+v['view_id'];d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);col.objects.link(o);o.location=v['eye'];o.rotation_euler=(Vector(v['target'])-o.location).to_track_quat('-Z','Y').to_euler();d.lens=v['lens_mm'];d.clip_start=.03;d.clip_end=1000;d.sensor_width=36
  if v.get('controlled_verticals'):
   direction=Vector(v['target'])-o.location;direction.z=0;o.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();d.shift_y=v['shift_y']
  cameras.append({'room_id':r['room_id'],**v,'camera_name':n,'quaternion':list(o.rotation_euler.to_quaternion()),'authority':'PRESENTATION'})
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.adaptive_threshold=.04
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU';scene.render.threads_mode='FIXED';scene.render.threads=2
scene.cycles.max_bounces=8;scene.cycles.diffuse_bounces=4;scene.cycles.transmission_bounces=6;scene.cycles.sample_clamp_indirect=3
scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.5
scene['authority']='PRESENTATION';scene['source_design_sha256']=plan['source_sha256'];scene['no_design_promotion']=True
for n,h in sourcefingerprints.items():assert geomhash(bpy.data.objects[n])==h,n
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==plan['source_sha256']
bpy.ops.file.pack_all();destination=OUT/'WHOLE_HOUSE_FAITHFUL_RENDER_V1.blend';bpy.ops.wm.save_as_mainfile(filepath=str(destination))
(M/'CAMERA_REGISTER_V1.json').write_text(json.dumps({'source_design':str(SOURCE),'source_sha256':plan['source_sha256'],'render_scene':str(destination),'cameras':cameras},ensure_ascii=False,indent=2)+'\n')
(M/'SOURCE_RENDER_FIDELITY.json').write_text(json.dumps({'status':'PASS','all976bound_geometry_and_world_matrices_unchanged':True,'floor_finish_authority':'presentation surfacesatmodelFFL','source_sha256':plan['source_sha256'],'render_scene_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'packed_cc0_assets':['ash_veneer','rough_linen','courtyard'],'no_furniture_topology_change':True},indent=2))
print('PRESENTATION_PREPARE_PASS',len(cameras),str(destination))
