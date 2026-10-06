import json,hashlib
from pathlib import Path
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
base=r/'proxy';out=r/'proxy_review6'
m=json.loads((out/'interaction_proxy.manifest.json').read_text())
bindings=json.loads((r/'spatial-canvas.bindings.review6.json').read_text())
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
graph=link(json.loads((base/'spatial-canvas.relationships.json').read_text()));graph['revision']='13-bookcase-short-rail-review'
for s in graph['sources']:
    if s['resource_id']=='spaces_c_type_r4':s.update(sha256=hashlib.sha256((out/'spatial-canvas.spaces.json').read_bytes()).hexdigest(),locator=str(out/'spatial-canvas.spaces.json'))
write(out/'spatial-canvas.relationships.json',graph)
m['extensions']['spatial_canvas.review'].update(correction='Only existing bookshelf assembly moved to packet-selectedG-DIN-LIV glass partition;25cm freestanding offset to clear grip. Existing rail shortened to90cm projected span,10cm ends;other geometry/bench/fitness unchanged.',handrail_horizontal_span_m=.9,handrail_ends_m=.1)
write(out/'interaction_proxy.manifest.json',m)
print('PACKAGED',m['source_revision'],m['entity_count'])
