import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import bounds
root=Path(__file__).parent
sofa=bpy.data.objects['B11_Rectangle047_CATALOG_00_00'];floor=bpy.data.objects['R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD']
def tree(o):return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],epsilon=1e-6)
print('SOFA_PLATFORM_SURFACE_INTERSECTIONS',len(tree(sofa).overlap(tree(floor))))
scene=bpy.context.scene
for o in scene.objects:
 if o.type=='MESH':o.hide_render=not o.visible_get()
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
camdata=bpy.data.cameras.new('LIVING_REVIEW_VIEW');cam=bpy.data.objects.new(camdata.name,camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.clip_start=.02;camdata.clip_end=100
# Read-only plan view makes the two target positions and window boundary explicit.
cam.location=(5.1,10.3,8.8);cam.rotation_euler=(Vector((5.1,10.3,0))-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=7.4
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(root/'LIVING_SWAP_TOP.png');bpy.ops.render.render(write_still=True)
# Close-up reference review: selected side table only, changes remain transient render state.
for o in scene.objects:
 if o.type=='MESH':o.hide_render=o.name!='B11_Circle_CATALOG_00_00'
camdata.type='PERSP';camdata.lens=45;cam.location=(4.6,11.5,.75);target=Vector((3.92425,12.27906,.23));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x=700;scene.render.resolution_y=700;scene.render.filepath=str(root/'ROUND_SIDE_TABLE_PREVIEW.png');bpy.ops.render.render(write_still=True)
print('Two requested decision previews complete; scene was not saved.')
