"""Remove the added D107 enclosure from the baked wall skin, with exact provenance."""
import json,runpy
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
source=ROOT/'design/wall_junctions_v4/WALL_SOLID_INPUTS.json'
d=json.loads(source.read_text());removed=[w for w in d['walls'] if 'D107' in w['name']]
kept=[w for w in d['walls'] if 'D107' not in w['name']]
# Restore the original pre-enclosure white west band. This source object was
# hidden when the angled surround was built; no black CAD wall is removed.
inv=json.loads((OUT/'BASE_INSPECTION.json').read_text());r=next(r for r in inv if r['name']=='W_wall_md_0018')
lo,hi=r['lo'],r['hi'];a,b,z0=lo;x,y,z1=hi
vs=[[a,b,z0],[x,b,z0],[x,y,z0],[a,y,z0],[a,b,z1],[x,b,z1],[x,y,z1],[a,y,z1]]
tris=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]
# Apply the same <=0.21mm axis snap and50micron corner overlap as V4.
cent=[(lo[i]+hi[i])/2 for i in range(2)]
for p in vs:
 for i in range(3):
  q=round(p[i]*1000)/1000
  if abs(q-p[i])<=.00021:p[i]=q
 for i in range(2):p[i]+=.00005 if p[i]>cent[i] else -.00005
kept.append(dict(name='RESTORED_PRE_D107_W_wall_md_0018',vertices=vs,triangles=tris))
# Keep the original height arrangement even after removing the door operands.
# Otherwise different slice fractions change remote thin cap triangulations.
levels=json.loads((ROOT/'design/wall_junctions_v4/CONTINUOUS_WALL_MESH.json').read_text())['levels']
kept.append(dict(name='NON_GEOMETRIC_ORIGINAL_HEIGHT_LEVELS',vertices=[[0,0,z] for z in levels],triangles=[]))
inp=OUT/'HOUSE_ROLLBACK_WALL_INPUT.json';inp.write_text(json.dumps(dict(walls=kept,cuts=d['cuts'])))
backend=runpy.run_path(str(ROOT/'design/wall_junctions_v4/solid_wall_backend.py'),run_name='rollback_backend')
backend['main'](str(inp),str(OUT/'HOUSE_ROLLBACK_WALL_MESH.json'))
reg=dict(status='USER_AUTHORIZED_MODEL_ROLLBACK_NOT_SITE_DEMOLITION',source_wall_input=str(source),removed_added_wall_sources=[w['name'] for w in removed],restored_original_white_wall='W_wall_md_0018',kept_original_wall_operands=len(kept)-1,black_original_wall_removed_count=0,original_opening_cuts_retained=d['cuts'],scope='Remove later-added angled leaf/frame/casing/header/returns; restore pre-enclosure open state before new FreeCAD west wall',reference='codex-clipboard-6d949081-6927-4f07-9b5b-5d9ec6ff0d9a.png')
(OUT/'D107_ROLLBACK_REGISTER.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(rollback_prepared='PASS',removed_added_wall_operands=len(removed),original_black_walls_removed=0)))
