import bpy, json
from mathutils import Vector
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'floorplan_v1.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    return m

wall = mat('Walls', (0.70, 0.68, 0.63))
floor = mat('Continuous usable floor', (0.68, 0.58, 0.43))
living = mat('Living floor', (0.80, 0.72, 0.58))
bed = mat('Bed', (0.85, 0.82, 0.76))
wood = mat('Wood', (0.24, 0.12, 0.05))
sofa = mat('Sofa', (0.18, 0.26, 0.30))
S = 0.001

def cube(name, loc, dims, material):
    bpy.ops.mesh.primitive_cube_add(location=tuple(v * S for v in loc))
    o = bpy.context.object
    o.name = name
    o.dimensions = tuple(v * S for v in dims)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    return o

def polygon(name, points, z, material):
    verts = [(x * S, y * S, z * S) for x, y in points]
    mesh = bpy.data.meshes.new(name + 'Mesh')
    mesh.from_pydata(verts, [], [list(range(len(verts)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj

# One continuous usable-space slab. The dark-looking regions in the source plan
# are interior floor area, so they must remain part of the slab.
outer = [(1750, 0), (5310, 0), (5310, 1500), (9820, 1500),
         (9820, 1740), (11310, 1740), (11310, 11600), (1750, 11600),
         (1750, 9000), (0, 9000), (0, 3700), (1750, 3700)]
polygon('Continuous usable floor', outer, -40, floor)

# Light room separators are kept as provisional design geometry only.
for r in DATA['rooms']:
    pts = r['polygon_mm']
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if r['name'] == '客餐厅':
        continue
    for x, y, dx, dy in [(x0, (y0+y1)/2, 70, y1-y0),
                         (x1, (y0+y1)/2, 70, y1-y0),
                         ((x0+x1)/2, y0, x1-x0, 70),
                         ((x0+x1)/2, y1, x1-x0, 70)]:
        cube(r['name'] + '_provisional_wall', (x, y, 1350), (dx, dy, 2700), wall)

# Outer envelope follows the irregular outline of the plan.
for (x1, y1), (x2, y2) in zip(outer, outer[1:] + outer[:1]):
    if x1 == x2:
        cube('Outer wall', (x1, (y1+y2)/2, 1350), (100, abs(y2-y1), 2700), wall)
    elif y1 == y2:
        cube('Outer wall', ((x1+x2)/2, y1, 1350), (abs(x2-x1), 100, 2700), wall)

cube('Dining table', (6250, 7900, 800), (1800, 900, 80), wood)
cube('Sofa', (6250, 10100, 450), (2200, 800, 850), sofa)
cube('Master bed', (3500, 8200, 300), (1800, 2100, 500), bed)
cube('Bed 1', (8150, 3900, 300), (1800, 2100, 500), bed)
cube('Bed 2', (9750, 8700, 300), (1600, 2000, 500), bed)

bpy.ops.object.camera_add(location=(14, -15, 15), rotation=(Vector((5.6, 5.8, 0)) - Vector((14, -15, 15))).to_track_quat('-Z', 'Y').to_euler())
bpy.context.scene.camera = bpy.context.object
bpy.ops.object.light_add(type='AREA', location=(5, 5, 12)); bpy.context.object.data.energy = 1800; bpy.context.object.data.size = 10
bpy.ops.object.light_add(type='AREA', location=(-5, 10, 8)); bpy.context.object.data.energy = 900; bpy.context.object.data.size = 8
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1000; scene.render.resolution_y = 820; scene.render.resolution_percentage = 100
scene.render.filepath = str(ROOT / 'blockout_v2.png')
scene.world = bpy.data.worlds.new('Interior World')
scene.world.color = (0.055, 0.055, 0.055)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'blockout_v2.blend'))
bpy.ops.render.render(write_still=True)
