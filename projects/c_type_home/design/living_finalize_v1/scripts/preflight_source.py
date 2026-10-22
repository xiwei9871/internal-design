import bpy,json,hashlib,sys,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[1];SRC=ROOT/'design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend'
bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update()
report=dict(source=str(SRC),source_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),object_count=len(bpy.data.objects),collection_count=len(bpy.data.collections),blender=bpy.app.version_string,ceilings=[],floor_objects=[],device={})
for o in bpy.data.objects:
 if o.type!='MESH':continue
 if 'CEILING' in o.name.upper():report['ceilings'].append(dict(name=o.name,hide_render=o.hide_render,hide_viewport=o.hide_viewport,loc=list(o.location),dims=list(o.dimensions),collections=[c.name for c in o.users_collection]))
 if 'FLOOR' in o.name.upper() and not o.hide_render:report['floor_objects'].append(dict(name=o.name,collections=[c.name for c in o.users_collection]))
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices();report['device']=dict(backend='METAL',devices=[dict(name=d.name,type=d.type) for d in pref.devices])
except Exception as e:report['device']=dict(backend='CPU',reason=str(e))
# Read floor geometry at actual exposed top surface, excluding inherited movable furniture/fixtures.
for o in bpy.data.objects:
 if any(c.name in ['COL_B11_CORE_FURNITURE','COL_B11_BATHROOMS','COL_B11_APPLIANCES','COL_B11_REVIEW_MARKERS','05_HUMAN_DESIGN_GUIDE'] for c in o.users_collection):o.hide_render=True;o.hide_set(True)
for obj in bpy.data.objects:
 if obj.hide_render:obj.hide_set(True)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
# Grid samples are reusable layout evidence, not any geometry change.
grid=[]
for ix in range(111):
 x=2.9+ix*.05
 for iy in range(171):
  y=5.45+iy*.05;hit=bpy.context.scene.ray_cast(dg,Vector([x,y,1.20]),Vector([0,0,-1]),distance=2)
  if hit[0]:grid.append([round(x,3),round(y,3),round(hit[1].z,4),hit[4].name])
(OUT/'reports/SOURCE_PREFLIGHT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(OUT/'reports/FLOOR_GRID.json').write_text(json.dumps(dict(step=.05,grid=grid),ensure_ascii=False)+'\n');print(json.dumps(dict(preflight='PASS',device=report['device'],ceilings=report['ceilings'],floors=report['floor_objects'],grid_samples=len(grid)),ensure_ascii=False))
