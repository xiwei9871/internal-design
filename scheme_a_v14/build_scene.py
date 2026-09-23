"""A14 deterministic scene: approved geometry, metric materials, no generative geometry."""
from pathlib import Path
import sys
import json
import math
import time
import hashlib
import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from design_model import load_design, design_hash, door_leaf_rect
DATA=load_design(); S=DATA['metres_per_pixel']; OX,OY=DATA['origin_source_px']
OUT=ROOT/'renders'; OUT.mkdir(parents=True,exist_ok=True)
GEOMETRY=[]

def xy(x,y,z=0): return ((x-OX)*S,(OY-y)*S,z)

def material(name,color,rough=.6,metal=0,texture=None):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=(*color,1)
    nodes=m.node_tree.nodes; links=m.node_tree.links; bs=nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metal
    if texture:
        tc=nodes.new('ShaderNodeTexCoord'); mp=nodes.new('ShaderNodeVectorMath'); mp.operation='MULTIPLY'
        links.new(tc.outputs['Generated'],mp.inputs[0]); mp.inputs[1].default_value=(6,130,4) if texture=='wood' else (140,140,140)
        noise=nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=1.8; noise.inputs['Detail'].default_value=3
        links.new(mp.outputs[0],noise.inputs['Vector'])
        ramp=nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.15; ramp.color_ramp.elements[1].position=.85
        ramp.color_ramp.elements[0].color=(*(v*.77 for v in color),1)
        ramp.color_ramp.elements[1].color=(*(min(v*1.12,1) for v in color),1)
        links.new(noise.outputs['Fac'],ramp.inputs[0]); links.new(ramp.outputs[0],bs.inputs['Base Color'])
        bump=nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.15
        bump.inputs['Distance'].default_value=.001 if texture=='wood' else .0005
        links.new(noise.outputs['Fac'],bump.inputs['Height']); links.new(bump.outputs[0],bs.inputs['Normal'])
    return m

def box(name,center,size,mat,bevel=.008,id=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center); ob=bpy.context.object; ob.name=name
    ob.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat)
    if bevel:
        mod=ob.modifiers.new('Manufactured edge radius','BEVEL'); mod.width=min(bevel,min(size)/4); mod.segments=3
        ob.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    if id: ob['design_id']=id
    return ob

def rect(name,r,z,h,mat,bevel=.008,id=None):
    x,y,w,l=r; return box(name,xy(x+w/2,y+l/2,z+h/2),(w*S,l*S,h),mat,bevel,id)

def prism(name,poly,z,h,mat,id=None):
    n=len(poly); v=[xy(x,y,z) for x,y in poly]+[xy(x,y,z+h) for x,y in poly]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    me=bpy.data.meshes.new(name); me.from_pydata(v,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat)
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free()
    if id: ob['design_id']=id
    return ob

def cylinder(name,loc,radius,depth,mat,axis='Z'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=depth,location=loc)
    ob=bpy.context.object; ob.name=name
    if axis=='X': ob.rotation_euler.y=math.pi/2
    if axis=='Y': ob.rotation_euler.x=math.pi/2
    ob.data.materials.append(mat)
    for p in ob.data.polygons: p.use_smooth=True
    bevel=ob.modifiers.new('Edge radius','BEVEL'); bevel.width=.003; bevel.segments=2
    return ob

def area(name,loc,target,energy,size,color=(1,.91,.79),size_y=None):
    light=bpy.data.lights.new(name,'AREA'); light.energy=energy; light.shape='RECTANGLE'; light.size=size; light.size_y=size_y or size
    light.color=color; ob=bpy.data.objects.new(name,light); bpy.context.collection.objects.link(ob); ob.location=loc
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler(); return ob

def bbox(objs):
    pts=[o.matrix_world@Vector(v) for o in objs if o.type=='MESH' for v in o.bound_box]
    return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]

