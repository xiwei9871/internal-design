"""Freezer816 full-house proxy and inherited evidence; keep bedrooms/study unchanged."""
import bpy, json, hashlib, sys, shutil, math
from pathlib import Path
from argparse import Namespace
from mathutils import Vector, Quaternion
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/secondary_bath850_review'
OUT=R/'proxy_full';OUT.mkdir(parents=True,exist_ok=True)
DELIVERY=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/secondary_bath850_review/full')
OLD=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/freezer816_review/full')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
reg=json.loads((R/'spatial-canvas.bindings.full.json').read_text())
layout=json.loads((R/'SECONDARY_BATH_850_REVIEW.json').read_text())
assert sha(reg['source_locator'])==reg['source_sha256']
bpy.ops.wm.open_mainfile(filepath=reg['source_locator'])
sys.path.insert(0,'/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/adapters/blender')
import export_proxy
ordinary=export_proxy.assign_flat_colors
def presentation(mesh,entity,cache,owned,counts,mode,source):
 name=entity['native_object_id']
 if name.startswith(('BW1_','STUDY_V1_','B11_Rectangle039','B11_Rectangle040',
  'WAVE_WALL_HANDRAIL','WAVE_HANDRAIL_','READING_','NORTH_WINDOW_FITNESS_RESERVE','STEP_','SUNROOM_')):
  return ordinary(mesh,entity,cache,owned,counts,'source-flat',source)
 if not name.startswith(('NORTH_BALCONY_GLASS_','NORTH_BALCONY_FRAME_')):
  return ordinary(mesh,entity,cache,owned,counts,mode,source)
 glass=name.startswith('NORTH_BALCONY_GLASS_');key='balcony_glass' if glass else 'balcony_aluminum'
 m=cache.get(key)
 if m is None:
  m=bpy.data.materials.new(key);m.use_nodes=True
  c=(.45,.70,.78,.32) if glass else (.055,.065,.075,1)
  m.diffuse_color=c;s=m.node_tree.nodes.get('Principled BSDF')
  s.inputs['Base Color'].default_value=c;s.inputs['Alpha'].default_value=c[3]
  s.inputs['Roughness'].default_value=.22 if glass else .4;m.use_backface_culling=False
  if glass:m.surface_render_method='DITHERED'
  owned.append(m);cache[key]=m
 mesh.materials.clear();mesh.materials.append(m)
 for f in mesh.polygons:f.material_index=0
 counts[key]=counts.get(key,0)+1
export_proxy.assign_flat_colors=presentation
m=export_proxy.export_proxy(Namespace(output=str(OUT),bindings=str(R/'spatial-canvas.bindings.full.json'),
 scope='full',room_id=None,global_ids=None,collection=None,color_mode='zoning-flat',
 source_resource_id=reg['source_resource_id'],source_revision=reg['source_revision']))
m['extensions']['spatial_canvas.review']={'status':'HUMAN_REVIEW','source_design_authority':'DERIVED_DESIGN_MODEL',
 'inherits_bedroom_revision':'bedrooms-wood-v1-review-3','freezer_size_mm':[816,550,876],'cabinet_gain_mm':334,'wardrobe_width_mm':1200,'bath_door_clear_mm':850,'frozen_r4_unchanged':True,'local_derived_partition_revised':True,
 'bed_widths_m':{'mother':1.5,'couple':1.8,'guest':1.2},'guest_bunk':False,
 'snapshot_note':'Bindings V1 frozen means a hash-locked exported snapshot; this is a derived furniture study, not new physical ground truth.'}
m['extensions']['spatial_canvas.presentation'].update(opaque=False,profile='secondary-bath850-review',glass_alpha=.32)
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
write(OUT/'interaction_proxy.manifest.json',m)
old=json.loads((OLD/'interaction_proxy.manifest.json').read_text())
replacements={old['source_resource_id']:m['source_resource_id'],old['resource_id']:m['resource_id'],
 old['source_revision']:m['source_revision'],old['source_sha256']:m['source_sha256'],old['source_resource']:m['source_resource']}
def relink(v):
 if isinstance(v,str):return replacements.get(v,v)
 if isinstance(v,list):return [relink(x) for x in v]
 if isinstance(v,dict):return {k:relink(x) for k,x in v.items()}
 return v
for n in ['spatial-canvas.project.json','spatial-canvas.spaces.json']:
 d=relink(json.loads((OLD/n).read_text()))
 if n=='spatial-canvas.project.json':
  for s in d['sources']:
   if s['resource_id']==m['source_resource_id']:s['diagnostics']=['HUMAN_REVIEW secondarybath850doorand1200wardrobe; candidate boundaries retained, localderivedpartition revised.']
 write(OUT/n,d)
g=relink(json.loads((OLD/'spatial-canvas.relationships.json').read_text()));g['revision']='27-secondary-bath850-wardrobe1200-review'
known={b['entity_id']:b for b in reg['bindings']}
g['nodes']=[n for n in g['nodes'] if n['kind']!='entity' or n['node_id'] in known]
ids={n['node_id'] for n in g['nodes']};g['edges']=[e for e in g['edges'] if e['from'] in ids and e['to'] in ids]
for gid,b in known.items():
 if gid not in ids:g['nodes'].append({'node_id':gid,'kind':'entity','name':b['native_id'],'native_id':b['native_id'],
  'resource_id':m['source_resource_id'],'revision':m['source_revision'],'sha256':m['source_sha256']})
