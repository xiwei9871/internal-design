# blender -b <blend> -P review_views.py -- <mode> <out.png> <x0> <x1> <y0> <y1> <manifest.json>
# P0.2 审核视图: 临时Scene集合隔离渲染, 不改源对象 hide_* 标志.
# mode=arch   : ARCH_FLOOR_PLAN_REVIEW — 排除天花集合/吊顶构件, 平面审图专用.
# mode=ceiling: REFLECTED_CEILING_REVIEW — 仅天花集合+楼梯+错层参照.
# 守卫: arch 模式下渲染集合中若出现天花对象 → FAIL, 不渲染.
import bpy, sys, json, re

argv = sys.argv[sys.argv.index('--')+1:]
mode, out = argv[0], argv[1]
X0,X1,Y0,Y1 = map(float, argv[2:6])
manifest_path = argv[6] if len(argv)>6 else out+'.manifest.json'

CEIL_COLL = re.compile(r'CEILING', re.I)
CEIL_OBJ  = re.compile(r'CEILING|吊顶', re.I)
CTX_COLL  = re.compile(r'STAIRS|SPLIT_LEVEL|CEILING', re.I)

src = bpy.context.scene
top_colls = list(src.collection.children)
def coll_objs(c):
    for o in c.objects: yield o
    for ch in c.children: yield from coll_objs(ch)

if mode=='arch':
    include=[c for c in top_colls if not CEIL_COLL.search(c.name)]
elif mode=='ceiling':
    include=[c for c in top_colls if CTX_COLL.search(c.name)]
else:
    sys.exit('mode must be arch|ceiling')

# 守卫: arch模式下, 渲染集合内不得有可渲染天花对象
# 判定: 名称含CEILING/吊顶, 或 z>2.5m 处水平面(|normal.z|>0.7)面积>1.0m²(吊顶板遮挡)
render_set=[]
for c in include:
    for o in coll_objs(c):
        if not o.hide_render: render_set.append(o.name)
STAIR_ZONE=(5.2,9.2,4.3,8.6)   # 守卫固定针对楼梯错层区, 与渲染窗口无关
def ceiling_slab(o):
    # 吊顶板: 主体为水平面, z>2.5m, 水平面积>1m² 且占总面>50%, 且XY与楼梯区重叠
    if o.type!='MESH': return False
    mw=o.matrix_world; n3=mw.to_3x3(); sc=mw.to_scale().x**2
    hz=tot=0.0; inwin=False
    for p in o.data.polygons:
        a=p.area*sc; tot+=a
        wn=(n3@p.normal).normalized(); c=mw@p.center
        if abs(wn.z)>0.7 and c.z>2.5: hz+=a
        if STAIR_ZONE[0]<=c.x<=STAIR_ZONE[1] and STAIR_ZONE[2]<=c.y<=STAIR_ZONE[3]:
            inwin=True
    return inwin and hz>1.0 and hz>0.5*tot
ceil_leak=[]
for c in include:
    for o in coll_objs(c):
        if o.hide_render: continue
        if CEIL_OBJ.search(o.name) or ceiling_slab(o):
            ceil_leak.append(o.name)
if mode=='arch' and ceil_leak:
    print('FAIL: arch view contains ceiling objects:', ceil_leak)
    sys.exit(2)
if mode=='ceiling':
    ceil_in=[n for n in render_set if CEIL_OBJ.search(n)]
    if not ceil_in: print('FAIL: ceiling view has no ceiling objects'); sys.exit(2)

rev = bpy.data.scenes.new('REVIEW_TMP')
for c in include: rev.collection.children.link(c)
rev.render.engine='BLENDER_WORKBENCH'
rev.display.shading.light='STUDIO'
rev.display.shading.color_type='OBJECT'
rev.display.shading.show_shadows=True
rev.display.shading.show_cavity=True
rev.display.shading.cavity_type='BOTH'
rev.render.film_transparent=True
cx,cy,span=(X0+X1)/2,(Y0+Y1)/2,(Y1-Y0)
rev.render.resolution_x=2100
rev.render.resolution_y=int(2100*span/(X1-X0))
rev.render.resolution_percentage=100
rev.render.image_settings.file_format='PNG'
rev.render.image_settings.color_mode='RGBA'
cam=bpy.data.objects.new('ORTHO_TOP',bpy.data.cameras.new('ORTHO_TOP'))
rev.collection.objects.link(cam)
cam.location=(cx,cy,30.0); cam.rotation_euler=(0,0,0)
cam.data.type='ORTHO'; cam.data.ortho_scale=span
rev.camera=cam
rev.render.filepath=out
try:
    with bpy.context.temp_override(scene=rev):
        bpy.ops.render.render(write_still=True)
except Exception:
    # temp_override(scene) 可能不被本版本支持 → 直接对rev场景渲染
    bpy.context.window.scene = rev
    bpy.ops.render.render(write_still=True)
manifest={'view': 'ARCH_FLOOR_PLAN_REVIEW' if mode=='arch' else 'REFLECTED_CEILING_REVIEW',
          'source_blend': bpy.data.filepath,
          'included_collections':[c.name for c in include],
          'excluded_collections':[c.name for c in top_colls if c not in include],
          'render_object_count':len(render_set),
          'ceiling_objects_in_view':[n for n in render_set if CEIL_OBJ.search(n)],
          'extent_mm':[X0*1000,X1*1000,Y0*1000,Y1*1000]}
json.dump(manifest, open(manifest_path,'w'), indent=1)
print('VIEW_RENDER ->', out, '| objs:', len(render_set), '| ceil_in_view:', manifest['ceiling_objects_in_view'])
