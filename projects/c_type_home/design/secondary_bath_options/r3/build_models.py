"""Reproducible A/B review branches from frozen V2 and actual latest FreeCAD shapes."""
import bpy,bmesh,json,math,sys,runpy,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
BASE=ROOT/'design/wall_corners_v5/HOUSE_BASE_GEOMETRY_V2_FROZEN.blend'
L=json.loads((OUT/'LAYOUT_CONTRACT.json').read_text());S=L['shared'];P=L['opening']
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='helpers')
sha=H['sha'];snapshot=H['snapshot']
def write(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def norm(d):return {n:{k:v for k,v in s.items() if k!='matrix_world' or not s['hide_viewport']} for n,s in d.items()}
def integrity():
 m=json.loads((BASE.parent/'HOUSE_BASE_GEOMETRY_V2_FROZEN_MANIFEST.json').read_text())
 assert sha(BASE)==m['model_sha256'];assert sha(L['freecad'])==L['freecad_sha256']
 H['b0_check']()
 km=json.loads((ROOT/'design/kitchen_frozen_v1/KITCHEN_FREEZE_MANIFEST.json').read_text())
 for c in ['files_sha256','sources_sha256','approved_render_sha256']:
  for p,h in km[c].items():assert sha(p)==h,p
 return km
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=m.diffuse_color
 return m
def objmesh(n,vs,fs,m,c):
 mesh=bpy.data.meshes.new(n+'_MESH');mesh.from_pydata(vs,[],fs);mesh.update()
 o=bpy.data.objects.new(n,mesh);c.objects.link(o)
 if m:o.data.materials.append(m);o.color=m.diffuse_color
 o['source_revision']='LATEST_FREECAD_R3';o['review_status']='HUMAN_REVIEW';return o
def box(n,lo,hi,m,c,parent=None):
 a,b,d=lo;x,y,z=hi
 vs=[(a,b,d),(x,b,d),(x,y,d),(a,y,d),(a,b,z),(x,b,z),(x,y,z),(a,y,z)]
 fs=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
 o=objmesh(n,vs,fs,m,c)
 if parent:o.parent=parent
 return o
def bevel(o,w=.003):
 b=o.modifiers.new('Small review edge','BEVEL');b.width=w;b.segments=2
 return o
def bounds(o):
 vs=[o.matrix_world@v.co for v in o.data.vertices]
 return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
def empty(n,c):o=bpy.data.objects.new(n,None);c.objects.link(o);return o
def segment(n,a,b,z0,z1,th,m,c):
 dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy);nx=-dy/length*th/2;ny=dx/length*th/2
 xy=[(a[0]+nx,a[1]+ny),(b[0]+nx,b[1]+ny),(b[0]-nx,b[1]-ny),(a[0]-nx,a[1]-ny)]
 vs=[(x,y,z) for z in (z0,z1) for x,y in xy]
 return objmesh(n,vs,[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]],m,c)
def slab(n,pts,z0,z1,m,c):
 # Convex room/shower boundary: fan caps are valid for these footprints.
 vs=[(x,y,z) for z in (z0,z1) for x,y in pts];count=len(pts)
 fs=[list(reversed(range(count))),list(range(count,count*2))]
 fs.extend([[i,(i+1)%count,(i+1)%count+count,i+count] for i in range(count)])
 return objmesh(n,vs,fs,m,c)
def copy_fitted(prefix,newprefix,oldrect,newrect,c,flip=False):
 out=[];ox0,oy0,ox1,oy1=oldrect;nx0,ny0,nx1,ny1=newrect
 for src in list(bpy.data.objects):
  if src.type!='MESH' or not src.name.startswith(prefix):continue
  vs=[]
  for v in src.data.vertices:
   p=src.matrix_world@v.co;u=(p.x-ox0)/(ox1-ox0);t=(p.y-oy0)/(oy1-oy0)
   if flip:u=1-u;t=1-t
   vs.append((nx0+u*(nx1-nx0),ny0+t*(ny1-ny0),p.z))
  o=objmesh(newprefix+src.name[len(prefix):],vs,[list(p.vertices) for p in src.data.polygons],None,c)
  for m in src.data.materials:o.data.materials.append(m)
  for p,q in zip(o.data.polygons,src.data.polygons):p.material_index=q.material_index;p.use_smooth=q.use_smooth
  o['fitted_to_latest_freecad']=True;out.append(o.name)
 return out
