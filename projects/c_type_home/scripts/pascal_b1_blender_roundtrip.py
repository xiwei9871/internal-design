# Blender headless: import Pascal full scene -> save blend -> render plan/axon/contact.
# run: Blender --background --python pascal_b1_blender_roundtrip.py
import bpy, json, os, math

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
SCENE = f'{BASE}/design/pascal_b1/pascal_full_scene_exported.json'
OUTD = f'{BASE}/design/pascal_b1'
BLEND = f'{OUTD}/世纪欣园_PASCAL_B1_FULL_V1.blend'

bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    bpy.ops.preferences.addon_enable(module='bl_ext.user_default.pascal_blender')
except Exception as e:
    print('addon_enable:', e)
bpy.ops.pascal.import_scene(filepath=SCENE, network=False)

objs = list(bpy.data.objects)
print('IMPORT objects:', len(objs))
kinds = {}
for o in objs:
    kinds[o.type] = kinds.get(o.type, 0) + 1
print('by type:', kinds)

# persist source scene in Text datablock for audit trail
if 'pascal_source.json' not in bpy.data.texts:
    t = bpy.data.texts.new('pascal_source.json')
    t.write(open(SCENE).read())

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)

# ---------- renders ----------
import mathutils
bpy.context.view_layer.update()
pts = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        for v in o.bound_box:
            pts.append(o.matrix_world @ mathutils.Vector(v))
xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
span = max(max(xs)-min(xs), max(ys)-min(ys)) * 1.08
print('BOUNDS x', round(min(xs),2), round(max(xs),2), 'y', round(min(ys),2), round(max(ys),2), 'z', round(min(zs),2), round(max(zs),2))

scn = bpy.context.scene
scn.render.engine = 'BLENDER_WORKBENCH'
scn.display.shading.light = 'STUDIO'
scn.display.shading.color_type = 'MATERIAL'
scn.display.shading.show_shadows = False
scn.render.resolution_x = 1600
scn.render.resolution_y = 1200
scn.render.film_transparent = False
scn.world = bpy.data.worlds.new('W'); scn.world.color = (0.9, 0.9, 0.9)

def add_cam(name, loc, rot, ortho):
    d = bpy.data.cameras.new(name); d.type = 'ORTHO'; d.ortho_scale = ortho
    o = bpy.data.objects.new(name, d); scn.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    return o

def render(cam, path):
    scn.camera = cam
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('RENDERED', path)

plan = add_cam('CAM_PLAN', (cx, cy, 40), (0, 0, 0), span)
render(plan, f'{OUTD}/PASCAL_B1_PLAN.png')

axon = add_cam('CAM_AXON', (cx+span*0.8, cy-span*0.9, 30),
               (math.radians(60), 0, math.radians(35)), span*1.15)
render(axon, f'{OUTD}/PASCAL_B1_AXON.png')
print('DONE')
