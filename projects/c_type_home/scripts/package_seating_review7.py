import json,hashlib
from pathlib import Path
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006');base=r/'proxy_review6';out=r/'proxy_review7'
m=json.loads((out/'interaction_proxy.manifest.json').read_text())
qa=json.loads((r/'SEATING_SOUTH_REVIEW7_QA.json').read_text())
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
    write(out/name,link(json.loads((base/name).read_text())))
g=link(json.loads((base/'spatial-canvas.relationships.json').read_text()));g['revision']='14-seating-south-1m-review'
for source in g['sources']:
    if source['resource_id']=='spaces_c_type_r4':source.update(sha256=hashlib.sha256((out/'spatial-canvas.spaces.json').read_bytes()).hexdigest(),locator=str(out/'spatial-canvas.spaces.json'))
changed=set(qa['selected_native_global_ids'].values())
for edge in g['edges']:
    if edge['from'] in changed or edge['to'] in changed:
        if edge['type'] not in ['part_of','same_component_group'] and edge['verification']['state']!='rejected':edge['verification']={'state':'candidate'}
write(out/'spatial-canvas.relationships.json',g)
m['extensions']['spatial_canvas.review'].update(correction='Only packet-selectedLsofa,round side table and coffee table rigidly translated1m source south(-Y);no other geometry/fitness-outline changes.',translation_source_xyz_m=[0,-1,0],translation_proxy_xyz_m=[0,0,1])
write(out/'interaction_proxy.manifest.json',m)
print('PACKAGED',m['source_revision'],m['entity_count'])
