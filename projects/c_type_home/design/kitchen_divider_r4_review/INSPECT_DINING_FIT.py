import bpy,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import bounds
for i in range(10,14):
 o=bpy.data.objects[f'B11_Circle{i:03d}_CATALOG_00_00'];v=[o.matrix_world@x.co for x in o.data.vertices]
 high=[p for p in v if p.z>.73];seat=[p for p in v if .35<p.z<.6]
 b=lambda pts:[[min(p[j] for p in pts) for j in range(3)],[max(p[j] for p in pts) for j in range(3)]]
 print(json.dumps({'chair':o.name,'high_bounds':b(high),'seat_bounds':b(seat),'parent':o.parent.name,'assembly':[(c.name,c.type,c.hide_render) for c in o.parent.children_recursive]}))
o=bpy.data.objects['B11_Rectangle050_CATALOG_00_00'];print('TABLE',o.name,'descendants',[(c.name,c.type) for c in o.parent.children_recursive]);print('table_z_levels',sorted(set(round(v.co.z,4) for v in o.data.vertices)))
