"""Read evaluated latest whole-house geometry, preserving source visibility records."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/whole_house_model_v1'
SOURCES={'lookdev':ROOT/'design/lookdev_v5/LIVING_DINING_LOOKDEV_V5.blend','stepped':ROOT/'design/sunroom_stepped_storage_v1/SUNROOM_STEPPED_STORAGE_V1.blend'}
all_records={}
for key,path in SOURCES.items():
 bpy.ops.wm.open_mainfile(filepath=str(path));vis={o.name:{'hidden':o.hide_render,'viewport_hidden':o.hide_viewport,'collection_hidden':any(c.hide_render for c in o.users_collection)} for o in bpy.data.objects}
 for c in bpy.data.collections:c.hide_viewport=False
 for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();records=[]
 for o in bpy.data.objects:
  if o.type not in ['MESH','CURVE']:continue
  e=o.evaluated_get(dg);me=e.to_mesh()
  if not me.vertices:e.to_mesh_clear();continue
  pts=[e.matrix_world@v.co for v in me.vertices]
  records.append({'name':o.name,'type':o.type,'bounds':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],'matrix':[list(row) for row in o.matrix_world],'materials':[m.name if m else None for m in o.data.materials],'collections':[c.name for c in o.users_collection],**vis[o.name]});e.to_mesh_clear()
 all_records[key]=records
(OUT/'ACTUAL_SOURCE_INVENTORY.json').write_text(json.dumps(all_records,indent=2)+'\n');print('SOURCE_INVENTORY', {k:len(v) for k,v in all_records.items()})
