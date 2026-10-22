import json, hashlib, shutil
from pathlib import Path
R=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
base=R/'proxy_review13';out=R/'proxy_review14'
m=json.loads((out/'interaction_proxy.manifest.json').read_text())
reg=json.loads((R/'spatial-canvas.bindings.review14.json').read_text())
report=json.loads((R/'SUNROOM_INTEGRATED_LAUNDRY_REVIEW14_REPORT.json').read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def link(v):
 if isinstance(v,list):return [link(x) for x in v]
 if isinstance(v,dict):
  d={k:link(x) for k,x in v.items()}
  if d.get('resource_id')==m['source_resource_id']:
   for k,x in [('revision',m['source_revision']),('sha256',m['source_sha256']),('locator',m['source_resource'])]:
    if k in d:d[k]=x
  return d
 return v
for name in ['spatial-canvas.project.json','spatial-canvas.spaces.json']:
 d=link(json.loads((base/name).read_text()))
 if name=='spatial-canvas.project.json':
  for s in d['sources']:
   if s['resource_id']==m['source_resource_id']:
    s['diagnostics']=['HUMAN_REVIEW: east-wall longitudinal chest freezer with no extra top; restored north plant ledge; integrated laundry upper cabinet. Regions remain inherited review evidence.']
 write(out/name,d)
g=link(json.loads((base/'spatial-canvas.relationships.json').read_text()))
g['revision']='21-integrated-laundry-review'
for s in g['sources']:
 if s['resource_id']=='spaces_c_type_r4':
  s.update(sha256=hashlib.sha256((out/'spatial-canvas.spaces.json').read_bytes()).hexdigest(),locator=str(out/'spatial-canvas.spaces.json'))
known={b['entity_id']:b for b in reg['bindings']}
g['nodes']=[n for n in g['nodes'] if n['kind']!='entity' or n['node_id'] in known]
ids={n['node_id'] for n in g['nodes']}
changed={b['entity_id'] for b in reg['bindings'] if b['native_id'] in report['modified_existing_native_ids']}
g['edges']=[e for e in g['edges'] if e['from'] in ids and e['to'] in ids and e['from'] not in changed and e['to'] not in changed]
for gid,b in known.items():
 if gid not in ids:g['nodes'].append({'node_id':gid,'kind':'entity','name':b['native_id'],'native_id':b['native_id'],'resource_id':m['source_resource_id'],'revision':m['source_revision'],'sha256':m['source_sha256']})
write(out/'spatial-canvas.relationships.json',g)
m['extensions']['spatial_canvas.review'].update(
 correction='Chest freezer long axis parallel to east wall, no added cover; restore2890mm north plant ledge; continuous2285mm laundry+sofa upper cabinetry with700mm depth and matching ash doors; sofa returns toreview12 station.',
 freezer_top_clear=True,freezer_parallel_to_east_wall=True,north_plant_ledge_length_m=2.89,
 integrated_laundry_cabinet=True,central_lane_m=report['central_lane_m'],
 appliance_dimensions_are_generic_review_only=True,manufacturer_lid_sweep_verified=False,utilities_verified=False)
write(out/'interaction_proxy.manifest.json',m)
view=json.loads((R/'sunroom_cabinet_freezer_swap_review_13.view-preset.json').read_text())
view.update(preset_id='sunroom_integrated_laundry_review_14',source_revision=m['source_revision'],
 source_sha256=m['source_sha256'],source_locator=m['source_resource'],
 bindings=m['extensions']['spatial_canvas.blender']['bindings'],preview_uri='SUNROOM_REVIEW14_FRONT.png')
# Keep the exact owner's north-facing composition from the latest ContextPacket.
packettext=Path('/Users/xiwei/.codex/attachments/5f1a20bc-241b-4093-a8a3-e4fc50e65507/Pasted text.txt').read_text()
packet=json.loads(packettext.split('<ContextPacket>')[1].split('</ContextPacket>')[0])
view.update(packet['view']['data'])
px,py,pz=view['position'];qx,qy,qz,qw=view['quaternion'];c=2**-.5
view['source_camera']={'position':[px,-pz,py],
 'quaternion':[c*(qx+qw),c*(qy-qz),c*(qz+qy),c*(qw-qx)],
 'frame_id':'c_type_world','unit':'meter','up_axis':'Z'}
write(R/'sunroom_integrated_laundry_review_14.view-preset.json',view)
delivery=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/v03-c-type/review14')
delivery.mkdir(parents=True,exist_ok=True)
for p in out.iterdir():
 if p.suffix in ['.json','.glb']:shutil.copy2(p,delivery/p.name)
for name in ['OPTION_A_R4_SUNROOM_INTEGRATED_LAUNDRY_REVIEW_14.blend','sunroom_integrated_laundry_review_14.view-preset.json',
 'SUNROOM_REVIEW14_FRONT.png','SUNROOM_REVIEW14_AXON.png','SUNROOM_INTEGRATED_LAUNDRY_REVIEW14_REPORT.json','REVIEW14_GEOMETRY_EVIDENCE.json']:
 shutil.copy2(R/name,delivery/name)
print('PACKAGED',m['source_revision'],m['entity_count'],str(delivery))
