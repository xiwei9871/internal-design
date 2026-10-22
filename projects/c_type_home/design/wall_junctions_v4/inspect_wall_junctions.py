"""Read-only active structural-wall inventory for global wall-joint repair."""
import bpy,bmesh,json,runpy
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
SOURCE=ROOT/'design/living_correction_v3/B1_LIVING_CORRECTED_V3.blend'
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='freeze_helpers')
H['b0_check']();m=json.loads((ROOT/'design/living_correction_v3/V3_MANIFEST.json').read_text())
for p,h in m['files_sha256'].items():assert H['sha'](p)==h,p
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update()
rows=[]
def structural(o):
    if o.type!='MESH' or o.hide_render or o.hide_viewport:return False
    if o.name.startswith('W_wall_'):return True
    mats={s.material.name for s in o.material_slots if s.material}
    return bool(mats & {'LIVING_REVIEW_WALL','SITE_REVIEW_CONTINUOUS_WALL'})
for o in bpy.data.objects:
    if not structural(o):continue
    coords=[list(o.matrix_world@v.co) for v in o.data.vertices]
    bm=bmesh.new();bm.from_mesh(o.data);boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free()
    rows.append(dict(name=o.name,vertices=coords,faces=[list(p.vertices) for p in o.data.polygons],
                     bounds=[[min(p[i] for p in coords) for i in range(3)],[max(p[i] for p in coords) for i in range(3)]],
                     materials=[s.material.name if s.material else None for s in o.material_slots],
                     color=list(o.color),boundary_edges=boundary,nonmanifold_edges=nonmanifold,
                     collection=[c.name for c in o.users_collection],protected=bool(o.get('kitchen_freeze_version'))))
result=dict(source=str(SOURCE),source_sha256=H['sha'](SOURCE),active_wall_meshes=len(rows),walls=rows)
(OUT/'ACTIVE_WALL_INVENTORY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(active_wall_meshes=len(rows),nonmanifold_sources=[r['name'] for r in rows if r['nonmanifold_edges']],
                     protected_wall_meshes=[r['name'] for r in rows if r['protected']],source_sha256=result['source_sha256']),ensure_ascii=False))
