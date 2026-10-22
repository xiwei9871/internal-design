import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[1];SRC=ROOT/'design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend'
bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update();report=dict(source=str(SRC),sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),objects=[])
for name in ['R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD','FASCIA_PLATFORM_CURVE','STEP_0','STEP_1','STEP_2','FLOOR_LOWER']:
 o=bpy.data.objects[name];me=o.data;vertices=[list(o.matrix_world@v.co) for v in me.vertices];polys=[list(p.vertices) for p in me.polygons];report['objects'].append(dict(name=name,vertices=vertices,polygons=polys,materials=[m.name for m in me.materials],hide_render=o.hide_render))
report['architecture_world_objects']=[dict(name=o.name,type=o.type,loc=list(o.location),dims=list(o.dimensions)) for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and any(k in o.name.upper() for k in ['DOOR','WALL']) and 4.5<o.location.y<8.5]
(OUT/'reports/SOURCE_LOCAL_GEOMETRY.json').write_text(json.dumps(report,ensure_ascii=False)+'\n');print(json.dumps(dict(source_sha256=report['sha256'],mesh_stats=[dict(name=o['name'],verts=len(o['vertices']),faces=len(o['polygons'])) for o in report['objects']])))
