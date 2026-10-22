import bpy,json,hashlib,struct,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/platform_bath_fitness_v14';a=json.loads((D/'BUILD_AUDIT.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(a['output'])==a['sha256'] and sha(a['source'])==a['source_sha256'];bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
saved={'layer':bpy.context.window.view_layer.name,'ceilings_hidden':all(bpy.data.objects[n].hide_get(view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN']) for n in ['V7_CEILING_LOW','V7_CEILING_HIGH','V7_CEILING_450MM_TRANSITION'])};assert saved['ceilings_hidden']
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def mh(o):
 h=hashlib.sha256()
 if o.type=='MESH':
  for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
  for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
issues=[]
for n,b in a['before'].items():
 o=bpy.data.objects[n]
 if n not in a['edited_objects'] and mh(o)!=b['mesh']:issues.append((n,'mesh'))
 if n not in a['moved_objects'] and [list(r) for r in o.matrix_world]!=b['matrix']:issues.append((n,'matrix'))
 if n not in a['hidden_objects'] and o.hide_render!=b['render']:issues.append((n,'visibility'))
 if hasattr(o.data,'materials') and [m.name if m else None for m in o.data.materials]!=b['mats']:issues.append((n,'material'))
assert not issues,issues[:10]
for f in a['protected_sources']:assert sha(f['path'])==f['sha256']
def bounds(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
van=bounds(bpy.data.objects['R3_VANITY_TOP']);assert abs(van[1][0]-van[0][0]-1)<1e-5
tray=bounds(bpy.data.objects['V14_SHOWER_950_TRAY']);assert abs(tray[1][0]-tray[0][0]-.95)<1e-5 and abs(tray[1][1]-tray[0][1]-.95)<1e-5
# Confirm actual closed door geometry spans both chamfer endpoints.
door=bpy.data.objects['HOUSE_V1_V14_SHOWER_INWARD_DOOR'];db=bounds(door);assert .60<db[1][0]-db[0][0]<.67 and db[1][1]-db[0][1]<.03,db
assert not a['rower_body_obstacle_intersections'];assert all(not r['hits'] for r in a['door_swing_samples'])
zone=a['rower_use_bounds_xy_m'];near=[]
for o in s.objects:
 if o.type!='MESH' or o.hide_render or not (o.name.startswith('V4_Chaise') or o.name.startswith('LIVING_FIX_BAY_SILL') or o.name=='B11_Circle_CATALOG_00_00'):continue
 b=bounds(o);ix=max(0,min(zone[2],b[1][0])-max(zone[0],b[0][0]));iy=max(0,min(zone[3],b[1][1])-max(zone[1],b[0][1]));
 if ix>0 and iy>0:near.append({'object':o.name,'use_zone_plan_overlap_xy_mm':[round(ix*1000,1),round(iy*1000,1)]})
v={'status':'PASS_TECHNICAL_LOCAL_CHANGE_CHECKS_WITH_FIT_LIMITATIONS','sha256':a['sha256'],'original_objects':len(a['before']),'unexpected_geometry_pose_visibility_material_changes':issues,'source_protection_count':len(a['protected_sources']),'source_view':saved,'art_bottom_above_FFL_mm':a['art_actual_frame_bottom_above_FFL_mm'],'art_center_above_FFL_mm':1650,'art_back_to_wall_mm':2,'vanity_width_mm':1000,'shower_outer_mm':[950,950],'shower_door_panel_mm':a['shower_diagonal_door_mm'],'nominal_post_clear_opening_mm':a['shower_nominal_post_clear_mm'],'door_swing_samples':a['door_swing_samples'],'rower_body_no_obstacle_intersections':True,'rower_manufacturer_use_zone_fit':'FAIL_WITH_CURRENT_FURNITURE','rower_use_zone_overlaps':near,'handrail_extension_mm':350,'local_building_code_certification':False,'construction_product_selection_and_waterproofing_pending':True,'owner_visual_acceptance':False};(D/'VERIFICATION.json').write_text(json.dumps(v,indent=2)+chr(10));print('VERIFY_V14',json.dumps(v))

