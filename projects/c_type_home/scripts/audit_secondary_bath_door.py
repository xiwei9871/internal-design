"""Read-only named wardrobe/secondary-bath sliding-door measurement."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/freezer816_review'
SRC=ROOT/'design/bedrooms_wood_v1/BEDROOMS_WOOD_V3.blend'
assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='93891e0b9c60a9d769e8e65ec4d04d592ea11dee4b9d713966d8b1033b9ebd31'
bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update()
reg=json.loads((ROOT/'design/bedrooms_wood_v1/spatial-canvas.bindings.full.json').read_text())
prefixes=('R3_WARDROBE','R3_FRAME','R3_SPLIT_JAMB','R3_CASING','R3_SLIDER','R3_SLIDING',
 'VIEW_WALL_R3_SOUTH','VIEW_WALL_R3_WEST')
rows=[]
for b in reg['bindings']:
 n=b['native_id']
 if not n.startswith(prefixes):continue
 o=bpy.data.objects[n];cs=[o.matrix_world@v.co for v in o.data.vertices]
 a=[min(v[i] for v in cs) for i in range(3)];c=[max(v[i] for v in cs) for i in range(3)]
 row={'name':n,'entity_id':b['entity_id'],'min':a,'max':c,'size':[c[i]-a[i] for i in range(3)],'properties':{k:str(v) for k,v in o.items()}}
 rows.append(row);print(json.dumps(row))
(R/'SECONDARY_BATH_DOOR_BOUNDED_AUDIT.json').write_text(json.dumps({'source':str(SRC),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'coordinate_frame':'c_type_world','axes':'X east/Y north/Z up','rows':rows},indent=2)+'\n')
