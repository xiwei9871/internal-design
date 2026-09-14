import bpy, json
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parent; DATA=json.loads((ROOT/'floorplan_v1.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(name,c):
    m=bpy.data.materials.new(name); m.diffuse_color=(*c,1); return m
wall=mat('Wall',(0.72,0.70,0.65)); floor=mat('Floor',(0.48,0.34,0.22)); living=mat('Living',(0.72,0.60,0.42)); bed=mat('Bed',(0.85,0.82,0.76)); dark=mat('DarkWood',(0.25,0.12,0.05)); sofa=mat('Sofa',(0.18,0.26,0.30))
S=0.001
def cube(name,loc,dims,material):
    bpy.ops.mesh.primitive_cube_add(location=tuple(v*S for v in loc)); o=bpy.context.object; o.name=name; o.dimensions=tuple(v*S for v in dims); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(material); return o
for r in DATA['rooms']:
    pts=r['polygon_mm']; xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; x0,x1=min(xs),max(xs); y0,y1=min(ys),max(ys)
    cube(r['name']+'_floor',((x0+x1)/2,(y0+y1)/2,0),(x1-x0,y1-y0,80),living if r['name']=='客餐厅' else floor)
    for x,y,dx,dy in [(x0,(y0+y1)/2,80,y1-y0),(x1,(y0+y1)/2,80,y1-y0),((x0+x1)/2,y0,x1-x0,80),((x0+x1)/2,y1,x1-x0,80)]: cube(r['name']+'_wall',(x,y,1400),(dx,dy,2800),wall)
cube('DiningTable',(6250,7900,800),(1800,900,80),dark); cube('Sofa',(6250,10100,450),(2200,800,850),sofa); cube('MasterBed',(3500,8200,300),(1800,2100,500),bed); cube('Bed1',(8150,3900,300),(1800,2100,500),bed); cube('Bed2',(9750,8700,300),(1600,2000,500),bed)
bpy.ops.object.camera_add(location=(14,-15,15),rotation=(Vector((5.6,5.8,0))-Vector((14,-15,15))).to_track_quat('-Z','Y').to_euler()); bpy.context.scene.camera=bpy.context.object
bpy.ops.object.light_add(type='AREA',location=(5,5,12)); bpy.context.object.data.energy=1800; bpy.context.object.data.size=10
bpy.ops.object.light_add(type='AREA',location=(-5,10,8)); bpy.context.object.data.energy=900; bpy.context.object.data.size=8
scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_x=1000; scene.render.resolution_y=820; scene.render.resolution_percentage=100; scene.render.filepath=str(ROOT/'blockout_v1.png'); scene.world=bpy.data.worlds.new('Interior World'); scene.world.color=(0.055,0.055,0.055)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blockout_v1.blend')); bpy.ops.render.render(write_still=True)
