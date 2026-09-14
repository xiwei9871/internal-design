import bpy
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parent; bpy.ops.wm.read_factory_settings(use_empty=True); PX=0.00982
def mat(n,c): m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); return m
floor=mat('Continuous usable floor',(0.66,0.52,0.32)); wall=mat('Walls',(0.78,0.76,0.70)); bath=mat('Wet areas',(0.45,0.70,0.74)); bedfloor=mat('Bedrooms',(0.69,0.58,0.75)); living=mat('Living',(0.82,0.72,0.55)); wood=mat('Wood',(0.23,0.11,0.04)); bedmat=mat('Beds',(0.85,0.80,0.72)); sofa=mat('Sofa',(0.16,0.27,0.32))
def cube(n,x,y,z,dx,dy,dz,m): bpy.ops.mesh.primitive_cube_add(location=(x*PX,y*PX,z)); o=bpy.context.object; o.name=n; o.dimensions=(dx*PX,dy*PX,dz); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m); return o
def poly(n,pts,z,m): me=bpy.data.meshes.new(n+'Mesh'); me.from_pydata([(x*PX,y*PX,z) for x,y in pts],[],[list(range(len(pts)))]); me.update(); o=bpy.data.objects.new(n,me); bpy.context.collection.objects.link(o); o.data.materials.append(m); return o
outer=[(403,145),(790,145),(790,310),(1184,310),(1184,674),(1160,674),(1160,760),(1485,760),(1485,1337),(403,1337),(403,1128),(200,1128),(200,534),(403,534)]; poly('Continuous usable interior floor',outer,0,floor)
zones=[('Kitchen',[(415,157),(779,157),(779,310),(415,310)],living),('Secondary bath',[(428,334),(592,334),(592,643),(428,643)],bath),('Laundry',[(592,334),(756,334),(756,556),(592,556)],bath),('Bedroom 1',[(790,334),(1160,334),(1160,654),(790,654)],bedfloor),('Master bath',[(224,558),(403,558),(403,843),(224,843)],bath),('Master bedroom',[(428,667),(766,667),(766,1131),(428,1131)],bedfloor),('Living dining',[(766,674),(1128,674),(1128,1337),(766,1337)],living),('Bedroom 2',[(1152,785),(1458,785),(1458,1128),(1152,1128)],bedfloor),('Bedroom 2 bay',[(1140,1151),(1458,1151),(1458,1314),(1140,1314)],bedfloor)]
for n,p,m in zones: poly(n+' floor',p,0.015,m)
segs=[(403,145,790,145),(790,145,790,310),(790,310,1184,310),(1184,310,1184,674),(1160,674,1160,760),(1160,760,1485,760),(1485,760,1485,1337),(1485,1337,403,1337),(403,1337,403,1128),(403,1128,200,1128),(200,1128,200,534),(200,534,403,534),(403,534,403,145),(403,310,592,310),(767,310,904,310),(767,310,767,558),(403,643,665,643),(403,643,403,1003),(652,667,652,781),(766,770,766,1128),(1128,760,1128,797),(1128,878,1128,1064),(1128,1088,1128,1128),(1128,1128,1235,1128),(428,1314,750,1314),(808,1314,1113,1314),(1160,1314,1458,1314)]
for x1,y1,x2,y2 in segs:
 if x1==x2: cube('Wall',x1,(y1+y2)/2,1.25,12,abs(y2-y1),2.5,wall)
 else: cube('Wall',(x1+x2)/2,y1,1.25,abs(x2-x1),12,2.5,wall)
cube('Dining table',968,812,0.76,920,460,0.10,wood); cube('Sofa',973,1030,0.42,1800,700,0.84,sofa); cube('Master bed',658,1000,0.28,2140,1870,0.42,bedmat); cube('Bed 1',1052,480,0.28,2150,1850,0.42,bedmat); cube('Bed 2',1350,995,0.28,2140,1580,0.42,bedmat)
bpy.ops.object.camera_add(location=(18,-18,22)); cam=bpy.context.object; cam.rotation_euler=(Vector((8.3,7.4,0))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.lens=52; bpy.context.scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(8,5,14)); bpy.context.object.data.energy=1800; bpy.context.object.data.size=12; bpy.ops.object.light_add(type='AREA',location=(2,10,8)); bpy.context.object.data.energy=900; bpy.context.object.data.size=8
scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_x=1100; scene.render.resolution_y=900; scene.render.resolution_percentage=100; scene.render.filepath=str(ROOT/'blockout_png_v1.png'); scene.world=bpy.data.worlds.new('Interior World'); scene.world.color=(0.055,0.055,0.055); bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blockout_png_v1.blend')); bpy.ops.render.render(write_still=True)
