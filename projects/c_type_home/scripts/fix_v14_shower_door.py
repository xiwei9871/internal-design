import bpy,json,hashlib,math,struct
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/platform_bath_fitness_v14';S=D/'WHOLE_HOUSE_PLATFORM_BATH_FITNESS_REVIEW_V14.blend';O=D/'WHOLE_HOUSE_PLATFORM_BATH_FITNESS_FINAL_V14.blend';a=json.loads((D/'BUILD_AUDIT.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(S)==a['sha256'] and not O.exists();bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
old=bpy.data.objects['HOUSE_V1_V14_SHOWER_INWARD_DOOR'];mat=old.data.materials[0];bpy.data.objects.remove(old,do_unlink=True)
# Correct closed leaf: diagonal side from (10.8999,5.5002) to (10.4499,5.9502), width636mm, vertical1.98m.
A=Vector((10.4499,5.9502,.47));B=Vector((10.8999,5.5002,.47));v=B-A;mid=(A+B)/2
bpy.ops.mesh.primitive_cube_add(size=1,location=(mid.x,mid.y,1.46));door=bpy.context.object;door.name='HOUSE_V1_V14_SHOWER_INWARD_DOOR';door.dimensions=(v.length,.008,1.98);door.rotation_euler.z=math.atan2(v.y,v.x);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);door.data.materials.append(mat);door['open_direction']='inward 0..90 degrees; hinge/SEAL/product pending';door['construction_status']='custom enclosure dimension study';
for c in list(door.users_collection):c.objects.unlink(door)
bpy.data.collections['V14_OWNER_LOCAL_REVIEW'].objects.link(door)
# Remove faulty hinge empty; motion samples are conceptual and geometry now has correct closed pose.
if bpy.data.objects.get('V14_SHOWER_DOOR_HINGE'):bpy.data.objects.remove(bpy.data.objects['V14_SHOWER_DOOR_HINGE'],do_unlink=True)
bpy.context.window.view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN'];bpy.ops.wm.save_as_mainfile(filepath=str(O));a['pre_door_parent_fix']={'output':str(S),'sha256':sha(S)};a['output']=str(O);a['sha256']=sha(O);a['door_parent_fix']='Rebuilt closed leaf at measured coordinates; removed faulty displaced parent; hinge/product remains a construction decision';a['status']='HUMAN_REVIEW';(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');print('V14_DOOR_FIX',a['sha256'])

