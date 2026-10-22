"""Single locked-camera daytime material test; only the render branch is edited."""
import bpy,json,math,runpy,sys,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
P=json.loads((OUT/'TEST_PREFLIGHT.json').read_text());SOURCE=Path(P['source']);BRANCH=Path(P['branch'])
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='helpers')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def material(n,color,rough=.6,metal=0):
 m=bpy.data.materials.new(n);m.use_nodes=True;m.diffuse_color=(*color,1)
 b=m.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
 return m
def textured(n,a,b,scale,rough,noise_scale,bump_distance):
 m=material(n,a,rough);nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes['Principled BSDF']
 tc=nodes.new('ShaderNodeTexCoord');mul=nodes.new('ShaderNodeVectorMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=scale;links.new(tc.outputs['Object'],mul.inputs[0])
 noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=noise_scale;noise.inputs['Detail'].default_value=2;noise.inputs['Roughness'].default_value=.6;links.new(mul.outputs[0],noise.inputs['Vector'])
 ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*a,1);ramp.color_ramp.elements[1].color=(*b,1);links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
 bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=bump_distance;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal']);return m
def glass():
 m=material('TEST_NEUTRAL_CLEAR_GLASS',(.96,.97,.98),.025);nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes['Principled BSDF'];bs.inputs['Transmission Weight'].default_value=1;bs.inputs['IOR'].default_value=1.45
 lp=nodes.new('ShaderNodeLightPath');trans=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');links.new(lp.outputs['Is Shadow Ray'],mix.inputs[0]);links.new(bs.outputs[0],mix.inputs[1]);links.new(trans.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes['Material Output'].inputs['Surface']);return m
def geometry_states():
 s=H['snapshot']();return {n:{k:v for k,v in r.items() if k in ['type','geometry_sha256','authored_transform','parent','modifiers']} for n,r in s.items()}
