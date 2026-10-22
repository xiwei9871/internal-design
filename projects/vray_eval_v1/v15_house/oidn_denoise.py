import bpy, sys
argv = sys.argv[sys.argv.index('--')+1:]
src, dst = argv[0], argv[1]
img = bpy.data.images.load(src)
scn = bpy.context.scene
ng = bpy.data.node_groups.new('cmp', 'CompositorNodeTree')
scn.compositing_node_group = ng
ng.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
inp = ng.nodes.new('CompositorNodeImage'); inp.image = img
dn = ng.nodes.new('CompositorNodeDenoise')
out = ng.nodes.new('NodeGroupOutput')
ng.links.new(inp.outputs['Image'], dn.inputs['Image'])
ng.links.new(dn.outputs['Image'], out.inputs['Image'])
scn.render.image_settings.file_format='PNG'
scn.render.filepath = dst
scn.render.resolution_x = img.size[0]; scn.render.resolution_y = img.size[1]; scn.render.resolution_percentage = 100
bpy.ops.render.render(write_still=True)
