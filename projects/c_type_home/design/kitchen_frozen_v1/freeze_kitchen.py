"""Freeze the approved V4 spatial model; never write to B0 or historic candidates.

Run with Blender --background --disable-autoexec --python-exit-code 1
--python <this file> -- build|verify|render
"""
import argparse
import csv
import hashlib
import json
import struct
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SITE = ROOT / 'design/site_photos'
SOURCE = SITE / 'B1_1_SITE_CORRECTED_V4.blend'
CAM_SOURCE = SITE / 'kitchen_multiview_v4/KITCHEN_REVIEW_CAMERA_SET_V4.blend'
MODEL = OUT / 'KITCHEN_APPROVED_AS_IS_V1.blend'
MANIFEST = OUT / 'KITCHEN_FREEZE_MANIFEST.json'
SCOPED_COLLECTIONS = {
    'COL_B11_KITCHEN', 'COL_SITE_KITCHEN_ISLAND_AND_UTILITY',
    'COL_SITE_WINDOW_AND_BUFFET_V4', 'COL_REVIEW_CAMERAS_V4',
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')


def b0_check():
    frozen = json.loads((ROOT / 'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
    result = {k: sha(ROOT / frozen['files'][k]) == v for k, v in frozen['sha256'].items()}
    assert all(result.values()), 'Frozen B0 file changed: ' + str(result)
    return result


def simple(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, 'name'):
        return {'id': value.name}
    try:
        return [simple(v) for v in value]
    except TypeError:
        return str(type(value))


def material_state(mat):
    nodes = []
    links = []
    if mat.node_tree:
        for n in mat.node_tree.nodes:
            nodes.append([n.name, n.bl_idname, [
                [i.name, simple(i.default_value)] for i in n.inputs
                if hasattr(i, 'default_value')
            ]])
        links = sorted([l.from_node.name, l.from_socket.identifier,
                        l.to_node.name, l.to_socket.identifier]
                       for l in mat.node_tree.links)
    return [mat.name, list(mat.diffuse_color), nodes, links]


def object_state(o):
    geom = hashlib.sha256()
    if o.type == 'MESH':
        for v in o.data.vertices:
            geom.update(struct.pack('<3f', *v.co))
        for e in o.data.edges:
            geom.update(struct.pack('<2I', *e.vertices))
        for p in o.data.polygons:
            geom.update(struct.pack('<II', len(p.vertices), p.material_index))
            geom.update(struct.pack('<' + 'I' * len(p.vertices), *p.vertices))
            geom.update(bytes([p.use_smooth]))
    modifiers = []
    for m in o.modifiers:
        values = {}
        for p in m.bl_rna.properties:
            if p.identifier == 'rna_type' or p.is_readonly:
                continue
            try:
                values[p.identifier] = simple(getattr(m, p.identifier))
            except (AttributeError, TypeError):
                pass
        modifiers.append([m.type, values])
    state = dict(type=o.type, geometry_sha256=geom.hexdigest(),
                 matrix_world=[list(row) for row in o.matrix_world],
                 authored_transform=[list(o.location), list(o.rotation_euler), list(o.scale)],
                 parent=o.parent.name if o.parent else None,
                 collections=sorted(c.name for c in o.users_collection),
                 hide_render=o.hide_render, hide_viewport=o.hide_viewport,
                 materials=[material_state(s.material) if s.material else None
                            for s in o.material_slots], modifiers=modifiers,
                 color=list(o.color))
    if o.type == 'CAMERA':
        state['camera'] = dict(type=o.data.type, lens=o.data.lens,
                               ortho_scale=o.data.ortho_scale,
                               clip_start=o.data.clip_start, clip_end=o.data.clip_end,
                               sensor_width=o.data.sensor_width,
                               sensor_fit=o.data.sensor_fit)
    return state


def snapshot():
    bpy.context.view_layer.update()
    return {o.name: object_state(o) for o in sorted(bpy.data.objects, key=lambda x: x.name)}


def scoped(o):
    return (o.name.startswith(('B11_K-', 'B11_SITE_', 'KITCHEN_REVIEW_CAM_'))
            or o.name == 'W_wall_md_0042'
            or any(c.name in SCOPED_COLLECTIONS for c in o.users_collection))


def bounds(objects):
    points = [o.matrix_world @ Vector(p) for o in objects if o.type == 'MESH'
              for p in o.bound_box]
    assert points, 'No geometry in assembly'
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]


def assembly(name):
    root = bpy.data.objects[name]
    return bounds([o for o in [root, *root.children_recursive]
                   if not o.hide_render and not o.hide_viewport])


def close(a, b, label, tol=.00001):
    assert abs(a - b) < tol, f'{label}: {a} != {b}'


def invariants():
    b0 = b0_check()
    nb = assembly('B11_K-NARROW-OUTER-320')
    fb = assembly('B11_K-FRIDGE')
    hb = assembly('B11_K-FRIDGE-OVERHEAD')
    ib = assembly('B11_K-TALL-L')
    assert nb[0][0] < nb[1][0] <= fb[0][0] + 1e-5
    assert fb[1][0] <= ib[0][0] + 1e-5
    close(nb[1][0] - nb[0][0], .320, 'narrow width')
    close(nb[1][1] - nb[0][1], .765, 'narrow model depth')
    close(nb[0][1], fb[0][1], 'front alignment')
    for i, expected in enumerate([.905, .710, 1.700]):
        close(fb[1][i] - fb[0][i], expected, 'fridge size')
    close(4.5 - fb[1][1], .055, 'rear allowance')
    close(hb[0][0], fb[0][0], 'overhead left')
    close(hb[1][0], fb[1][0], 'overhead right')
    fronts = [bounds([bpy.data.objects[f'B11_K-NARROW-OUTER-320_FRONT_{n}']])
              for n in range(4)]
    ref = bounds([bpy.data.objects['B11_K-FRIDGE-OVERHEAD_FRONT_0']])
    fronts.sort(key=lambda f: f[0][2])
    close(fronts[-1][0][2], ref[0][2], 'top narrow door bottom alignment')
    close(fronts[-1][1][2], ref[1][2], 'top narrow door top alignment')
    heights = [f[1][2] - f[0][2] for f in fronts[:-1]]
    close(max(heights), min(heights), 'three lower fronts equal height')
    kw = assembly('B11_SITE_KITCHEN_WINDOW')
    bw = assembly('B11_SITE_BALCONY_WINDOW')
    for got, expected, label in [(kw[0][0],6.1,'kitchen x0'),(kw[1][0],7.1,'kitchen x1'),
                                  (kw[0][2],1.02,'kitchen sill'),(kw[1][2],2.4,'kitchen head'),
                                  (bw[0][0],2.1,'balcony x0'),(bw[1][0],5.1,'balcony x1'),
                                  (bw[0][2],1.05,'balcony sill'),(bw[1][2],2.4,'balcony head')]:
        close(got, expected, label)
    parapet = bpy.data.objects['W_wall_md_0042']
    pb = bounds([parapet])
    close(pb[1][2], 1.05, 'complete window under wall')
    assert parapet.get('review_keep_full_height')
    assert parapet.get('semantic_role') == 'WINDOW_UNDER_WALL; NOT_CABINET'
    for name in ['GLZ_W-KIT-S', 'GLZ_W-LBALC-S', 'B11_OPENING_W-KIT-S',
                 'B11_OPENING_W-LBALC-S', 'B11_Rectangle029']:
        root = bpy.data.objects.get(name)
        if root:
            assert all(o.hide_render and o.hide_viewport
                       for o in [root, *root.children_recursive]), name + ' obsolete proxy active'
    buffet = bpy.data.objects['B11_SITE_PHOTO5_BUFFET_R029']
    for category, count in [('UPPER_DOOR',4),('LOWER_DOOR',4),('DRAWER',2)]:
        assert len([o for o in buffet.children_recursive
                    if o.name.startswith('B11_SITE_BUFFET_' + category + '_')]) == count
    bb = assembly(buffet.name)
    for got, expected, label in [(bb[1][0]-bb[0][0],.5,'buffet depth'),
                                  (bb[1][1]-bb[0][1],1.5,'buffet width'),
                                  (bb[1][2],2.71,'buffet model top')]:
        close(got, expected, label)
    counter = bounds([bpy.data.objects['B11_SITE_BUFFET_COUNTER']])
    close(counter[1][2], 1.1, 'buffet counter top')
    island = assembly('B11_K-ISLAND-PDF-C')
    for i, expected in enumerate([.467,.800,.960]):
        close(island[1][i]-island[0][i], expected, 'island model size')
    ub = assembly('B11_K-UTILITY-TALL-600')
    ac = assembly('B11_K-UTILITY-WALL-AC')
    close(ub[1][0]-ub[0][0], .600, 'utility width')
    close(ub[1][2]-ub[0][2], 2.000, 'utility height')
    assert ac[0][2] > ub[1][2], 'AC must be above utility cabinet'
    cams = json.loads((OUT/'CAMERA_REGISTER.json').read_text())
    for v in cams:
        o = bpy.data.objects[v['camera']]
        for got, expected in zip(o.location, v['pos']):
            close(got, expected, v['camera'] + ' position')
        expected_q = (Vector(v['target'])-o.location).to_track_quat('-Z','Y')
        assert o.rotation_euler.to_quaternion().rotation_difference(expected_q).angle < .0001
        assert o.data.type == v['projection']
        close(o.data.ortho_scale if o.data.type=='ORTHO' else o.data.lens,
              v['scale'] if o.data.type=='ORTHO' else v['lens'], 'camera projection')
    return dict(B0_INTEGRITY='PASS', b0_files_match=len(b0),
                cabinet_order='NARROW -> FRIDGE_AND_OVERHEAD -> INNER_NICHE',
                fridge_front_alignment_error_mm=abs(nb[0][1]-fb[0][1])*1000,
                narrow_four_fronts='PASS', windows='PASS',
                balcony_model_span_mm=(bw[1][0]-bw[0][0])*1000,
                balcony_span_precision='APPROX_DIAGRAM_AXIS_READ; NOT_SITE_SURVEY',
                full_window_under_wall='PASS', buffet_structure='4+4 doors; 2 drawers',
                island='PASS', utility_and_ac='PASS', approved_cameras=len(cams))


def register():
    rows = []
    for root in sorted(bpy.data.objects, key=lambda o:o.name):
        if root.type != 'EMPTY' or not root.name.startswith(('B11_K-', 'B11_SITE_')):
            continue
        meshes = [o for o in root.children_recursive if o.type=='MESH'
                  and not o.hide_render and not o.hide_viewport]
        if not meshes:
            continue
        b = bounds(meshes)
        rows.append(dict(assembly=root.name, parent=root.parent.name if root.parent else None,
                         bounds_mm=[[round(v*1000,3) for v in p] for p in b],
                         world_axis_envelope_mm=[round((b[1][i]-b[0][i])*1000,3) for i in range(3)],
                         active_meshes=[o.name for o in meshes],
                         status='HUMAN_APPROVED_SPATIAL_MODEL_FROZEN',
                         measurement_basis='AUTHORED_MODEL_BOUNDING_BOX; NOT_FABRICATION_MEASUREMENT'))
    return rows


def build():
    assert not MANIFEST.exists(), 'Existing freeze must not be overwritten. Create a new version.'
    b0_check()
    prior = json.loads((SITE/'WINDOW_AND_BUFFET_SITE_REGISTER_V04.json').read_text())
    assert sha(SOURCE) == prior['model_sha256'], 'V4 differs from its register'
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    base = snapshot()
    bpy.ops.wm.open_mainfile(filepath=str(CAM_SOURCE))
    approved = snapshot()
    assert all(approved.get(n)==s for n,s in base.items()), 'Camera source changed V4 objects'
    views = json.loads((SITE/'kitchen_multiview_v4/RENDER_MANIFEST_V4.json').read_text())
    for v in views:
        assert v['source_sha256'] == sha(SOURCE)
        v['original_render_path'] = str((SITE/'kitchen_multiview_v4'/v['path']).resolve())
        v['original_render_sha256'] = sha(v['original_render_path'])
    write('CAMERA_REGISTER.json', views)
    checks = invariants()
    protected = []
    for o in bpy.data.objects:
        if scoped(o):
            o.hide_select = True
            o.lock_location = (True,True,True)
            o.lock_rotation = (True,True,True)
            o.lock_scale = (True,True,True)
            o['kitchen_freeze_version'] = 'V1'
            o['review_status'] = 'HUMAN_APPROVED_SPATIAL_MODEL_FROZEN'
            protected.append(o.name)
    for c in bpy.data.collections:
        if c.name in SCOPED_COLLECTIONS:
            c.hide_select = True
            c['kitchen_freeze_version'] = 'V1'
    scene = bpy.context.scene
    scene['B1_SITE_CORRECTION'] = 'HUMAN_APPROVED_SPATIAL_MODEL_FROZEN'
    scene['kitchen_freeze_manifest'] = str(MANIFEST)
    scene['fabrication_status'] = 'SITE_MEASUREMENTS_AND_EQUIPMENT_DETAILS_REQUIRED'
    scene['approval_date'] = '2026-10-01'
    scene['context_size_rule'] = 'GENERATED_IMAGES_ON_FILESYSTEM; RETURN_PATHS_ONLY'
    scene.camera = bpy.data.objects['KITCHEN_REVIEW_CAM_05']
    assert snapshot() == approved, 'Freeze changed authored object state'
    write('APPROVED_OBJECT_SNAPSHOT.json', approved)
    write('KITCHEN_MODEL_REGISTER.json', register())
    bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))
    b0_check()
    dependencies = [SOURCE,CAM_SOURCE,
                    SITE/'WINDOW_AND_BUFFET_SITE_REGISTER_V04.json',
                    SITE/'KITCHEN_COLUMN_LOGIC_V02.json',
                    SITE/'NARROW_FRONT_REFINEMENT_V03.json',
                    SITE/'KITCHEN_ISLAND_AND_UTILITY_REGISTER_V01.json',
                    SITE/'originals/USER_APPROVED_WINDOW_OVERLAY_V04.png',
                    ROOT/'source/世纪欣园3-1-901_cabinet_plan.pdf',
                    ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json']
    pinned = [MODEL,OUT/'APPROVED_OBJECT_SNAPSHOT.json',OUT/'KITCHEN_MODEL_REGISTER.json',
              OUT/'CAMERA_REGISTER.json',OUT/'FREEZE_CONTRACT.md',Path(__file__)]
    manifest = dict(spec='KITCHEN AS-IS SPATIAL MODEL FREEZE V1',
                    status='HUMAN_APPROVED_SPATIAL_MODEL_FROZEN', frozen_at=now(),
                    model=str(MODEL), geometry_source=str(SOURCE),
                    camera_source=str(CAM_SOURCE),
                    human_authorization='几张图都基本正确，厨房可以基本定下来，你整理并把厨房建设彻底锁定',
                    approval_scope=['kitchen layout','cabinet and equipment relationships',
                                    'window corrections','complete window under wall',
                                    'photo5 buffet structure','eleven review cameras'],
                    material_stage='SIMPLE_REVIEW', fabrication_release=False,
                    reopening='EXPLICIT_USER_INSTRUCTION; NEW_VERSION; PRESERVE_V1',
                    source_object_count=len(base), master_object_count=len(approved),
                    source_objects_preserved=True, protected_objects=sorted(protected),
                    checks=checks, files_sha256={str(p):sha(p) for p in pinned},
                    sources_sha256={str(p):sha(p) for p in dependencies},
                    approved_render_paths=[v['original_render_path'] for v in views],
                    approved_render_sha256={v['original_render_path']:v['original_render_sha256'] for v in views},
                    image_context_policy='FILESYSTEM_AND_PATHS_ONLY')
    write(MANIFEST.name,manifest)
    print(json.dumps({'build':'PASS','master':str(MODEL),
                      'source_objects_preserved':len(base),'master_objects':len(approved),
                      'protected_objects':len(protected)},ensure_ascii=False))


def verify():
    manifest = json.loads(MANIFEST.read_text())
    for category in ['files_sha256','sources_sha256','approved_render_sha256']:
        for path, expected in manifest[category].items():
            assert sha(path)==expected, f'Hash mismatch: {path}'
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    expected = json.loads((OUT/'APPROVED_OBJECT_SNAPSHOT.json').read_text())
    actual = snapshot()
    assert actual==expected, 'Fresh-open geometry / pose / material / visibility / camera mismatch'
    for name in manifest['protected_objects']:
        o=bpy.data.objects[name]
        assert o.hide_select and all(o.lock_location) and all(o.lock_rotation) and all(o.lock_scale)
    for name in SCOPED_COLLECTIONS:
        assert bpy.data.collections[name].hide_select
    assert bpy.context.scene['B1_SITE_CORRECTION']=='HUMAN_APPROVED_SPATIAL_MODEL_FROZEN'
    checks = invariants()
    checks.update(status='PASS', checked_at=now(), blender_version=bpy.app.version_string,
                  fresh_open_object_states_match=len(actual),
                  protected_objects=len(manifest['protected_objects']),
                  source_files_and_renders_hashes='PASS',
                  master_sha256=sha(MODEL), temporary_render_cuts_saved_to_master=False)
    # Keep the signed release evidence intact when checking the freeze later.
    output = 'KITCHEN_QA_LAST_CHECK.json' if manifest.get('verification_status')=='PASS' else 'KITCHEN_QA.json'
    write(output,checks)
    print(json.dumps(checks,ensure_ascii=False))


def render():
    import bmesh
    manifest=json.loads(MANIFEST.read_text())
    assert sha(MODEL)==manifest['files_sha256'][str(MODEL)]
    finalized=manifest.get('verification_status')=='PASS'
    render_out=(OUT/'rechecks'/datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d-%H%M%S-%f')
                if finalized else OUT/'verification_renders')
    render_out.mkdir(parents=True,exist_ok=True)
    result=[]
    for v in json.loads((OUT/'CAMERA_REGISTER.json').read_text()):
        if v['id'] not in ['05','10']:
            continue
        bpy.ops.wm.open_mainfile(filepath=str(MODEL))
        s=bpy.context.scene;s.camera=bpy.data.objects[v['camera']]
        s.render.engine='BLENDER_WORKBENCH'
        shading=s.display.shading
        shading.light='STUDIO';shading.color_type='MATERIAL'
        shading.show_shadows=False;shading.show_cavity=True;shading.cavity_type='BOTH'
        shading.show_specular_highlight=True;shading.background_type='WORLD'
        s.world.color=(.94,.95,.96);s.display.render_aa='32'
        s.view_settings.view_transform='Standard'
        s.render.resolution_x=2000;s.render.resolution_y=1500;s.render.resolution_percentage=100
        s.render.film_transparent=False
        s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
        roi=v['roi'];cuts=[]
        for o in bpy.data.objects:
            if o.type=='FONT':o.hide_render=True;continue
            if o.type!='MESH':continue
            lo,hi=bounds([o])
            if hi[0]<roi[0] or lo[0]>roi[2] or hi[1]<roi[1] or lo[1]>roi[3]:
                o.hide_render=True;continue
            if o.name=='SITE_GROUND' or o.name.startswith(('GLZ_','G_wall_')) or 'GLASS' in o.name:
                o.hide_render=True;continue
            if any(c.name in ['03_EXISTING_CEILING','05_HUMAN_DESIGN_GUIDE','99_TO_VERIFY',
                               '91_ACCESSIBILITY_OPTIONS'] for c in o.users_collection):
                o.hide_render=True;continue
            if (o.name.startswith('W_wall_') and not o.get('review_keep_full_height',False)
                    and o.name!='W_wall_md_0004'):
                o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
                z=(.45 if lo[2]>.30 else 0)+v['cut']
                p=o.matrix_world.inverted()@Vector([0,0,z])
                n=(o.matrix_world.to_3x3().inverted()@Vector([0,0,1])).normalized()
                bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                                      plane_co=p,plane_no=n,clear_outer=True,clear_inner=False,dist=1e-6)
                edges=[e for e in bm.edges if e.is_boundary
                       and all(abs((o.matrix_world@q.co).z-z)<1e-4 for q in e.verts)]
                if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
                bm.to_mesh(o.data);bm.free();cuts.append(o.name)
        assert 'W_wall_md_0042' not in cuts
        bpy.context.view_layer.update()
        path=render_out/f"VERIFIED_{v['id']}_{v['slug']}.png"
        s.render.filepath=str(path)
        start=time.perf_counter();bpy.ops.render.render(write_still=True)
        result.append(dict(id=v['id'],path=str(path),reference=v['original_render_path'],
                           sha256=sha(path),resolution=[2000,1500],engine='WORKBENCH',
                           antialias_samples=32,view_transform='Standard',
                           blender_version=bpy.app.version_string,
                           duration_seconds=round(time.perf_counter()-start,3),
                           temporary_cuts=cuts,source_saved=False))
    assert sha(MODEL)==manifest['files_sha256'][str(MODEL)]
    b0_check()
    write('RENDER_LAST_CHECK_MANIFEST.json' if finalized else 'RENDER_VERIFICATION_MANIFEST.json',result)
    print(json.dumps({'render':'PASS','count':len(result),'master_unchanged':True}))


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['build','verify','render'])
    mode=parser.parse_args(args).mode
    {'build':build,'verify':verify,'render':render}[mode]()