def build():
 assert sha(SOURCE)==P['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(SOURCE));base=geometry_states();write('R3_SOURCE_GEOMETRY_LOCK.json',base)
 col=bpy.data.collections.new('R3_RENDER_TEST_LIVING_ONLY');bpy.context.scene.collection.children.link(col)
 wood=textured('TEST_LIGHT_ASH',(.60,.52,.41),(.70,.63,.53),(.6,15,2),.42,3,.0003)
 floor=textured('TEST_PALE_WOOD_FLOOR',(.47,.43,.37),(.59,.55,.48),(18,.5,2),.48,4,.0002)
 fabric=textured('TEST_OFFWHITE_LINEN',(.65,.625,.585),(.72,.70,.66),(1,1,1),.83,850,.00015)
 wall=material('TEST_WARM_OFFWHITE',(.79,.77,.73),.83);ceiling=material('TEST_WARM_WHITE_CEILING',(.84,.83,.80),.86)
 metal=material('TEST_RESTRAINED_CHARCOAL',(.10,.12,.12),.3,.62);stone=textured('TEST_LIGHT_WARM_STONE',(.66,.65,.61),(.76,.74,.69),(1,1,1),.45,18,.0001)
 gl=glass();mapped={};excluded=[]
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  # These are reference/semantic guides, not the visible R3 design assemblies.
  if any(c.name in ['05_HUMAN_DESIGN_GUIDE','06_FUTURE_DESIGN_OPTIONS'] for c in o.users_collection):
   if not o.hide_render:excluded.append(o.name)
   o.hide_render=True;continue
  if o.hide_render or o.hide_viewport:continue
  pts=[o.matrix_world@Vector(p) for p in o.bound_box]
  if max(p.x for p in pts)<2.85 or min(p.x for p in pts)>7.8 or max(p.y for p in pts)<7.5 or min(p.y for p in pts)>14.0:continue
  o.data=o.data.copy();old=[m.name if m else '' for m in o.data.materials]
  for i,m in enumerate(list(o.data.materials)):
   name=m.name.upper() if m else '';on=o.name.upper()
   if 'GLASS' in name or (('GLASS' in on or on.startswith('GLZ_')) and 'FRAME' not in on):new=gl
   elif 'CEILING' in on:new=ceiling
   elif on.startswith(('FLOOR_','SITE_GROUND')):new=floor
   elif 'WALL' in name or 'CONTINUOUS' in name or on.startswith(('V5_CORNER_PATCH','R3_HOUSE_WALL')):new=wall
   elif 'WINDOW_FRAME' in name or 'METAL' in name or 'TRACK' in on:new=metal
   elif 'FABRIC' in name or on.startswith(('B11_RECTANGLE046','B11_RECTANGLE047','B11_RECTANGLE048')):new=fabric
   elif 'SILL' in name or 'CERAMIC' in name or 'COUNTERTOP' in name:new=stone
   else:new=wood
   o.data.materials[i]=new
  if not o.data.materials:o.data.materials.append(wall)
  mapped[o.name]=dict(before=old,after=[m.name for m in o.data.materials])
 camdata=bpy.data.cameras.new('R3_LIVING_DAY_TEST_01');cam=bpy.data.objects.new(camdata.name,camdata);col.objects.link(cam)
 cam.location=(7.15,8.25,1.55);target=Vector((4.85,11.45,1.20));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=28;camdata.sensor_width=36;camdata.clip_start=.035;camdata.clip_end=150
 s=bpy.context.scene;s.camera=cam;s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.film_transparent=False
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.30;s.view_settings.gamma=1
 for o in bpy.data.objects:
  if o.type=='LIGHT':o.hide_render=True
 # Large diffuse daylight source outside the actual outer bay glazing.
 def area(n,pos,target,power,size,color,size_y=None):
  d=bpy.data.lights.new(n,'AREA');d.energy=power;d.color=color;d.shape='RECTANGLE';d.size=size;d.size_y=size_y or size
  o=bpy.data.objects.new(n,d);col.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 area('DAYLIGHT_EXISTING_BAY',(5.3,14.10,2.10),(5.0,10.4,1.0),450,3.0,(.92,.96,1.0),1.5)
 area('SOFT_NEUTRAL_ARCH_FILL',(5.3,10.3,2.68),(5.3,10.3,0),65,3.0,(1.0,.91,.82),2.0)
 world=bpy.data.worlds.new('R3_DAYLIGHT_WORLD');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.84,.91,1.0,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18;s.world=world
 s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True;s.cycles.max_bounces=8;s.cycles.transmission_bounces=8;s.cycles.transparent_max_bounces=8
 device='CPU'
 try:
  cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='METAL';cp.get_devices()
  if any(d.type=='METAL' for d in cp.devices):
   for d in cp.devices:d.use=d.type=='METAL'
   s.cycles.device='GPU';device='METAL'
 except Exception:s.cycles.device='CPU'
 # Record source geometry before/after separately from the permitted materials.
 after=geometry_states()
 for n,r in base.items():assert after[n]==r,('Locked geometry changed',n)
 write('R3_CAMERA_REGISTER.json',dict(stage='SINGLE_IMAGE_TEST',camera=cam.name,position_m=list(cam.location),target_m=list(target),floor_ffl_m=0,eye_height_m=1.55,lens_mm=28,sensor_width_mm=36,resolution=[1536,1024],visible_story='north bay + west three-seat sofa + north loveseat + center coffee table',behind_camera='split-level leisure area and most of chaise; do not invent them in this view'))
 write('R3_MATERIAL_REGISTER.json',dict(stage='HUMAN_REVIEW_SINGLE_TEST',materials={m.name:list(m.diffuse_color) for m in [wood,floor,fabric,wall,ceiling,metal,stone,gl]},object_material_mapping=mapped))
 write('TEST_BRANCH_MANIFEST.json',dict(source=str(SOURCE),source_sha256=sha(SOURCE),branch=str(BRANCH),geometry_locked_objects=len(base),locked_geometry='PASS',source_active_design_visibility_preserved=True,excluded_nonphysical_reference_guides=excluded,device=device,engine='Cycles',samples=64,blender=bpy.app.version_string,source_geometry_authority='ONLY_R3_OPTION_A',scope='ONE_LIVING_CAMERA_TEST_NOT_FULL_BATCH'))
 s['render_style_stage']='R3_VISUAL_STYLE_HUMAN_REVIEW_SINGLE_TEST';s['authoritative_geometry_source']=str(SOURCE)
 bpy.ops.wm.save_as_mainfile(filepath=str(BRANCH));assert sha(SOURCE)==P['source_sha256']
 print(json.dumps(dict(build='PASS',branch=str(BRANCH),source_geometry_objects=len(base),device=device)))
def render(mode):
 m=json.loads((OUT/'TEST_BRANCH_MANIFEST.json').read_text());assert sha(SOURCE)==m['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(BRANCH));s=bpy.context.scene
 base=json.loads((OUT/'R3_SOURCE_GEOMETRY_LOCK.json').read_text());states=geometry_states()
 for n,r in base.items():assert states[n]==r,n
 if mode=='plan':
  rows=[]
  for o in bpy.data.objects:
   if o.type=='MESH' and not o.hide_render and (o.name=='R3_HOUSE_WALLS_D107_ROLLED_BACK' or o.name.startswith('V5_CORNER_PATCH_')):
    o.data.calc_loop_triangles();rows.append(dict(name=o.name,vertices=[list(o.matrix_world@v.co) for v in o.data.vertices],triangles=[list(t.vertices) for t in o.data.loop_triangles]))
  write('LIVING_PLAN_SOURCE_GEOMETRY.json',dict(source_sha256=m['source_sha256'],walls=rows));print('PLAN_EXPORT_PASS');return
 if mode=='preview':
  s.render.engine='BLENDER_WORKBENCH';s.render.resolution_percentage=50;s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=False;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.display.render_aa='16';s.view_settings.view_transform='Standard'
  p=OUT/'living/diagnostics/LIVING_01_COMPOSITION_PROXY.png'
 else:
  s.render.engine='CYCLES'
  if m['device']=='METAL':
   cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='METAL';cp.get_devices()
   for d in cp.devices:d.use=d.type=='METAL'
   s.cycles.device='GPU'
  p=OUT/'living/authoritative/LIVING_01_DAY_CYCLES_TEST.png'
 p.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 assert sha(SOURCE)==m['source_sha256'];print(json.dumps(dict(render='PASS',mode=mode,path=str(p),source_preserved=True)))
if __name__=='__main__':
 mode=sys.argv[sys.argv.index('--')+1]
 if mode=='build':build()
 else:render(mode)
