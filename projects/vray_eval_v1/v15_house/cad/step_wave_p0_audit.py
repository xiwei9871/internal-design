# blender -b V15_WORK.blend -P step_wave_p0_audit.py -- <out_dir>
# P0_STEP_WAVE_AUTHORITY_BREAK — 权威源核查 + 错层区正交俯视直渲
# 输出: 控制台JSON(场景/视图层/参与渲染对象清单/hide状态) + evidence_01 PNG
import bpy, sys, json, hashlib
from mathutils import Vector

argv = sys.argv[sys.argv.index('--')+1:]
OUT = argv[0] if argv else '/tmp'

blend_path = bpy.data.filepath
scn = bpy.context.scene
vl = bpy.context.view_layer

# ---- 错层窗口(米) ----
X0, X1, Y0, Y1 = 5.2, 9.2, 4.3, 8.6

def ob_info(o):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box] if o.type == 'MESH' else []
    if not bb: return None
    xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
    return {'name': o.name, 'type': o.type,
            'bbox': [round(min(xs),3), round(max(xs),3),
                     round(min(ys),3), round(max(ys),3),
                     round(min(zs),3), round(max(zs),3)],
            'hide_viewport': o.hide_viewport, 'hide_render': o.hide_render,
            'hide_get': o.hide_get(),
            'visible_in_view_layer': o.visible_get(),
            'collections': [c.name for c in o.users_collection]}

region_objs = []
for o in scn.objects:
    inf = ob_info(o)
    if not inf: continue
    x0,x1,y0,y1,z0,z1 = inf['bbox']
    if x1 >= X0 and x0 <= X1 and y1 >= Y0 and y0 <= Y1:
        region_objs.append(inf)

watch = {}
for name in ('STEP_0','STEP_1','STEP_2','WAVE_STEP_3_ARRIVAL',
             'FASCIA_PLATFORM_CURVE','FASCIA_CEILING_CURVE',
             'R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD','FLOOR_LOWER',
             'D107_V3_PLATFORM_BASE_CLOSURE'):
    o = bpy.data.objects.get(name)
    watch[name] = ob_info(o) if o else {'exists': False}

report = {
    'blend_path': blend_path,
    'scene': scn.name,
    'view_layer': vl.name,
    'render_engine': scn.render.engine,
    'scene_objects_total': len(scn.objects),
    'region_window_m': [X0,X1,Y0,Y1],
    'region_objects': sorted(region_objs, key=lambda d: d['name']),
    'watch_objects': watch,
}
print('P0_AUDIT_JSON=' + json.dumps(report))

# ---- 错层区正交俯视直渲(同审图裁剪窗) ----
cx, cy, span = (X0+X1)/2, (Y0+Y1)/2, (Y1-Y0)
scn.render.engine = 'BLENDER_WORKBENCH'
scn.display.shading.light = 'STUDIO'
scn.display.shading.color_type = 'OBJECT'
scn.display.shading.show_shadows = True
scn.display.shading.show_cavity = True
scn.display.shading.cavity_type = 'BOTH'
scn.display.shading.curvature_ridge_factor = 1.2
scn.display.shading.curvature_valley_factor = 0.8
scn.render.film_transparent = True
scn.render.resolution_x = 2400
scn.render.resolution_y = int(2400*span/(X1-X0))
scn.render.resolution_percentage = 100
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGBA'

cam = bpy.data.objects.new('ORTHO_TOP', bpy.data.cameras.new('ORTHO_TOP'))
bpy.context.collection.objects.link(cam)
cam.location = (cx, cy, 30.0)
cam.rotation_euler = (0.0, 0.0, 0.0)
cam.data.type = 'ORTHO'
cam.data.ortho_scale = span
scn.camera = cam
scn.render.filepath = OUT + '/step_wave_evidence_01_blender.png'
bpy.ops.render.render(write_still=True)
print('ORTHO_TOP ->', scn.render.filepath, '| extent_mm:', X0*1000, X1*1000, Y0*1000, Y1*1000)
