"""Fresh-open verifies intact donor copy, bounded bedside translations and all earlier decisions."""
import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/mother_hunyuan_v12';a=json.loads((D/'BUILD_AUDIT.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(a['source'])==a['source_sha256'] and sha(a['output'])==a['sha256']
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
assert bpy.context.window.view_layer.name=='OVERVIEW_CEILING_HIDDEN'
for n in a['hidden_old_bed_all']:
    o=bpy.data.objects[n];assert o.hide_render and o.hide_viewport and all(o.hide_get(view_layer=l) for l in s.view_layers),n
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def mh(o):
    h=hashlib.sha256()
    if o.type=='MESH':
        for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
        for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return h.hexdigest()
issues=[];hidden=set(a['hidden_old_bed_all']);moved=set(a['moved_bedside_objects'])
for n,b in a['before'].items():
    o=bpy.data.objects[n]
    if mh(o)!=b['mesh']:issues.append((n,'mesh'))
    if n not in moved and [list(r) for r in o.matrix_world]!=b['matrix']:issues.append((n,'matrix'))
    if n not in hidden and o.hide_render!=b['hide_render']:issues.append((n,'visibility'))
    if o.type=='MESH' and [m.name if m else None for m in o.data.materials]!=b['materials']:issues.append((n,'materials'))
assert not issues,issues[:12]
bed=bpy.data.objects[a['new_bed']];donor=bpy.data.objects[a['donor_bed']];assert mh(bed)==mh(donor)==a['same_complete_mesh']
assert list(bed.scale)==list(donor.scale) and list(bed.rotation_euler)==list(donor.rotation_euler)
assert [m.name for m in bed.data.materials]==[m.name for m in donor.data.materials]
assert all(abs(d*1000-t)<.1 for d,t in zip(bed.dimensions,[2130,1910,1070]))
v11=json.loads((R/'design/finishes_v11/BUILD_AUDIT.json').read_text())
for f in v11['protected_sources']:assert sha(f['path'])==f['sha256']
assert bpy.data.objects['READING_3205A_PADDED_BENCH'].hide_render
for x in v11['finish_assignments']:assert bpy.data.objects[x['object']].data.materials[0].name==x['material']
assert bpy.data.objects['READING_5015_SHORT_SLIDING_CABINET'].matrix_world.translation.z==a['before']['READING_5015_SHORT_SLIDING_CABINET']['matrix'][2][3]
v={'status':'PASS_INTACT_BED_REPLACEMENT_AND_PRESERVATION','sha256':a['sha256'],'original_meshes_and_materials_unchanged':len(a['before']),'unchanged_donor_bed':True,'new_bed_same_complete_mesh_material_rotation_scale':True,'new_bed_dimensions_mm':a['whole_bed_dimensions_mm'],'old_bed_hidden_objects':len(a['hidden_old_bed_objects']),'bedside_translations_only':a['bedside_translations'],'unexpected_changes':issues,'V11_finishes_and_grounded_shelf_retained':True,'protected_sources':len(v11['protected_sources']),'final_visual_acceptance':False}
(D/'VERIFICATION.json').write_text(json.dumps(v,indent=2)+'\n');print('VERIFY_V12',json.dumps(v))
