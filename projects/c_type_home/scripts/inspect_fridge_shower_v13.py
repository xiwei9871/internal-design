import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/fridge_finish_v13';D.mkdir(exist_ok=True);S=R/'design/mother_hunyuan_v12/WHOLE_HOUSE_MOTHER_HUNYUAN_V12.blend';assert hashlib.sha256(S.read_bytes()).hexdigest()=='da6e5a80dec49831e9d856d0bab90113e87a5ae19316c162d869d7b65a280fd6';bpy.ops.wm.open_mainfile(filepath=str(S))
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();rows=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.hide_render:continue
 if o.name.startswith(('B11_K-FRIDGE-OVERHEAD','R3_SHOWER','R3_WC','R3_VANITY','R3_SLIDING')) or o.name in ['B11_K-TALL-L_UPPER_FRONT_0','VIEW_WALL_W_wall_md_0022','VIEW_WALL_W_wall_md_0050','VIEW_WALL_R3_SOUTH_POCKET_PARTITION','VIEW_WALL_R3_WEST_PARTITION']:
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();rows.append({'name':o.name,'bounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],'materials':[m.name if m else None for m in o.data.materials],'dimensions':list(o.dimensions)})
(D/'INSPECTION.json').write_text(json.dumps(rows,indent=2))
for x in rows:print(x['name'],[[round(v,4) for v in p] for p in x['bounds']],x['materials'])
