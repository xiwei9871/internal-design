import json,hashlib
from pathlib import Path
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006');base=r/'proxy_review9';out=r/'proxy_review10'
m=json.loads((out/'interaction_proxy.manifest.json').read_text())
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
g=link(json.loads((base/'spatial-canvas.relationships.json').read_text()));g['revision']='17-long-side-cabinet-chaise-south-review'
for s in g['sources']:
    if s['resource_id']=='spaces_c_type_r4':s.update(sha256=hashlib.sha256((out/'spatial-canvas.spaces.json').read_bytes()).hexdigest(),locator=str(out/'spatial-canvas.spaces.json'))
changed={'ent_311cfcbe5e124d8cb67059ade476d139','ent_75bb7f35c8d251fc9f077f25086e4ca7'}
for e in g['edges']:
    if changed.intersection([e['from'],e['to']]) and e['type'] not in ['part_of','same_component_group'] and e['verification']['state']!='rejected':e['verification']={'state':'candidate'}
write(out/'spatial-canvas.relationships.json',g)
m['extensions']['spatial_canvas.review'].update(correction='Only standaloneLsofa-side cabinet rebuilt1200x350x450mm;original window chaise shifted900mm source south(-Y) without mesh/rotation changes. Balcony/appliances remain unchanged pending layout review.',cabinet_is_custom_dimension_study=True,chaise_south_shift_m=.9,fitness_equipment_fit_verified=False)
write(out/'interaction_proxy.manifest.json',m);print('PACKAGED',m['source_revision'],m['entity_count'])