def camera_visibility(scene, keys, minimum_clearance_m=.15):
    """Reject near-surface obstruction at the centre, edge midpoints and corners.

    These nine first-hit rays include glass and start at the camera origin,
    before near clipping can conceal a door immediately in front of the lens.
    They are a near-obstruction check, not a full image visibility guarantee.
    """
    depsgraph=bpy.context.evaluated_depsgraph_get()
    checks={}; failures=[]
    samples=[(0,0),(-.5,-.5),(-.5,0),(-.5,.5),(0,-.5),(0,.5),(.5,-.5),(.5,0),(.5,.5)]
    for key in keys:
        camera=bpy.data.objects['Camera_'+key]
        frame=camera.data.view_frame(scene=scene)
        left=min(v.x for v in frame); right=max(v.x for v in frame)
        bottom=min(v.y for v in frame); top=max(v.y for v in frame)
        origin=camera.matrix_world.translation.copy(); rays=[]
        for u,v in samples:
            local=Vector(((left+right)/2+u*(right-left),
                          (bottom+top)/2+v*(top-bottom),frame[0].z))
            direction=(camera.matrix_world.to_3x3()@local).normalized()
            hit,point,normal,index,obj,matrix=scene.ray_cast(depsgraph,origin,direction,distance=100)
            distance=(point-origin).length if hit else None
            blocked=hit and distance<=minimum_clearance_m
            rays.append({'frame_uv':[u,v],'hit_object':obj.name if hit else None,
                         'distance_m':distance,'near_obstruction':blocked})
            if blocked: failures.append(f'{key} ray ({u},{v}) hits {obj.name} at {distance:.4f} m')
        distances=[r['distance_m'] for r in rays if r['distance_m'] is not None]
        checks[key]={'rays':rays,'minimum_hit_distance_m':min(distances) if distances else None,
                     'minimum_required_clearance_m':minimum_clearance_m,
                     'status':'fail' if any(r['near_obstruction'] for r in rays) else 'pass'}
    if failures:
        raise ValueError('Camera near obstruction: '+'; '.join(failures))
    return checks

