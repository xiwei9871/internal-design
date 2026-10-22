"""Read the already exported real FreeCAD shape data; construct additive partitions."""
import json,hashlib,runpy,shutil
from pathlib import Path
from shapely.geometry import Polygon,MultiPoint,box
from shapely.ops import unary_union
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
FC=ROOT/'cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd'
EXPECTED='d69004b9912eaa6021cb793bee180615d49ef25528bc351033ec450f5de68c8f'
assert hashlib.sha256(FC.read_bytes()).hexdigest()==EXPECTED,'Latest saved FreeCAD changed; inspect again'
raw=json.loads((OUT.parent/'FREECAD_CURRENT_GEOMETRY_RAW.json').read_text())
def xy(v):return [(v[0]-1298172)/1000,(v[1]+296458)/1000]
reg={r['name']:dict(label=r['label'],bounds=[*xy(r['bounds'][:2]),*xy(r['bounds'][2:])],vertices=[xy(v) for v in r['vertices']]) for r in raw['objects']}
west=reg['Rectangle054']['bounds'];south=reg['Rectangle067']['bounds'];guide=reg['Rectangle063']['bounds']
ward=reg['Rectangle066']['bounds'];vanity=reg['Rectangle068']['bounds'];wc=reg['Rectangle061']['bounds']
x0=west[2];x1=south[0];clear0=x0+.025;clear1=x1-.025
yp=(guide[1]+guide[3])/2
# Saved wire is an open screen with a redundant 9.25 mm last endpoint.
# North/east closure follows immutable existing wall inner faces, not a new rectangle.
screen=reg['Wire']['vertices'][:4]
shower=[[screen[0][0],6.4502],screen[1],screen[2],[11.3999,screen[3][1]],[11.3999,6.4502]]
# Latest site-photo clarification: west wall is the complete saved rectangle
# at the yellow line. No offset, door avoidance notch, or inferred conflict.
westpoly=box(*west)
layout=dict(status='AUTHORIZED_AB_REGENERATION_REVIEW',freecad=str(FC),freecad_sha256=EXPECTED,
 coordinate_conversion_mm=dict(x_offset=-1298172,y_offset=296458),source_shapes=reg,
 semantic_mapping={'Rectangle068':'northwest vanity, confirmed by latest user screenshot','Wire':'northeast chamfered shower screen, confirmed by latest user screenshot'},
 shared=dict(vanity=vanity,wc=wc,wardrobe=ward,screen=screen,shower=shower,west_wall=west,supplemental_wall=south),
 opening=dict(gross=[x0,x1],clear=[clear0,clear1],gross_width_mm=(x1-x0)*1000,clear_width_mm=(clear1-clear0)*1000,
              south_y=south[1],north_y=guide[3]+.030,sliding_y=yp,z_floor=.45,z_head=2.55,z_ceiling=3.25),
 sliding=dict(closed=[clear0-.020,clear1+.020],travel=x1-x0,pocket=[x1,10.7779],cavity_y=[guide[1],guide[3]],
              guide_width_is_not_clear_opening=True,full_rail=[clear0-.02,clear1+.02+x1-x0]),
 hinged=dict(hinge=[clear0+.0025,guide[3]+.0515],leaf_width=clear1-clear0-.005,leaf_thickness=.040,angle_degrees=85,opening_limit_reason='West-wall handle clearance; a floor stop limits opening at85 degrees.'),
 review_dimensions={'frame_each_side_mm':25,'door_height_mm':2100,'pocket_north_skin_mm':30,'pocket_cavity_mm':100,'vanity_height_mm':850,'door_profiles':'SCHEMATIC_NOT_SITE_SURVEY'},
 alignment_notes=['Original saved supplementary wall retained as south pocket backing; its north face is extended by 19.125mm to close to the saved 100mm guide cavity.',
 'South closure extends from x10738.125 through the existing stub to east inner wall x11399.9; new finish boxing makes the bathroom-facing surface flush at y4823.0625. Existing walls are retained inside this additive enclosure.',
 'Latest yellow-line site photos override the earlier door-avoidance inference: build the full saved west rectangle without shift or notch; the angled bedroom door remains inherited.',
 'A and B use the same completed south partition outer band for a controlled comparison. B needs no pocket.',
 'Saved shower north wire endpoint y6456.875 overlaps the existing north wall by 6.675mm; retain this frame contact and close tray against y6450.2.',
 '1200x100mm FreeCAD sliding rectangle is recorded exactly as an assembly guide. Actual full rail/parking length follows the normal entrance and leaf travel.'])
