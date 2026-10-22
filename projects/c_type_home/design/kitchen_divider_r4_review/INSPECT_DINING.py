import bpy,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import bounds
names=['B11_Circle010_CATALOG_00_00','B11_Circle011_CATALOG_00_00','B11_Circle012_CATALOG_00_00','B11_Circle013_CATALOG_00_00']
registry=json.loads((Path(__file__).parent/'spatial-canvas.bindings.thinner-raised.json').read_text())
names += [x['native_id'] for x in registry['bindings'] if 'CATALOG' in x['native_id'] and 'Rectangle' in x['native_id']]
records=[]
for n in names:
 o=bpy.data.objects.get(n)
 if not o:continue
 rec={'name':n,'bounds':bounds(o),'parent':o.parent.name if o.parent else None,'children':[c.name for c in o.children_recursive],'matrix':[list(r) for r in o.matrix_world],'properties':dict(o.items())}
 if 'Circle01' in n:rec['local_bounds']=[list(v) for v in o.bound_box];rec['materials']=[m.name if m else None for m in o.data.materials];rec['vertices']=len(o.data.vertices)
 records.append(rec)
p=Path(__file__).parent/'DINING_INSPECTION.json';p.write_text(json.dumps(records,ensure_ascii=False,default=str,indent=2));print(json.dumps(records,ensure_ascii=False,default=str))
