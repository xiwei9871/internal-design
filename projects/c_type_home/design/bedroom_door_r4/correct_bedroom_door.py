"""User correction: secondary-bedroom entrance remains, now E-W inward hinged."""
import bpy,bmesh,json,hashlib,runpy,math,sys,shutil
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
R3=ROOT/'design/secondary_bath_options/r3'
H=runpy.run_path(str(R3/'build_models.py'),run_name='door_helpers')
snapshot=H['snapshot'];norm=H['norm'];sha=H['sha'];box=H['box'];mat=H['mat'];empty=H['empty'];cylinder=H['cylinder'];bounds=H['bounds']
FFL=.45;HEAD=2.55;TOP=3.25;YS=4.5002;YN=4.7002
# A normal850mm leaf plus5mm installation clearance and25mm jambs.
# Right outer jamb meets the latest west-partition outer face x9059mm.
GROSS=[8.149,9.059];CLEAR=[8.174,9.034];HINGE=[8.179,YS-.020];LEAF_W=.850
def write(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def worldray(o,start,direction,maxdist=20):
 tree=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons]);return tree.ray_cast(Vector(start),Vector(direction),maxdist)
def add_cameras(c):
 specs=[dict(id='DOOR_CONTEXT',pos=[6.9,7.10,2.00],target=[8.59,4.61,1.58],lens=28,eye_ffl=.45),
 dict(id='DOOR_FRONT',pos=[8.59,6.50,1.98],target=[8.59,4.52,1.58],lens=32,eye_ffl=.45),
 dict(id='DOOR_AXON',pos=[6.5,7.5,8],target=[8.5,4.6,1.15],scale=5.5,eye_ffl=.45)]
 for s in specs:
  d=bpy.data.cameras.new('R4_'+s['id']);o=bpy.data.objects.new(d.name,d);c.objects.link(o);o.location=s['pos'];o.rotation_euler=(Vector(s['target'])-o.location).to_track_quat('-Z','Y').to_euler();d.clip_start=.025;d.clip_end=100
  if 'scale' in s:d.type='ORTHO';d.ortho_scale=s['scale']
  else:d.lens=s['lens'];d.sensor_width=36
  s['camera']=o.name
 return specs
