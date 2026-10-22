"""Read only the named bedroom furniture and registered local wall parts."""
import bpy, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design/bedrooms_wood_v1'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'design/study_room_v1/STUDY_ROOM_DAYBED_V1.blend'))
bpy.context.view_layer.update()
reg=json.loads((ROOT/'design/study_room_v1/spatial-canvas.bindings.full.json').read_text())
prefixes=('B11_Rectangle011','B11_Rectangle012','B11_Rectangle013','B11_Rectangle014',
 'B11_Rectangle015','B11_Rectangle017','B11_Rectangle022','B11_Rectangle023',
 'B11_Rectangle045','B11_Rectangle051','B11_Rectangle052','B11_Circle009','R3_WARDROBE',
 'R4_BEDROOM_DOOR','V4_D-MB','V4_D-SMB','V4_D-GUEST-ROOM','V4_GUEST_',
 'V4_W-MB','V4_W-SMB')
def bounds(o):
 c=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [[min(v[i] for v in c) for i in range(3)],[max(v[i] for v in c) for i in range(3)]]
names=[b['native_id'] for b in reg['bindings'] if b['native_id'].startswith(prefixes)]
idx=json.loads(Path('/Users/xiwei/interior_design/projects/c_type_home/design/wall_identity_r4_review/WALL_PART_INDEX.json').read_text())
zones={'mother':(11.55,15.35,.0,4.60),'couple':(7.95,11.45,.0,4.60),'guest':(9.75,13.05,7.85,10.95)}
wallgroups={}
for zone,(x0,x1,y0,y1) in zones.items():
 wallgroups[zone]=[r['native_id'] for r in idx['parts'] if r['world_bounds'][1][0]>x0 and r['world_bounds'][0][0]<x1 and r['world_bounds'][1][1]>y0 and r['world_bounds'][0][1]<y1]
names+=sum(wallgroups.values(),[])
rows=[]
for n in sorted(set(names)):
 o=bpy.data.objects.get(n)
 if o:rows.append({'name':n,'bounds':bounds(o),'active':not(o.hide_render or o.hide_viewport),'type':o.type,'parent':o.parent.name if o.parent else None})
d={'rows':rows,'wall_groups':wallgroups,'frame':'c_type_world','unit':'meter'}
(OUT/'EXISTING_BOUNDED_AUDIT.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
for r in rows:
 if not r['name'].startswith('VIEW_WALL_'):print(json.dumps(r,ensure_ascii=False))
print('BEDROOM_AUDIT',len(rows),str(OUT))
