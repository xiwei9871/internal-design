"""Inspect supplier OBJ in isolation; save editable data for asset assessment."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design/asset_model_v3';ASSET=OUT/'assets/fly_sc2/3D_Fly_SC2/3D_Fly_SC2/obj/SC2_medium.obj'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(ASSET))
rows=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 me=o.data;adj=[[] for v in me.vertices]
 for e in me.edges:a,b=e.vertices;adj[a].append(b);adj[b].append(a)
 seen=set();parts=[]
 for start in range(len(adj)):
  if start in seen:continue
  queue=[start];seen.add(start);ids=[]
  while queue:
   a=queue.pop();ids.append(a)
   for b in adj[a]:
    if b not in seen:seen.add(b);queue.append(b)
  points=[o.matrix_world@me.vertices[i].co for i in ids]
  parts.append({'indices':ids,'vertices':len(ids),'bounds':[[min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]]})
 rows.append({'object':o.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'materials':[m.name for m in me.materials],'uv_layers':[u.name for u in me.uv_layers],'parts':parts})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SUPPLIER_FLY_SC2_INSPECT.blend'))
(OUT/'SUPPLIER_COMPONENTS.json').write_text(json.dumps(rows,indent=2))
print('SUPPLIER_INSPECT',json.dumps([{**{k:v for k,v in o.items() if k!='parts'},'parts':[{k:v for k,v in p.items() if k!='indices'} for p in o['parts']]} for o in rows]))