def cylinder(n,pos,r,depth,m,c,parent=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=depth,location=pos)
 o=bpy.context.object;o.name=n
 for cc in list(o.users_collection):cc.objects.unlink(o)
 c.objects.link(o);o.data.materials.append(m);o.color=m.diffuse_color
 if parent:o.parent=parent
 return o
def fixtures(c,ceramic,floor,glass,metal):
 vanity=copy_fitted('B11_Rectangle037','R3_VANITY',[9.4195,4.750094,10.4195,5.250094],S['vanity'],c,flip=True)
 wardrobe=copy_fitted('B11_Rectangle021','R3_WARDROBE',[9.8636246,3.8532813,11.3636246,4.4532814],S['wardrobe'],c)
 # Existing calibrated WC faces south. Rotate -90 degrees to face west,
 # with its cistern toward the existing east wall; 600x500 saved footprint.
 src=bpy.data.objects['B11_Rectangle038_CATALOG_00_00'];lo,hi=bounds(src);cx=(lo[0]+hi[0])/2;cy=(lo[1]+hi[1])/2
 nx=(S['wc'][0]+S['wc'][2])/2;ny=(S['wc'][1]+S['wc'][3])/2
 vs=[]
 for v in src.data.vertices:
  p=src.matrix_world@v.co;vs.append((nx+p.y-cy,ny-(p.x-cx),p.z))
 wc=objmesh('R3_WC_LATEST',vs,[list(p.vertices) for p in src.data.polygons],ceramic,c)
 for p,q in zip(wc.data.polygons,src.data.polygons):p.use_smooth=q.use_smooth
 room=[(9.209,4.8230625),(11.3999,4.8230625),(11.3999,6.4502),(9.209,6.4502)]
 slab('R3_BATH_FLOOR',room,.4501,.452,floor,c)
 # Closed tray against existing room walls; screen points remain exact.
 tray=[(10.557875,6.4502),(10.557875,5.91865625),(10.89025,5.665375),(11.3999,5.665375),(11.3999,6.4502)]
 slab('R3_SHOWER_TRAY',tray,.452,.470,ceramic,c)
 pts=S['screen'];z0=.47;z1=2.45
 for i,(a,b) in enumerate(zip(pts,pts[1:])):
  # The chamfer is the shower door, the other two spans fixed screens.
  segment('R3_SHOWER_GLASS_'+str(i),a,b,z0,z1,.008,glass,c)
  segment('R3_SHOWER_LOWER_FRAME_'+str(i),a,b,z0,z0+.018,.018,metal,c)
  segment('R3_SHOWER_UPPER_FRAME_'+str(i),a,b,z1-.018,z1,.018,metal,c)
 for i,p in enumerate(pts):box('R3_SHOWER_POST_'+str(i),[p[0]-.009,p[1]-.009,z0],[p[0]+.009,p[1]+.009,z1],metal,c)
 a,b=pts[1:3];h=[a[0]*.23+b[0]*.77,a[1]*.23+b[1]*.77]
 box('R3_SHOWER_HANDLE',[h[0]-.008,h[1]-.023,1.40],[h[0]+.008,h[1]-.008,1.55],metal,c)
 box('R3_SHOWER_DRAIN',[11.15,6.05,.470],[11.24,6.14,.474],metal,c)
 return dict(vanity=vanity,wardrobe=wardrobe,wc=[wc.name],shower=['R3_SHOWER_TRAY'])
