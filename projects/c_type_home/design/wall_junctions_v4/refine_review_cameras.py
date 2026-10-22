"""Adjust only the four occluded review cameras; preserve all authored geometry."""
import bpy,json,runpy
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
t=runpy.run_path(str(OUT/'build_continuous_walls.py'),run_name='v4_camera_refinement')
t['integrity']();m=json.loads((OUT/'V4_MANIFEST.json').read_text());assert t['sha'](t['MODEL'])==m['model_sha256']
bpy.ops.wm.open_mainfile(filepath=str(t['MODEL']));before=t['snapshot']()
r=json.loads((OUT/'OPENING_AND_BAY_REGISTER.json').read_text())
changes={'03':dict(pos=[9.75,7.10,1.85],target=[12.60,7.10,1.85],lens=26),
 'DOOR_D-MB':dict(pos=[12.20,5.175,1.85],target=[13.0,5.175,1.85],scale=3.9),
 'DOOR_D-GUEST-BATH':dict(pos=[9.225,7.20,1.85],target=[9.225,7.9,1.85],scale=3.9),
 'DOOR_D-GUEST-ROOM':dict(pos=[10.425,7.20,1.85],target=[10.425,7.9,1.85],scale=3.9)}
allviews=t['VIEWS']+r['views'];changed=[]
for v in allviews:
 if v['id'] not in changes:continue
 v.update(changes[v['id']]);o=bpy.data.objects[v['camera']]
 o.location=v['pos'];o.rotation_euler=(Vector(v['target'])-o.location).to_track_quat('-Z','Y').to_euler()
 if 'scale' in changes[v['id']]:o.data.type='ORTHO';o.data.ortho_scale=v['scale'];v.pop('lens',None)
 else:o.data.type='PERSP';o.data.lens=v['lens']
 changed.append(o.name)
bpy.context.view_layer.update();after=t['snapshot']()
for n in before:
 if n not in changed:assert t['normalize']({n:before[n]})==t['normalize']({n:after[n]}),n
t['write']('OPENING_AND_BAY_REGISTER.json',r);t['write']('V4_OBJECT_STATES.json',after)
bpy.ops.wm.save_as_mainfile(filepath=str(t['MODEL']));m['model_sha256']=t['sha'](t['MODEL']);m['camera_refinements']=changes
t['write']('V4_MANIFEST.json',m);print(json.dumps(dict(camera_refinement='PASS',cameras=len(changed),geometry_unchanged=True)))
