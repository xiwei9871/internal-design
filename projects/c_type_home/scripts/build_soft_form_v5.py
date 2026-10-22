"""Local test: cotton preset, cut-pattern ease, flexible seams and supported filling."""
import bpy,json,math,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/lookdev_v5';DEST=OUT/'soft_form_v3';DEST.mkdir(exist_ok=True)
INPUT=ROOT/'design/product_rebuild_v4/PRESSURE_CUSHION_FORM.blend'
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.gravity=(0,0,-2)
with bpy.data.libraries.load(str(INPUT),link=False) as(a,b):b.meshes=['Closed upholstery sewn sheets.001'] if 'Closed upholstery sewn sheets.001' in a.meshes else [a.meshes[-1]]
base=b.meshes[0]
def prototype(name,thickness):
    me=base.copy();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o)
    bounds=[[min(v.co[i] for v in me.vertices),max(v.co[i] for v in me.vertices)] for i in range(3)]
    dims=[.92,.76,thickness]
    for v in me.vertices:
        for i in range(3):v.co[i]=(v.co[i]-(bounds[i][0]+bounds[i][1])*.5)/(bounds[i][1]-bounds[i][0])*dims[i]
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    # Preserve the original pin locations and grow cloth rest-lengths, rather than
    # starting the simulation from an already larger, relaxed shape key.
    vg=o.vertex_groups.new(name='SupportedLowerPanel')
    for v in me.vertices:
        if v.co.z<-.04:vg.add([v.index],1,'REPLACE')
        elif abs(v.co.x)>.45 or abs(v.co.y)>.37:vg.add([v.index],.2,'REPLACE')
    cl=o.modifiers.new('Cotton cover with filling and fabric ease','CLOTH');s=cl.settings
    # Blender5.2 shipped Cotton preset, with documented local upholstery adjustments.
    s.quality=8;s.mass=.3;s.tension_stiffness=15;s.compression_stiffness=.8;s.shear_stiffness=15;s.bending_stiffness=.035
    s.tension_damping=5;s.compression_damping=5;s.shear_damping=5;s.air_damping=1;s.bending_damping=3
    s.vertex_group_mass=vg.name;s.pin_stiffness=1;s.shrink_min=-.02
    s.use_internal_springs=True;s.internal_tension_stiffness=2;s.internal_compression_stiffness=2
    s.use_pressure=True;s.uniform_pressure_force=.15;s.pressure_factor=8
    cl.collision_settings.use_self_collision=False;cl.point_cache.frame_start=1;cl.point_cache.frame_end=52
    return o
records=[]
for name,thickness in [('SEAT_LOOSE_COTTON',.155),('BACK_LOOSE_COTTON',.214)]:
    o=prototype(name,thickness);scene.frame_set(1);t=time.time();checkpoints=[]
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST/(name+'_SETUP.blend')))
    for frame in range(1,53):
        scene.frame_set(frame);scene.view_layers.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh()
        if frame in [1,26,52]:checkpoints.append({'frame':frame,'bounds_m':[[min(v.co[i] for v in me.vertices) for i in range(3)],[max(v.co[i] for v in me.vertices) for i in range(3)]]})
        e.to_mesh_clear()
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());final=bpy.data.meshes.new_from_object(e);p=bpy.data.objects.new(name+'_STATIC',final);scene.collection.objects.link(p)
    for f in final.polygons:f.use_smooth=True
    o.hide_render=True;o.hide_viewport=True
    records.append({'name':p.name,'checkpoints':checkpoints,'seconds':round(time.time()-t,2)})
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST/(name+'_RESULT.blend')))
    bpy.data.objects.remove(o,do_unlink=True);p.hide_render=True;p.hide_viewport=True
(DEST/'FORM_EVIDENCE.json').write_text(json.dumps({'method':'BlenderCotton preset basis +2pctcloth growth, loose seam group and internal springs/pressure','not_certified':'static styling prototype, not upholstery mechanics certification','records':records},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(DEST/'LOOSE_COTTON_FORMS.blend'));print('V5_SOFT_FORMS_READY')
