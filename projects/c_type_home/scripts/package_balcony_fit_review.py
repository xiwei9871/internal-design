"""Relink exact derived revision; retain unmodified evidence and downgrade changed stair/region claims."""
import json,hashlib
from pathlib import Path
root=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006')
out=root/'proxy_aluminum_fit_2'
base=root/'proxy_wave35_aluminum'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(out/'interaction_proxy.manifest.json')
rid=manifest['source_resource_id'];rev=manifest['source_revision'];digest=manifest['source_sha256'];locator=manifest['source_resource']
oldsha=read(base/'interaction_proxy.manifest.json')['source_sha256']
def relink(v):
    if isinstance(v,list):return [relink(x) for x in v]
    if isinstance(v,dict):
        result={k:relink(x) for k,x in v.items()}
        if result.get('resource_id')==rid:
            if 'revision' in result:result['revision']=rev
            if 'sha256' in result:result['sha256']=digest
            if 'locator' in result:result['locator']=locator
        return result
    return v
project=relink(read(base/'spatial-canvas.project.json'))
spaces=relink(read(base/'spatial-canvas.spaces.json'))
spaces['registry_revision']='12-wave35-second-retreat-review'
for space in spaces['spaces']:
    if space['space_id']=='space_lounge' or 'stair' in space['space_id'].lower():
        space['verification']={'state':'candidate'}
        if 'provenance' in space:
            space['provenance']['evidence']+=' Changed by four-step review; prior footprint/transition is no longer verified and needs owner review.'
write(out/'spatial-canvas.spaces.json',spaces)
graph=relink(read(base/'spatial-canvas.relationships.json'))
graph['revision']='9-wave35-second-retreat-review'
for source in graph['sources']:
    if source['resource_id']==spaces['registry_id']:
        source.update(revision=spaces['registry_revision'],sha256=sha(out/'spatial-canvas.spaces.json'),locator=str(out/'spatial-canvas.spaces.json'))
bindings=read(root/'spatial-canvas.bindings.aluminum-fit-2.json')
known={b['entity_id']:b for b in bindings['bindings']}
graph['nodes']=[n for n in graph['nodes'] if n['kind']!='entity' or n['node_id'] in known]
node_ids={n['node_id'] for n in graph['nodes']}
for gid,b in known.items():
    if b['native_id'].startswith(('NORTH_BALCONY_','WAVE_STEP_')) and gid not in node_ids:
        graph['nodes'].append({'node_id':gid,'kind':'entity','name':b['native_id'],'resource_id':rid,'native_id':b['native_id'],'revision':rev,'sha256':digest})
node_ids={n['node_id'] for n in graph['nodes']}
graph['edges']=[e for e in graph['edges'] if e['from'] in node_ids and e['to'] in node_ids]
step_ids={gid for gid,b in known.items() if b['native_id'].startswith(('STEP_','WAVE_STEP_'))}
for edge in graph['edges']:
    if edge['from'] in step_ids or edge['to'] in step_ids or 'cmp_stair' in [edge['from'],edge['to']] or 'space_lounge' in [edge['from'],edge['to']]:
        if edge['verification']['state']!='rejected':edge['verification']={'state':'candidate'}
write(out/'spatial-canvas.relationships.json',graph)
write(out/'spatial-canvas.project.json',project)
print('PACKAGED',rev,digest)
