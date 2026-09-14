import bpy, json, math, os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT.parent/'scheme_a_v7'/'scheme_a_geometry.json').read_text())
PX=DATA['metres_per_pixel']; Hpx=1485
OUT=ROOT/'renders'; OUT.mkdir(parents=True,exist_ok=True)
# fresh scene
bpy.ops.wm.read_factory_settings(use_empty=True)
# materials
def material(name,color,rough=.45,metal=.0, emission=None):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough; bs.inputs['Metallic'].default_value=metal
    if emission:
        bs.inputs['Emission Color'].default_value=(*emission,1); bs.inputs['Emission Strength'].default_value=0.2
    return m
wood=material('白蜡木·木蜡油',(0.62,.40,.21),.34)
wood_light=material('白蜡木浅色',(0.78,.58,.34),.38)
wood_dark=material('白蜡木边框',(0.32,.18,.08),.38)
fabric=material('麻棉·暖灰',(0.52,.49,.43),.72)
fabric_light=material('麻棉·米灰',(0.70,.65,.56),.72)
wallmat=material('墙面·暖白',(0.90,.88,.82),.8)
ceilingmat=material('吊顶·纯白',(0.97,.97,.95),.9,0.0,emission=(1.0,1.0,1.0))
floorwood=material('地板·浅原木',(0.69,.51,.31),.48)
tile=material('瓷砖·暖灰',(0.72,.75,.72),.32)
tile_dark=material('瓷砖缝',(0.38,.42,.39),.7)
stone=material('台面·浅石材',(0.86,.84,.77),.28)
metal=material('家电·不锈钢',(0.25,.28,.28),.26,.7)
black=material('家电玻璃',(0.03,.04,.04),.18,.35)
ceramic=material('TOTO/科勒·洁具白',(0.96,.97,.94),.16)
glass=material('淋浴玻璃',(0.74,.90,.89),.1)
glass.use_nodes=True; glass.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value=.32; glass.blend_method='BLEND'; glass.show_transparent_back=True
brass=material('卫浴五金',(0.30,.20,.09),.25,.7)
leaf=material('绿植',(0.16,.35,.16),.65)
# conversions
def wp(x,y,z=0): return (x*PX,(Hpx-y)*PX,z)
def rect_loc(x,y,w,h): return wp(x+w/2,y+h/2,0)
def cube(name,loc,dims,mat,bevel=.015):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.dimensions=dims; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if mat:o.data.materials.append(mat)
    if bevel and min(dims)>bevel*2:
        mod=o.modifiers.new('soft edges','BEVEL'); mod.width=bevel; mod.segments=2
    return o
def polygon_prism(name,poly,z0,z1,mat):
    verts=[(*wp(x,y,z0)[:2],z0) for x,y in poly]+[(*wp(x,y,z1)[:2],z1) for x,y in poly]; n=len(poly); faces=[tuple(range(n)),tuple(range(n,2*n))]
    for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(verts,[],faces); me.materials.append(mat); o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); return o
def floor_poly(name,poly,mat,z=.015): return polygon_prism(name,poly,0,z,mat)
def rect_obj(name,x,y,w,h,height,mat,bevel=.015,z=None):
    if z is None:z=height/2
    return cube(name,rect_loc(x,y,w,h)[:2]+(z,),(w*PX,h*PX,height),mat,bevel)
def detail_cube(name,x,y,w,h,z0,z1,mat,bevel=.012): return rect_obj(name,x,y,w,h,z1-z0,mat,bevel,z0+(z1-z0)/2)
def text_empty(name,body,loc,size=.08):
    bpy.ops.object.text_add(location=loc); o=bpy.context.object; o.name=name; o.data.body=body; o.data.align_x='CENTER'; o.data.size=size; o.data.extrude=.002; o.data.materials.append(wallmat); return o
# architecture: exact PNG wall polygons, full-height warm white walls
for entry in DATA['walls']: polygon_prism('Wall_'+entry['name'],entry['polygon'],0,2.65,wallmat)
# floors: outer slab plus room finishes
floor_poly('Whole home floor',DATA['outer'],floorwood,.02)
for z in DATA['zones']:
    mat=tile if z['material']=='wet' else (stone if z['material']=='tile' else floorwood)
    floor_poly('Floor_'+z['name'],z['polygon'],mat,.035)
# ceiling: flat white, kept as separate object for clean ceiling design
ceiling=polygon_prism('平吊顶·白色',DATA['outer'],2.62,2.65,ceilingmat)
# windows: glass planes and warm white trim from source segments
for name,(x1,y1,x2,y2) in [(w['name'],w['segment']) for w in DATA['windows']]:
    # segment midpoint and length, slim glass panel elevated
    mx,my=(x1+x2)/2,(y1+y2)/2; L=math.hypot(x2-x1,y2-y1)*PX
    o=cube('WindowGlass_'+name,wp(mx,my,1.45),(L,.025,1.15),glass,.005)
    if abs(y2-y1)>abs(x2-x1): o.rotation_euler[2]=math.pi/2
    # sill
    cube('WindowSill_'+name,wp(mx,my,0.9),(max(L,.4),.08,.06),wood_light,.01)
