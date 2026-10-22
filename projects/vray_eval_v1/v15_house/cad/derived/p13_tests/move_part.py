import bpy
o = bpy.data.objects['VIEW_WALL_R3_WEST_PARTITION']
for v in o.data.vertices: v.co.x += 0.1
o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('MOVED partition +0.1m')