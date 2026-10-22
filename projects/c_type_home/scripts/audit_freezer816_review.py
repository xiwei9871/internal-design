"""Bounded native appliance/cabinet audit, no scene rediscovery."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/freezer816_review'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'design/bedrooms_wood_v1/BEDROOMS_WOOD_V3.blend'))
bpy.context.view_layer.update()
reg=json.loads((ROOT/'design/bedrooms_wood_v1/spatial-canvas.bindings.full.json').read_text())
prefixes=('B11_Rectangle039','SUNROOM_EAST_LOW','SUNROOM_EAST_STORAGE',
 'SUNROOM_NORTH_PLANT_LEDGE','NORTH_BALCONY_GLASS','NORTH_BALCONY_FRAME_EAST','V4_GUEST_')
names=[b['native_id'] for b in reg['bindings'] if b['native_id'].startswith(prefixes)]
names+=['VIEW_WALL_W_wall_md_0054','VIEW_WALL_W_wall_md_0055','VIEW_WALL_W_wall_md_0026','VIEW_WALL_W_wall_md_0062']
rows=[]
for n in names:
 o=bpy.data.objects.get(n)
 if not o or o.type!='MESH':continue
 vs=[o.matrix_world@v.co for v in o.data.vertices]
 a=[min(v[i] for v in vs) for i in range(3)];b=[max(v[i] for v in vs) for i in range(3)]
 r={'name':n,'min':a,'max':b,'size':[b[i]-a[i] for i in range(3)],'active':not(o.hide_render or o.hide_viewport)}
 rows.append(r);print(json.dumps(r))
(R/'EXISTING_FREEZER_BOUNDS.json').write_text(json.dumps(rows,indent=2)+'\n')
