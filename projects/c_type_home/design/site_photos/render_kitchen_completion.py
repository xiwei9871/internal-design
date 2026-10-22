"""Final kitchen and island/cabinet relationship review views; never save temporary cuts."""
import bpy
import bmesh
import json
import sys
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
MODEL=OUT/'B1_1_SITE_CORRECTED_V2.blend'
views=['KITCHEN_COMPLETE','ISLAND_UTILITY','KITCHEN_TOP']
if '--' in sys.argv:views=sys.argv[sys.argv.index('--')+1:]
manifest_path=OUT/'KITCHEN_COMPLETION_RENDER_MANIFEST.json'
evidence=[e for e in json.loads(manifest_path.read_text()) if e['view'] not in views] if manifest_path.exists() else []
for view in views:
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
    scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=True
    scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD'
    scene.world.color=(.94,.95,.96);scene.view_settings.view_transform='Standard'
    scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG'
    scene.render.resolution_percentage=100;scene.render.resolution_x=1800;scene.render.resolution_y=1350
    scene.camera=bpy.data.objects['SITE_LOGIC_'+view]
    if view=='KITCHEN_TOP':scene.camera.data.ortho_scale=7.0
    if view=='ISLAND_UTILITY':
        visible={o.name for o in bpy.data.collections['COL_SITE_KITCHEN_ISLAND_AND_UTILITY'].objects if o.type=='MESH'}
        for o in bpy.data.objects:
            if o.type in ['MESH','FONT']:o.hide_render=o.name not in visible
    else:
        for o in list(bpy.data.objects):
            if o.type=='FONT':o.hide_render=True
            if o.type!='MESH':continue
            pts=[o.matrix_world@Vector(v) for v in o.bound_box]
            lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
            if hi[0]<4.7 or lo[0]>8.1 or hi[1]<-.3 or lo[1]>4.6:o.hide_render=True;continue
            if o.name=='SITE_GROUND' or o.name.startswith(('GLZ_','G_wall_')) or 'GLASS' in o.name:o.hide_render=True;continue
            if o.name.startswith('W_wall_'):
                o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
                z=(.45 if lo[2]>.3 else 0)+.45
                p=o.matrix_world.inverted()@Vector([0,0,z]);n=(o.matrix_world.to_3x3().inverted()@Vector([0,0,1])).normalized()
                bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=p,plane_no=n,
                    clear_outer=True,clear_inner=False,dist=1e-6)
                boundary=[e for e in bm.edges if e.is_boundary and all(abs((o.matrix_world@v.co).z-z)<1e-4 for v in e.verts)]
                if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
                bm.to_mesh(o.data);bm.free()
    bpy.context.view_layer.update()
    scene.render.filepath=str(OUT/f'RAW_SITE_{view}.png');bpy.ops.render.render(write_still=True)
    evidence.append(dict(view=view,camera=scene.camera.name,ortho_scale=scene.camera.data.ortho_scale,file=scene.render.filepath,engine='WORKBENCH',
        temporary_display_cuts_only=True,source_saved=False))
(OUT/'KITCHEN_COMPLETION_RENDER_MANIFEST.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
print('KITCHEN_COMPLETION_VIEWS_DONE')