(OUT/'LAYOUT_CONTRACT.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n')
base=json.loads((OUT/'BASE_WALLS.json').read_text())
def prism(name,poly,z0=.45,z1=3.25):
 pts=list(poly.exterior.coords)[:-1]
 assert not poly.interiors
 n=len(pts);vs=[[x,y,z] for z in (z0,z1) for x,y in pts]
 # triangulate polygon caps using constrained Delaunay, preserving concavity
 import shapely
 ids={tuple(p):i for i,p in enumerate(pts)};faces=[]
 for tri in shapely.constrained_delaunay_triangles(poly).geoms:
  t=[ids[tuple(p)] for p in list(tri.exterior.coords)[:3]]
  faces.extend([list(reversed(t)),[i+n for i in t]])
 for i in range(n):j=(i+1)%n;faces.extend([[i,j,j+n],[i,j+n,i+n]])
 return dict(name=name,vertices=vs,triangles=faces,footprint=pts)
backend=runpy.run_path(str(OUT/'solid_backend.py'),run_name='backend')
for opt in 'AB':
 parts=[prism('NEW_FC_WEST_PARTITION',westpoly),
        prism('NEW_ENTRY_HEADER',box(x0,south[1],x1,guide[3]+.03),2.55,3.25)]
 if opt=='A':
  parts.extend([prism('FC_SOUTH_WALL_AND_YELLOW_CLOSURE',box(x1,south[1],10.8099,guide[1])),
                prism('POCKET_NORTH_SKIN',box(x1,guide[3],10.8099,guide[3]+.03)),
                prism('POCKET_EAST_CLOSURE_FLUSH_TO_ROOM_EAST_WALL',box(10.7779,south[1],11.3999,guide[3]+.03)),
                prism('POCKET_HEADER',box(x1,guide[1],10.8099,guide[3]),2.57,3.25)])
 else:parts.append(prism('FC_SOUTH_SOLID_WALL_AND_YELLOW_CLOSURE',box(x1,south[1],11.3999,guide[3]+.03)))
 # Keep all approved base meshes active and untouched. Union only the additions;
 # the frozen V5 itself already uses separately closed corner patches.
 data=dict(walls=parts,cuts=[],skin_overlap_m=0)
 p=OUT/f'{opt}_WALL_INPUT.json';p.write_text(json.dumps(data))
 backend['main'](str(p),str(OUT/f'{opt}_UNIFIED_WALL_MESH.json'))
refs=OUT/'references';refs.mkdir(exist_ok=True)
for n,ext in [('cec2437f-e292-4eb2-aaf4-d2f15dbdb7c6','png'),('f4a4ed59-72b9-4a91-aa50-0e9d276600b2','png'),('5c73909c-89d5-48fe-874f-caab028bb19a','png'),('cf9ce4fa-9ef6-4325-90e0-603ab9acde34','png'),('bfcdaaf7-6103-4fd8-bfb1-f6f783eb74f9','png'),('5f307eaa-e314-41c7-bedc-8c926c7ec75b','jpg'),('354c1424-3a6a-4396-9b53-593f25202854','png')]:
 p=Path('/var/folders/ch/yf284jsj7f7_b0tgqkpxhwq00000gn/T')/f'codex-clipboard-{n}.{ext}'
 if p.exists():shutil.copy2(p,refs/p.name)
print(json.dumps(dict(prepare='PASS',opening_mm=layout['opening']['clear_width_mm'],models='additive walls, no frozen shell cuts')))
