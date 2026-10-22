import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/platform_bath_fitness_v14';a=json.loads((D/'BUILD_AUDIT.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['output'])
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
for o in bpy.context.scene.objects:
 if o.name not in a['new_objects'] or o.type not in ['MESH','CURVE']:continue
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear()
 if vs:print(o.name,[[round(min(v[i] for v in vs),4) for i in range(3)],[round(max(v[i] for v in vs),4) for i in range(3)]], 'parent',o.parent.name if o.parent else None)

