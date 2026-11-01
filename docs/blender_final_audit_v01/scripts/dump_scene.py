# Read-only scene dump. Never saves.  blender -b X.blend -P dump_scene.py -- out.json
import bpy, json, sys, math
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
def render_cols(scene):
    ok, st = {scene.collection}, [scene.collection]
    while st:
        c = st.pop()
        for ch in c.children:
            if not ch.hide_render and ch not in ok: ok.add(ch); st.append(ch)
    return ok
RC = render_cols(sc)
vis = lambda o: not o.hide_render and any(c in RC for c in o.users_collection)
def bb(o):
    w = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [round(min(v.x for v in w)*1000), round(min(v.y for v in w)*1000), round(max(v.x for v in w)*1000),
            round(max(v.y for v in w)*1000), round(min(v.z for v in w)*1000), round(max(v.z for v in w)*1000)]
objs = []
for o in bpy.data.objects:
    r = {'n': o.name, 't': o.type, 'vis': vis(o), 'col': o.users_collection[0].name if o.users_collection else ''}
    if o.type in ('MESH', 'CURVE'):
        r['b'] = bb(o); r['mats'] = [s.material.name for s in o.material_slots if s.material]
        if o.type == 'MESH':
            r['nv'] = len(o.data.vertices); r['nf'] = len(o.data.polygons)
            r['mods'] = [m.type + ':' + m.name for m in o.modifiers]
            r['bevel'] = any(m.type == 'BEVEL' for m in o.modifiers)
            r['uv'] = len(o.data.uv_layers)
    if o.type == 'LIGHT':
        L = o.data; r.update(lt=L.type, energy=L.energy, color=[round(c, 3) for c in L.color], loc=[round(v*1000) for v in o.matrix_world.translation],
                             size=getattr(L, 'size', None), size_y=getattr(L, 'size_y', None), shape=getattr(L, 'shape', None),
                             use_shadow=L.use_shadow, temp=getattr(L, 'temperature', None),
                             vis_cam=o.visible_camera, vis_glossy=o.visible_glossy, vis_trans=o.visible_transmission)
    if o.type == 'CAMERA':
        C = o.data; r.update(lens=round(C.lens, 1), sensor=C.sensor_width, ctype=C.type, clip=[C.clip_start, C.clip_end],
                             loc=[round(v*1000) for v in o.matrix_world.translation],
                             rot=[round(math.degrees(a), 1) for a in o.matrix_world.to_euler()], shift=[C.shift_x, C.shift_y],
                             dof=C.dof.use_dof)
    objs.append(r)
def node_info(m):
    if not m.use_nodes or not m.node_tree: return {'nodes': False}
    nt = m.node_tree; info = {'nodes': True, 'node_types': sorted({n.type for n in nt.nodes})}
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            def iv(k):
                s = n.inputs.get(k)
                if s is None: return None
                if s.is_linked: return 'LINK:' + s.links[0].from_node.type
                v = s.default_value
                try: return [round(x, 3) for x in v]
                except TypeError: return round(v, 3)
            info['bsdf'] = {k: iv(k) for k in ('Base Color', 'Roughness', 'Metallic', 'Specular IOR Level', 'IOR',
                            'Transmission Weight', 'Coat Weight', 'Sheen Weight', 'Normal', 'Alpha', 'Subsurface Weight', 'Emission Strength')}
        if n.type == 'TEX_IMAGE' and n.image:
            info.setdefault('images', []).append({'img': n.image.name, 'res': list(n.image.size), 'cs': n.image.colorspace_settings.name,
                                                  'file': bpy.path.abspath(n.image.filepath)[-80:]})
        if n.type == 'MAPPING':
            info.setdefault('mapping', []).append({'scale': [round(x, 3) for x in n.inputs['Scale'].default_value],
                                                   'rot': [round(math.degrees(x), 1) for x in n.inputs['Rotation'].default_value]})
        if n.type == 'BUMP': info['bump'] = round(n.inputs['Strength'].default_value, 3)
        if n.type == 'NORMAL_MAP': info['normal_map'] = round(n.inputs['Strength'].default_value, 3)
        if n.type == 'DISPLACEMENT': info['displacement'] = True
    return info
used = {}
for o in bpy.data.objects:
    if o.type in ('MESH', 'CURVE') and vis(o):
        for s in o.material_slots:
            if s.material: used.setdefault(s.material.name, []).append(o.name)
mats = [{'m': m.name, 'users_vis': len(used.get(m.name, [])), 'sample_objs': used.get(m.name, [])[:6], **node_info(m)}
        for m in bpy.data.materials if m.name in used]
R = sc.render; cyc = getattr(sc, 'cycles', None); ee = getattr(sc, 'eevee', None)
w = sc.world
env = {}
if w and w.use_nodes:
    for n in w.node_tree.nodes:
        if n.type == 'BACKGROUND': env['bg_strength'] = n.inputs['Strength'].default_value; env['bg_color'] = [round(x, 3) for x in n.inputs['Color'].default_value] if not n.inputs['Color'].is_linked else 'LINK:' + n.inputs['Color'].links[0].from_node.type
        if n.type == 'TEX_ENVIRONMENT' and n.image: env['hdri'] = n.image.name
        if n.type == 'TEX_SKY': env['sky'] = n.sky_type; env['sun_elev'] = round(math.degrees(getattr(n, 'sun_elevation', 0)), 1); env['sun_rot'] = round(math.degrees(getattr(n, 'sun_rotation', 0)), 1)
render = {'engine': R.engine, 'res': [R.resolution_x, R.resolution_y, R.resolution_percentage], 'camera': sc.camera.name if sc.camera else None,
          'view_transform': sc.view_settings.view_transform, 'look': sc.view_settings.look, 'exposure': sc.view_settings.exposure,
          'gamma': sc.view_settings.gamma, 'display': sc.display_settings.display_device, 'film_transparent': R.film_transparent,
          'cycles': {'samples': cyc.samples, 'denoise': cyc.use_denoising, 'denoiser': cyc.denoiser, 'max_bounces': cyc.max_bounces,
                     'light_tree': getattr(cyc, 'use_light_tree', None), 'clamp_ind': cyc.sample_clamp_indirect} if cyc else None,
          'eevee': {'taa': ee.taa_render_samples, 'raytrace': getattr(ee, 'use_raytracing', None),
                    'shadows': getattr(ee, 'use_shadows', None)} if ee else None,
          'world': env, 'frame': sc.frame_current, 'version': bpy.app.version_string, 'scenes': [s.name for s in bpy.data.scenes]}
cols = []
def walk(c, d=0):
    cols.append({'n': c.name, 'd': d, 'hide_render': c.hide_render, 'n_obj': len(c.objects)})
    for ch in c.children: walk(ch, d + 1)
walk(sc.collection)
json.dump({'blend': bpy.data.filepath, 'render': render, 'collections': cols, 'objects': objs, 'materials': mats},
          open(out, 'w'), ensure_ascii=False)
print('DUMP_OK', len(objs), len(mats))
