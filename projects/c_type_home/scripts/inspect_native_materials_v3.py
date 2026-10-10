"""Read supplier native shader graphs and record their physical baseline."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/asset_model_v3'
reports=[]
for id in ['linen','ash']:
 path=OUT/'assets'/f'{id}_native_1k'/('rough_linen_1k.blend' if id=='linen' else 'ash_veneer_1k.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path))
 row={'asset':id,'materials':[]}
 for m in bpy.data.materials:
  if not m.use_nodes:continue
  nodes=[]
  for n in m.node_tree.nodes:
   inputs={}
   for s in n.inputs:
    if hasattr(s,'default_value'):
     v=s.default_value
     inputs[s.name]={'value':list(v) if hasattr(v,'__len__') and not isinstance(v,str) else v,'linked':s.is_linked}
   nodes.append({'type':n.type,'name':n.name,'inputs':inputs,'image':n.image.filepath if n.type=='TEX_IMAGE' and n.image else None})
  row['materials'].append({'name':m.name,'nodes':nodes,'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]})
 reports.append(row)
(OUT/'NATIVE_MATERIAL_NODES.json').write_text(json.dumps(reports,indent=2))
for r in reports:
 for m in r['materials']:
  print('NATIVE',r['asset'],m['name'],[(n['type'],n['name'],{k:v for k,v in n['inputs'].items() if k in ['Scale','IOR','Sheen Weight','Specular IOR Level','Vector','Strength','Midlevel']},n['image']) for n in m['nodes']])
