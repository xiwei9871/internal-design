"""Metric construction helpers for evidence-backed custom presentation furniture.

Uses the project's established panel/frame/UV workflows. Product dimensions are
recorded source bounds; AI appearance never supplies architecture dimensions.
"""
import bpy,math
from mathutils import Vector

class Parts:
 def __init__(self,collection,wood,cloth):
  self.collection=collection;self.wood=wood;self.cloth=cloth;self.group=None;self.created=[]
 def assembly(self,name,reference):
  o=bpy.data.objects.new('HOUSE_V1_'+name,None);self.collection.objects.link(o);o['construction_reference']=reference;o['status']='CUSTOM_APPEARANCE_CANDIDATE_NOT_PROCUREMENT';self.group=o;return o
 def finish(self,o,name,mat):
  o.name='HOUSE_V1_'+name
  for c in list(o.users_collection):c.objects.unlink(o)
  self.collection.objects.link(o)
  if self.group:o.parent=self.group
  if mat:o.data.materials.append(mat)
  self.created.append(o)
  if o.type=='MESH':self.uv(o)
  return o
 def uv(self,o):
  me=o.data;uv=me.uv_layers.get('ProductMeters') or me.uv_layers.new(name='ProductMeters');uv.active_render=True
  dimensions=[max(v.co[i] for v in me.vertices)-min(v.co[i] for v in me.vertices) for i in range(3)];long=max(range(3),key=lambda i:dimensions[i])
  for face in me.polygons:
   axes=[i for i in range(3) if i!=max(range(3),key=lambda j:abs(face.normal[j]))]
   if long in axes:axes=[long]+[i for i in axes if i!=long]
   for li in face.loop_indices:
    p=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(p[axes[0]],p[axes[1]])
 def box(self,name,c,size,mat=None,r=.004):
  bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);self.finish(o,name,mat or self.wood)
  if r:
   b=o.modifiers.new('Manufactured radius','BEVEL');b.width=min(r,min(size)*.40);b.segments=6;o.modifiers.new('Planar normals','WEIGHTED_NORMAL')
  return o
 def rod(self,name,a,b,r=.018,mat=None,r2=None):
  a,b=Vector(a),Vector(b);v=b-a;bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=r,radius2=r2 or r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();self.finish(o,name,mat or self.wood)
  for f in o.data.polygons:f.use_smooth=True
  m=o.modifiers.new('Rounded end','BEVEL');m.width=.0015;m.segments=3;return o
 def curve(self,name,pts,r=.006,mat=None,closed=False):
  d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=4;s=d.splines.new('POLY');s.points.add(len(pts)-1);s.use_cyclic_u=closed
  for p,co in zip(s.points,pts):p.co=(*co,1)
  o=bpy.data.objects.new('HOUSE_V1_'+name,d);self.collection.objects.link(o);d.materials.append(mat or self.wood)
  if self.group:o.parent=self.group
  self.created.append(o);return o
 def soft(self,name,c,size,mat=None):
  # Elliptic filled panel with sewn perimeter; supported/crowned, not a box shader.
  nx,ny=48,32;w,d,t=size;verts=[];faces=[]
  for layer in [0,1]:
   for j in range(ny+1):
    v=2*j/ny-1
    for i in range(nx+1):
     u=2*i/nx-1;x=u*w/2*math.sqrt(1-.22*v*v/2);y=v*d/2*math.sqrt(1-.22*u*u/2)
     f=max(0,1-u*u)**.65*max(0,1-v*v)**.6
     z=(-t*.35-t*.15*f) if layer==0 else (t*.12+t*.38*f)
     verts.append((x,y,z))
  stride=(nx+1)*(ny+1)
  for layer in [0,1]:
   for j in range(ny):
    for i in range(nx):
     a=layer*stride+j*(nx+1)+i;q=(a,a+1,a+nx+2,a+nx+1);faces.append(q if layer else q[::-1])
  ring=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
  for k,a in enumerate(ring):b=ring[(k+1)%len(ring)];faces.append((a,b,b+stride,a+stride))
  me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('HOUSE_V1_'+name,me);self.collection.objects.link(o);o.location=c
  if self.group:o.parent=self.group
  me.materials.append(mat or self.cloth)
  for f in me.polygons:f.use_smooth=True
  self.uv(o);self.created.append(o);o['construction']='filled panel/sewn perimeter; static shape, not certified mechanics';return o
 def art(self,name,center,width,height,axis,image=None,mat=None):
  # axis X -> x wall, U follows y. axis Y -> y wall, U follows x.
  x,y,z=center;self.assembly(name,'owner-selected quiet landscape; appearance only, actual wall bounds control position')
  if image:
   m=bpy.data.materials.new('HOUSE_V1_'+name+'_PRINT');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.95;tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(image),check_existing=True);m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
  else:m=mat
  if axis=='X':
   obj=self.box(name+'_canvas',(x,y,z),(.004,width,height),m,r=0)
   for sign in [-1,1]:self.box(name+'_horizontal',(x-.003,y,z+sign*(height/2+.01)),(.026,width+.04,.020));self.box(name+'_vertical',(x-.003,y+sign*(width/2+.01),z),(.026,.020,height+.04))
  else:
   obj=self.box(name+'_canvas',(x,y,z),(width,.004,height),m,r=0)
   for sign in [-1,1]:self.box(name+'_horizontal',(x,y-.003,z+sign*(height/2+.01)),(width+.04,.026,.020));self.box(name+'_vertical',(x+sign*(width/2+.01),y-.003,z),(.020,.026,height+.04))
  uv=obj.data.uv_layers.get('ProductMeters')
  for f in obj.data.polygons:
   for li in f.loop_indices:
    p=obj.data.vertices[obj.data.loops[li].vertex_index].co;uv.data[li].uv=((p.y/width+.5 if axis=='X' else p.x/width+.5),p.z/height+.5)
  return obj
 def bottle(self,name,c,h=.12,r=.027,mat=None):
  x,y,z=c;self.rod(name+'_body',(x,y,z),(x,y,z+h*.82),r,mat);self.rod(name+'_neck',(x,y,z+h*.82),(x,y,z+h),r*.45,mat)
 def towel(self,name,c,size=(.24,.13,.04)):
  return self.soft(name,c,size)
