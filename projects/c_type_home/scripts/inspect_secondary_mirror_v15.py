import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/secondary_mirror_v15';D.mkdir(exist_ok=True);S=R/'design/platform_bath_fitness_v14/WHOLE_HOUSE_PLATFORM_BATH_FITNESS_FINAL_V14.blend';assert hashlib.sha256(S.read_bytes()).hexdigest()=='0ef86d31de4ab8afb4befcb6ac639054c955e970f85bd4007f04dc3252055144';bpy.ops.wm.open_mainfile(filepath=str(S))
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();rows=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.hide_render:continue
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear()
 if not vs:continue
 b=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
 if b[1][0]<9.2 or b[0][0]>11.42 or b[1][1]<5.88 or b[0][1]>6.49 or b[1][2]<.5:continue
 rows.append({'name':o.name,'bounds':b,'materials':[m.name if m else None for m in o.data.materials],'parent':o.parent.name if o.parent else None})
(D/'INSPECTION.json').write_text(json.dumps(rows,indent=2));print('\n'.join(str((x['name'],[[round(v,4) for v in p] for p in x['bounds']])) for x in rows))

