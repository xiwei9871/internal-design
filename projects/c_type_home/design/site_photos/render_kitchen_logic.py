"""Simple human-readable north-row logic evidence; no saved render-only cuts."""
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]

def setup():
    s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH'
    s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL'
    s.display.shading.show_shadows=False;s.display.shading.show_cavity=True
    s.display.shading.cavity_type='BOTH';s.display.shading.background_type='WORLD'
    s.world.color=(.94,.95,.96);s.view_settings.view_transform='Standard'
    s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
    s.render.film_transparent=False;return s

def camera(name,location,target,scale):
    o=bpy.data.objects.get(name)
    if not o:
        c=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,c);bpy.context.scene.collection.objects.link(o)
    o.location=location;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    o.data.type='ORTHO';o.data.ortho_scale=scale;return o

def row_only(prefix):
    roots=[bpy.data.objects.get(n) for n in ['B11_K-FRIDGE','B11_K-FRIDGE-OVERHEAD','B11_K-TALL-L','B11_K-NARROW-OUTER-320']]
    visible=set(o.name for root in roots if root for o in root.children_recursive if o.type=='MESH')
    for o in bpy.data.objects:
        if o.type in ['MESH','FONT']:o.hide_render=o.name not in visible
    s=setup()
    for name,loc,target,scale,wh in [
        ('FRONT',(6.66,1.0,1.205),(6.66,4.0,1.205),3.3,(1500,1300)),
        ('TOP',(6.66,4.0,10),(6.66,4.0,0),2.7,(1800,1100)),
        ('AXON',(3.8,1.5,3.9),(6.66,4.0,1.15),4.0,(1600,1300))]:
        if prefix=='BEFORE' and name!='FRONT':continue
        s.camera=camera('REVIEW_LOGIC_'+name,loc,target,scale)
        s.render.resolution_x=wh[0];s.render.resolution_y=wh[1]
        s.render.filepath=str(OUT/f'RAW_KITCHEN_{prefix}_{name}.png');bpy.ops.render.render(write_still=True)

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'design/blender_b1_1/B1_1_DESIGN_MODEL_V1.blend'))
row_only('BEFORE')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'B1_1_SITE_CORRECTED_V1.blend'))
row_only('AFTER')

# Full kitchen from the original review camera, with presentation cuts in memory only.
bpy.ops.wm.open_mainfile(filepath=str(OUT/'B1_1_SITE_CORRECTED_V1.blend'))
s=setup();s.camera=bpy.data.objects['B11_CAM_KITCHEN'];s.render.resolution_x=1800;s.render.resolution_y=1350
for o in list(bpy.data.objects):
    if o.type=='FONT':o.hide_render=True
    if o.type!='MESH':continue
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
    if hi[0]<5.50 or lo[0]>8.10 or hi[1]<-.30 or lo[1]>4.60:o.hide_render=True;continue
    if o.name=='SITE_GROUND' or o.name.startswith(('GLZ_','G_wall_')) or 'GLASS' in o.name:o.hide_render=True;continue
    if o.name.startswith('W_wall_'):
        o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
        z=(.45 if lo[2]>.30 else 0)+.45
        plane=o.matrix_world.inverted()@Vector([0,0,z])
        normal=(o.matrix_world.to_3x3().inverted()@Vector([0,0,1])).normalized()
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=plane,plane_no=normal,
            clear_outer=True,clear_inner=False,dist=1e-6)
        edges=[e for e in bm.edges if e.is_boundary and all(abs((o.matrix_world@v.co).z-z)<1e-4 for v in e.verts)]
        if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
        bm.to_mesh(o.data);bm.free()
bpy.context.view_layer.update();s.render.filepath=str(OUT/'RAW_KITCHEN_LOGIC_CORRECTED.png')
bpy.ops.render.render(write_still=True)
print('KITCHEN_LOGIC_VIEWS_DONE')
