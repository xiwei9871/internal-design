import bpy
from mathutils import Vector

scene = bpy.context.scene
scene.render.filepath = "/Users/xiwei/interior_design/scheme_a_v11/diagnostic_top.png"
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100

bpy.ops.object.camera_add(location=(6.3, 5.85, 20.0))
camera = bpy.context.object
camera.data.type = "ORTHO"
camera.data.ortho_scale = 13.2
camera.rotation_euler = (Vector((6.3, 5.85, 0.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = camera
scene.render.film_transparent = False
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.12, 0.12, 0.12, 1.0)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
bpy.ops.render.render(write_still=True)
print("wrote diagnostic_top.png")
