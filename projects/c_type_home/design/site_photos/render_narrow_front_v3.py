"""Re-render unchanged view 03 to inspect only the narrow cabinet front refinement."""
import bpy
import bmesh
import json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
dest=OUT/'kitchen_multiview_v3';dest.mkdir(exist_ok=True)
view=json.loads((OUT/'kitchen_multiview_v2/CAMERA_DEFINITIONS.json').read_text())[2]
bpy.ops.wm.open_mainfile(filepath=str(OUT/'B1_1_SITE_CORRECTED_V3.blend'))
scene=bpy.context.scene
data=bpy.data.cameras.new('KITCHEN_REVIEW_CAM_03_V3');camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera)
camera.location=view['pos'];camera.rotation_euler=(Vector(view['target'])-camera.location).to_track_quat('-Z','Y').to_euler()
data.lens=view['lens'];data.sensor_width=36;data.sensor_fit='HORIZONTAL';data.clip_start=.025;data.clip_end=100
scene.camera=camera;scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=True
scene.display.shading.background_type='WORLD';scene.world.color=(.94,.95,.96)
scene.display.render_aa='32';scene.view_settings.view_transform='Standard'
scene.render.resolution_x=2000;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
for o in list(bpy.data.objects):
    if o.type=='FONT':o.hide_render=True;continue
    if o.type!='MESH':continue
    pts=[o.matrix_world@Vector(v) for v in o.bound_box];lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
    if hi[0]<4.65 or lo[0]>8.10 or hi[1]<-.30 or lo[1]>4.75:o.hide_render=True;continue
    if o.name=='SITE_GROUND' or o.name.startswith(('GLZ_','G_wall_')) or 'GLASS' in o.name:o.hide_render=True;continue
    if any(c.name in ['03_EXISTING_CEILING','05_HUMAN_DESIGN_GUIDE','99_TO_VERIFY','91_ACCESSIBILITY_OPTIONS'] for c in o.users_collection):o.hide_render=True;continue
    if o.name.startswith('W_wall_'):
        o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
        z=(.45 if lo[2]>.30 else 0)+view['cut'];p=o.matrix_world.inverted()@Vector([0,0,z]);n=(o.matrix_world.to_3x3().inverted()@Vector([0,0,1])).normalized()
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=p,plane_no=n,clear_outer=True,clear_inner=False,dist=1e-6)
        edges=[e for e in bm.edges if e.is_boundary and all(abs((o.matrix_world@v.co).z-z)<1e-4 for v in e.verts)]
        if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
        bm.to_mesh(o.data);bm.free()
bpy.context.view_layer.update();scene.render.filepath=str(dest/'FULL_03_fridge_columns_V3.png')
bpy.ops.render.render(write_still=True)
(dest/'RENDER_MANIFEST_V3.json').write_text(json.dumps(dict(view=view,resolution=[2000,1500],engine='BLENDER_WORKBENCH',blender_version=bpy.app.version_string,
    same_camera_as_V2=True,source_saved=False,temporary_cuts_only=True),ensure_ascii=False,indent=2))
print('NARROW_FRONT_V3_VIEW_DONE')
