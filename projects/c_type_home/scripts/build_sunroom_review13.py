"""Derived C-Type sunroom review 13."""
import bpy
import json
import math
import hashlib
import uuid
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
SOURCE = ROOT / 'OPTION_A_R4_SUNROOM_DOOR_CLEAR_SOFA_REVIEW_12.blend'
OUTPUT = ROOT / 'OPTION_A_R4_SUNROOM_CABINET_FREEZER_SWAP_REVIEW_13.blend'
REGISTRY_IN = ROOT / 'spatial-canvas.bindings.review12.json'
REGISTRY_OUT = ROOT / 'spatial-canvas.bindings.review13.json'
EXPECTED_SOURCE_SHA = 'd73835d9b0c3ab0b7edab5469a8421d1e65ef65d79ddf168bede725d48ffc78f'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def bounds(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [[min(v[i] for v in cs) for i in range(3)], [max(v[i] for v in cs) for i in range(3)]]

def material(name, color, roughness=.55):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*color, 1)
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color, 1)
        bsdf.inputs['Roughness'].default_value = roughness
    return m

def box(name, lo, hi, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=[(lo[i] + hi[i]) / 2 for i in range(3)])
    o = bpy.context.object
    o.name = name
    o.scale = [hi[i] - lo[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new('Soft edge', 'BEVEL')
        mod.width = bevel
        mod.segments = 4
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(mat)
    return o

def join(name, parts):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    return o

assert sha(SOURCE) == EXPECTED_SOURCE_SHA
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.view_layer.update()

# Remove every review12 worktop and hinge object. The chest freezer stays open.
removed_worktop_names = [o.name for o in list(bpy.context.scene.objects)
    if o.name.startswith(('SUNROOM_FREEZER_FLIP_WORKTOP_', 'SUNROOM_FREEZER_WORKTOP_HINGE_'))]
for name in removed_worktop_names:
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)

# Swap the freezer into the former low-cabinet bay, rotating it to the
# available 1200 x 600 mm footprint. The cabinet moves to the former freezer
# bay and retains its stable object identities.
freezer_parts = [
    'B11_Rectangle039_BODY', 'B11_Rectangle039_LID_SEAM',
    'SUNROOM_FREEZER_SIDE_FINISH_SOUTH', 'SUNROOM_FREEZER_SIDE_FINISH_NORTH',
    'SUNROOM_FREEZER_FRONT_PLINTH',
] + [f'SUNROOM_FREEZER_VENT_SLAT_{i}' for i in range(5)]
old_pivot = Vector((12.45, 11.95, 0))
new_freezer_center = Vector((12.00, 12.95, 0))
freezer_transform = (Matrix.Translation(new_freezer_center)
    @ Matrix.Rotation(-math.pi / 2, 4, 'Z')
    @ Matrix.Translation(-old_pivot))
for name in freezer_parts:
    bpy.data.objects[name].matrix_world = freezer_transform @ bpy.data.objects[name].matrix_world

for name in ('SUNROOM_EAST_LOW_STORAGE', 'SUNROOM_EAST_STORAGE_COUNTER'):
    bpy.data.objects[name].location.y -= 1.30

# Trim the north plant ledge so the rotated freezer has a clear lid and rear
# service zone, then bring its third plant into the remaining ledge length.
for name, left, width in [
    ('SUNROOM_NORTH_PLANT_LEDGE_BASE', 9.15, 2.00),
    ('SUNROOM_NORTH_PLANT_LEDGE_TOP', 9.13, 2.00),
]:
    o = bpy.data.objects[name]
    old_width = o.dimensions.x
    o.scale.x *= width / old_width
    bpy.context.view_layer.update()
    o.location.x = left + width / 2
for o in bpy.context.scene.objects:
    if o.name.startswith('SUNROOM_PLANT_2'):
        o.location.x -= .55

# Move the compact sofa 200 mm north to make a shallow high cabinet possible
# on the solid wall behind it. This leaves a provisional 960 mm central lane.
sofa = bpy.data.objects['SUNROOM_COMPACT_TWO_SEAT_SOFA']
sofa.location.y += .20

oak = material('SUNROOM_REVIEW13_PALE_ASH', (.60, .44, .28), .62)
warm = material('SUNROOM_REVIEW13_WARM_WHITE', (.76, .77, .73), .72)
accent = material('SUNROOM_REVIEW13_SOFT_GREY', (.42, .45, .43), .70)

# Shallow floor-to-ceiling cabinet, kept west of the glazed opening. Its
# fronts are a sliding-front study so no door sweep enters the sofa lane.
x0, x1 = 8.95, 9.65
y0, y1 = 11.115, 11.315
z0, z1 = .05, 2.35
parts = [
    box('SUNROOM_HIGH_CABINET_SIDE_L', (x0, y0, z0), (x0 + .018, y1, z1), warm, .002),
    box('SUNROOM_HIGH_CABINET_SIDE_R', (x1 - .018, y0, z0), (x1, y1, z1), warm, .002),
    box('SUNROOM_HIGH_CABINET_TOP', (x0, y0, z1 - .018), (x1, y1, z1), warm, .002),
    box('SUNROOM_HIGH_CABINET_BOTTOM', (x0, y0, z0), (x1, y1, z0 + .018), warm, .002),
    box('SUNROOM_HIGH_CABINET_BACK', (x0 + .018, y0, z0 + .018), (x1 - .018, y0 + .015, z1 - .018), oak, .001),
    box('SUNROOM_HIGH_CABINET_DIVIDER', ((x0 + x1) / 2 - .009, y0 + .015, z0 + .018), ((x0 + x1) / 2 + .009, y1 - .018, z1 - .018), warm, .001),
    box('SUNROOM_HIGH_CABINET_FRONT_L', (x0 + .018, y1 - .018, z0 + .018), ((x0 + x1) / 2 - .009, y1, z1 - .018), accent, .004),
    box('SUNROOM_HIGH_CABINET_FRONT_R', ((x0 + x1) / 2 + .009, y1 - .018, z0 + .018), (x1 - .018, y1, z1 - .018), accent, .004),
]
high_cabinet = join('SUNROOM_SOFA_REAR_HIGH_CABINET', parts)
high_cabinet['design_status'] = 'HUMAN_REVIEW'
high_cabinet['door_mode'] = 'sliding_front_study'
high_cabinet['depth_m'] = .20
high_cabinet['clearance_note'] = '200mm sofa north shift; provisional central lane 960mm.'

# Keep all existing stable IDs, remove deleted worktop IDs, and add one ID for
# the new high cabinet.
registry = json.loads(REGISTRY_IN.read_text())
registry['bindings'] = [b for b in registry['bindings']
    if b['native_id'] not in set(removed_worktop_names)]
registry['bindings'].append({
    'entity_id': 'ent_' + uuid.uuid5(uuid.NAMESPACE_URL,
        'c_type_home:sunroom:review13:SUNROOM_SOFA_REAR_HIGH_CABINET').hex,
    'adapter': 'blender',
    'native_id': 'SUNROOM_SOFA_REAR_HIGH_CABINET',
    'semantic_type': 'cabinet',
    'room_id': 'unassigned',
    'authority_level': 'HUMAN_DESIGN_GUIDE',
})
registry.update({
    'registry_revision': '23-sunroom-cabinet-freezer-swap-no-cover',
    'source_revision': 'r4-sunroom-cabinet-freezer-swap-review-13',
    'source_locator': str(OUTPUT),
    'source_authority': 'frozen',
})

bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
registry['source_sha256'] = sha(OUTPUT)
REGISTRY_OUT.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n')

report = {
    'status': 'HUMAN_REVIEW',
    'revision': registry['source_revision'],
    'source': str(SOURCE),
    'source_sha256': EXPECTED_SOURCE_SHA,
    'output': str(OUTPUT),
    'output_sha256': registry['source_sha256'],
    'removed_worktop_native_ids': sorted(removed_worktop_names),
    'freezer_bounds_m': bounds(bpy.data.objects['B11_Rectangle039_BODY']),
    'cabinet_bounds_m': bounds(bpy.data.objects['SUNROOM_EAST_LOW_STORAGE']),
    'high_cabinet_bounds_m': bounds(high_cabinet),
    'freezer_top_clear': True,
    'fixed_countertop_over_freezer': False,
    'freezer_and_low_cabinet_swapped': True,
    'sofa_north_shift_m': .20,
    'provisional_central_lane_m': 13.055 - bounds(sofa)[1][1],
    'north_plant_ledge_shortened_for_freezer_clearance': True,
    'manufacturer_lid_sweep_verified': False,
    'utilities_verified': False,
    'frozen_r4_sha256': 'd109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb',
}
(ROOT / 'SUNROOM_CABINET_FREEZER_SWAP_REVIEW13_QA.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False))
