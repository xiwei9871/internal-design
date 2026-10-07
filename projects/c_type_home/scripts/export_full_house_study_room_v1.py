"""Publish the accepted study successor as a full-house proxy without source edits."""
import bpy,json,hashlib,sys,math,shutil
from pathlib import Path
from argparse import Namespace
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/study_room_v1'
SOURCE=R/'STUDY_ROOM_DAYBED_V1.blend';OUT=R/'proxy_full'
BASE=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
DELIVERY=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/study_room_v1/full')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
truths={
 Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend'):'d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb',
 Path('/Users/xiwei/interior_design/projects/c_type_home/design/blender_b0/B0_EXISTING_AS_IS.blend'):'717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb'}
assert all(sha(p)==h for p,h in truths.items())
study=json.loads((R/'spatial-canvas.bindings.daily.json').read_text())
parent=json.loads((BASE/'spatial-canvas.bindings.review14.json').read_text())
assert sha(SOURCE)==study['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update()
# Known bindings, intersected with current visible entities; no semantic reconstruction.
bound={}
retired=[]
for b in parent['bindings']:
 o=bpy.data.objects.get(b['native_id'])
 if o and not o.hide_render and not o.hide_viewport and o.visible_get():bound[b['native_id']]=b
 else:retired.append(b['native_id'])
for b in study['bindings']:
 if b['native_id']!='STUDY_V1_CONTEXT_FLOOR':bound[b['native_id']]=b
reg={k:v for k,v in study.items() if k!='bindings'}
reg['registry_revision']='study-room-daybed-v1-r5-full'
reg['bindings']=list(bound.values())
REG=R/'spatial-canvas.bindings.full.json'
REG.write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,'/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/adapters/blender')
import export_proxy
ordinary=export_proxy.assign_flat_colors
def presentation(mesh,entity,cache,owned,counts,mode,source):
 name=entity['native_object_id']
 if name.startswith(('B11_Rectangle039','B11_Rectangle040','WAVE_WALL_HANDRAIL','WAVE_HANDRAIL_',
 'READING_','NORTH_WINDOW_FITNESS_RESERVE','STEP_','SUNROOM_')):
  return ordinary(mesh,entity,cache,owned,counts,'source-flat',source)
 if not name.startswith(('NORTH_BALCONY_GLASS_','NORTH_BALCONY_FRAME_')):
  return ordinary(mesh,entity,cache,owned,counts,mode,source)
 glass=name.startswith('NORTH_BALCONY_GLASS_');key='balcony_glass' if glass else 'balcony_aluminum'
 material=cache.get(key)
 if material is None:
  material=bpy.data.materials.new(key);material.use_nodes=True
  color=(.45,.70,.78,.32) if glass else (.055,.065,.075,1)
  material.diffuse_color=color;shader=material.node_tree.nodes.get('Principled BSDF')
  shader.inputs['Base Color'].default_value=color;shader.inputs['Alpha'].default_value=color[3]
  shader.inputs['Roughness'].default_value=.22 if glass else .4
  material.use_backface_culling=False
  if glass:material.surface_render_method='DITHERED'
  owned.append(material);cache[key]=material
 mesh.materials.clear();mesh.materials.append(material)
 for p in mesh.polygons:p.material_index=0
 counts[key]=counts.get(key,0)+1
export_proxy.assign_flat_colors=presentation
m=export_proxy.export_proxy(Namespace(output=str(OUT),bindings=str(REG),scope='full',room_id=None,
 global_ids=None,collection=None,color_mode='zoning-flat',source_resource_id=reg['source_resource_id'],
 source_revision=reg['source_revision']))
m['extensions']['spatial_canvas.presentation'].update(opaque=False,profile='full-house-zoning-with-sunroom-glass',glass_alpha=.32)
m['extensions']['spatial_canvas.review']={'status':'HUMAN_REVIEW','mode':'daily',
 'source_design_authority':'DERIVED_DESIGN_MODEL','inherits_sunroom_revision':'r4-sunroom-integrated-laundry-review-14',
 'accepted_study_revision':'study-room-daybed-v1-r5-daily','tea_table_size_m':[2.0,.8,.75],
 'parent_source_resource_id':'c_type_r4','parent_source_revision':'r4',
 'parent_source_sha256':list(truths.values())[0],'architecture_unchanged':True,
 'task_only_context_floor_excluded':True}
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
write(OUT/'interaction_proxy.manifest.json',m)
# Inherited semantic evidence keeps its reviewed/candidate states; geometry has not changed.
oldrid=parent['source_resource_id'];newrid=reg['source_resource_id']
def relink(v):
 if isinstance(v,list):return [relink(x) for x in v]
 if isinstance(v,dict):
  d={k:relink(x) for k,x in v.items()}
  if d.get('resource_id')==oldrid:
   d['resource_id']=newrid
   for k,x in [('revision',m['source_revision']),('sha256',m['source_sha256']),('locator',m['source_resource'])]:
    if k in d:d[k]=x
  return d
 return v