# helper furniture
def bed(name,x,y,w,h,head='north'):
    rect_obj(name+' frame',x,y,w,h,.25,wood_dark,.04,.125)
    rect_obj(name+' mattress',x+0.05*PX/PX,y+0.05,w-.1,h-.1,.28,fabric_light,.05,.40)
    # headboard along top of image rect (world y reversed, but visible)
    rect_obj(name+' headboard',x,y,w,55,.95,wood_light,.035,.72)
    rect_obj(name+' duvet',x+0.12,y+0.24,w-.24,h*.54,.06,fabric,.025,.57)
    rect_obj(name+' pillow1',x+w*.58,y+0.14,w*.30,h*.17,.10,ceramic,.04,.67)
    rect_obj(name+' pillow2',x+w*.25,y+0.14,w*.25,h*.17,.10,ceramic,.04,.67)
def wardrobe(name,x,y,w,h):
    rect_obj(name,x,y,w,h,2.35,wood_light,.025,1.175)
    # panel lines / slim pulls
    for xx in [x+w*.33,x+w*.66]: cube(name+' seam',wp(xx,y+h*.5,1.2),(.009,.01,2.1),wood_dark,.002)
    cube(name+' handle',wp(x+w*.52,y+h*.5,1.2),(.018,.018,.55),brass,.004)
def sofa(name,x,y,w,h):
    # wooden outer base and arms inspired by 1030-2 / 2100x900 catalog sofa
    rect_obj(name+' wood base',x,y,w,h*.16,.22,wood_light,.03,.19)
    rect_obj(name+' seat',x+.08*100,y+.12,w-.16*100,h*.58,.42,fabric_light,.07,.50)
    rect_obj(name+' back',x+.12*100,y+.08,w-.24*100,h*.20,.70,fabric_light,.05,.93)
    rect_obj(name+' left arm',x,y,w*.10,h,.78,wood_light,.04,.48)
    rect_obj(name+' right arm',x+w*.90,y,w*.10,h,.78,wood_light,.04,.48)
    for i in range(3): rect_obj(name+f' cushion {i}',x+w*(.14+i*.25),y+.18,w*.22,h*.40,.06,fabric,.03,.73)
def chair(name,x,y,w=.45,h=.52):
    rect_obj(name+' seat',x,y,w/PX,h/PX,.47,wood_light,.025,.50)
    rect_obj(name+' cushion',x+.04/PX,y+.04/PX,w/PX-.08/PX,h/PX-.08/PX,.07,fabric_light,.03,.78)
    # back board at image upper side
    rect_obj(name+' back',x,y,w/PX,.06/PX,.82,wood_light,.02,1.0)
    for dx in [.08,.37]: cube(name+' leg',wp(x+dx/PX,y+h*.82,0.45),(.035,.035,.85),wood_dark,.005)
def cabinet(name,x,y,w,h,height=2.3,mat=wood_light): wardrobe(name,x,y,w,h)
def table(name,x,y,w,h,thick=.12):
    rect_obj(name+' top',x,y,w,h,thick,wood_light,.05,.78)
    for dx in [.10,.90]:
        for dy in [.14,.86]: cube(name+' leg',wp(x+w*dx,y+h*dy,.39),(.07,.07,.74),wood_dark,.02)
def coffee_table(name,x,y,w,h):
    rect_obj(name+' top',x,y,w,h,.11,wood_light,.06,.42)
    for dx in [.18,.82]:
        for dy in [.2,.8]: cube(name+' leg',wp(x+w*dx,y+h*dy,.2),(.045,.045,.38),wood_dark,.015)
def add_tv(name,x,y,w,h):
    rect_obj(name+' cabinet',x,y,w,h,.47,wood_light,.035,.30)
    cube(name+' screen',wp(x+w/2,y-0.015,1.55),(w*PX*.84,.04,1.0),black,.01)
    for xx in [x+w*.38,x+w*.62]: cube(name+' shelf',wp(xx,y+h*.4,.36),(.02,.02,.17),brass,.003)
def add_plant(name,x,y):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.18,depth=.38,location=wp(x,y,.19)); pot=bpy.context.object; pot.name=name+' pot'; pot.data.materials.append(wood_dark)
    for i in range(7):
        a=i*math.tau/7; bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=wp(x+35*math.cos(a),y+30*math.sin(a),.72+(.12 if i%2 else 0))); leafobj=bpy.context.object; leafobj.name=name+' leaf'; leafobj.scale=(.18,.07,.38); leafobj.rotation_euler[2]=a; leafobj.data.materials.append(leaf)
