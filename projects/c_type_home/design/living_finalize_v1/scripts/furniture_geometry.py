"""Production furniture primitives in metres. Closed solids, named supports and physical UV."""
import bpy,math,hashlib,random
from mathutils import Vector
import materials_library as ML
COL=None;MATS=None

def setup(col,mats):
 global COL,MATS
 COL,MATS=col,mats

def move_collection(obj,col=None):
 target=col or COL
 for c in list(obj.users_collection):c.objects.unlink(obj)
 target.objects.link(obj)

def finish(o,mat,grain='X',bevel=0,segments=4,smooth=True):
 move_collection(o);o.data.materials.append(mat)
 if bevel:
  b=o.modifiers.new('Manufactured edge radius','BEVEL');b.width=bevel;b.segments=segments;b.harden_normals=True
  w=o.modifiers.new('Face-weighted normals','WEIGHTED_NORMAL');w.keep_sharp=True
 for p in o.data.polygons:p.use_smooth=smooth
 ML.assign_uv(o,grain_axis=grain);o['LF_authored']=True;return o

def box(name,loc,dims,mat,bevel=.006,grain=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return finish(o,mat,grain or 'XYZ'[max(range(3),key=lambda i:dims[i])],bevel,4)

def cylinder(name,loc,radius,depth,mat,vertices=64,grain='Z',bevel=.003):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc);o=bpy.context.object;o.name=name;return finish(o,mat,grain,bevel,4)

def rod(name,a,b,radius,mat,vertices=24):
 a,b=Vector(a),Vector(b);o=cylinder(name,(a+b)/2,radius,(b-a).length,mat,vertices,'Z',min(radius*.22,.002));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def tapered_leg(name,xy,topz,width=.05,top_width=.065,lean=(0,0),mat=None):
 x,y=xy;verts=[]
 for z,w,dx,dy in [(.004,width,0,0),(topz,top_width,lean[0],lean[1])]:
  verts += [(x+dx+u*w/2,y+dy+v*w/2,z) for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]]
 mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata(verts,[],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update();o=bpy.data.objects.new(name,mesh);COL.objects.link(o);o.data.materials.append(mat or MATS['WOOD']);b=o.modifiers.new('Leg edge radius','BEVEL');b.width=.004;b.segments=3
 for p in o.data.polygons:p.use_smooth=True
 ML.assign_uv(o,'Z');o['LF_ground_pad']=True;o['LF_authored']=True
 pad=cylinder(name+'_floor_pad',(x,y,.002),width*.40,.004,MATS['DARK'],32,'Z',.0004);pad['LF_ground_contact']=True;return o

def curve_tube(name,points,radius,mat,closed=False,bezier=False):
 data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=16;data.bevel_depth=radius;data.bevel_resolution=3
 s=data.splines.new('BEZIER' if bezier else 'POLY')
 if bezier:
  s.bezier_points.add(len(points)-1)
  for p,v in zip(s.bezier_points,points):p.co=v;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 else:
  s.points.add(len(points)-1)
  for p,v in zip(s.points,points):p.co=(*v,1)
 s.use_cyclic_u=closed;o=bpy.data.objects.new(name,data);COL.objects.link(o);data.materials.append(mat);o['LF_authored']=True;return o

def signpow(x,e):return math.copysign(abs(x)**e,x)

def cushion(name,xy,width,depth,thickness,base_z,mat,e=.32,rotation=None):
 # Superelliptic upholstery, compressed flat support panel, soft upper crown.
 c=thickness/1.8;a,b=width/2,depth/2;nt,np=64,28;verts=[];faces=[]
 phase=(int(hashlib.sha256(name.encode()).hexdigest()[:6],16)%1000)/1000*math.pi*2
 for j in range(np+1):
  phi=-math.pi/2+j*math.pi/np;cp=abs(math.cos(phi))**e;rawz=signpow(math.sin(phi),e)*c;z=max(rawz,-.8*c)
  for i in range(nt):
   t=2*math.pi*i/nt;x=a*cp*signpow(math.cos(t),.22);y=b*cp*signpow(math.sin(t),.22)
   # Small localized cover tension, not large periodic wrinkles.
   relief=.0012*math.sin(7*t+phase)*math.sin(phi*2)**2*abs(math.cos(phi))
   verts.append((x*(1+relief/max(a,.1)),y*(1+relief/max(b,.1)),z+.8*c))
 for j in range(np):
  for i in range(nt):ni=(i+1)%nt;faces.append((j*nt+i,j*nt+ni,(j+1)*nt+ni,(j+1)*nt+i))
 me=bpy.data.meshes.new(name+'_cover');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);COL.objects.link(o);o.location=(*xy,base_z);me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 ML.assign_uv(o,'X');o['LF_authored']=True;o['LF_soft_support_z']=base_z
 # Fine tailored cover piping along the middle panel perimeter.
 points=[]
 for i in range(128):
  t=2*math.pi*i/128;points.append((xy[0]+a*signpow(math.cos(t),.22),xy[1]+b*signpow(math.sin(t),.22),base_z+.8*c))
 pipe=curve_tube(name+'_stitched_piping',points,.00115,MATS['SEAM'],True)
 pipe.parent=o;pipe.matrix_parent_inverse=o.matrix_world.inverted()
 if rotation:o.rotation_euler=rotation
 return o

