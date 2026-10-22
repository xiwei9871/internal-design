"""Exact known kitchen parts read-only audit from current derivative."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/asset_model_v3'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'design/appearance_match_v2/LIVING_DINING_APPEARANCE_V2.blend'))
rows=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH' or not o.name.startswith(('B11_K-','LD_Chaise_back_pad')):continue
 points=[o.matrix_world@Vector(v) for v in o.bound_box]
 rows.append({'name':o.name,'hidden':o.hide_render,'bounds':[[min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]],'materials':[m.name for m in o.data.materials]})
(OUT/'KITCHEN_PARTS_BASELINE.json').write_text(json.dumps(rows,indent=2))
print('KITCHEN_READ_ONLY_COUNT',len(rows))
for r in rows:
 if 'COOK' in r['name'] or 'SINK' in r['name'] or 'COUNTER' in r['name']:print(json.dumps(r))