def casing(c,frame,metal,opt):
 x0,x1=P['gross'];q0,q1=P['clear'];ys=P['south_y'];yn=P['north_y'];z0=.45;zh=2.55
 box('R3_FRAME_WEST',[x0,ys,z0],[q0,yn,zh],frame,c)
 if opt=='B':box('R3_FRAME_EAST',[q1,ys,z0],[x1,yn,zh],frame,c)
 else:
  # Split jamb around the real sliding cavity; never block the parked leaf.
  a,b=L['sliding']['cavity_y']
  box('R3_SPLIT_JAMB_EAST_S',[q1,ys,z0],[x1,a,zh],frame,c)
  box('R3_SPLIT_JAMB_EAST_N',[q1,b,z0],[x1,yn,zh],frame,c)
 if opt=='A':
  a,b=L['sliding']['cavity_y']
  box('R3_FRAME_HEAD_S',[x0,ys,zh-.025],[x1,a,zh],frame,c)
  box('R3_FRAME_HEAD_N',[x0,b,zh-.025],[x1,yn,zh],frame,c)
 else:box('R3_FRAME_HEAD',[x0,ys,zh-.025],[x1,yn,zh],frame,c)
 for face,y0,y1 in [('S',ys-.016,ys),('N',yn,yn+.016)]:
  box('R3_CASING_'+face+'_WEST',[x0-.05,y0,z0],[q0,y1,zh+.065],frame,c)
  box('R3_CASING_'+face+'_EAST',[q1,y0,z0],[x1+.05,y1,zh+.065],frame,c)
  box('R3_CASING_'+face+'_HEAD',[x0-.05,y0,zh-.025],[x1+.05,y1,zh+.065],frame,c)
 if opt=='A':
  a,b=L['sliding']['full_rail'];yc=P['sliding_y']
  box('R3_SLIDER_CONTINUOUS_RAIL',[a-.012,yc-.021,2.550],[b+.012,yc+.021,2.570],metal,c)
  box('R3_SLIDER_END_STOP',[10.766,yc-.025,.46],[10.7779,yc+.025,2.53],metal,c)
  box('R3_SLIDER_MAINTENANCE_COVER',[x0,ys-.020,2.54],[10.8099,ys-.016,2.60],frame,c)
def doors(c,panel,metal,opt):
 if opt=='A':
  root=empty('R3_SLIDING_MOTION_ROOT',c);a,b=L['sliding']['closed'];yc=P['sliding_y']
  leaf=bevel(box('R3_SLIDING_LEAF',[a,yc-.020,.46],[b,yc+.020,2.525],panel,c,root))
  for side,sgn in [('S',-1),('N',1)]:
   # Recessed pulls stay inside the 40mm leaf envelope.
   box('R3_SLIDING_RECESSED_PULL_'+side,[a+.036,yc+sgn*.019-.001,1.37],[a+.053,yc+sgn*.019+.001,1.53],metal,c,root)
  for i,x in enumerate([a+.085,b-.085]):cylinder('R3_SLIDER_HANGER_'+str(i),(x,yc,2.54),.008,.036,metal,c,root)
  root.location=(0,0,0);root.keyframe_insert(data_path='location',frame=1)
  root.location.x=L['sliding']['travel'];root.keyframe_insert(data_path='location',frame=100)
 else:
  root=empty('R3_HINGED_MOTION_ROOT',c);hx,hy=L['hinged']['hinge'];root.location=(hx,hy,.45);w=L['hinged']['leaf_width']
  leaf=bevel(box('R3_HINGED_LEAF',[0,-.020,.01],[w,.020,2.075],panel,c,root))
  for s in [-1,1]:
   box('R3_HINGED_HANDLE_'+str(s),[w-.125,s*.050-.006,.97],[w-.065,s*.050+.006,.981],metal,c,root)
   box('R3_HINGED_ROSETTE_'+str(s),[w-.071,s*.025-.015,.945],[w-.059,s*.025+.015,1.005],metal,c,root)
  for i,z in enumerate([.20,1.02,1.83]):cylinder('R3_HINGE_'+str(i),(hx,hy,.45+z),.008,.075,metal,c)
  root.rotation_euler.z=0;root.keyframe_insert(data_path='rotation_euler',frame=1)
  angle=math.radians(L['hinged']['angle_degrees']);root.rotation_euler.z=angle;root.keyframe_insert(data_path='rotation_euler',frame=100)
  stopx=hx+.566*math.cos(angle)-.020*math.sin(angle)-.009
  stopy=hy+.566*math.sin(angle)
  cylinder('R3_HINGED_FLOOR_STOP',(stopx,stopy,.477),.009,.05,metal,c)
 root['pose_semantics']='frame 1 CLOSED; frame 100 OPEN';return root.name
