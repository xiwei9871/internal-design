import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];src=R/'design/pale_ash_review_v7/WHOLE_HOUSE_PALE_ASH_DELIVERY_V7.blend';bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
mats={}
for m in bpy.data.materials:
 if not m.use_nodes:continue
 ns=[]
 for n in m.node_tree.nodes:
  if n.type=='BSDF_PRINCIPLED':
   ns.append({'node':n.name,'type':n.type,'sockets':{k:{'value':list(n.inputs[k].default_value) if hasattr(n.inputs[k].default_value,'__len__') else n.inputs[k].default_value,'linked':n.inputs[k].is_linked} for k in ['Base Color','Metallic','Roughness','IOR','Transmission Weight','Alpha']}})
  elif n.type in ['BSDF_GLASS','VOLUME_ABSORPTION','BSDF_TRANSPARENT','MIX_SHADER']:ns.append({'node':n.name,'type':n.type,'inputs':{k.name:str(k.default_value) for k in n.inputs if hasattr(k,'default_value')}})
 if 'glass' in m.name.lower() or any(n['type']!='BSDF_PRINCIPLED' or n.get('sockets',{}).get('Transmission Weight',{}).get('value',0)>.01 for n in ns):mats[m.name]={'nodes':ns,'objects':[]}
for o in s.objects:
 if o.type!='MESH' or o.hide_render:continue
 for idx,m in enumerate(o.data.materials):
  if m and m.name in mats:
   vs=[o.matrix_world@v.co for v in o.data.vertices];mats[m.name]['objects'].append({'name':o.name,'slot':idx,'faces':sum(f.material_index==idx for f in o.data.polygons),'bounds_m':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]})
mats={k:v for k,v in mats.items() if v['objects']}
out=R/'design/glass_privacy_v8';out.mkdir(exist_ok=True);(out/'SOURCE_GLASS_AUDIT.json').write_text(json.dumps({'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'materials':mats},indent=2))
for n,v in mats.items():print(n,'objects',len(v['objects']),'nodes',v['nodes'])
print('DOOR/PARTITION CANDIDATES',[(o['name'],n,[[round(v,3) for v in p] for p in o['bounds_m']]) for n,mat in mats.items() for o in mat['objects'] if any(t in o['name'].upper() for t in ['BALC','DOOR','SHOWER','SLID','GLASS_PANE','G-GB','BATH','SUNROOM','LIVING'])])
