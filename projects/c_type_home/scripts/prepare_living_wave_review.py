import json,math
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006');rows=json.loads((r/'export_step_source.json').read_text())
upper=unary_union([Polygon([p[:2] for p in f]) for f in rows[0]['faces']]);lower=unary_union([Polygon([p[:2] for p in f]) for f in rows[1]['faces']])
y0,y1=4.7,7.8;N=124
tread_run=.35
overall_retraction=1.00
# East is the actual original stair ascent direction. Each marching section has350mm tread depth;
# the whole stair is translated1000mm toward the lower living floor (owner's second500mm trial).
front=[]
for i in range(N+1):
 t=i/N;s=t*t*t*(10-15*t+6*t*t);front.append((6.66-overall_retraction+1.34*s,y0+(y1-y0)*t))
lines=[[(x+tread_run*k,y) for x,y in front] for k in range(5)]
# Terminate tread bodies against the actual south pier inner face (Y4.71510),
# leaving1mm clearance; the conceptual wave path itself retains its exact translation.
bands=[Polygon(lines[k]+list(reversed(lines[k+1]))).intersection(box(3,4.7161,10,y1)) for k in range(4)]
cut=Polygon([(3,y0),(10,y0),(10,y1),(3,y1)])
remaining=upper.difference(cut)
# Retain the whole rear upper floor and extend its front to meet the moved arrival.
# A800mm planar landing strip joins the fourth band to the existing upper slab;
# this fills the small areas outside the former curved footprint without touching remote floors.
back_region=Polygon(lines[4]+[(16.5,y1),(16.5,y0)])
landing=Polygon(lines[4]+list(reversed([(x+.8,y) for x,y in lines[4]])))
new_upper=unary_union([remaining,upper.intersection(cut).intersection(back_region),landing])
# The removed former platform returns to the existing lower level, excluding new raised strips.
removed=upper.difference(new_upper);first_three=unary_union(bands[:3]);floor_fill=removed.difference(unary_union(bands))
new_lower=unary_union([lower,floor_fill])
assert all(p.is_valid for p in bands) and new_upper.is_valid and new_lower.is_valid
assert upper.symmetric_difference(new_upper).difference(cut).area<1e-8
# Fourth walking strip is the full-height arrival surface, with400mm usable run reserved.
# Remove it from the upper slab and model it from lower floor to finished upper height;
# this prevents coplanar overlap at the landing edge.
arrival=bands[3]
new_upper=new_upper.difference(arrival)
shapes=[('FLOOR_LOWER',new_lower,-.1,0),('R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD',new_upper,0,.45)]
for k,poly in enumerate(bands[:3]):shapes.append(('STEP_'+str(k),poly,0,.1125*(k+1)))
shapes.append(('WAVE_STEP_3_ARRIVAL',arrival,0,.450))
def mesh(poly,z0,z1):
 verts=[];faces=[];lookup={}
 def node(p,z):
  key=(round(p[0],7),round(p[1],7),z)
  if key not in lookup:lookup[key]=len(verts);verts.append(key)
  return lookup[key]
 components=[poly] if poly.geom_type=='Polygon' else list(poly.geoms)
 for comp in components:
  if comp.area<1e-10:continue
  for tri in constrained_delaunay_triangles(comp).geoms:
   pts=list(tri.exterior.coords)[:3]
   if (pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0])<0:pts.reverse()
   faces.extend([[node(p,z1) for p in pts],[node(p,z0) for p in reversed(pts)]])
  for ring in [comp.exterior,*comp.interiors]:
   pts=list(ring.coords)[:-1]
   for a,b in zip(pts,pts[1:]+pts[:1]):faces.append([node(a,z0),node(b,z0),node(b,z1),node(a,z1)])
 return {'vertices':verts,'faces':faces,'area_m2':poly.area}
result={'objects':{name:mesh(poly,z0,z1) for name,poly,z0,z1 in shapes},'front_lines':lines,'scope':[3,y0,10,y1],'rise_m':.1125,'tread_run_m':tread_run,'overall_retraction_m':overall_retraction,'additional_living_shift_m':.5,'landing_front_extension_m':.8,'lower_edge_retraction_m':7.2-front[0][0],'reclaimed_lower_floor_m2':floor_fill.area,'upper_nonlocal_delta_m2':upper.symmetric_difference(new_upper).difference(cut).area}
assert result['tread_run_m']==.35
assert result['overall_retraction_m']==1.00
(r/'WAVE_STEP_GEOMETRY.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['objects','front_lines']})
