import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
img = bpy.data.images.load(str(ROOT / 'xuedaojie44_crop2.png'), check_existing=True)

mat = bpy.data.materials.new('DWG reference (unlit)')
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial')
em = nodes.new('ShaderNodeEmission')
tex = nodes.new('ShaderNodeTexImage')
tex.image = img
links.new(tex.outputs['Color'], em.inputs['Color'])
links.new(em.outputs['Emission'], out.inputs['Surface'])

# The crop is 16,000 x 18,000 mm. Keep the aspect ratio exact.
w, h = 16.0, 14.4
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
plane = bpy.context.object
plane.name = 'DWG verified plan reference'
plane.dimensions = (w, h, 1)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
plane.data.materials.append(mat)

bpy.ops.object.camera_add(location=(0, 0, 18), rotation=(0, 0, 0))
cam = bpy.context.object
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 18.0
bpy.context.scene.camera = cam
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1000
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.filepath = str(ROOT / 'blender_dwg_reference.png')
scene.world = bpy.data.worlds.new('Reference World')
scene.world.color = (1, 1, 1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'blender_dwg_reference.blend'))
bpy.ops.render.render(write_still=True)
