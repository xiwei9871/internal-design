"""Complete registered doors and remaining projecting bays before wall union."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix

def prepare(root_dir):
    global COL,WALL,WOOD,SOLID,METAL,GLASS,STONE,EXTRA,DISABLED
    COL=bpy.data.collections.new('COL_V4_COMPLETE_DOORS_AND_BAYS');bpy.context.scene.collection.children.link(COL)
    WALL=bpy.data.materials['LIVING_REVIEW_WALL'];WOOD=bpy.data.materials['DOOR_V2_REVIEW_TIMBER_FRAME']
    SOLID=bpy.data.materials['LIVING_REVIEW_SOLID_DOOR'];METAL=bpy.data.materials['LIVING_REVIEW_WINDOW_FRAME']
    GLASS=bpy.data.materials['LIVING_REVIEW_GLASS'];STONE=bpy.data.materials['LIVING_REVIEW_SILL']
    EXTRA=[];DISABLED=[];cuts=[];doors=[];bays=[];rays=[];views=[]
    def disable(name):
        o=bpy.data.objects[name]
        for x in [o,*o.children_recursive]:
            x.hide_render=True;x.hide_viewport=True;x.hide_set(True);DISABLED.append(x.name)
    def group(name):
        o=bpy.data.objects.new('V4_'+name,None);COL.objects.link(o);o['review_status']='HUMAN_REVIEW';return o
    def box(name,lo,hi,mat,parent,wall=False):
        bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)])
        o=bpy.context.object;o.name='V4_'+name;o.dimensions=[hi[i]-lo[i] for i in range(3)]
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        for c in list(o.users_collection):c.objects.unlink(o)
        COL.objects.link(o);o.parent=parent;o.data.materials.append(mat);o.color=mat.diffuse_color
        o['physical_ground_truth']=False;o['review_status']='HUMAN_REVIEW'
        if wall:EXTRA.append(o)
        return o
    def frame_segment(name,a,b,sill,head,parent):
        av,bv=Vector((*a,0)),Vector((*b,0));d=bv-av;length=d.length;u=d.normalized()
        angle=math.atan2(u.y,u.x);t=.035
        def piece(label,low,high,z0,z1,depth,mat):
            o=box(name+'_'+label,[-(high-low)/2,-depth/2,-(z1-z0)/2],[(high-low)/2,depth/2,(z1-z0)/2],mat,parent)
            center=av+u*((low+high)/2);o.location=(center.x,center.y,(z0+z1)/2);o.rotation_euler.z=angle;return o
        piece('JAMB_A',0,t,sill,head,.046,METAL);piece('JAMB_B',length-t,length,sill,head,.046,METAL)
        piece('RAIL_LOW',0,length,sill,sill+t,.046,METAL);piece('RAIL_HIGH',0,length,head-t,head,.046,METAL)
        segments=[0,.18*length,.82*length,length] if length>1 else [0,length]
        for n,(x0,x1) in enumerate(zip(segments,segments[1:])):
            piece(f'GLASS_{n}',x0+t,x1-t,sill+t,head-t,.008,GLASS)
            if n:piece(f'MULLION_{n}',x0-t/2,x0+t/2,sill,head,.046,METAL)
    # All remaining F-DOOR registered ordinary openings, plus entry double leaf.
    records=[
        dict(id='D-STUDY',label='现书房门',axis='x',band=[12.9,6.4,13.1,8.0],span=[6.7,7.55],ffl=.45,ceiling=3.25,hinge_high=False),
        dict(id='D-BATHM',label='内侧卫生间门',axis='y',band=[11.6,6.4,13.1,6.6],span=[11.95,12.8],ffl=.45,ceiling=3.25,hinge_high=True),
        dict(id='D-MB',label='主卫门',axis='x',band=[12.9,4.5,13.1,6.4],span=[4.8,5.55],ffl=.45,ceiling=3.25,hinge_high=False),
        dict(id='D-GUEST-BATH',label='客卫门',axis='y',band=[8.0,7.8,10.0,8.0],span=[8.85,9.6],ffl=.45,ceiling=3.25,hinge_high=True),
        dict(id='D-GUEST-ROOM',label='客房普通门',axis='y',band=[9.85,7.8,12.9,8.0],span=[10.0,10.85],ffl=.45,ceiling=3.25,hinge_high=False),
        dict(id='ENT-1',label='入户子母门',axis='x',band=[2.7,5.2,2.9,6.8],span=[5.44,6.54],ffl=0,ceiling=2.8,hinge_high=True,double=[.35,.75]),
    ]
    for rec in records:
        id=rec['id'];parent=group('DOOR_'+id);axis=rec['axis'];band=rec['band'];a,b=rec['span'];z=rec['ffl'];head=z+2.1
        if axis=='x':normal_lo,normal_hi=band[0],band[2]
        else:normal_lo,normal_hi=band[1],band[3]
        center=(normal_lo+normal_hi)/2
        def oriented(label,t0,t1,n0,n1,z0,z1,mat,wall=False):
            lo=[n0,t0,z0] if axis=='x' else [t0,n0,z0];hi=[n1,t1,z1] if axis=='x' else [t1,n1,z1]
            return box(id+'_'+label,lo,hi,mat,parent,wall)
        box(id+'_COMPLETE_HOST_WALL',[band[0],band[1],z],[band[2],band[3],rec['ceiling']],WALL,parent,True)
        opening_lo=[normal_lo-.02,a-.05,z] if axis=='x' else [a-.05,normal_lo-.02,z]
        opening_hi=[normal_hi+.02,b+.05,head+.05] if axis=='x' else [b+.05,normal_hi+.02,head+.05]
        cuts.append(dict(id=id,lo=opening_lo,hi=opening_hi))
        oriented('JAMB_A',a-.05,a,normal_lo,normal_hi,z,head,WOOD)
        oriented('JAMB_B',b,b+.05,normal_lo,normal_hi,z,head,WOOD)
        oriented('FRAME_HEAD',a-.05,b+.05,normal_lo,normal_hi,head,head+.05,WOOD)
        for side,n0,n1 in [('FRONT',normal_lo-.025,normal_lo),('BACK',normal_hi,normal_hi+.025)]:
            oriented('CASING_A_'+side,a-.07,a-.005,n0,n1,z,head+.075,WOOD)
            oriented('CASING_B_'+side,b+.005,b+.07,n0,n1,z,head+.075,WOOD)
            oriented('CASING_HEAD_'+side,a-.07,b+.07,n0,n1,head+.005,head+.075,WOOD)
        leaves=[];offset=a
        for i,width in enumerate(rec.get('double',[b-a])):
            o=oriented(f'LEAF_{i}',offset,offset+width,center-.02,center+.02,z,head,SOLID);leaves.append(o.name);offset+=width
        hinge=b if rec['hinge_high'] else a;latch=a+.10 if rec['hinge_high'] else b-.10
        for i,zz in enumerate([z+.25,z+1.0,z+1.75]):
            oriented(f'HINGE_{i}',hinge-.012,hinge+.012,normal_lo-.006,normal_lo+.04,zz,zz+.065,METAL)
        oriented('HANDLE_BASE',latch-.018,latch+.018,center-.054,center-.016,z+.90,z+1.09,METAL)
        oriented('HANDLE_LEVER',latch-.06,latch+.06,center-.068,center-.035,z+.98,z+1.01,METAL)
        mid=(a+b)/2;origin=[normal_lo-.5,mid,z+1.0] if axis=='x' else [mid,normal_lo-.5,z+1.0]
        direction=[1,0,0] if axis=='x' else [0,1,0]
        rays.append(dict(label=id+' clear wall aperture',origin=origin,direction=direction,distance=normal_hi-normal_lo+.7))
        parent['door_width_mm']=(b-a)*1000;parent['door_height_mm']=2100;parent['source']='F-DOOR_registered_span; height_review2100'
        doors.append(dict(**rec,root=parent.name,leaves=leaves,width_mm=round((b-a)*1000),height_mm=2100,clear_opening_cut=cuts[-1]))
        pos=[normal_lo-2.8,mid,z+1.4] if axis=='x' else [mid,normal_lo-2.8,z+1.4]
        target=[center,mid,z+1.4] if axis=='x' else [mid,center,z+1.4]
        view=dict(id='DOOR_'+id,name=rec['label']+'完整门洞',camera='V4_CAM_'+id,pos=pos,target=target,lens=24)
        if id in ['D-GUEST-BATH','D-GUEST-ROOM']:
            view.update(pos=[mid,7.20,z+1.4],target=[mid,center,z+1.4],scale=3.9);view.pop('lens')
        elif id=='D-MB':
            view.update(pos=[12.20,mid,z+1.4],target=[center,mid,z+1.4],scale=3.9);view.pop('lens')
        views.append(view)
    # G-GB-BALC glazing occupied old canonical y10.8, outside actual CAD host.
    gp=group('GUEST_ROOM_SLIDING_DOOR')
    source=bpy.data.objects['B11_OPENING_G-GB-BALC']
    for old in source.children_recursive:
        if old.type!='MESH':continue
        o=old.copy();o.data=old.data.copy();COL.objects.link(o);matrix=old.matrix_world.copy();o.parent=gp
        o.matrix_world=matrix;o.matrix_world.translation.y+=.2;o.name='V4_GUEST_'+old.name
    disable('GLZ_G-GB-BALC');disable('B11_OPENING_G-GB-BALC')
    cuts.append(dict(id='G-GB-BALC',lo=[10.4,10.88,.45],hi=[12.4,11.12,2.85]))
    for suffix,z0,z1 in [('BOTTOM',.45,.475),('TOP',2.825,2.85)]:
        box('GUEST_SLIDING_TRACK_'+suffix,[10.4,10.965,z0],[12.4,11.035,z1],METAL,gp)
    for label,lo,hi in [('CASING_LEFT',[10.35,10.86,.45],[10.425,10.90,2.92]),
                        ('CASING_RIGHT',[12.375,10.86,.45],[12.45,10.90,2.92]),
                        ('CASING_HEAD',[10.35,10.86,2.835],[12.45,10.90,2.91])]:box('GUEST_'+label,lo,hi,METAL,gp)
    for i,x in enumerate([11.35,11.45]):box(f'GUEST_HANDLE_{i}',[x,10.96,1.4],[x+.02,10.986,1.57],METAL,gp)
    gp['actual_host_center_y_mm']=11000;gp['old_center_y_mm']=10800
    rays.append(dict(label='Guest sliding through actual host',origin=[11.4,10.5,1.5],direction=[0,1,0],distance=.9))
    views.append(dict(id='GUEST_GLASS',name='客房移门贯穿门洞',camera='V4_CAM_GUEST_GLASS',pos=[11.4,8.35,1.9],target=[11.4,11,1.85],lens=24))
    # Complete surroundings and casing at the existing three-track glass door.
    sp=group('G_DIN_LIV_COMPLETE_SURROUND');disable('GLZ_G-DIN-LIV')
    box('G_DIN_LIV_LEFT_PIER',[2.70,4.53,0],[2.95,4.715,2.8],WALL,sp,True)
    box('G_DIN_LIV_RIGHT_PIER',[5.65,4.50,0],[5.90,4.715,3.25],WALL,sp,True)
    box('G_DIN_LIV_SOLID_HEAD',[2.90,4.53,2.4],[5.70,4.715,2.8],WALL,sp,True)
    for label,lo,hi in [('LEFT',[2.90,4.50,0],[2.975,4.54,2.46]),
                        ('RIGHT',[5.625,4.50,0],[5.70,4.54,2.46]),
                        ('HEAD',[2.90,4.50,2.385],[5.70,4.54,2.46])]:box('G_DIN_LIV_CASING_'+label,lo,hi,METAL,sp)
    cuts.append(dict(id='G-DIN-LIV',lo=[2.95,4.49,0],hi=[5.65,4.755,2.4]))
    rays.append(dict(label='Existing three-track slider clear aperture',origin=[4.30,4.15,1.4],direction=[0,1,0],distance=.9))
    views.append(dict(id='LEISURE_GLASS',name='休闲平台旁移门完整围合',camera='V4_CAM_LEISURE_GLASS',pos=[4.30,7.35,1.65],target=[4.30,4.62,1.4],lens=24))
    # Remaining three bays use the accepted living bay's physical construction.
    defs=[
        dict(id='W-SMB-S',label='次主卧飘窗',old=['W_wall_md_0017','W_wall_md_0020','W_wall_md_0034'],inner=[8.5,-.2,10.9,.2],front=[8.4,-.6498,11.0,-.6498],side_end=.0002,side_x=[8.4499,10.9499],platform=[8.4499,-.673,10.9499,.05],pos=[9.7,2.3,1.85],target=[9.7,-.4,1.85]),
        dict(id='W-MB-S',label='主卧飘窗',old=['W_wall_md_0023','W_wall_md_0029','W_wall_md_0035'],inner=[12.1,-.2,14.8,.2],front=[12.0,-.6498,14.9,-.6498],side_end=.0002,side_x=[12.0499,14.8499],platform=[12.0499,-.673,14.8499,.05],pos=[13.45,2.3,1.85],target=[13.45,-.4,1.85]),
        dict(id='W-STUDY-NE',label='现书房飘窗',old=['W_wall_md_0028','W_wall_md_0031','W_wall_md_0058'],inner=[13.6,10.9,15.7,11.1],front=[13.5,11.7502,15.8,11.7502],side_end=11.1002,side_x=[13.5499,15.7499],platform=[13.5499,11.05,15.7499,11.773],pos=[14.65,8.6,1.9],target=[14.65,11.55,1.8]),
    ]
    for rec in defs:
        id=rec['id'];bp=group('BAY_'+id);sill=.9;head=2.85;roof=3.25
        for old in rec['old']:disable(old)
        for old in ['GLZ_'+id,'B11_OPENING_'+id,'B11_BAY_'+id]:disable(old)
        for old in rec['old']:
            src=bpy.data.objects[old];pts=[src.matrix_world@Vector(c) for c in src.bound_box]
            lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
            # Hidden objects still have cached bounds during this authoring process.
            box(id+'_'+old+'_LOWER',[lo[0],lo[1],0],[hi[0],hi[1],sill-.025],WALL,bp,True)
            box(id+'_'+old+'_HEAD',[lo[0],lo[1],head],[hi[0],hi[1],roof],WALL,bp,True)
        inner=rec['inner'];box(id+'_INNER_LOWER',[inner[0],inner[1],0],[inner[2],inner[3],sill-.025],WALL,bp,True)
        box(id+'_INNER_HEAD',[inner[0],inner[1],head],[inner[2],inner[3],roof],WALL,bp,True)
        pp=rec['platform'];box(id+'_SILL_PLATFORM',[pp[0],pp[1],sill-.025],[pp[2],pp[3],sill],STONE,bp)
        box(id+'_SOLID_UNDER_PLATFORM',[inner[0],pp[1],0],[inner[2],pp[3],sill-.025],WALL,bp,True)
        box(id+'_SOFFIT',[pp[0],pp[1],roof-.025],[pp[2],pp[3],roof],WALL,bp,True)
        f=rec['front'];frame_segment(id+'_FRONT',[f[0],f[1]],[f[2],f[3]],sill,head,bp)
        for n,x in enumerate(rec['side_x']):frame_segment(id+f'_SIDE_{n}',[x,rec['side_end']],[x,f[1]],sill,head,bp)
        cuts.append(dict(id=id+'_INNER_PORTAL',lo=[inner[0],inner[1]-.02,sill],hi=[inner[2],inner[3]+.02,head]))
        if f[1]<0:
            rays.append(dict(label=id+' open inner portal',origin=[(inner[0]+inner[2])/2,.35,1.8],direction=[0,-1,0],distance=.50))
        else:rays.append(dict(label=id+' open inner portal',origin=[(inner[0]+inner[2])/2,10.65,1.8],direction=[0,1,0],distance=.60))
        bp['physical_logic']='OPEN_INNER_PORTAL; PROJECTING_PLATFORM; OUTER_FRONT_AND_SIDE_GLASS'
        bp['projection_mm']=700;bp['sill_mm']=900;bp['head_mm']=2850
        bays.append(dict(id=id,root=bp.name,old_wall_sources=rec['old'],sill_mm=900,head_mm=2850,ceiling_mm=3250,projection_mm=700,platform=pp))
        views.append(dict(id='BAY_'+id,name=rec['label']+'外挑平台与外窗',camera='V4_CAM_BAY_'+id,pos=rec['pos'],target=rec['target'],lens=24))
    return dict(extra_walls=EXTRA,disabled_source_names=list(dict.fromkeys(DISABLED)),cuts=cuts,doors=doors,bays=bays,rays=rays,views=views)