def door_build(opt):
 src=R3/('OPTION_A_SLIDING_R3.blend' if opt=='A' else 'OPTION_B_INWARD_R3.blend');manifest=json.loads((R3/f'OPTION_{opt}_MANIFEST.json').read_text());assert sha(src)==manifest['model_sha256'];before_hash=sha(src)
 bpy.ops.wm.open_mainfile(filepath=str(src));bpy.context.view_layer.update();before=snapshot()
 c=bpy.data.collections.new('COL_R4_SECONDARY_BEDROOM_EW_INWARD_DOOR');bpy.context.scene.collection.children.link(c)
 wall=bpy.data.materials['V4_CONTINUOUS_REVIEW_WALL'];wood=mat('R4_DOOR_PALE_ASH',(.64,.57,.47));metal=mat('R4_DOOR_MUTED_METAL',(.24,.26,.24))
 # Only additions into the previously open area. Frozen/R3 skins remain untouched.
 box('R4_DOOR_WEST_CONNECTED_RETURN',[7.7999,YS,FFL],[GROSS[0],YN,TOP],wall,c)
 box('R4_DOOR_COMPLETE_HEADER',[GROSS[0],YS,HEAD+.025],[GROSS[1],YN,TOP],wall,c)
 box('R4_WEST_PARTITION_SOUTH_FLUSH_CONNECTION',[9.059,YS,FFL],[9.209,4.50725,TOP],wall,c)
 # Repair the actual floor contour, not a thin visual cover. Remote footprint
 # remains identical; only the authorized former angled threshold gap fills.
 floor_data=json.loads((OUT/'CORRECTED_UPPER_FLOOR_MESH.json').read_text())
 fixed=H['objmesh']('R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD',floor_data['vertices'],floor_data['faces'],None,c)
 for mm in bpy.data.objects['FLOOR_UPPER'].data.materials:fixed.data.materials.append(mm)
 bm=bmesh.new();bm.from_mesh(fixed.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(fixed.data);bm.free()
 topology=H['topology'](fixed);assert topology['boundary']==0 and topology['nonmanifold']==0,topology
 changed_floor_sources=['FLOOR_UPPER','FLOOR_UPPER_SEAM_0','FLOOR_UPPER_SEAM_1','FLOOR_UPPER_SEAM_4']
 for name in changed_floor_sources:
  src_floor=bpy.data.objects[name];src_floor.hide_render=True;src_floor.hide_viewport=True;src_floor.hide_set(True)
 box('R4_DOOR_FRAME_WEST',[GROSS[0],YS,FFL],[CLEAR[0],YN,HEAD+.025],wood,c)
 box('R4_DOOR_FRAME_EAST',[CLEAR[1],YS,FFL],[GROSS[1],YN,HEAD+.025],wood,c)
 box('R4_DOOR_FRAME_HEAD',[CLEAR[0],YS,HEAD],[CLEAR[1],YN,HEAD+.025],wood,c)
 for face,y0,y1 in [('ROOM_SOUTH',YS-.016,YS),('PUBLIC_NORTH',YN,YN+.016)]:
  box('R4_DOOR_CASING_'+face+'_WEST',[GROSS[0]-.05,y0,FFL],[CLEAR[0],y1,HEAD+.065],wood,c)
  box('R4_DOOR_CASING_'+face+'_EAST',[CLEAR[1],y0,FFL],[GROSS[1]+.05,y1,HEAD+.065],wood,c)
  box('R4_DOOR_CASING_'+face+'_HEAD',[GROSS[0]-.05,y0,HEAD],[GROSS[1]+.05,y1,HEAD+.065],wood,c)
 root=empty('R4_BEDROOM_INWARD_HINGE_ROOT',c);root.location=(HINGE[0],HINGE[1],FFL)
 root['opening_axis']='EAST_WEST';root['swing_direction']='SOUTH_INTO_SECONDARY_BEDROOM';root['nominal_leaf_mm']=850;root['max_swing_degrees']=90
 leaf=box('R4_BEDROOM_DOOR_LEAF',[0,-.020,.005],[LEAF_W,.020,2.095],wood,c,root)
 H['bevel'](leaf,.0025)
 for sign in [-1,1]:
  box('R4_BEDROOM_HANDLE_'+str(sign),[LEAF_W-.14,sign*.047-.006,1.00],[LEAF_W-.06,sign*.047+.006,1.012],metal,c,root)
  box('R4_BEDROOM_HANDLE_STEM_'+str(sign),[LEAF_W-.077,min(sign*.02,sign*.047),.982],[LEAF_W-.061,max(sign*.02,sign*.047),1.028],metal,c,root)
 for i,z in enumerate([.24,1.04,1.84]):cylinder('R4_BEDROOM_HINGE_'+str(i),(HINGE[0]-.005,YS-.010,FFL+z),.012,.08,metal,c)
 root.rotation_euler.z=0
 views=add_cameras(c);s=bpy.context.scene;s.camera=bpy.data.objects['R4_DOOR_CONTEXT'];s['secondary_bedroom_door']='EW_ALIGNED_INWARD_SOUTH; USER_CORRECTION_2026_10_02';s['render_authoritative_model']='R4_OPTION_A_DOOR_CORRECTED'
 after=snapshot()
 expected=json.loads(json.dumps(before))
 for n in changed_floor_sources:expected[n]['hide_render']=True;expected[n]['hide_viewport']=True
 for n,r in norm(expected).items():assert norm(after)[n]==r,('Unintended inherited change',n)
 out=OUT/('OPTION_A_SLIDING_R4.blend' if opt=='A' else 'OPTION_B_INWARD_R4.blend')
 bpy.ops.wm.save_as_mainfile(filepath=str(out));assert sha(src)==before_hash
 write(f'R4_OPTION_{opt}_MANIFEST.json',dict(status='USER_REQUESTED_DOOR_AND_THRESHOLD_CORRECTION_HUMAN_REVIEW',model=str(out),model_sha256=sha(out),source=str(src),source_sha256=before_hash,source_objects_preserved=len(before),door=dict(orientation='EAST_WEST',inward='SOUTH',hinge_m=HINGE,leaf_width_mm=850,leaf_height_mm=2090,nominal_door_height_mm=2100,gross_width_mm=910,frame_clear_width_mm=860,frame_each_side_mm=25,host_y_mm=[YS*1000,YN*1000],rough_opening_height_mm=2125,review_sections=True),floor_repair=dict(topology=topology,source_objects_hidden=changed_floor_sources,local_rect=floor_data['repair_scope_m'],top_m=.45,nonlocal_plan_delta_m2=floor_data['nonlocal_plan_delta_m2'],old_invalid_top_faces=floor_data['invalid_source_top_faces']),added_objects=[o.name for o in c.objects],views=views,black_wall_demolition_count=0,old_angled_door_stays_inactive=True))
 write(f'R4_OPTION_{opt}_EXPECTED_R3_STATES.json',expected)
 print(json.dumps(dict(build='PASS',option=opt,model=str(out),door_axis='EW',swing='SOUTH',source_preserved=True)))
def verify(opt):
 m=json.loads((OUT/f'R4_OPTION_{opt}_MANIFEST.json').read_text());assert sha(m['model'])==m['model_sha256'];assert sha(m['source'])==m['source_sha256'];bpy.ops.wm.open_mainfile(filepath=m['model']);bpy.context.view_layer.update();states=norm(snapshot());expected=norm(json.loads((OUT/f'R4_OPTION_{opt}_EXPECTED_R3_STATES.json').read_text()))
 for n,s in expected.items():assert states[n]==s,('Fresh-open source changed',n)
 old=[o.name for o in bpy.data.objects if 'D107' in o.name and not o.hide_render and o.type=='MESH' and o.name!='R3_HOUSE_WALLS_D107_ROLLED_BACK'];assert not old,old
 root=bpy.data.objects['R4_BEDROOM_INWARD_HINGE_ROOT'];leaf=bpy.data.objects['R4_BEDROOM_DOOR_LEAF'];bpy.context.view_layer.update();closed=bounds(leaf)
 assert abs(closed[1][0]-closed[0][0]-.85)<1e-5;assert abs(closed[1][1]-closed[0][1]-.04)<1e-5
 world={}
 for angle in [0,45,90]:
  root.rotation_euler.z=-math.radians(angle);bpy.context.view_layer.update();world[str(angle)]=dict(bounds=bounds(leaf),vertices=[list(leaf.matrix_world@v.co) for v in leaf.data.vertices],moving_meshes=[dict(name=o.name,vertices=[list(o.matrix_world@v.co) for v in o.data.vertices]) for o in bpy.data.objects if o.type=='MESH' and o.parent==root])
 assert world['90']['bounds'][0][1]<HINGE[1]-.84
 root.rotation_euler.z=0;bpy.context.view_layer.update()
 floor=bpy.data.objects['R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD'];ftree=BVHTree.FromPolygons([v.co for v in floor.data.vertices],[list(f.vertices) for f in floor.data.polygons]);floor_heights=[]
 for ix in range(9):
  for iy in range(7):
   x=8.18+ix*(9.02-8.18)/8;y=4.455+iy*(4.94-4.455)/6;hit=ftree.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),1)
   assert hit[0] is not None and abs(hit[0].z-.45)<1e-6,(x,y,hit[0]);floor_heights.append(hit[0].z)
 walls=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and o.name in ['R3_HOUSE_WALLS_D107_ROLLED_BACK','R3_COMPLETE_PARTITION_WALLS','R4_DOOR_WEST_CONNECTED_RETURN','R4_DOOR_COMPLETE_HEADER','R4_WEST_PARTITION_SOUTH_FLUSH_CONNECTION']]
 opening_clear=[]
 for x in [8.23,8.60,8.96]:
  hits=[worldray(o,[x,YN+.05,1.6],[0,-1,0],.40)[0] for o in walls];assert all(h is None for h in hits);opening_clear.append(x)
 # Complete wall beyond casing, both sides and above; three real physical ray hits.
 probes=[]
 for point in [[8.10,YN+.05,1.6],[9.13,YN+.05,1.6],[8.60,YN+.05,2.9]]:
  hits=[o.name for o in walls if worldray(o,point,[0,-1,0],.40)[0] is not None];assert hits,(point,hits);probes.append(dict(point=point,wall_hits=hits))
 for o in walls:o.data.calc_loop_triangles()
 geometry=dict(door_poses=world,wall_meshes=[dict(name=o.name,vertices=[list(o.matrix_world@v.co) for v in o.data.vertices],faces=[list(p.vertices) for p in o.data.polygons],triangles=[list(t.vertices) for t in o.data.loop_triangles]) for o in walls],other_active_meshes=[])
 # Export local nearby objects for floor-plan sweep review.
 for o in bpy.data.objects:
  if o.type!='MESH' or o.hide_render or o.hide_viewport:continue
  b=bounds(o)
  if b[0][0]<9.3 and b[1][0]>7.7 and b[0][1]<4.7 and b[1][1]>3.3 and o not in walls:
   geometry['other_active_meshes'].append(dict(name=o.name,vertices=[list(o.matrix_world@v.co) for v in o.data.vertices]))
 write(f'R4_{opt}_ACTUAL_GEOMETRY.json',geometry)
 write(f'R4_OPTION_{opt}_QA.json',dict(status='PASS',source_objects_preserved=len(expected),authorized_floor_source_visibility_changes=m['floor_repair']['source_objects_hidden'],door_nominal_width_mm=850,door_axis='EAST_WEST',swing='SOUTH_INWARD',old_slanted_door_active_count=0,doorway_wall_clear_rays=opening_clear,door_enclosure_probes=probes,continuous_threshold_floor_samples=len(floor_heights),floor_sample_height_m=min(floor_heights),floor_height_range_mm=(max(floor_heights)-min(floor_heights))*1000,floor_topology=H['topology'](floor),nonlocal_floor_plan_change_m2=m['floor_repair']['nonlocal_plan_delta_m2'],base_files_preserved=True))
 print(json.dumps(dict(verify='PASS',option=opt,source_states=len(expected),door_enclosure='COMPLETE')))
