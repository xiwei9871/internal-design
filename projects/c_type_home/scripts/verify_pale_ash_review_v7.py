"""Fresh-open geometry, product dimensions, ceiling and material checks."""
import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/pale_ash_review_v7';a=json.loads((D/'BUILD_AUDIT.json').read_text())
def h(o):
 v=hashlib.sha256()
 for p in o.data.vertices:v.update(struct.pack('<fff',*p.co))
 for f in o.data.polygons:v.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return v.hexdigest()
assert hashlib.sha256(Path(a['source']).read_bytes()).hexdigest()==a['source_sha256']
assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==a['sha256']
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
saved_view={'active_layer':bpy.context.window.view_layer.name,'overview_render_enabled':s.view_layers['OVERVIEW_CEILING_HIDDEN'].use,'interior_render_enabled':s.view_layers['INTERIOR_CLOSED_CEILING'].use,'roof_hidden_in_overview':all(bpy.data.objects[n].hide_get(view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN']) for n in a['new_ceiling_objects']),'roof_visible_in_interior':all(not bpy.data.objects[n].hide_get(view_layer=s.view_layers['INTERIOR_CLOSED_CEILING']) for n in a['new_ceiling_objects'])}
assert saved_view['roof_hidden_in_overview'] and saved_view['roof_visible_in_interior']
assert not saved_view['overview_render_enabled'] and saved_view['interior_render_enabled']
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();issues=[]
for n,b in a['before'].items():
 o=bpy.data.objects[n]
 if o.type=='MESH' and h(o)!=b['mesh']:issues.append((n,'geometry'))
 if [list(v) for v in o.matrix_world]!=b['matrix']:issues.append((n,'world_matrix'))
 if n not in a['old_ceiling_hidden']+[a.get('slider_hidden_source','')] and o.hide_render!=b['hide_render']:issues.append((n,'render_visibility'))
assert not issues,issues[:10]
if a.get('slider_frame_created'):
 assert bpy.data.objects['R3_SLIDING_LEAF'].hide_render
 panel=bpy.data.objects[a['slider_frame_created'][0]]
 assert abs(panel.dimensions.y-.010)<1e-5
 assert panel.data.materials[0].name=='V7_SLIDING_CLEAR_GLASS'
protected=json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files']
for f in protected:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256']
for n in ['V4_ENT-1_LEAF_0','V4_ENT-1_LEAF_1']:assert bpy.data.objects[n].data.materials[0].name=='V7_ENTRY_SATIN_METAL'
assert bpy.data.objects['R3_SLIDING_LEAF'].data.materials[0].node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value==1
wooddoors=[o.name for o in s.objects if o.type=='MESH' and not o.hide_render and (o.name.startswith('V4_D-') and '_LEAF_' in o.name or o.name=='R4_BEDROOM_DOOR_LEAF')]
for n in wooddoors:assert bpy.data.objects[n].data.materials[0].name=='V7_CATALOG_PALE_NATURAL_ASH'
l=bpy.data.objects['V7_CEILING_LOW'];u=bpy.data.objects['V7_CEILING_HIGH']
bottom=lambda o:min(v.co.z for v in o.data.vertices)
assert abs(bottom(u)-bottom(l)-.45)<1e-5
r={'status':'PASS_REQUESTED_TECHNICAL_CHECKS','output_sha256':a['sha256'],'original_objects_geometry_pose_unchanged':len(a['before']),'unexpected_changes':issues,'protected_sources':len(protected),'wood_interior_leaves':wooddoors,'ceiling_soffit_elevations_m':[bottom(l),bottom(u)],'saved_view_state':saved_view,'ceiling_delta_mm':450,'bed_dimensions_mm':[round(v*1000,3) for v in bpy.data.objects['HUNYUAN_V3_COUPLE_BED'].dimensions],'ceiling_top_normal_z_means':{},'ceiling_repair_is_presentation_only':True,'owner_appearance_accepted':False}
for n in [l.name,u.name]:
 o=bpy.data.objects[n];top=max(v.co.z for v in o.data.vertices);fs=[f.normal.z for f in o.data.polygons if all(abs(o.data.vertices[i].co.z-top)<1e-5 for i in f.vertices)];r['ceiling_top_normal_z_means'][n]=sum(fs)/len(fs);assert r['ceiling_top_normal_z_means'][n]>.99
(D/'VERIFICATION.json').write_text(json.dumps(r,indent=2)+'\n');print('VERIFY_V7',json.dumps(r))
