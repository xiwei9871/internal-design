import bpy
o = bpy.data.objects['R3_COMPLETE_PARTITION_WALLS']
for v in o.data.vertices: v.co.x += 0.1
o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('MOVED R3 mesh +0.1m')