def cameras(c):
 specs=[('ENTRY',[9.60,2.80,1.86],[9.95,4.80,1.67],24,None),
 ('INTERIOR',[9.55,5.03,1.85],[10.63,5.61,1.42],18,None),
 ('CONTEXT_AXON',[7.4,1.3,7.8],[10.05,5.15,1.35],None,5.9),
 ('CUTAWAY_AXON',[12.8,2.4,9.2],[10.12,5.22,.95],None,4.7),
 ('RESTORED_AREA',[5.5,1.8,8.5],[9.1,5.1,1.35],None,7.5),
 ('STUDY',[13.40,10.25,2.05],[15.12,8.05,1.40],22,None),
 ('TEA_COUNTER',[14.05,7.9,2.05],[14.93,6.865,1.40],24,None)]
 rows=[]
 for n,pos,target,lens,scale in specs:
  data=bpy.data.cameras.new('R3_CAM_'+n);o=bpy.data.objects.new(data.name,data);c.objects.link(o);o.location=pos
  o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.clip_start=.025;data.clip_end=100
  if scale:data.type='ORTHO';data.ortho_scale=scale
  else:data.lens=lens;data.sensor_width=36
  rows.append(dict(name=n,camera=o.name,pos=pos,target=target,lens=lens,ortho_scale=scale))
 return rows
def topology(o):
 bm=bmesh.new();bm.from_mesh(o.data);r=dict(vertices=len(bm.verts),faces=len(bm.faces),boundary=sum(e.is_boundary for e in bm.edges),nonmanifold=sum(not e.is_manifold for e in bm.edges));bm.free();return r
def preserve_outside_rollback(old,new):
 """Join the original exterior outside the local rollback box to its restored interior.

 Remote thin caps in the approved baked skin must retain their exact surfaces;
 global re-triangulation alone can change those caps by1-2mm. This operation
 modifies only the local patch, with matched subdivided boundary edge loops.
 """
 xl,xh,yl,yh=7.79,9.23,4.48,6.61;eps=2e-5;raw=[]
 def boundary(p):return ((abs(p[0]-xl)<eps or abs(p[0]-xh)<eps) and yl-eps<=p[1]<=yh+eps) or ((abs(p[1]-yl)<eps or abs(p[1]-yh)<eps) and xl-eps<=p[0]<=xh+eps)
 for obj,inside in [(old,False),(new,True)]:
  bm=bmesh.new();bm.from_mesh(obj.data)
  for co,no in [((xl,0,0),(1,0,0)),((xh,0,0),(1,0,0)),((0,yl,0),(0,1,0)),((0,yh,0),(0,1,0))]:
   bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=co,plane_no=no)
  for f in bm.faces:
   p=f.calc_center_median();local=xl-1e-7<=p.x<=xh+1e-7 and yl-1e-7<=p.y<=yh+1e-7
   # Preserve even sub-float-area original cap triangles: discarding them
   # changes the closed indexed source topology far outside this repair.
   if local==inside and len(f.verts)>=3:raw.append([tuple(v.co) for v in f.verts])
  bm.free()
 nodes={};verts=[];faces=[]
 def node(p):
  k=tuple(round(x,5 if boundary(p) else 8) for x in p)
  if k not in nodes:nodes[k]=len(verts);verts.append(list(p))
  return nodes[k]
 for f in raw:
  for p in f:node(p)
 candidates=[(i,Vector(p)) for i,p in enumerate(verts) if boundary(p)]
 for f in raw:
  ids=[]
  for a,b in zip(f,f[1:]+f[:1]):
   ai=node(a);bi=node(b);ids.append(ai)
   if not (boundary(a) and boundary(b)):continue
   av,bv=Vector(verts[ai]),Vector(verts[bi]);v=bv-av;ll=v.length_squared
   if ll<1e-15:continue
   inserts=[]
   for i,p in candidates:
    if i in [ai,bi]:continue
    t=(p-av).dot(v)/ll
    if 1e-6<t<1-1e-6 and (p-(av+v*t)).length<eps:inserts.append((t,i))
   ids.extend(i for _,i in sorted(inserts))
  clean=[]
  for i in ids:
   if not clean or clean[-1]!=i:clean.append(i)
  if len(set(clean))>=3:faces.append(clean)
 mesh=bpy.data.meshes.new('R3_LOCAL_ONLY_ROLLBACK_MESH');mesh.from_pydata(verts,[],faces);mesh.update();new.data=mesh
 bm=bmesh.new();bm.from_mesh(new.data)
 gaps=[e for e in bm.edges if e.is_boundary]
 write('LOCAL_ROLLBACK_JOIN_BOUNDARY_DEBUG.json',[[list(v.co) for v in e.verts] for e in gaps])
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(new.data);bm.free();new.data.update()
 return dict(local_xy_bounds=[xl,yl,xh,yh],boundary_nodes=len(candidates),original_nonlocal_surfaces_preserved=True)
