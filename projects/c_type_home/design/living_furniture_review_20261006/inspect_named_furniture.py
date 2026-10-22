import bpy,sys,json
from pathlib import Path
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import bounds
names=['B11_Circle_CATALOG_00_00','B11_Rectangle047_CATALOG_00_00','B11_Rectangle048_CATALOG_00_00','B11_Rectangle046_CATALOG_00_00','B11_Rectangle049_CATALOG_00_00']
rows=[]
for name in names:
 o=bpy.data.objects[name];root=o.parent or o
 high=[o.matrix_world@v.co for v in o.data.vertices if (o.matrix_world@v.co).z>.65]
 rows.append({'name':name,'parent':o.parent.name if o.parent else None,'root':root.name,'assembly':[(c.name,c.type,c.visible_get(),c.hide_render) for c in [root,*root.children_recursive]],'bounds':bounds(o),'matrix':[list(v) for v in o.matrix_world],'rotation':list(o.rotation_euler),'scale':list(o.scale),'properties':dict(o.items()),'high_bounds':[[min(v[i] for v in high) for i in range(3)],[max(v[i] for v in high) for i in range(3)]] if high else None})
Path(__file__).with_suffix('.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2,default=str));print(json.dumps(rows,ensure_ascii=False,default=str))
