import bpy
def mv(name,x,y,z=None):
    o=bpy.data.objects.get(name)
    if o:
        o.location.x=x/1000; o.location.y=y/1000
        if z is not None: o.location.z=z/1000
        print(name,'->',o.location[:])
# 主卫镜前灯:移到北墙镜子上方
mv('BATH_MST_MIRRORBAR',13600,6330,2320)
# 母卧右床头灯:床东侧外
mv('MOTHER_LAMP_R',15250,1100)
# 主卧右床头灯:床东侧外(床x9137-11267)
mv('COUPLE_LAMP_R',11350,1100)
bpy.ops.wm.save_mainfile()
print('saved')