def add_fridge(name,x,y,w=840,h=600,height=1.9):
    rect_obj(name,x,y,w,h,height,metal,.035,height/2)
    rect_obj(name+' door glass',x+w*.06,y+h*.04,w*.88,h*.03,height*.82,black,.006,height*.82)
    cube(name+' handle',wp(x+w*.86,y+h*.52,height*.58),(.025,.025,.75),brass,.006)
def add_appliance(name,x,y,w,h,height,kind):
    rect_obj(name+' carcass',x,y,w,h,height,wood_dark,.02,height/2)
    rect_obj(name+' face',x+w*.06,y+h*.06,w*.88,h*.88,height*.08,black,.01,height*.56)
    if kind=='washer':
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=min(w*PX,h*PX)*.28,depth=.02,location=wp(x+w*.5,y+h*.5,.62)); q=bpy.context.object; q.name=name+' drum'; q.rotation_euler[0]=math.pi/2; q.data.materials.append(glass)
# main furniture from A7 layout
bed('夫妻主卧床',551,906,214,187); bed('老人床',945,390,215,185); bed('儿童床',1244,917,214,158)
for args in [('主卧北衣柜',428,667,224,60),('主卧西衣柜',428,727,60,145),('老人房衣柜',799,334,52,205),('儿童房衣柜',1255,785,203,63),('衣帽区长柜',224,856,60,235)]: wardrobe(*args)
# window custom furniture
rect_obj('主卧窗边书写/梳妆台',489,1268,122,46,.74,wood_light,.025,.77); rect_obj('主卧窗边椅',530,1208,46,49,.45,fabric_light,.03,.62)
rect_obj('儿童窗边学习桌',1200,1252,183,61,.74,wood_light,.025,.77); wardrobe('儿童窗边书柜',1427,1151,31,163)
# dining / living in catalog language
table('白蜡木餐桌·3046',922,789,92,245)
for i,(x,y) in enumerate([(878,827),(878,955),(1020,821),(1020,891)]): chair(f'餐椅·3125_{i}',x,y)
sofa('客厅沙发·1030-2',1020,1090,92,224)
add_tv('电视柜·5015-TS',792,1110,35,184)
coffee_table('客厅茶几',920,1195,56,91); # 简约风首轮不加入大型绿植，避免遮挡客厅动线
# kitchen / service wall
rect_obj('厨房地柜',415,157,364,61,.86,wood_light,.025,.46); rect_obj('厨房石材台面',415,157,364,13,.08,stone,.012,.91)
rect_obj('厨房吊柜',415,228,364,43,1.0,wood_light,.02,1.65)
# hob and sink
rect_obj('厨房灶台',530,168,85,38,.035,black,.006,.965); rect_obj('厨房水槽',690,165,72,43,.03,ceramic,.008,.96)
add_fridge('西门子/同级薄型冰箱',592,322,63,63,1.9); add_appliance('微波蒸箱高柜',592,413,63,70,2.3,'oven'); add_appliance('洗烘一体机柜',592,483,63,73,2.0,'washer')
# bathrooms: sanitary envelopes and brass fittings
# main bath tub in shower bay, plus glass shower screen
def tub(name,x,y,w,h):
    rect_obj(name+' body',x,y,w,h,.52,ceramic,.08,.30); rect_obj(name+' inner',x+35,y+35,w-70,h-70,.08,stone,.06,.60); cube(name+' faucet',wp(x+w*.8,y+h*.5,1.0),(.035,.035,.6),brass,.005)
def wc(name,x,y):
    rect_obj(name+' ceramic',x,y,71,41,.45,ceramic,.11,.23); rect_obj(name+' tank',x+8,y+7,55,18,.60,ceramic,.04,.72)
def sink(name,x,y,w=51,h=61):
    rect_obj(name+' cabinet',x,y,w,h,.82,wood_light,.03,.41); rect_obj(name+' basin',x+5,y+5,w-10,h-10,.08,ceramic,.03,.87); cube(name+' tap',wp(x+w*.5,y+h*.2,1.1),(.025,.025,.48),brass,.004)
