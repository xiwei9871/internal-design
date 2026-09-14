import bpy

scene = bpy.context.scene
scene.camera = bpy.data.objects.get("Camera_living")
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.35, 0.35, 1.0)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
scene.render.filepath = "/Users/xiwei/interior_design/scheme_a_v11/diagnostic_living_world.png"
bpy.ops.render.render(write_still=True)
print("wrote diagnostic_living_world.png")
