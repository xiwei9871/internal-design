"""Rebind existing semantic candidates and the owner's camera to the exact V11 snapshot."""
import json,hashlib,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];APP=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas');O=APP/'task-output/c_type_v11';F=O/'full'
m=json.loads((F/'interaction_proxy.manifest.json').read_text());regpath=O/'spatial-canvas.bindings.json';reg=json.loads(regpath.read_text());ref={k:m[k] for k in ['source_resource_id','source_revision','source_sha256']}
source={'resource_id':ref['source_resource_id'],'type':'blender','revision':ref['source_revision'],'sha256':ref['source_sha256'],'locator':m['source_resource'],'semantic_capability':'geometry_only','diagnostics':['Derived V11 owner finish rules, grounded reading rack and duplicate bench hidden. Inherited space candidates retain their original verification states; no stale furniture relationship graph imported.']}
p=json.loads((APP/'task-output/c_type_v9/full/spatial-canvas.project.json').read_text());p['sources'].append(source)
spaces=json.loads((APP/'task-output/c_type_v9/full/spatial-canvas.spaces.json').read_text());spaces['registry_revision']+='-v11-snapshot';spaces['applies_to'].append({'resource_id':source['resource_id'],'revision':source['revision'],'sha256':source['sha256']});spaces['source_context']['sources'].append(source)
for n,x in [('spatial-canvas.project.json',p),('spatial-canvas.spaces.json',spaces)]:
    dest=F/n;assert not dest.exists();dest.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
v=json.loads((R/'design/reading_wall_v10/OWNER_TARGET_PACKET.json').read_text())['view']['data'];q=v['quaternion'];c=math.sqrt(.5);sourceq=[c*(q[0]+q[3]),c*(q[1]-q[2]),c*(q[2]+q[1]),c*(q[3]-q[0])]
pose={k:v[k] for k in ['projection','fov_degrees','near','far','position','quaternion','orbit_target','viewport','frame_id','unit','up_axis']}
pose.update({'schema':'spatial-canvas.view-preset.v1','preset_id':'v11_owner_reading_and_finishes','preview_uri':'v11_owner_reading_and_finishes.png','design_id':m['design_id'],**ref,'source_locator':m['source_resource'],'bindings':{'locator':str(regpath),'registry_id':reg['registry_id'],'registry_revision':reg['registry_revision'],'sha256':hashlib.sha256(regpath.read_bytes()).hexdigest()},'hidden_entity_ids':[],'ghost_entity_ids':[],'source_camera':{'frame_id':'c_type_world','position':[v['position'][0],-v['position'][2],v['position'][1]],'quaternion':sourceq,'unit':'meter','up_axis':'Z'}})
(O/'owner-view-preset.json').write_text(json.dumps(pose,indent=2)+'\n')
record={'status':'READY_FOR_BROWSER_IMPORT','url':'http://127.0.0.1:5176/','source':source,'proxy':str(F/'interaction_proxy.glb'),'manifest':str(F/'interaction_proxy.manifest.json'),'bindings':str(regpath),'semantic_regions':len(spaces['spaces']),'semantic_verification_states_preserved':True,'old_relationship_graph_imported':False,'view_preset':str(O/'owner-view-preset.json')}
(O/'DEPLOYMENT.json').write_text(json.dumps(record,indent=2)+'\n');print('PACKAGE_V11',m['entity_count'],len(spaces['spaces']))
