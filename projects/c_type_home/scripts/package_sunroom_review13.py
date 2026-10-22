import json
import hashlib
from pathlib import Path

r = Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
base = r / 'proxy_review12'
out = r / 'proxy_review13'
m = json.loads((out / 'interaction_proxy.manifest.json').read_text())
registry = json.loads((r / 'spatial-canvas.bindings.review13.json').read_text())

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def link(value):
    if isinstance(value, list):
        return [link(x) for x in value]
    if isinstance(value, dict):
        d = {k: link(x) for k, x in value.items()}
        if d.get('resource_id') == m['source_resource_id']:
            for k, x in [('revision', m['source_revision']), ('sha256', m['source_sha256']), ('locator', m['source_resource'])]:
                if k in d:
                    d[k] = x
        return d
    return value

for name in ['spatial-canvas.project.json', 'spatial-canvas.spaces.json']:
    write(out / name, link(json.loads((base / name).read_text())))

g = link(json.loads((base / 'spatial-canvas.relationships.json').read_text()))
g['revision'] = '20-sunroom-cabinet-freezer-swap-review'
for s in g['sources']:
    if s['resource_id'] == 'spaces_c_type_r4':
        s.update(sha256=hashlib.sha256((out / 'spatial-canvas.spaces.json').read_bytes()).hexdigest(), locator=str(out / 'spatial-canvas.spaces.json'))

known = {b['entity_id']: b for b in registry['bindings']}
g['nodes'] = [n for n in g['nodes'] if n['kind'] != 'entity' or n['node_id'] in known]
ids = {n['node_id'] for n in g['nodes']}
g['edges'] = [e for e in g['edges'] if e['from'] in ids and e['to'] in ids]
for gid, b in known.items():
    if gid not in ids:
        g['nodes'].append({'node_id': gid, 'kind': 'entity', 'name': b['native_id'], 'native_id': b['native_id'], 'resource_id': m['source_resource_id'], 'revision': m['source_revision'], 'sha256': m['source_sha256']})
write(out / 'spatial-canvas.relationships.json', g)

m['extensions']['spatial_canvas.review'].update(
    correction='Swap chest freezer and adjacent low cabinet; remove every freezer top cover and hinge; add 700x200x2300mm shallow sliding-front high cabinet behind compact sofa; shorten north plant ledge for freezer clear lid zone.',
    freezer_top_clear=True,
    freezer_countertop_fixed=False,
    freezer_and_low_cabinet_swapped=True,
    sofa_rear_high_cabinet=True,
    manufacturer_lid_sweep_verified=False,
    utilities_verified=False,
)
write(out / 'interaction_proxy.manifest.json', m)
print('PACKAGED', m['source_revision'], m['entity_count'])
