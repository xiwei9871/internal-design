"""Render locked views and lossless auxiliary passes from the saved A14 scene."""
import bpy
import sys
import json
import hashlib
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['kitchen','master']
preview='--preview' in args; keys=[x for x in args if not x.startswith('--')]
scene=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences
if sys.platform=='darwin':
    prefs.compute_device_type='METAL'; prefs.get_devices()
    for d in prefs.devices: d.use=(d.type=='METAL')
    if any(d.use for d in prefs.devices): scene.cycles.device='GPU'
if preview:
    scene.render.resolution_x=1000; scene.render.resolution_y=691; scene.cycles.samples=32; scene.cycles.adaptive_threshold=.04
else:
    scene.render.resolution_x=2500; scene.render.resolution_y=1727; scene.cycles.samples=128; scene.cycles.adaptive_threshold=.015
out=ROOT/('preview' if preview else 'renders'); out.mkdir(exist_ok=True)
for key in keys:
    scene.camera=bpy.data.objects['Camera_'+key]; t=time.time()
    if hasattr(scene.render.image_settings,'media_type'): scene.render.image_settings.media_type='IMAGE'
    scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(out/f'{key}.png')
    bpy.ops.render.render(write_still=True)
    if not preview:
        if hasattr(scene.render.image_settings,'media_type'): scene.render.image_settings.media_type='MULTI_LAYER_IMAGE'
        scene.render.image_settings.file_format='OPEN_EXR_MULTILAYER'; scene.render.image_settings.color_depth='16'
        bpy.data.images['Render Result'].save_render(str(out/f'{key}_passes.exr'),scene=scene)
    data={'key':key,'design_sha256':scene['design_sha256'],'build_script_sha256':scene['build_script_sha256'],'camera':scene.camera.name,'device':scene.cycles.device,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'samples':scene.cycles.samples,'seconds':round(time.time()-t,2),'sha256':hashlib.sha256((out/f'{key}.png').read_bytes()).hexdigest(),'status':'physical render, manual review pending'}
    (out/f'{key}.json').write_text(json.dumps(data,indent=2))
    print('VIEW_DONE',json.dumps(data),flush=True)

if not preview:
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='FLAT'; scene.display.shading.color_type='MATERIAL'
    scene.display.shading.show_shadows=False; scene.display.shading.show_cavity=False
    scene.display.shading.show_object_outline=True
    if hasattr(scene.render.image_settings,'media_type'): scene.render.image_settings.media_type='IMAGE'
    scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_depth='8'
    for key in keys:
        scene.camera=bpy.data.objects['Camera_'+key]
        scene.render.filepath=str(out/f'{key}_structure.png'); bpy.ops.render.render(write_still=True)
