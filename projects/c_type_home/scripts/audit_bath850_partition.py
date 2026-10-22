"""Read only named partition pieces and the current derived wall mesh islands."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/secondary_bath850_review'
reg=json.loads((ROOT/'design/freezer816_review/spatial-canvas.bindings.full.json').read_text())
bpy.ops.wm.open_mainfile(filepath=reg['source_locator']);bpy.context.view_layer.update()
names=['ENTRY_HEADER_ABOVE_RAIL_CHANNEL','ENTRY_HEADER_FRONT_LIP','ENTRY_HEADER_NORTH_LIP',
 'FC_SOUTH_WALL_AND_YELLOW_CLOSURE','POCKET_EAST_CLOSURE_FLUSH_TO_ROOM_EAST_WALL','POCKET_HEADER','POCKET_NORTH_SKIN',
 'VIEW_WALL_R3_SOUTH_POCKET_PARTITION']
def coords(o):return [o.matrix_world@v.co for v in o.data.vertices]
def box(vs):return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
rows=[]
for n in names:
 o=bpy.data.objects.get(n)
 if not o:print('MISSING',n);continue
 r={'name':n,'bounds':box(coords(o)),'active':not(o.hide_render or o.hide_viewport)};rows.append(r);print(json.dumps(r))
 if n=='VIEW_WALL_R3_SOUTH_POCKET_PARTITION':
  vs=coords(o);links={i:set() for i in range(len(vs))}
  for e in o.data.edges:links[e.vertices[0]].add(e.vertices[1]);links[e.vertices[1]].add(e.vertices[0])
  remaining=set(links);islands=[]
  while remaining:
   seed=remaining.pop();stack=[seed];group={seed}
   while stack:
    for i in links[stack.pop()]:
     if i in remaining:remaining.remove(i);group.add(i);stack.append(i)
   islands.append({'bounds':box([vs[i] for i in group]),'vertex_count':len(group),'indices':sorted(group)})
  r['islands']=islands
  for x in islands:print('ISLAND',x['bounds'],x['vertex_count'])
(R/'PARTITION_AUDIT.json').write_text(json.dumps(rows,indent=2)+'\n')