def back_cushion(name,loc,width,height=.42,thickness=.17,west=True,mat=None):
 # Reorient supported upholstered panel with its bottom compressed at seat.
 o=cushion(name,(loc[0],loc[1]),width,height,thickness,loc[2],mat or MATS['FABRIC'])
 # Mesh originalXY panel: map its heightY to worldZ and thicknessZ to depth.
 o.rotation_euler=(math.pi/2,0,math.pi/2) if west else (math.pi/2,0,0)
 # Set world-space evaluated center, then small back rake.
 o.location=loc
 return o

def rounded_outline(length,width,radius,kind='racetrack',steps=24):
 if kind=='oval':return [(length/2*math.cos(i*2*math.pi/(steps*4)),width/2*math.sin(i*2*math.pi/(steps*4))) for i in range(steps*4)]
 r=min(radius,length/2,width/2);pts=[]
 for cx,cy,start in [(length/2-r,width/2-r,0),(-length/2+r,width/2-r,90),(-length/2+r,-width/2+r,180),(length/2-r,-width/2+r,270)]:
  for j in range(steps+1):ang=math.radians(start+j*90/steps);pts.append((cx+r*math.cos(ang),cy+r*math.sin(ang)))
 return pts

def shaped_top(name,center,length,width,z,thickness,mat,kind='racetrack',grain='Y',radius=None):
 outline=rounded_outline(length,width,radius if radius is not None else width/2,kind);n=len(outline);verts=[(x,y,zz) for zz in [-thickness/2,thickness/2] for x,y in outline];faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
 faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new(name+'_solid');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);COL.objects.link(o);o.location=(*center,z);o.data.materials.append(mat);b=o.modifiers.new('Stone/timber softened edge','BEVEL');b.width=.004 if mat==MATS['STONE'] else .005;b.segments=4;w=o.modifiers.new('Top normals','WEIGHTED_NORMAL');w.keep_sharp=True
 for p in me.polygons:p.use_smooth=True
 ML.assign_uv(o,grain);o['LF_authored']=True;return o

def lathe(name,loc,profile,mat,wall=.006):
 seg=96;outer=list(profile);inner=[(max(r-wall,.004),z) for r,z in reversed(profile[1:])];path=outer+inner+[(max(profile[0][0]-wall,.004),profile[0][1]+wall)];verts=[];faces=[]
 for r,z in path:
  for i in range(seg):t=i*math.tau/seg;verts.append((r*math.cos(t),r*math.sin(t),z))
 for j in range(len(path)-1):
  for i in range(seg):ni=(i+1)%seg;faces.append((j*seg+i,j*seg+ni,(j+1)*seg+ni,(j+1)*seg+i))
 faces += [tuple(range(seg-1,-1,-1)),tuple(range((len(path)-1)*seg,len(path)*seg))]
 me=bpy.data.meshes.new(name+'_hollow');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);COL.objects.link(o);o.location=loc;me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 ML.assign_uv(o,'Z');o['LF_authored']=True;return o

def leaf(name,base,direction,length,width,angle=0):
 d=Vector(direction).normalized();u=d.cross(Vector((0,0,1)))
 if u.length<.1:u=Vector((1,0,0))
 u.normalize();verts=[]
 for j in range(9):
  t=j/8;center=Vector(base)+d*length*t+Vector((0,0,math.sin(t*math.pi)*.009));w=width*.5*math.sin(math.pi*t)**.8
  for v in [-1,0,1]:verts.append(tuple(center+u*w*v+Vector((0,0,-abs(v)*.004*math.sin(t*math.pi)))))
 faces=[(j*3+i,j*3+i+1,(j+1)*3+i+1,(j+1)*3+i) for j in range(8) for i in range(2)];me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);COL.objects.link(o);me.materials.append(MATS['LEAF']);s=o.modifiers.new('Leaf thickness','SOLIDIFY');s.thickness=.0008
 for p in me.polygons:p.use_smooth=True
 o['LF_authored']=True;return o

def material_plain(name,color,rough=.6,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;m.diffuse_color=(*color,1);return m
