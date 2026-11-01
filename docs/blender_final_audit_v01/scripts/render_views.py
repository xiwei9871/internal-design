# Read-only EEVEE preview renders of existing cameras. Never saves the .blend.
import bpy, sys, json, time
args = sys.argv[sys.argv.index('--') + 1:]
out_dir, cams = args[0], args[1].split(',')
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
sc.eevee.taa_render_samples = 32
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1600, 900, 100
sc.render.image_settings.file_format = 'PNG'
log = []
for c in cams:
    o = bpy.data.objects.get(c)
    if not o: log.append({'cam': c, 'status': 'MISSING'}); continue
    sc.camera = o; sc.render.filepath = f'{out_dir}/{c}.png'
    t = time.time(); bpy.ops.render.render(write_still=True)
    log.append({'cam': c, 'status': 'OK', 'sec': round(time.time() - t, 1), 'lens': o.data.lens})
json.dump({'engine': sc.render.engine, 'samples': 32, 'res': [1600, 900], 'view_transform': sc.view_settings.view_transform,
           'look': sc.view_settings.look, 'exposure': sc.view_settings.exposure, 'renders': log},
          open(f'{out_dir}/render_log.json', 'w'), indent=1)
print('RENDER_OK', log)
