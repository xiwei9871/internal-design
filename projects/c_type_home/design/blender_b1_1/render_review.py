"""Review-only cuts made in memory; never save over the candidate/source blend."""
import bpy
import bmesh
import json
import sys
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
MODEL=OUT/'B1_1_DESIGN_MODEL_V1.blend'
bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=True
scene.display.shading.background_type='WORLD';scene.world.color=(.92,.93,.94)
scene.render.resolution_x=1800;scene.render.resolution_y=1350
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard'
region_specs={
 'LIVING':(2.85,7.1,7.8,14.0),
 'KITCHEN':(5.7,-.30,8.1,4.6),
 'LEISURE':(5.5,4.45,8.9,8.1),
 'OWNER_BED':(7.95,-.8,11.55,4.6),
 'MOTHER_BED':(11.55,-.8,15.5,4.6),
 'STUDY':(13.0,6.5,16.4,11.9),
 'GUEST_BED':(9.7,7.8,13.1,11.2),
 'BATH_OWNER':(9.15,4.7,11.4,6.5),
 'BATH_MOTHER':(13.05,4.7,16.35,6.5),
 'BATH_GUEST':(7.95,7.9,9.8,10.95)}
views=list(region_specs)+['TOP','AXON']
if '--' in sys.argv:
    requested=sys.argv[sys.argv.index('--')+1:]
    if requested:views=requested
manifest=[]
prior_manifest=OUT/'B1_1_RENDER_MANIFEST.json'
if prior_manifest.exists():
    manifest=[r for r in json.loads(prior_manifest.read_text()) if r['view'] not in views]
base_hidden={o.name:o.hide_render for o in bpy.data.objects}
render_collection=bpy.data.collections.new('REVIEW_ONLY_IN_MEMORY_CUTS')
scene.collection.children.link(render_collection)

def bounds(o):
    p=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [min(v.x for v in p),min(v.y for v in p),min(v.z for v in p),
            max(v.x for v in p),max(v.y for v in p),max(v.z for v in p)]

def cut_wall(o,top):
    copy=o.copy();copy.data=o.data.copy();copy.name='REVIEW_CUT_'+o.name
    render_collection.objects.link(copy)
    bm=bmesh.new();bm.from_mesh(copy.data)
    # Source wall meshes are in world coordinates with identity object transforms.
    point=copy.matrix_world.inverted()@Vector([0,0,top])
    normal=(copy.matrix_world.to_3x3().inverted()@Vector([0,0,1])).normalized()
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                           plane_co=point,plane_no=normal,clear_outer=True,clear_inner=False,dist=1e-6)
    boundary=[e for e in bm.edges if e.is_boundary and all(abs((copy.matrix_world@v.co).z-top)<1e-4 for v in e.verts)]
    if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
    bm.to_mesh(copy.data);bm.free();copy.hide_render=False
    o.hide_render=True
    return copy

for view in views:
    for o in list(render_collection.objects):bpy.data.objects.remove(o,do_unlink=True)
    for o in bpy.data.objects:
        if o.name in base_hidden:o.hide_render=base_hidden[o.name]
    camera=bpy.data.objects['B11_CAM_'+view];scene.camera=camera
    rect=region_specs.get(view)
    hidden=[];cuts=[]
    for o in list(bpy.data.objects):
        if o.type not in ['MESH','FONT']:continue
        if o.type=='FONT':o.hide_render=True;continue
        if any(c.name in ['03_EXISTING_CEILING','99_TO_VERIFY','05_HUMAN_DESIGN_GUIDE','91_ACCESSIBILITY_OPTIONS'] for c in o.users_collection):
            o.hide_render=True;hidden.append(o.name);continue
        # Transparent faces are suppressed for a legible Workbench dimensional review.
        if o.name.startswith(('GLZ_','G_wall_')) or 'GLASS' in o.name:
            o.hide_render=True;hidden.append(o.name);continue
        if o.name=='SITE_GROUND':
            o.hide_render=True;hidden.append(o.name);continue
        b=bounds(o)
        if rect and (b[3]<rect[0] or b[0]>rect[2] or b[4]<rect[1] or b[1]>rect[3]):
            o.hide_render=True;hidden.append(o.name);continue
        if o.name.startswith('W_wall_'):
            ffl=.45 if b[2]>.30 else 0
            height=.45 if rect else 1.0
            cut_wall(o,ffl+height);cuts.append(dict(source=o.name,review_cut_z_m=ffl+height))
    bpy.context.view_layer.update()
    scene.render.filepath=str(OUT/f'RAW_B1_1_{view}.png')
    bpy.ops.render.render(write_still=True)
    manifest.append(dict(view=view,raw_image=scene.render.filepath,camera=camera.name,
                         resolution=[scene.render.resolution_x,scene.render.resolution_y],
                         engine='BLENDER_WORKBENCH',purpose='DIMENSIONAL_REVIEW_CUTAWAY',
                         temporary_wall_cuts=cuts,hidden_for_review=hidden,
                         source_or_candidate_saved=False,glass_faces_hidden_for_readability=True))
    print('REVIEW_VIEW_DONE '+view,flush=True)
(OUT/'B1_1_RENDER_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('B1_REVIEW_RENDER_DONE',flush=True)
