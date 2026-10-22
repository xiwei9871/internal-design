# Re-render from saved blend: colored workbench plan/axon/crops.
# run: Blender --background <blend> --python pascal_b1_render.py
import bpy, math, mathutils

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
OUTD = f'{BASE}/design/pascal_b1'

scn = bpy.context.scene
scn.render.engine = 'BLENDER_WORKBENCH'
scn.display.shading.light = 'STUDIO'
scn.display.shading.color_type = 'OBJECT'
scn.display.shading.show_shadows = True
scn.display.shading.show_cavity = True
scn.display.shading.cavity_type = 'WORLD'
scn.render.resolution_x = 1800
scn.render.resolution_y = 1400
scn.render.film_transparent = False
if not scn.world:
    scn.world = bpy.data.worlds.new('W')
scn.world.color = (0.95, 0.95, 0.95)

# object colors by role (importer names objects after node types/labels)
COLOR = {'wall': (0.25, 0.25, 0.28, 1), 'item': (0.45, 0.62, 0.85, 1),
         'zone': (0.9, 0.9, 0.6, 1), 'door': (0.85, 0.55, 0.2, 1),
         'window': (0.35, 0.75, 0.8, 1)}
def role_of(o):
    nm = (o.name or '').lower()
    if 'wall' in nm: return 'wall'
    if 'door' in nm: return 'door'
    if 'window' in nm: return 'window'
    if 'zone' in nm or 'room' in nm: return 'zone'
    return 'item' if o.type in ('MESH', 'EMPTY') else 'wall'
for o in bpy.data.objects:
    o.color = COLOR.get(role_of(o), (0.6, 0.6, 0.6, 1))

bpy.context.view_layer.update()
pts = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        pts += [o.matrix_world @ mathutils.Vector(v) for v in o.bound_box]
xs = [p.x for p in pts]; ys = [p.y for p in pts]
cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
span = max(max(xs)-min(xs), max(ys)-min(ys)) * 1.06
print('BOUNDS', round(min(xs),1), round(max(xs),1), round(min(ys),1), round(max(ys),1))

def add_cam(name, loc, rot, ortho):
    d = bpy.data.cameras.new(name); d.type = 'ORTHO'; d.ortho_scale = ortho
    d.clip_start = 0.1; d.clip_end = 500
    o = bpy.data.objects.new(name, d); scn.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    return o

def look_at(cam, tx, ty, tz):
    d = cam.location - mathutils.Vector((tx, ty, tz))
    cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

# zone slab surfaces off for cleaner blockout plan
zone_objs = [o for o in bpy.data.objects
             if o.name.lower().startswith(('zone_', 'r-')) or 'zone' in o.name.lower()]

def render(cam, path, hide_zones=False):
    for zo in zone_objs:
        zo.hide_render = hide_zones
    scn.camera = cam; scn.render.filepath = path
    bpy.ops.render.render(write_still=True); print('RENDERED', path)

render(add_cam('CAM_PLAN', (cx, cy, 40), (0, 0, 0), span),
       f'{OUTD}/PASCAL_B1_PLAN.png', hide_zones=True)

ax = add_cam('CAM_AXON', (cx+span*0.9, cy-span*1.1, span*0.9), (0, 0, 0), span*1.1)
look_at(ax, cx, cy, 0)
render(ax, f'{OUTD}/PASCAL_B1_AXON.png', hide_zones=True)

# contact crops: living+nbalc (north), master suite (east-upper), dining+kitchen (west-lower)
for i, (lx, ly, ortho) in enumerate([(cx, min(ys)+span*0.22, span*0.55),
                                     (max(xs)-span*0.22, cy, span*0.55),
                                     (min(xs)+span*0.24, max(ys)-span*0.22, span*0.5)]):
    scn.render.resolution_x = 1200; scn.render.resolution_y = 900
    render(add_cam(f'CAM_CROP{i}', (lx, ly, 40), (0, 0, 0), ortho),
           f'{OUTD}/_crop{i}.png', hide_zones=True)
print('DONE')
