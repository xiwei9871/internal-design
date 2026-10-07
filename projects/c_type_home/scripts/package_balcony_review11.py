import json,hashlib
from pathlib import Path
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006');base=r/'proxy_review10';out=r/'proxy_review11'
m=json.loads((out/'interaction_proxy.manifest.json').read_text());bindings=json.loads((r/'spatial-canvas.bindings.review11.json').read_text())
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
for name in ['spatial-canvas.project.json','spatial-canvas.spaces.json']:write(out/name,link(json.loads((base/name).read_text())))
g=link(json.loads((base/'spatial-canvas.relationships.json').read_text()));g['revision']='18-balcony-sunroom-review'
for s in g['sources']:
    if s['resource_id']=='spaces_c_type_r4':s.update(sha256=hashlib.sha256((out/'spatial-canvas.spaces.json').read_bytes()).hexdigest(),locator=str(out/'spatial-canvas.spaces.json'))
ids={n['node_id'] for n in g['nodes']}
for b in bindings['bindings']:
    if b['entity_id'] not in ids:g['nodes'].append({'node_id':b['entity_id'],'kind':'entity','name':b['native_id'],'native_id':b['native_id'],'resource_id':m['source_resource_id'],'revision':m['source_revision'],'sha256':m['source_sha256']})
write(out/'spatial-canvas.relationships.json',g)
m['extensions']['spatial_canvas.review'].update(correction='Sunroom first layout study:original1200x600x850 chest freezer rotated to east open-top cabinet bay;original stack laundry moved southwest;1500mm south seat;300mm north plant ledge. No utility or manufacturer compliance claims. Prior living furniture unchanged.',freezer_not_built_in_certified=True,utilities_verified=False)
write(out/'interaction_proxy.manifest.json',m);print('PACKAGED',m['source_revision'],m['entity_count'])
