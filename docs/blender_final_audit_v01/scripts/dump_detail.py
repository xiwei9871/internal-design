# Read-only detail dump. Never saves.
import bpy, json, sys
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
def rc(scene):
    ok, st = {scene.collection}, [scene.collection]
    while st:
        c = st.pop()
        for ch in c.children:
            if not ch.hide_render and ch not in ok: ok.add(ch); st.append(ch)
    return ok
RC = rc(sc); vis = lambda o: not o.hide_render and any(c in RC for c in o.users_collection)
res = {'emission': {}, 'ceilings': [], 'textured_no_uv': [], 'bevel': {'with': 0, 'without': 0}, 'world': {}}
for m in bpy.data.materials:
    if not (m.use_nodes and m.node_tree): continue
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            s = n.inputs.get('Emission Strength'); c = n.inputs.get('Emission Color')
            if s and (s.is_linked or s.default_value > 0):
                res['emission'][m.name] = {'strength': None if s.is_linked else s.default_value,
                                           'color': 'LINK' if c.is_linked else [round(x, 3) for x in c.default_value][:3]}
tex_mats = {m.name for m in bpy.data.materials if m.use_nodes and m.node_tree and any(n.type == 'TEX_IMAGE' for n in m.node_tree.nodes)
            and not any(n.type in ('TEX_COORD',) and n.outputs['Generated'].is_linked or n.outputs['Object'].is_linked for n in m.node_tree.nodes if n.type == 'TEX_COORD')}
for o in bpy.data.objects:
    if o.type != 'MESH' or not vis(o): continue
    if any(k in o.name.upper() for k in ('CEIL',)):
        res['ceilings'].append(o.name)
    if any(s.material and s.material.name in tex_mats for s in o.material_slots) and len(o.data.uv_layers) == 0:
        res['textured_no_uv'].append(o.name)
    b = any(m.type == 'BEVEL' for m in o.modifiers)
    res['bevel']['with' if b else 'without'] += 1
for c in bpy.data.collections:
    if 'CEIL' in c.name.upper(): res.setdefault('ceiling_cols', []).append([c.name, c.hide_render, len(c.objects), [o.name for o in c.objects][:6]])
w = sc.world
if w and w.use_nodes:
    for n in w.node_tree.nodes:
        if n.type == 'MAPPING': res['world']['mapping_rot_deg'] = [round(x * 57.2958, 1) for x in n.inputs['Rotation'].default_value]
vl = sc.view_layers[0]
res['view_layer_excluded'] = []
def lw(lc):
    if lc.exclude: res['view_layer_excluded'].append(lc.name)
    for ch in lc.children: lw(ch)
lw(vl.layer_collection)
json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
print('DETAIL_OK')
