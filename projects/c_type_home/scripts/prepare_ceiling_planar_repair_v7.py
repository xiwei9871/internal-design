"""Use Shapely 2.1 planar unions/constrained triangulation for ceiling seams."""
import sys,json
from pathlib import Path
# Task-local package fallback; no Blender or user Python environment modified.
sys.path.insert(0,'/tmp/c-type-finish-v7-deps')
from shapely import Polygon,make_valid,unary_union,set_precision,constrained_delaunay_triangles
R=Path(__file__).resolve().parents[1];D=R/'design/pale_ash_review_v7';src=D/'SOURCE_CEILING_GEOMETRY.json';dest=D/'CEILING_PLANAR_REPAIR.json';assert not dest.exists(),'Preserved repair exists'
r=json.loads(src.read_text());groups={}
for n,v in r['ceilings'].items():
 z=min(p[2] for p in v['vertices']);key='low' if z<3 else 'high'
 for f in v['faces']:
  pts=[v['vertices'][i] for i in f]
  if max(p[2] for p in pts)-min(p[2] for p in pts)<.00001 and abs(pts[0][2]-z)<.00001:
   poly=make_valid(Polygon([(p[0],p[1]) for p in pts]))
   if poly.area>1e-8:groups.setdefault(key,[]).append(poly)
raw={k:set_precision(unary_union(g),.0001) for k,g in groups.items()};geoms={}
for k,g in raw.items():
 geoms[k]=set_precision(g.buffer(.101,join_style='mitre').buffer(-.101,join_style='mitre'),.0001)
 parts=list(geoms[k].geoms) if geoms[k].geom_type=='MultiPolygon' else [geoms[k]]
 geoms[k]=unary_union([Polygon(p.exterior,[ring.coords for ring in p.interiors if Polygon(ring).area>.15]) for p in parts])
geoms['low']=geoms['low'].difference(geoms['high'])
data={'policy':'Presentation ceiling repairs only; planar union of existing coverage, close <=202mm panel/wall seams, fill enclosed holes <=0.15m2; preserve 450mm soffit elevation difference. Source authority unchanged.','source_inspection':str(src),'groups':{},'shared_boundary_lines':[]}
for k,g in geoms.items():
 parts=list(g.geoms) if g.geom_type=='MultiPolygon' else [g];tris=[]
 for p in parts:
  for tri in constrained_delaunay_triangles(p).geoms:tris.append(list(tri.exterior.coords)[:3])
 data['groups'][k]={'z':2.8 if k=='low' else 3.25,'thickness':.12,'triangles_xy':tris,'rings_xy':[[list(p.exterior.coords)]+[list(r.coords) for r in p.interiors] for p in parts],'before_area':raw[k].area,'after_area':g.area,'added_area_m2':g.difference(raw[k]).area,'removed_overlap_area_m2':raw[k].difference(g).area,'bounds_before':list(raw[k].bounds),'bounds_after':list(g.bounds)}
shared=geoms['low'].boundary.intersection(geoms['high'].boundary)
for line in ([shared] if shared.geom_type=='LineString' else list(getattr(shared,'geoms',[]))):
 if line.geom_type=='LineString' and line.length>.005:data['shared_boundary_lines'].append(list(line.coords))
dest.write_text(json.dumps(data,indent=2)+'\n');print('PLANAR_REPAIR',str(dest))
