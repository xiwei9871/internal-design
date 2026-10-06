import json,hashlib
from pathlib import Path
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006')
base=r/'proxy_handrail_3';out=r/'proxy_l_sofa_4'
m=json.loads((out/'interaction_proxy.manifest.json').read_text());b=json.loads((r/'spatial-canvas.bindings.l-sofa-4.json').read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def link(v):
    if isinstance(v,list):return [link(x) for x in v]
    if isinstance(v,dict):
        d={k:link(x) for k,x in v.items()}
        if d.get('resource_id')==m['source_resource_id']:
            for key,value in [('revision',m['source_revision']),('sha256',m['source_sha256']),('locator',m['source_resource'])]:
                if key in d:d[key]=value
        return d
    return v
for name in ['spatial-canvas.spaces.json','spatial-canvas.project.json']:
    write(out/name,link(json.loads((base/name).read_text())))
g=link(json.loads((base/'spatial-canvas.relationships.json').read_text()));g['revision']='11-l-sofa-review'
for source in g['sources']:
    if source['resource_id']=='spaces_c_type_r4':source.update(sha256=hashlib.sha256((out/'spatial-canvas.spaces.json').read_bytes()).hexdigest(),locator=str(out/'spatial-canvas.spaces.json'))
known={x['entity_id'] for x in b['bindings']}
g['nodes']=[n for n in g['nodes'] if n['kind']!='entity' or n['node_id'] in known]
node_ids={n['node_id'] for n in g['nodes']}
g['edges']=[e for e in g['edges'] if e['from'] in node_ids and e['to'] in node_ids]
changed={'ent_d25c02916e634c6b810c2d13e29a9a62','ent_58cf3a9dc50143578ee3d8cfd272c045'}
for edge in g['edges']:
    if edge['from'] in changed or edge['to'] in changed:
        if edge['type']!='part_of' and edge['verification']['state']!='rejected':edge['verification']={'state':'candidate'}
write(out/'spatial-canvas.relationships.json',g)
m['extensions']['spatial_canvas.review'].update(correction='Packet-selected two-seat retired;three-seat replaced with3300x1800x700mm L sofa;no ottoman;coffee table moved to clear chaise;window chaise and all architecture retained.',sofa_reference_module_widths_m=[1.19,.92,1.19],ottoman_added=False)
write(out/'interaction_proxy.manifest.json',m)
print('PACKAGED',m['source_revision'],m['entity_count'])
