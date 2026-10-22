"""Read-only V4 export for true missing-corner audit and identical-view repair."""
import bpy,json,runpy
from pathlib import Path
from mathutils import Matrix,Vector
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];PRIOR=ROOT/'design/wall_junctions_v4'
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='h');sha=H['sha']
m=json.loads((PRIOR/'V4_MANIFEST.json').read_text())
for f,h in m['files_sha256'].items():assert sha(f)==h,f
bpy.ops.wm.open_mainfile(filepath=m['model']);bpy.context.view_layer.update()
register=json.loads((PRIOR/'OPENING_AND_BAY_REGISTER.json').read_text())
excluded=set(register['disabled_source_names'])
names=[n for n in m['wall_sources'] if n not in excluded]
names.extend(o.name for o in bpy.data.collections['COL_V4_COMPLETE_DOORS_AND_BAYS'].objects
             if o.type=='MESH' and any(s.material and s.material.name=='LIVING_REVIEW_WALL' for s in o.material_slots))
cache={}
def authored_world(o):
 if o.name not in cache:
  cache[o.name]=(authored_world(o.parent)@o.matrix_parent_inverse@o.matrix_basis if o.parent else o.matrix_basis.copy())
 return cache[o.name]
rows=[]
for name in dict.fromkeys(names):
 o=bpy.data.objects[name];mat=authored_world(o);vs=[list(mat@v.co) for v in o.data.vertices];o.data.calc_loop_triangles()
 rows.append(dict(name=name,vertices=vs,triangles=[list(t.vertices) for t in o.data.loop_triangles],
                  bounds=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]))
skin=bpy.data.objects['V4_CONTINUOUS_WALL_SHELL'];skin.data.calc_loop_triangles()
actual=dict(name=skin.name,vertices=[list(skin.matrix_world@v.co) for v in skin.data.vertices],triangles=[list(t.vertices) for t in skin.data.loop_triangles])
(OUT/'V4_JUNCTION_REFERENCE.json').write_text(json.dumps(dict(source=m['model'],source_sha256=m['model_sha256'],wall_bands=rows,skin=actual,
      cuts=register['cuts'],intentional_open_regions=[dict(id='CURRENT_STUDY_SOUTH_OPEN',lo=[9.05,4.4,.45],hi=[10.8,4.75,3.25])]),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(read_only_reference='PASS',wall_bands=len(rows),skin_vertices=len(actual['vertices']),intentional_study_opening_preserved=True),ensure_ascii=False))