def furniture(f):
    """Metric assemblies fit inside the approved envelope, without stretching assets."""
    id=f['id']; r=f['rect']; x,y,w,l=r; W,L=w*S,l*S; H=f['height_m']; z=f.get('z_mm',0)/1000
    cx,cy,_=xy(x+w/2,y+l/2); before=set(bpy.data.objects)
    def part(n,u,v,zz,sx,sy,sz,mat,bevel=.012):
        return box(id+'_'+n,(cx+u,cy+v,z+zz),(sx,sy,sz),mat,bevel,id)
    kind=f['kind']; axis=f.get('front_axis','-Y')
    if kind=='bed':
        for u in [-W*.38,W*.38]:
            for v in [-L*.37,L*.37]: part('foot',u,v,.05,.065,.065,.10,WOOD,.008)
        part('ash_frame',0,0,.19,W,L,.22,WOOD)
        part('mattress',-.012,0,H-.12,W-.07,L-.06,.24,LINEN,.05)
        # Headboard remains inside the positive-X short end.
        part('headboard',W/2-.035,0,.46,.07,L,.92,WOOD,.025)
        part('duvet',-W*.13,0,H+.025,W*.69,L-.05,.10,FABRIC,.045)
        for v in [-L*.24,L*.24]: part('pillow',W*.29,v,H+.065,.40,L*.39,.13,LINEN,.06)
    elif kind=='sofa':
        for u in [-W*.35,W*.35]:
            for v in [-L*.4,L*.4]: part('foot',u,v,.05,.055,.055,.10,WOOD,.008)
        part('base',0,0,.22,W,L,.30,FABRIC,.065)
        part('back',W/2-.11,0,.58,.22,L,.5,FABRIC,.075)
        for v in [-L/2+.095,L/2-.095]: part('arm',0,v,.48,W,.19,.48,FABRIC,.065)
        for v in [-L*.23,L*.23]: part('seat',-.06,v,.43,W-.22,L*.43,.18,LINEN,.055)
    elif kind=='chair':
        seat=.45; part('seat',0,0,seat,W,L,.065,FABRIC,.03)
        for u in [-W*.35,W*.35]:
            for v in [-L*.35,L*.35]: part('leg',u,v,.22,.027,.027,.44,WOOD,.006)
        if axis in ['-Y','+Y']:
            sign=1 if axis=='-Y' else -1
            part('back',0,sign*(L/2-.035),(seat+H)/2,W,.06,H-seat,WOOD,.02)
        else: part('back',(-1 if axis=='+X' else 1)*(W/2-.03),0,(seat+H)/2,.06,L,H-seat,WOOD,.02)
    elif kind=='wc':
        part('tank',-W/2+.13,0,.51,.25,L*.90,.62,CERAMIC,.065)
        part('pedestal',W*.06,0,.19,W*.55,L*.62,.38,CERAMIC,.07)
        part('bowl',W*.09,0,.35,W*.76,L,.22,CERAMIC,.10)
        part('seat',W*.13,0,.465,W*.71,L*.90,.05,CERAMIC,.08)
    elif kind=='bathtub':
        part('base',0,0,.12,W,L,.24,CERAMIC,.04)
        for u in [-W/2+.045,W/2-.045]: part('end',u,0,H/2,.09,L,H,CERAMIC,.025)
        for v in [-L/2+.045,L/2-.045]: part('side',0,v,H/2,W,.09,H,CERAMIC,.025)
    elif kind=='shower':
        part('wet_floor',0,0,.008,W,L,.016,TILE,.003)
        # 10 mm real glass; clear side opening maintained rather than a full wall.
        part('glass',W*.22,-L/2+.05,1.05,W*.56,.01,2.10,GLASS,.001)
        part('top_rail',W*.22,-L/2+.05,2.105,W*.56,.016,.016,METAL,.002)
    elif kind=='sink':
        part('cabinet',0,0,(H-.03)/2,W,L,H-.03,WOOD)
        part('counter',0,0,H-.015,W,L,.03,STONE)
        part('bowl',W*.08,0,H+.04,W*.68,L*.72,.1,CERAMIC,.045)
        cylinder(id+'_tap', (cx-W*.3,cy,z+H+.19),.012,.32,METAL)
    elif id=='FURN-028':
        part('mirror_cabinet',0,0,H/2,W,L,H,WOOD)
        part('mirror',W/2+.001,0,H/2,.003,L-.035,H-.035,MIRROR,.001)
    elif kind in ['table','lowcab'] and (kind=='table' or id in ['FURN-036','FURN-039']):
        part('top',0,0,H-.018,W,L,.036,WOOD,.012)
        for u in [-W*.42,W*.42]:
            for v in [-L*.37,L*.37]: part('leg',u,v,(H-.035)/2,.035,.035,H-.035,WOOD,.004)
    else:
        # Recess carcass behind separate door faces so gaps are real, not coplanar.
        if axis in ['-Y','+Y']:
            sign=-1 if axis=='-Y' else 1
            part('carcass',0,-sign*.012,H/2,W,L-.024,H,WOOD,.003)
        else:
            sign=1 if axis=='+X' else -1
            part('carcass',-sign*.012,0,H/2,W-.024,L,H,WOOD,.003)
        if id in ['FURN-005','FURN-010']:
            part('counter',0,0,H-.015,W,L,.03,STONE,.008)
        # Door gaps inset on the visible face. Faces share the same approved envelope.
        span=W if axis in ['-Y','+Y'] else L
        count=max(1,round(span/.5)); panel=span/count
        for i in range(count):
            off=-span/2+panel*(i+.5)
            if axis in ['-Y','+Y']:
                sign=-1 if axis=='-Y' else 1
                part('front',off,sign*(L/2-.01),H/2,panel-.004,.018,H-.008,WOOD,.002)
                part('finger_pull',off+panel*.30,sign*(L/2+.0005),min(H*.5,1.0),.015,.006,.14,METAL,.002)
            else:
                sign=1 if axis=='+X' else -1
                part('front',sign*(W/2-.01),off,H/2,.018,panel-.004,H-.008,WOOD,.002)
                part('finger_pull',sign*(W/2+.0005),off+panel*.30,min(H*.5,1.0),.006,.015,.14,METAL,.002)
    objects=[o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    GEOMETRY.append({'id':id,'rect_px':r,'height_m':H,'bbox_m':bbox(objects),'part_count':len(objects)})

def service_wall():
    sw=DATA['design']['service_wall']; H=sw['height_mm']/1000
    for b in sw['bays']:
        before=set(bpy.data.objects)
        x,y,w,l=b['rect_px']; cx,cy,_=xy(x+w/2,y+l/2); W,L=w*S,l*S
        for yy in [-L/2+.009,L/2-.009]: box(b['id']+'_side',(cx,cy+yy,H/2),(W,.018,H),WOOD)
        box(b['id']+'_top',(cx,cy,H-.009),(W,L,.018),WOOD)
        box(b['id']+'_back',(cx-W/2+.009,cy,H/2),(.018,L,H),WOOD)
        appliances=[a for a in sw['appliances'] if a['bay']==b['id']]
        top=max((a['z_mm']+a['height_mm'])/1000 for a in appliances)+.025
        rect(b['id']+'_overhead',b['rect_px'],top,H-top,WOOD)
        for a in appliances:
            aw=a['width_mm']/1000; ah=a['height_mm']/1000; z=a['z_mm']/1000
            name='Appliance_'+a['id']; front=cx+W/2-.055
            box(name,(cx-.02,cy,z+ah/2),(W-.08,aw,ah),WHITE,.01)
            if a['id'] in ['washer','dryer']:
                box(name+'_fascia',(front,cy,z+ah/2),(.018,aw,ah),WHITE,.006)
                cylinder(name+'_rim',(front+.016,cy,z+ah*.47),.215,.024,METAL,'X')
                cylinder(name+'_glass',(front+.03,cy,z+ah*.47),.179,.027,BLACK,'X')
                cylinder(name+'_dial',(front+.022,cy-aw*.30,z+ah*.89),.024,.018,METAL,'X')
                box(name+'_display',(front+.012,cy+aw*.18,z+ah*.90),(.007,.15,.047),BLACK,.002)
            elif a['id'] in ['oven','steam']:
                box(name+'_glass',(front+.007,cy,z+ah/2),(.016,aw-.015,ah-.015),BLACK,.005)
                box(name+'_handle',(front+.045,cy,z+ah*.76),(.026,aw*.72,.025),METAL,.005)
            else:
                box(name+'_steel',(front+.006,cy,z+ah/2),(.018,aw,ah),METAL,.006)
                box(name+'_seam',(front+.018,cy,z+ah*.34),(.002,aw,.003),BLACK,.001)
                box(name+'_handle',(front+.04,cy-aw*.39,z+ah*.66),(.025,.022,.6),METAL,.006)
        if b['id']=='oven': rect('oven_lower_storage',b['rect_px'],0,.52,WOOD)
        objects=[o for o in bpy.data.objects if o not in before]
        for ob in objects: ob['design_id']=b['furniture_id']
        bpy.context.view_layer.update()
        GEOMETRY.append({'id':b['furniture_id'],'rect_px':b['rect_px'],'height_m':H,'bbox_m':bbox(objects),'part_count':len(objects)})

def openings():
    wall_height=DATA['design']['wall_height_mm']/1000
    for w in DATA['windows']:
        x1,y1,x2,y2=w['segment']; horizontal=abs(x2-x1)>abs(y2-y1)
        length=math.hypot(x2-x1,y2-y1)*S; cx,cy,_=xy((x1+x2)/2,(y1+y2)/2)
        sill=w['sill_mm']/1000; head=w['head_mm']/1000
        dims=(length,.025,head-sill) if horizontal else (.025,length,head-sill)
        box(w['id']+'_glass',(cx,cy,(sill+head)/2),dims,GLASS,.001,w['id'])
        if w['type']=='window':
            box(w['id']+'_sillwall',(cx,cy,sill/2),(length,.12,sill) if horizontal else (.12,length,sill),WALL,0,w['id'])
        if head<wall_height: box(w['id']+'_lintel',(cx,cy,(head+wall_height)/2),(length,.12,wall_height-head) if horizontal else (.12,length,wall_height-head),WALL,0,w['id'])
        for z in [sill+.025,head-.025]:
            box(w['id']+'_frame',(cx,cy,z),(length,.06,.05) if horizontal else (.06,length,.05),METAL,.003)
        count=max(1,round(length/1.1))
        for i in range(count+1):
            offset=-length/2+i*length/count
            box(w['id']+'_mullion',(cx+offset if horizontal else cx,cy if horizontal else cy+offset,(sill+head)/2),(.035,.06,head-sill) if horizontal else (.06,.035,head-sill),METAL,.002)
        if w['type']=='window':
            center=Vector((cx,cy,(sill+head)/2)); direction=Vector((0,-1 if cy>5 else 1,0)) if horizontal else Vector((1 if cx<4 else -1,0,0))
            area(w['id']+'_daylight',center-direction*.18,center+direction,80*length,length,(.82,.90,1),head-sill)
    for d in DATA['doors']:
        rect(d['id'],door_leaf_rect(d),0,d['height_mm']/1000,WOOD,.008,d['id'])
        hx,hy=d['hinge']; lx,ly=d['closed']; horizontal=abs(lx-hx)>abs(ly-hy)
        length=math.hypot(lx-hx,ly-hy)*S; cx,cy,_=xy((hx+lx)/2,(hy+ly)/2)
        head=d['height_mm']/1000
        box(d['id']+'_lintel',(cx,cy,(head+wall_height)/2),(length,.12,wall_height-head) if horizontal else (.12,length,wall_height-head),WALL,0)

def main():
    global WOOD,WALL,TILE,STONE,FABRIC,LINEN,GLASS,METAL,BLACK,WHITE,CERAMIC,MIRROR
    bpy.ops.wm.read_factory_settings(use_empty=True)
    WOOD=material('White ash / matte grain',(.56,.42,.28),.43,texture='wood')
    WALL=material('Warm white plaster',(.78,.76,.72),.82)
    TILE=material('Warm grey porcelain',(.44,.43,.40),.48,texture='stone')
    STONE=material('Ivory quartz',(.70,.68,.62),.30,texture='stone')
    FABRIC=material('Warm linen woven',(.46,.43,.37),.88,texture='fabric')
    LINEN=material('Ivory cotton',(.81,.79,.72),.9,texture='fabric')
    WHITE=material('Appliance enamel',(.8,.82,.8),.27)
    CERAMIC=material('Ceramic glaze',(.88,.88,.84),.18)
    METAL=material('Brushed nickel',(.40,.43,.44),.26,.82)
    BLACK=material('Smoked appliance glass',(.018,.022,.023),.18,.25)
    GLASS=material('Clear glass / physical transmission',(.98,.99,1),.025)
    bs=GLASS.node_tree.nodes.get('Principled BSDF'); bs.inputs['Transmission Weight'].default_value=1; bs.inputs['IOR'].default_value=1.45
    MIRROR=material('Bathroom mirror',(.85,.85,.85),.025,1)
    FLOOR=material('Natural oak floor',(.43,.29,.17),.48,texture='wood')
    # Metric plank pattern shares a single global coordinate system.
    n=FLOOR.node_tree.nodes; lk=FLOOR.node_tree.links; geo=n.new('ShaderNodeNewGeometry'); brick=n.new('ShaderNodeTexBrick')
    brick.inputs['Scale'].default_value=1; brick.inputs['Brick Width'].default_value=1.8; brick.inputs['Row Height'].default_value=.16
    brick.inputs['Mortar Size'].default_value=.0015; brick.inputs['Color1'].default_value=(.48,.34,.21,1); brick.inputs['Color2'].default_value=(.40,.27,.15,1); brick.inputs['Mortar'].default_value=(.2,.13,.08,1)
    lk.new(geo.outputs['Position'],brick.inputs['Vector']); lk.new(brick.outputs['Color'],n.get('Principled BSDF').inputs['Base Color'])
    heights=DATA['design']; slab=heights['floor_slab_thickness_mm']/1000; wall_h=heights['wall_height_mm']/1000
    dry_h=heights['ceiling_mm']['dry']/1000; wet_h=heights['ceiling_mm']['wet']/1000
    prism('Floor',DATA['outer'],-slab-.004,slab,FLOOR)
    for z in DATA['zones']:
        prism(z['id'],z['polygon'],-.004,.004,TILE if z.get('material') in ['wet','tile'] else FLOOR,z['id'])
    for w in DATA['walls']: prism(w['id'],w['polygon'],0,wall_h,WALL,w['id'])
    prism('Dry ceiling',DATA['outer'],dry_h,wall_h-dry_h,WALL)
    for z in DATA['zones']:
        if z.get('material') in ['wet','tile']: prism(z['id']+'_ceiling',z['polygon'],wet_h,.025,WALL)
    openings()
    for f in DATA['furniture']:
        if f.get('status')=='reserved_not_installed' or f.get('role')=='service_column_envelope': continue
        furniture(f)
    service_wall()
    # Kitchen sink is on the approved west return, hob on the northern counter.
    kitchen=DATA['design']['kitchen']; counter_h=kitchen['counter_height_mm']/1000
    rect('Kitchen hob',kitchen['hob_rect_px'],counter_h+.002,.018,BLACK,.005)
    rect('Kitchen sink steel',kitchen['sink_rect_px'],counter_h+.001,.009,METAL,.035)
    r=kitchen['sink_rect_px']; x,y,_=xy(r[0]+r[2]*.15,r[1]+r[3]/2)
    cylinder('Kitchen faucet',(x,y,counter_h+.14),.014,.28,METAL)
    # Television is an appearance component within the approved television cabinet footprint.
    f=next(f for f in DATA['furniture'] if f['id']=='FURN-020'); x,y,w,l=f['rect']
    rect('TV panel',[x+4,y+18,2,l-36],.60,.82,BLACK,.008)
    # Soft ceiling fixtures tied to room centres; lighting refinements remain a design preview.
    for i,(px,py,power,size) in enumerate([(980,1030,160,2.2),(600,230,110,1.8),(600,1000,100,1.6),(980,480,95,1.6),(1300,950,95,1.6),(320,700,80,1.0),(500,470,80,1.0)]):
        h=2.30 if i in [1,5,6] else 2.50
        area('Room fill '+str(i),xy(px,py,h),xy(px,py,0),power,size)
    world=bpy.data.worlds.new('Daylight'); bpy.context.scene.world=world; world.use_nodes=True
    sky=world.node_tree.nodes.new('ShaderNodeTexSky')
    sky.sky_type='MULTIPLE_SCATTERING' if 'MULTIPLE_SCATTERING' in sky.bl_rna.properties['sky_type'].enum_items.keys() else 'NISHITA'
    sky.sun_elevation=math.radians(35); sky.sun_rotation=math.radians(135); sky.sun_disc=True; sky.sun_intensity=.5
    world.node_tree.links.new(sky.outputs[0],world.node_tree.nodes['Background'].inputs['Color']); world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25
    # Neutral exterior context for camera/transmission rays; daylight still illuminates the model.
    wn=world.node_tree.nodes; wl=world.node_tree.links
    context=wn.new('ShaderNodeBackground'); context.inputs['Color'].default_value=(.58,.69,.82,1); context.inputs['Strength'].default_value=.8
    ray=wn.new('ShaderNodeLightPath'); mx=wn.new('ShaderNodeMath'); mx.operation='MAXIMUM'
    wl.new(ray.outputs['Is Camera Ray'],mx.inputs[0]); wl.new(ray.outputs['Is Transmission Ray'],mx.inputs[1])
    mix=wn.new('ShaderNodeMixShader'); wl.new(mx.outputs[0],mix.inputs[0]); wl.new(wn['Background'].outputs[0],mix.inputs[1]); wl.new(context.outputs[0],mix.inputs[2]); wl.new(mix.outputs[0],wn['World Output'].inputs[0])
    anchors=json.loads((ROOT.parent/'scheme_a_v11'/'scene_manifest.json').read_text())['camera_anchors']
    anchors['main_bath']['previous_camera_px']=anchors['main_bath']['camera_px']
    anchors['main_bath']['camera_px']=[360,825]
    anchors['main_bath']['override_reason']='A11 camera sightline intersects open DOOR-006 within 30mm; moved inside bathroom without changing geometry'
    scene=bpy.context.scene
    for key,a in anchors.items():
        data=bpy.data.cameras.new('Camera_'+key); ob=bpy.data.objects.new('Camera_'+key,data); scene.collection.objects.link(ob)
        ob.location=xy(*a['camera_px'],a['height_mm']/1000); target=Vector(xy(*a['target_px'],1.10))
        ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler(); data.lens=a['lens_mm']; data.sensor_width=36; data.clip_start=.03
        a.update(target_height_mm=1100,sensor_width_mm=36,shift_x=0,shift_y=0)
    scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=96
    scene.cycles.use_adaptive_sampling=True; scene.cycles.adaptive_threshold=.02; scene.cycles.use_denoising=True
    scene.cycles.max_bounces=10; scene.cycles.transmission_bounces=8
    scene.render.resolution_x=1500; scene.render.resolution_y=1036; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGB'
    scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'; scene.view_settings.exposure=0
    layer=scene.view_layers[0]; layer.use_pass_z=True; layer.use_pass_normal=True; layer.use_pass_cryptomatte_object=True; layer.use_pass_cryptomatte_material=True
    scene['design_sha256']=design_hash(); scene['geometry_rule']='Geometry from approved_v14.json; A11 cameras except documented A14 main-bath clearance correction'
    scene['build_script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    bpy.context.view_layer.update()
    visibility=camera_visibility(scene,anchors)
    (ROOT/'geometry_audit.json').write_text(json.dumps({'design_sha256':design_hash(),'furniture':GEOMETRY},ensure_ascii=False,indent=2))
    manifest={'design_sha256':design_hash(),'build_script_sha256':scene['build_script_sha256'],'camera_anchors':anchors,'camera_visibility':visibility,'renderer':'Cycles; render_views selects Metal when available','samples':96,'resolution':[1500,1036],'status':'design preview / not client-approved; no AI geometry','scene_file':'方案A14_同模精细渲染.blend'}
    (ROOT/'scene_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'方案A14_同模精细渲染.blend'))
    print('SCENE_READY',len(scene.objects))

if __name__=='__main__': main()