# Reviseddoor/wardrobe/partition:retainmembership,retirestalephysical/adjacencyclaims.
editedids={b['entity_id'] for b in reg['bindings'] if b['native_id'] in layout['changed_native_ids']}
g['edges']=[e for e in g['edges'] if not(e['from'] in editedids or e['to'] in editedids) or e.get('type') in ['part_of','same_component_group']]
for s in g['sources']:
 if s['resource_id']=='spaces_c_type_r4':s.update(sha256=sha(OUT/'spatial-canvas.spaces.json'),locator=str(OUT/'spatial-canvas.spaces.json'))
write(OUT/'spatial-canvas.relationships.json',g)
byname={b['native_id']:b for b in reg['bindings']}
views=[('secondary-bath',(8.40,2.0,3.65),(10.05,4.38,1.40),['VIEW_WALL_W_wall_md_0015'])]
for name,eye,target,hides in views:
 q=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y');pq=Quaternion((2**-.5,-2**-.5,0,0))@q
 preset={'schema':'spatial-canvas.view-preset.v1','preset_id':'secondary_bath850_'+name,'projection':'perspective',
  'fov_degrees':45,'near':.02,'far':1000,'position':[eye[0],eye[2],-eye[1]],
  'quaternion':[pq.x,pq.y,pq.z,pq.w],'orbit_target':[target[0],target[2],-target[1]],
  'viewport':{'width':1000,'height':780,'pixel_ratio':1},'projection_matrix':[1.883086,0,0,0,0,2.414214,0,0,0,0,-1.00004,-1,0,0,-.0400008,0],
  'frame_id':'blender_proxy_world','unit':'meter','up_axis':'Y','design_id':m['design_id'],
  'source_resource_id':m['source_resource_id'],'source_revision':m['source_revision'],'source_sha256':m['source_sha256'],
  'source_locator':m['source_resource'],'bindings':m['extensions']['spatial_canvas.blender']['bindings'],
  'source_camera':{'position':eye,'quaternion':[q.x,q.y,q.z,q.w],'frame_id':'c_type_world','unit':'meter','up_axis':'Z'},
  'hidden_entity_ids':[byname[n]['entity_id'] for n in hides if n in byname],'ghost_entity_ids':[],
  'preview_uri':'BATH850_ENTRY.png'}
 write(OUT/(name+'.view-preset.json'),preset)
# GLB must independentlyopenwith unchangedstable nativebindingIDs.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(OUT/'interaction_proxy.glb'))
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(entities)==m['entity_count']==len(reg['bindings'])
assert all(entities[b['native_id']]['global_id']==b['entity_id'] for b in reg['bindings'])
assert len(reg['bindings'])==937
for n in ['BW1_GUEST_DESK','BW1_GUEST_PEGBOARD','BW1_GUEST_CLOUD_WALL_LIGHT','BW1_MOTHER_VANITY',
 'BW1_COUPLE_SHALLOW_SHELF','B11_Rectangle022_CATALOG_00_00','B11_Rectangle017_CATALOG_00_00',
 'STUDY_V1_MOVABLE_DESK','SUNROOM_SOFA_REAR_HIGH_CABINET','STEP_0']:assert n in entities,n
for n,w in [('B11_Rectangle012_CATALOG_00_00',1.8),('B11_Rectangle013_CATALOG_00_00',1.5),('B11_Rectangle017_CATALOG_00_00',1.2)]:
 o=entities[n];coords=[o.matrix_world@v.co for v in o.data.vertices]
 # Blender glTF importer restores the original Z-up source frame; bed width is Y.
 assert abs(max(v.y for v in coords)-min(v.y for v in coords)-w)<1e-4
rest=entities['BW1_COUPLE_SOFT_HEADREST'];cs=[rest.matrix_world@v.co for v in rest.data.vertices]
assert abs(max(v.y for v in cs)-min(v.y for v in cs)-1.8)<1e-4
assert 'BW1_MOTHER_BEDSIDE' in entities and 'BW1_MOTHER_BEDSIDE_N' in entities
assert sha(reg['source_locator'])==reg['source_sha256']
assert all(sha(p)==h for p,h in layout['frozen_hashes'].items())
def bounds(n):
 o=entities[n];vs=[o.matrix_world@v.co for v in o.data.vertices]
 return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
wa,wb=bounds('R3_WARDROBE_TOP');assert abs(wb[0]-wa[0]-1.2)<1e-4
fa,fb=bounds('R3_FRAME_WEST');ea,eb=bounds('R3_SPLIT_JAMB_EAST_S');assert abs(ea[0]-fb[0]-.85)<1e-4
assert len([n for n in entities if n.startswith('R3_WARDROBE_FRONT_')])==3
write(OUT/'EXPORT_EVIDENCE.json',{'status':'PASS','entities':len(entities),'source_revision':m['source_revision'],
 'stable_ids_match':True,'door850_and_wardrobe1200_verified_fresh_import':True,'other_room_features_preserved':True,'frozen_hashes_unchanged':True})
DELIVERY.mkdir(parents=True,exist_ok=True)
for p in OUT.iterdir():
 if p.is_file() and p.suffix in ['.json','.glb']:shutil.copy2(p,DELIVERY/p.name)
shutil.copy2(R/'SECONDARY_BATH_850_REVIEW.json',DELIVERY/'SECONDARY_BATH_850_REVIEW.json')
print('BATH850_EXPORT_PASS',len(entities),str(DELIVERY))