def build(opt):
 km=integrity();bpy.ops.wm.open_mainfile(filepath=str(BASE));bpy.context.view_layer.update();before=snapshot();write('BASE_STATES.json',before)
 col=bpy.data.collections.new('COL_SECONDARY_BATH_R3_'+opt);bpy.context.scene.collection.children.link(col)
 wall=bpy.data.materials['V4_CONTINUOUS_REVIEW_WALL'];frame=mat('R3_FRAME',(.43,.37,.29));panel=mat('R3_DOOR',(.39,.43,.43));metal=mat('R3_METAL',(.12,.14,.15));ceramic=mat('R3_CERAMIC',(.89,.9,.88));floor=mat('R3_FLOOR',(.67,.68,.65));glass=mat('R3_GLASS_REVIEW',(.62,.77,.8))
 # The removal happens in the active whole-house geometry, not in render-only
 # visibility: replace the baked skin with the source-provenance rollback.
 rb=json.loads((OUT/'HOUSE_ROLLBACK_WALL_MESH.json').read_text())
 rolled=objmesh('R3_HOUSE_WALLS_D107_ROLLED_BACK',rb['vertices'],rb['faces'],wall,col)
 preservation=preserve_outside_rollback(bpy.data.objects['V5_CONTINUOUS_WALL_SHELL'],rolled)
 rolled.data.materials.append(wall);rolled['local_rollback_bounds']=str(preservation['local_xy_bounds'])
 bm=bmesh.new();bm.from_mesh(rolled.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(rolled.data);bm.free()
 rt=topology(rolled);assert rt['boundary']==0 and rt['nonmanifold']==0,rt
 rollback_inactive=[]
 for obj in bpy.data.objects:
  if obj.name in before and ('D107' in obj.name or obj.name=='V5_CONTINUOUS_WALL_SHELL'):
   obj.hide_render=True;obj.hide_viewport=True;obj.hide_set(True);rollback_inactive.append(obj.name)
 legacy_study,study=runpy.run_path(str(OUT/'study_tea.py'),run_name='study')['build'](globals(),col,0)
 write('STUDY_TEA_REGISTER.json',study)
 # Translucency for review engines; geometry remains the exact 8mm screen.
 glass.diffuse_color=(.62,.77,.8,.20)
 glass.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value=.20
 mesh=json.loads((OUT/f'{opt}_UNIFIED_WALL_MESH.json').read_text());o=objmesh('R3_COMPLETE_PARTITION_WALLS',mesh['vertices'],mesh['faces'],wall,col)
 o['west_partition_policy']='FULL_LATEST_FREECAD_RECTANGLE_NO_NOTCH';o['black_wall_demolition_count']=0
 t=topology(o);assert t['boundary']==0 and t['nonmanifold']==0,t
 # Save the requested restored state BEFORE adding the new west partition.
 # Remove the newly created partition temporarily from visibility for this
 # sibling file; it is enabled immediately for the actual A/B branch.
 o.hide_render=True;o.hide_viewport=True
 views=cameras(col)
 if opt=='A':
  bpy.context.scene.camera=bpy.data.objects['R3_CAM_RESTORED_AREA'];bpy.context.scene['D107_added_enclosure_rollback']='APPLIED_BY_USER_REQUEST'
  pre=OUT/'RESTORED_OPEN_STATE_BEFORE_BATH_R3.blend';bpy.ops.wm.save_as_mainfile(filepath=str(pre));write('RESTORED_STATE_MANIFEST.json',dict(model=str(pre),model_sha256=sha(pre),base_sha256=sha(BASE),status='RESTORED_BEFORE_NEW_BATH_PARTITIONS_REVIEW',wall_rollback=str(OUT/'D107_ROLLBACK_REGISTER.json')))
 o.hide_render=False;o.hide_viewport=False
 groups=fixtures(col,ceramic,floor,glass,metal);casing(col,frame,metal,opt);motion=doors(col,panel,metal,opt)
 inactive=list(set(rollback_inactive+legacy_study))
 for obj in bpy.data.objects:
  if obj.name.startswith(('B11_Rectangle021','B11_Rectangle036','B11_Rectangle037','B11_Rectangle038')) or obj.name in ['FN_次主卧衣柜','FN_次主卫台盆和柜体','FN_次主卫马桶','G_wall_gf_0036','G_wall_gs_0036'] or obj.name.startswith('FN_次主卫湿区'):
   obj.hide_render=True;obj.hide_viewport=True;obj.hide_set(True);inactive.append(obj.name)
 scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=100;scene.frame_set(100);scene.camera=bpy.data.objects['R3_CAM_ENTRY'];scene['secondary_bath_revision']='R3_LATEST_FREECAD';scene['option']=opt;scene['base_frozen_sha256']=sha(BASE)
 scene.timeline_markers.new('CLOSED',frame=1);scene.timeline_markers.new('OPEN',frame=100)
 after=snapshot();expected=json.loads(json.dumps(before))
 for n in inactive:expected[n]['hide_render']=True;expected[n]['hide_viewport']=True
 for n,s in norm(expected).items():assert norm(after)[n]==s,('Unintended source edit',n)
 model=OUT/('OPTION_A_SLIDING_R3.blend' if opt=='A' else 'OPTION_B_INWARD_R3.blend')
 scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1800;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
 scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
 scene.display.shading.show_shadows=False;scene.display.shading.background_type='WORLD';scene.world.color=(.92,.935,.94);scene.view_settings.view_transform='Standard';scene.display.render_aa='32'
 bpy.ops.wm.save_as_mainfile(filepath=str(model));integrity()
 write(f'{opt}_EXPECTED_BASE_STATES.json',expected)
 manifest=dict(status='HUMAN_REVIEW_NOT_CONSTRUCTION_RELEASED',option=opt,model=str(model),model_sha256=sha(model),base=str(BASE),base_sha256=sha(BASE),freecad=L['freecad'],freecad_sha256=L['freecad_sha256'],layout_contract=str(OUT/'LAYOUT_CONTRACT.json'),fixture_groups=groups,views=views,inactive_legacy_objects=inactive,motion_root=motion,topology=t,rollback_wall_topology=rt,black_wall_demolition_count=0,source_wall_meshes_preserved=True,added_D107_enclosure_removed=True,kitchen_preserved=True,study=study,clear_width_mm=P['clear_width_mm'])
 write(f'OPTION_{opt}_MANIFEST.json',manifest)
 print(json.dumps(dict(build='PASS',option=opt,model=str(model),topology=t),ensure_ascii=False))
def export_wall(o):
 o.data.calc_loop_triangles();return dict(name=o.name,vertices=[list(o.matrix_world@v.co) for v in o.data.vertices],triangles=[list(t.vertices) for t in o.data.loop_triangles])
def verify(opt):
 integrity();m=json.loads((OUT/f'OPTION_{opt}_MANIFEST.json').read_text());assert sha(m['model'])==m['model_sha256'];bpy.ops.wm.open_mainfile(filepath=m['model']);bpy.context.view_layer.update()
 expected=norm(json.loads((OUT/f'{opt}_EXPECTED_BASE_STATES.json').read_text()));got=norm(snapshot())
 for n,s in expected.items():assert got[n]==s,('Fresh-open source mismatch',n)
 t=topology(bpy.data.objects['R3_COMPLETE_PARTITION_WALLS']);assert t['boundary']==0 and t['nonmanifold']==0
 walls=[export_wall(o) for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and (o.name=='R3_HOUSE_WALLS_D107_ROLLED_BACK' or o.name.startswith('V5_CORNER_PATCH_') or o.name=='R3_COMPLETE_PARTITION_WALLS')]
 assert not [o.name for o in bpy.data.objects if 'D107' in o.name and not o.hide_render and o.name!='R3_HOUSE_WALLS_D107_ROLLED_BACK']
 # Surface-preservation check outside the explicitly rolled-back local zone.
 old=bpy.data.objects['V5_CONTINUOUS_WALL_SHELL'];new=bpy.data.objects['R3_HOUSE_WALLS_D107_ROLLED_BACK']
 tree=BVHTree.FromPolygons([v.co for v in new.data.vertices],[list(f.vertices) for f in new.data.polygons]);diffs=[];miss=[];double_checks=0
 new.data.calc_loop_triangles()
 triangles=[[tuple(new.data.vertices[i].co) for i in t.vertices] for t in new.data.loop_triangles]
 def precise_distance(p,fallback):
  # Blender BVH's float closest-point math is ill-conditioned on long, very
  # thin cap triangles. Test projected containment with Python float64 math.
  best=fallback;p=tuple(p)
  def sub(a,b):return [a[i]-b[i] for i in range(3)]
  for a,b,c in triangles:
   if any(p[i]<min(a[i],b[i],c[i])-.00035 or p[i]>max(a[i],b[i],c[i])+.00035 for i in range(3)):continue
   u,v=sub(b,a),sub(c,a);n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];nn=sum(x*x for x in n)
   if nn<1e-28:continue
   signed=sum((p[i]-a[i])*n[i] for i in range(3))/nn;pp=[p[i]-signed*n[i] for i in range(3)]
   axis=max(range(3),key=lambda i:abs(n[i]));j,k=[i for i in range(3) if i!=axis]
   def orient(a,b,p):return (b[j]-a[j])*(p[k]-a[k])-(b[k]-a[k])*(p[j]-a[j])
   signs=[orient(a,b,pp),orient(b,c,pp),orient(c,a,pp)]
   if min(signs)>=-1e-12 or max(signs)<=1e-12:best=min(best,abs(signed)*math.sqrt(nn))
  return best
 for f in old.data.polygons:
  p=f.center
  if 7.79<=p.x<=9.23 and 4.48<=p.y<=6.61:continue
  hit=tree.find_nearest(p)
  assert hit[0] is not None;distance=hit[3]
  if distance>.00035:
   double_checks+=1;distance=precise_distance(p,distance)
  diffs.append(distance)
  if distance>.00035:miss.append(dict(point=list(p),nearest=list(hit[0]),distance_mm=distance*1000,face_vertices=[list(old.data.vertices[i].co) for i in f.vertices]))
 write('ROLLBACK_SURFACE_DEBUG.json',miss)
 assert max(diffs)<.00035,('Unrelated wall surface changed',max(diffs))
 states={}
 for frame in [1,100]:
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
  states[str(frame)]={o.name:dict(bounds=bounds(o),vertices=[list(o.matrix_world@v.co) for v in o.data.vertices]) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('R3_SLIDING_LEAF','R3_HINGED_LEAF','R3_HINGED_HANDLE','R3_FRAME','R3_SPLIT','R3_CASING','R3_SLIDER_CONTINUOUS'))}
 groups={}
 for k,names in m['fixture_groups'].items():
  vs=[o.matrix_world@v.co for n in names for o in [bpy.data.objects[n]] for v in o.data.vertices]
  groups[k]=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
 study_bounds={}
 for k in ['bookcase','tea_table','tea_counter']:
  row=m['study'][k];names=row.get('objects',row.get('body_objects',[]))
  vs=[bpy.data.objects[n].matrix_world@v.co for n in names for v in bpy.data.objects[n].data.vertices]
  rect=[min(v.x for v in vs),min(v.y for v in vs),max(v.x for v in vs),max(v.y for v in vs)]
  error=max(abs(rect[i]*1000-row['bounds_mm'][i]) for i in range(4));assert error<.03,(k,error)
  study_bounds[k]=dict(actual_bounds_mm=[v*1000 for v in rect],max_error_mm=error)
 write(f'{opt}_ACTUAL_GEOMETRY.json',dict(walls=walls,door_states=states,fixture_bounds=groups,partition_topology=t))
 write(f'{opt}_FRESH_OPEN_QA.json',dict(status='PASS',source_states_checked=len(expected),kitchen_objects_unchanged=True,added_D107_enclosure_removed=True,unrelated_wall_surface_samples=len(diffs),unrelated_wall_max_deviation_mm=max(diffs)*1000,thin_cap_float64_rechecks=double_checks,study_bounds=study_bounds,study_table_shift_mm=m['study']['tea_table']['shift_north_mm'],topology=t,model_sha256=m['model_sha256']))
 print(json.dumps(dict(fresh_open='PASS',option=opt,source_states=len(expected),actual_geometry_exported=True)))
