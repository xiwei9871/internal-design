# Read-only Cycles spot check with the file's own colour management. Never saves.
import bpy, sys, json, time
a = sys.argv[sys.argv.index('--') + 1:]; out, cams = a[0], a[1].split(',')
sc = bpy.context.scene; sc.render.engine = 'CYCLES'
sc.cycles.samples = 64; sc.cycles.use_denoising = True
try:
    sc.cycles.device = 'GPU'
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
log = []
for c in cams:
    o = bpy.data.objects.get(c); sc.camera = o; sc.render.filepath = f'{out}/{c}_cycles64.png'
    t = time.time(); bpy.ops.render.render(write_still=True); log.append({'cam': c, 'sec': round(time.time() - t, 1)})
json.dump({'engine': 'CYCLES', 'samples': 64, 'denoise': True, 'res': [1280, 720], 'view_transform': sc.view_settings.view_transform,
           'look': sc.view_settings.look, 'exposure': sc.view_settings.exposure, 'renders': log}, open(f'{out}/cycles_log.json', 'w'), indent=1)
print('CYCLES_OK', log)