tub('主卫科勒浴缸',224,558,153,71); cube('主卫浴缸玻璃屏',wp(377,593,1.1),(.02,0.7,1.75),glass,.005)
wc('主卫TOTO坐便器',224,697); sink('主卫TOTO台盆',224,766)
# secondary shower basin / glass
rect_obj('次卫淋浴底盘',428,334,152,103,.05,stone,.02,.045); cube('次卫玻璃屏',wp(428+76,334+3,1.05),(1.49,.02,2.1),glass,.005); wc('次卫TOTO坐便器',428,467); sink('次卫TOTO台盆',428,551)
# ceiling diffusers / central air indication
for name,x,y,w,h in [('客厅中央空调送风',865,1080,85,18),('餐区中央空调送风',865,770,85,18),('主卧中央空调送风',560,680,75,18),('儿童房中央空调送风',1280,800,75,18),('老人房中央空调送风',910,345,75,18),('厨房中央空调送风',680,160,65,18)]:
    rect_obj(name,x,y,w,h,.025,ceilingmat,.005,2.63)
# lighting
world=bpy.context.scene.world or bpy.data.worlds.new('World'); bpy.context.scene.world=world; world.use_nodes=True; world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.055,0.05,0.04,1); world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8
# Large soft daylight keeps the flat white ceiling readable in every room.
bpy.ops.object.light_add(type='SUN', location=(8,6,8)); sun=bpy.context.object; sun.name='全屋漫射日光'; sun.data.energy=1.8; sun.data.angle=math.radians(25); sun.rotation_euler=(math.radians(28),math.radians(-18),math.radians(25))
def area(name,px,py,energy=450,size=3.0):
    bpy.ops.object.light_add(type='AREA',location=wp(px,py,2.45)); l=bpy.context.object; l.name=name; l.data.energy=energy; l.data.shape='DISK'; l.data.size=size; l.data.color=(1.0,.82,.62); return l
area('客餐厅暖光',980,1040,700,4); area('厨房暖光',600,230,480,3); area('主卧暖光',600,1000,500,3); area('老人房暖光',980,480,450,3); area('儿童房暖光',1300,950,450,3); area('主卫暖光',320,700,350,2); area('次卫暖光',500,470,300,2)
# camera
def look_at(obj,target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def camera(name,loc,target,lens=30):
    bpy.ops.object.camera_add(location=loc); c=bpy.context.object; c.name=name; c.data.lens=lens; look_at(c,target); return c
cams={
 'overview':camera('Camera_Overview',(15,-1,13),wp(850,760,0.8),38),
 'living':camera('Camera_Living',wp(1080,900,1.55),wp(930,1130,1.05),22),
 'kitchen':camera('Camera_Kitchen',wp(735,470,1.48),wp(620,225,1.1),25),
 'master':camera('Camera_Master',wp(730,1240,1.55),wp(570,980,1.0),20),
 'child':camera('Camera_Child',wp(1168,1080,1.48),wp(1320,1000,1.0),20),
 'elder':camera('Camera_Elder',wp(810,620,1.5),wp(980,480,1.05),22),
 'main_bath':camera('Camera_MainBath',wp(395,835,1.42),wp(310,690,1.0),20),
 'secondary_bath':camera('Camera_SecondaryBath',wp(570,625,1.42),wp(500,470,1.0),20),
}
scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_x=960; scene.render.resolution_y=720; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'; scene.render.film_transparent=False; scene.view_settings.look='AgX - Medium High Contrast'; scene.render.image_settings.color_depth='8'; scene.render.resolution_percentage=100
# render overview with ceiling hidden, then interiors with ceiling visible
for key,c in cams.items():
    scene.camera=c; ceiling.hide_render=(key=='overview')
    scene.render.filepath=str(OUT/f'{key}.png'); bpy.ops.render.render(write_still=True)
# restore and save
ceiling.hide_render=False
scene['design_basis']='A7 PNG-anchored layout, white flat ceiling, warm white walls, ash wood furniture, custom cabinetry'
scene['catalog_furniture']='木甲木乙白蜡木系列: 1030-2 sofa; 3046 dining; 3125 chair; 5015-TS TV cabinet; 2019 bed family'
scene['appliance_basis']='Siemens/LG family visual placeholders; final model selection pending electrical schedule'
scene['sanitary_basis']='TOTO/Kohler class proportions; tub is 1500x700 concept in main bath'
scene['central_air']='LG low-static duct / slim duct concept; diffuser positions are design placeholders'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'方案A8_原木简约效果场景.blend'))
manifest={'style':'简约风·原木色·白色平吊顶·中央空调','catalog_pdf':'木甲木乙-白蜡木系列.pdf','catalog_items':['1030-2 双位沙发 2100x900x900','3046-1.4 餐台 1400x800x750','3125 书椅/餐椅 450x520x855','5015-TS 电视柜 1580x400x470','2019系列床','2106系列床头柜/妆台系列'],'cameras':list(cams),'renders':[str(p.relative_to(ROOT)) for p in OUT.glob('*.png')],'note':'尺寸按A7包络建模，墙线来自PNG geometry; appliances/fixtures are visual placeholders until model numbers are chosen'}
(ROOT/'scene_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(manifest,ensure_ascii=False))
