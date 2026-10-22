import bpy, math
from mathutils import Vector
sc=bpy.context.scene
# 1. 分类材质→viewport色 (不改节点,不保存文件)
TILE=('TILE','CERAMIC','STONE','MARBLE','PORCELAIN','TERRAZZO','BATH','KITCHEN')
WOOD=('WOOD','TIMBER','ASH','OAK','PLANK','PARQUET','FLOOR','DECK')
WALLM=('WALL','PAINT','GYPSUM','PLASTER','CONCRETE','WHITE','GLASS','WINDOW','DOOR','FRAME','JAMB','MULLION','RAIL','SILL','SCREEN','CURTAIN')
def cls(n):
    n=n.upper()
    for k in TILE:
        if k in n: return 'tile'
    for k in WOOD:
        if k in n: return 'wood'
    for k in WALLM:
        if k in n: return 'wall'
    return 'other'
C={'wood':(0.8,0.1,0.1,1),'tile':(0.1,0.8,0.2,1),'wall':(0.1,0.3,0.9,1),'other':(0.5,0.5,0.5,1)}
for m in bpy.data.materials:
    m.diffuse_color=C[cls(m.name)]
# 2. 隐藏天花/屋顶(原俯视隐藏集合) + 高空物体不管(家具留灰)
for c in bpy.data.collections:
    if 'CEILING' in c.name.upper() or 'ROOF' in c.name.upper():
        c.hide_render=True
# 3. 场景XY范围(有体积的对象)
mn=[1e9]*3; mx=[-1e9]*3
for o in sc.objects:
    if o.type=='MESH' and o.visible_get():
        for v in o.bound_box:
            w=o.matrix_world@Vector(v)
            for i in range(3):
                mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
cx,cy=(mn[0]+mx[0])/2,(mn[1]+mx[1])/2
span=max(mx[0]-mn[0],mx[1]-mn[1])*1.02
# 4. 正交相机顶视
cam=bpy.data.objects.new('TOPMAP_CAM',bpy.data.cameras.new('TC'))
cam.data.type='ORTHO'; cam.data.ortho_scale=span
cam.data.clip_end=50000
cam.location=(cx,cy,20000); cam.rotation_euler=(0,0,0)
sc.collection.objects.link(cam); sc.camera=cam
# 5. Workbench材质色平光渲染
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='FLAT'
sc.display.shading.color_type='MATERIAL'
sc.display.shading.show_shadows=False
sc.display.shading.show_cavity=False
sc.render.resolution_x=2048; sc.render.resolution_y=2048; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.render.film_transparent=False
sc.render.filepath='/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad/topmap.png'
bpy.ops.render.render(write_still=True)
print('SPAN',span,'CX',cx,'CY',cy)