def render(opt):
 m=json.loads((OUT/f'R4_OPTION_{opt}_MANIFEST.json').read_text());rows=[];rd=OUT/'renders';rd.mkdir(exist_ok=True)
 for view,angle in [('DOOR_CONTEXT',0),('DOOR_FRONT',0),('DOOR_FRONT',45),('DOOR_AXON',90)]:
  bpy.ops.wm.open_mainfile(filepath=m['model']);s=bpy.context.scene;s.camera=bpy.data.objects['R4_'+view];root=bpy.data.objects['R4_BEDROOM_INWARD_HINGE_ROOT'];root.rotation_euler.z=-math.radians(angle)
  for o in bpy.data.objects:
   if any(c.name in ['05_HUMAN_DESIGN_GUIDE','06_FUTURE_DESIGN_OPTIONS'] for c in o.users_collection):o.hide_render=True
   if view=='DOOR_AXON' and 'CEILING' in o.name:o.hide_render=True
  s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='Standard';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';s.display.render_aa='32'
  path=rd/f'R4_{opt}_{view}_{angle:02d}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);rows.append(dict(camera=view,angle=angle,path=str(path),sha256=sha(path),source_saved=False))
 write(f'R4_{opt}_RENDER_MANIFEST.json',rows);assert sha(m['model'])==m['model_sha256'];print(json.dumps(dict(render='PASS',option=opt,views=len(rows))))
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:];mode=args[0];opt=args[1]
 for x in ('AB' if opt=='AB' else opt):globals()[mode](x)