for n in ['spatial-canvas.project.json','spatial-canvas.spaces.json']:
 d=relink(json.loads((BASE/'proxy_review14'/n).read_text()))
 if n=='spatial-canvas.project.json':
  for s in d['sources']:
   if s['resource_id']==newrid:s['diagnostics']=['HUMAN_REVIEW full-house inheritedreview14 + studydaybedv1-r4. Candidate regions retained; newfurniture isnotspatial evidence.']
 write(OUT/n,d)
g=relink(json.loads((BASE/'proxy_review14/spatial-canvas.relationships.json').read_text()))
g['revision']='22-study-room-v1-r5-full'
for s in g['sources']:
 if s['resource_id']=='spaces_c_type_r4':
  s.update(sha256=sha(OUT/'spatial-canvas.spaces.json'),locator=str(OUT/'spatial-canvas.spaces.json'))
known={b['entity_id']:b for b in reg['bindings']}
g['nodes']=[n for n in g['nodes'] if n['kind']!='entity' or n['node_id'] in known]
ids={n['node_id'] for n in g['nodes']}
g['edges']=[e for e in g['edges'] if e['from'] in ids and e['to'] in ids]
for gid,b in known.items():
 if gid not in ids:g['nodes'].append({'node_id':gid,'kind':'entity','name':b['native_id'],
 'native_id':b['native_id'],'resource_id':newrid,'revision':m['source_revision'],'sha256':m['source_sha256']})
write(OUT/'spatial-canvas.relationships.json',g)
# Full-house overview camera, preserving exact export frame conversions.
eye=Vector((22,20,24));target=Vector((8.5,6.5,.8))
sq=(target-eye).to_track_quat('-Z','Y');pq=Quaternion((2**-.5,-2**-.5,0,0))@sq
preset={'schema':'spatial-canvas.view-preset.v1','preset_id':'c_type_full_study_r5_overview',
 'projection':'perspective','fov_degrees':45,'near':.02,'far':1000,
 'position':[eye.x,eye.z,-eye.y],'quaternion':[pq.x,pq.y,pq.z,pq.w],
 'orbit_target':[target.x,target.z,-target.y],'viewport':{'width':1000,'height':780,'pixel_ratio':1},
 'projection_matrix':[1.883086,0,0,0,0,2.414214,0,0,0,0,-1.00004,-1,0,0,-.0400008,0],
 'frame_id':'blender_proxy_world','unit':'meter','up_axis':'Y','design_id':m['design_id'],
 'source_resource_id':newrid,'source_revision':m['source_revision'],'source_sha256':m['source_sha256'],
 'source_locator':m['source_resource'],'bindings':m['extensions']['spatial_canvas.blender']['bindings'],
 'source_camera':{'position':list(eye),'quaternion':[sq.x,sq.y,sq.z,sq.w],
 'frame_id':'c_type_world','unit':'meter','up_axis':'Z'},'hidden_entity_ids':[],'ghost_entity_ids':[],
 'preview_uri':'full-house-overview.png'}
write(OUT/'full-house-overview.view-preset.json',preset)
# Validate fresh export against sidecar, including selected previousliving/sunroomchanges.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'interaction_proxy.glb'))
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(entities)==len(reg['bindings'])==m['entity_count']
assert all(entities[b['native_id']]['global_id']==b['entity_id'] for b in reg['bindings'])
for n in ['STUDY_V1_MOVABLE_DESK','STUDY_V1_DAYBED_TIMBER_TOP','STUDY_V1_BOOKCASE_LOWER_CARCASS',
 'SUNROOM_SOFA_REAR_HIGH_CABINET','B11_Rectangle039_BODY','B11_Rectangle046_CATALOG_00_00','STEP_0']:
 assert n in entities,n
assert not any(n in entities for n in retired)
assert 'STUDY_V1_CONTEXT_FLOOR' not in entities
assert 'STUDY_V1_MOVABLE_STOOL' not in entities
assert 'STUDY_V1_WORK_CHAIR' in entities
assert sha(SOURCE)==study['source_sha256']
assert all(sha(p)==h for p,h in truths.items())
evidence={'status':'PASS','full_house_entities':len(entities),'same_study_source_sha256':sha(SOURCE),
 'all_exported_ids_match':True,'prior_living_sunroom_and_study_present':True,'optional_stool_removed':True,'retired_objects_absent':True,
 'duplicate_task_context_floor_absent':True,'r4_b0_hashes_unchanged':True}
write(OUT/'FULL_HOUSE_EXPORT_EVIDENCE.json',evidence)
DELIVERY.mkdir(parents=True,exist_ok=True)
for p in OUT.iterdir():
 if p.is_file() and p.suffix in ['.glb','.json']:shutil.copy2(p,DELIVERY/p.name)
print('FULL_HOUSE_EXPORT_PASS',json.dumps(evidence),str(DELIVERY))
