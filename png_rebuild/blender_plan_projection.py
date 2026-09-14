import bpy, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent; DATA=json.loads((ROOT/'plan_geometry.json').read_text()); PX=DATA['metres_per_pixel']; bpy.ops.wm.read_factory_settings(use_empty=True)
line_mat=bpy.data.materials.new('Blender projected wall lines'); line_mat.use_nodes=True; nodes=line_mat.node_tree.nodes; links=line_mat.node_tree.links; nodes.clear(); out=nodes.new('ShaderNodeOutputMaterial'); em=nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value=(0.9,0.04,0.04,1); em.inputs['Strength'].default_value=2.0; links.new(em.outputs['Emission'],out.inputs['Surface'])
for entry in DATA['walls']:
 pts=entry['polygon']; curve=bpy.data.curves.new('Projected_'+entry['name'],'CURVE'); curve.dimensions='3D'; curve.bevel_depth=0.014; curve.bevel_resolution=0; spline=curve.splines.new('POLY'); spline.points.add(len(pts)-1)
 for point,(x,y) in zip(spline.points,pts): point.co=(x*PX,y*PX,0.10,1)
 spline.use_cyclic_u=True; obj=bpy.data.objects.new('Projected_'+entry['name'],curve); bpy.context.collection.objects.link(obj); obj.data.materials.append(line_mat)
bpy.ops.object.camera_add(location=(831.5*PX,742.5*PX,20)); cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=1663*PX; cam.rotation_euler=(0,0,0); bpy.context.scene.camera=cam
scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_x=1663; scene.render.resolution_y=1485; scene.render.resolution_percentage=100; scene.render.film_transparent=True; scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'; scene.render.filepath=str(ROOT/'blender_projection_raw.png'); scene.view_settings.view_transform='Standard'; scene.view_settings.look='None'; scene.view_settings.exposure=0; scene.view_settings.gamma=1
bpy.ops.render.render(write_still=True)