def render_section(o,crop=False):
 # Clip surfaces directly, avoiding Boolean inside/outside decisions on the
 # inherited multi-part wall shell. This affects only transient render data.
 o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
 mw=o.matrix_world.copy()
 for v in bm.verts:v.co=mw@v.co
 o.parent=None;o.matrix_world=Matrix.Identity(4)
 def bisect(co,no,clear=False):
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=co,plane_no=no,clear_inner=clear,clear_outer=False)
 if crop:
  for co,no in [((9.035,0,0),(1,0,0)),((11.75,0,0),(-1,0,0)),((0,3.4,0),(0,1,0)),((0,6.8,0),(0,-1,0))]:bisect(co,no,True)
 bisect((0,4.86,0),(0,1,0));bisect((0,0,1.14),(0,0,1))
 remove=[f for f in bm.faces if f.calc_center_median().y<4.86-1e-6 and f.calc_center_median().z>1.14+1e-6]
 bmesh.ops.delete(bm,geom=remove,context='FACES_ONLY');bm.to_mesh(o.data);bm.free();o.data.update()
def render(opt):
 integrity();m=json.loads((OUT/f'OPTION_{opt}_MANIFEST.json').read_text());rows=[];rd=OUT/'renders';rd.mkdir(exist_ok=True)
 requests=[('ENTRY',1),('ENTRY',100),('INTERIOR',100),('CONTEXT_AXON',100),('CUTAWAY_AXON',100),('RESTORED_AREA',100)]
 if opt=='A':requests+=[('STUDY',100),('TEA_COUNTER',100),('ROLLBACK_BEFORE',1)]
 for view,frame in requests:
  src=m['model'] if view!='ROLLBACK_BEFORE' else str(OUT/'RESTORED_OPEN_STATE_BEFORE_BATH_R3.blend')
  bpy.ops.wm.open_mainfile(filepath=src);s=bpy.context.scene;s.frame_set(frame);s.camera=bpy.data.objects['R3_CAM_'+(view if view!='ROLLBACK_BEFORE' else 'RESTORED_AREA')];bpy.context.view_layer.update()
  for o in bpy.data.objects:
   if any(c.name in ['03_EXISTING_CEILING','05_HUMAN_DESIGN_GUIDE','06_FUTURE_DESIGN_OPTIONS'] for c in o.users_collection):o.hide_render=True
   if 'CEILING' in o.name or 'LABEL' in o.name:o.hide_render=True
   if o.type in ['CAMERA','EMPTY']:continue
   if o.name.startswith('R3_SHOWER_GLASS_') and view in ['INTERIOR','CUTAWAY_AXON']:o.hide_render=True
  cuts=[]
  if view=='CUTAWAY_AXON':
   # A declared temporary sectional view; full branch/source are not saved.
   # Keep real wall solids, clipped only in this render to expose floor layout.
   for o in list(bpy.data.objects):
    if o.type!='MESH' or o.name.startswith('TEMP_') or o.hide_render:continue
    lo,hi=bounds(o)
    if hi[0]<9.035 or lo[0]>11.75 or hi[1]<3.4 or lo[1]>6.8:o.hide_render=True;continue
    if o.name=='R3_HOUSE_WALLS_D107_ROLLED_BACK' or o.name.startswith(('V5_CORNER_PATCH_','R3_COMPLETE_PARTITION','R3_WARDROBE','R3_FRAME','R3_SPLIT','R3_CASING','R3_SLIDING_LEAF','R3_HINGED_LEAF')):
     render_section(o,crop=o.name=='R3_HOUSE_WALLS_D107_ROLLED_BACK');cuts.append(o.name)
   # Upper moving hardware would float in a sectional view.
   for o in bpy.data.objects:
    if o.name.startswith(('R3_SLIDER_HANGER','R3_SLIDER_CONTINUOUS_RAIL','R3_SLIDER_MAINTENANCE_COVER','R3_HINGED_HANDLE','R3_HINGED_ROSETTE','R3_SLIDING_RECESSED_PULL','R3_HINGE_')):o.hide_render=True
  s.render.filepath=str(rd/f'{opt}_{view}_{frame:03d}.png');s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
  bpy.ops.render.render(write_still=True)
  rows.append(dict(option=opt,view=view,frame=frame,path=s.render.filepath,sha256=sha(s.render.filepath),source=src,source_sha256=sha(src),resolution=[1800,1400],engine='Workbench',temporary_section_objects=cuts,glass_hidden=view in ['INTERIOR','CUTAWAY_AXON'],source_saved=False))
 write(f'{opt}_RENDER_MANIFEST.json',rows);assert sha(m['model'])==m['model_sha256'];integrity();print(json.dumps(dict(render='PASS',option=opt,views=len(rows),images='FILESYSTEM_ONLY')))
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:];mode,opt=args
 if opt=='AB':
  for x in 'AB':globals()[mode](x)
 else:globals()[mode](opt)
