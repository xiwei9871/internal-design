"""Build a true closed upper floor and remove legacy angled-door cap overlap."""
import json
from pathlib import Path
import shapely
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
OUT=Path(__file__).resolve().parent
d=json.loads((OUT/'THRESHOLD_ACTUAL_GEOMETRY_DEBUG.json').read_text())
floor=next(r for r in d if r['name']=='FLOOR_UPPER')
# Full top-face export is supplied by Blender; the local debug is not enough
# to rebuild any remote floor, so do not infer that geometry from room bounds.
raw=json.loads((OUT/'UPPER_FLOOR_FULL_SOURCE.json').read_text())
shapes=[];invalid=[]
for f in raw['faces']:
 if not f['normal'][2]>.9:continue
 if max(abs(p[2]-.45) for p in f['vertices'])>1e-5:continue
 poly=Polygon([p[:2] for p in f['vertices']])
 if not poly.is_valid:invalid.append(dict(index=f['index'],reason=shapely.is_valid_reason(poly)))
 valid=shapely.make_valid(poly)
 if valid.geom_type=='Polygon':shapes.append(valid)
 elif hasattr(valid,'geoms'):shapes.extend(p for p in valid.geoms if p.geom_type=='Polygon')
original=shapely.set_precision(unary_union(shapes),.000001)
local=box(7.7999,4.4499,9.209,5.1502)
corrected=shapely.set_precision(unary_union([original,local]),.000001)
assert corrected.is_valid
delta=corrected.symmetric_difference(original);nonlocal_area=delta.difference(local.buffer(.000002)).area
assert nonlocal_area<1e-8,nonlocal_area
verts=[];faces=[];lookup={};component=0
def node(p,z):
 coords=(round(float(p[0]),6),round(float(p[1]),6),z);k=(component,*coords)
 # Remote rooms already consist of slabs that meet at isolated plan points.
 # Keep those distinct closed components, rather than welding a4-face edge.
 if k not in lookup:lookup[k]=len(verts);verts.append(list(coords))
 return lookup[k]
polygons=[corrected] if corrected.geom_type=='Polygon' else list(corrected.geoms)
for component,poly in enumerate(polygons):
 for t in shapely.constrained_delaunay_triangles(poly).geoms:
  pts=list(t.exterior.coords)[:3]
  area=(pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0])
  if area<0:pts.reverse()
  faces.append([node(p,0) for p in reversed(pts)]);faces.append([node(p,.45) for p in pts])
 for ring in [poly.exterior,*poly.interiors]:
  pts=list(ring.coords)[:-1]
  for a,b in zip(pts,pts[1:]+pts[:1]):faces.append([node(a,0),node(b,0),node(b,.45),node(a,.45)])
out=dict(vertices=verts,faces=faces,source='FLOOR_UPPER actual world mesh top faces',repair_scope_m=[7.7999,4.4499,9.209,5.1502],floor_top_m=.45,bottom_m=0,invalid_source_top_faces=invalid,nonlocal_plan_delta_m2=nonlocal_area,filled_area_m2=delta.area,original_top_footprint=original.__geo_interface__,corrected_top_footprint=corrected.__geo_interface__)
(OUT/'CORRECTED_UPPER_FLOOR_MESH.json').write_text(json.dumps(out,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['vertices','faces','original_top_footprint','corrected_top_footprint']},ensure_ascii=False))
