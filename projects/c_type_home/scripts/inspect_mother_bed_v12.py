import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/mother_hunyuan_v12';D.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'design/finishes_v11/WHOLE_HOUSE_FINISHES_READING_V11.blend'))
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();rows=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.hide_render:continue
 if o.name=='HUNYUAN_V3_COUPLE_BED' or any(x in o.name.upper() for x in ['MOTHER','RECTANGLE012']):
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear()
  rows.append({'name':o.name,'bounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],'matrix':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None,'collections':[c.name for c in o.users_collection],'materials':[m.name if m else None for m in o.data.materials]})
(D/'INSPECTION.json').write_text(json.dumps(rows,indent=2))
for x in rows:print(x['name'],[[round(v,4) for v in p] for p in x['bounds']])
