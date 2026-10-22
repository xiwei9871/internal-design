import json,math,runpy
from pathlib import Path
from shapely.geometry import Polygon,MultiPoint,Point,box
from shapely.affinity import rotate
from shapely.ops import unary_union
OUT=Path(__file__).resolve().parent
B=runpy.run_path(str(OUT.parent/'secondary_bath_options/r3/solid_backend.py'),run_name='slice_helpers')
for opt in 'AB':
 d=json.loads((OUT/f'R4_{opt}_ACTUAL_GEOMETRY.json').read_text());m=json.loads((OUT/f'R4_OPTION_{opt}_MANIFEST.json').read_text());hinge=m['door']['hinge_m']
 closed=unary_union([MultiPoint([p[:2] for p in r['vertices']]).convex_hull for r in d['door_poses']['0']['moving_meshes']])
 poses=[rotate(closed,-i/8,origin=hinge) for i in range(721)]
 sweep=unary_union(poses)
 walls=[]
 for r in d['wall_meshes']:
  zs=[p[2] for p in r['vertices']];r['minz']=min(zs);r['maxz']=max(zs);walls.append(B['cross_section'](r,1.5))
 walls=unary_union(walls);wall_collision=sweep.intersection(walls).area*1e6
 obstacles={}
 for row in d['other_active_meshes']:
  if row['name'].startswith('R4_') or row['name'].startswith(('FLOOR','SITE_GROUND','CEILING')) or 'FN_' in row['name']:continue
  vs=[p for p in row['vertices'] if .55<p[2]<2.55]
  if not vs:continue
  poly=MultiPoint([p[:2] for p in vs]).convex_hull
  area=sweep.intersection(poly).area
  if area>1e-7:obstacles[row['name']]=area*1e6
 q=json.loads((OUT/f'R4_OPTION_{opt}_QA.json').read_text());q.update(angular_sweep_samples=721,includes_actual_handle_and_stem=True,swing_sector_area_m2=sweep.area,fixture_overlap_mm2=obstacles,wall_overlap_mm2=wall_collision,door_sweep='PASS' if not obstacles and wall_collision<1 else 'REVIEW')
 (OUT/f'R4_OPTION_{opt}_QA.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(option=opt,door_sweep=q['door_sweep'],collisions=obstacles),ensure_ascii=False))
