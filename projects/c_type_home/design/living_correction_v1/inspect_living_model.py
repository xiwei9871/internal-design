"""Read-only inventory for the living-room correction; writes JSON, no scene edits."""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Vector

out=Path(__file__).resolve().parent
model=Path(sys.argv[sys.argv.index('--')+1]).resolve() if '--' in sys.argv else out.parents[1]/'design/blender_b1_1/B1_1_DESIGN_MODEL_V1.blend'
def bounds(o):
    pts=[o.matrix_world@Vector(p) for p in o.bound_box]
    return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
def item(o):
    return dict(name=o.name,type=o.type,bounds=bounds(o) if o.type=='MESH' else None,
                parent=o.parent.name if o.parent else None,
                collections=[c.name for c in o.users_collection],hide_render=o.hide_render,hide_viewport=o.hide_viewport,
                props={k:o[k] for k in o.keys() if k not in ['_RNA_UI']})
bpy.ops.wm.open_mainfile(filepath=str(model));bpy.context.view_layer.update()
names=[]
for o in bpy.data.objects:
    s=o.name.lower()
    if any(t in s for t in ['bay','w-liv','g-liv','guest','bath','客卫','liv','nbalc','window','wall_md_00']):names.append(item(o))
result=dict(model=str(model),model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),blend_version=bpy.app.version_string,
            object_count=len(bpy.data.objects),collections=[c.name for c in bpy.data.collections],objects=sorted(names,key=lambda x:x['name']))
(out/'LIVING_MODEL_INVENTORY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['model','model_sha256','blend_version','object_count']},ensure_ascii=False))
