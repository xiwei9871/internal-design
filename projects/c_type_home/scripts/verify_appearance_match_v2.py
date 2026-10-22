"""Fresh-reopen invariants, surface/material dependencies and protected asset checks."""
import bpy,json,struct,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/appearance_match_v2'
manifest=json.loads((OUT/'BUILD_MANIFEST.json').read_text())
def geometry(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 return h.hexdigest(),[float(x) for row in o.matrix_world for x in row]
def localbounds(o):
 return [[min(v.co[i] for v in o.data.vertices) for i in range(3)],[max(v.co[i] for v in o.data.vertices) for i in range(3)]]
soft=manifest['soft_refinements_with_locked_bounds']
bpy.ops.wm.open_mainfile(filepath=manifest['source'])
baseline_bounds={n:localbounds(bpy.data.objects[n]) for n in soft}
bpy.ops.wm.open_mainfile(filepath=manifest['output'])
for o in bpy.context.scene.objects:
 if o.type=='MESH':o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
baseline=json.loads((OUT/'PRESERVED_MESHES.json').read_text())
for n,f in baseline.items():
 o=bpy.data.objects[n];actual=geometry(o);assert actual[1]==f[1],n
 if n not in soft:assert actual[0]==f[0],n
for n,wanted in baseline_bounds.items():
 actual=localbounds(bpy.data.objects[n]);assert max(abs(actual[j][i]-wanted[j][i]) for j in range(2) for i in range(3))<.00001,n
assert bpy.data.objects['FLOOR_LOWER'].data.materials[0].name=='AM2_WOOD_FLOOR_BOARDS'
assert bpy.data.objects['LD_Coffee_tabletop'].data.materials[0].name=='AM2_WHITE_ASH_HONEY_MATTE'
assert bpy.data.objects['LD_Sofa_upholstery_04'].data.materials[0].name=='AM2_SOFA_OATMEAL_LINEN'
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()]
assert not missing,missing
for f in json.loads((OUT/'PRESERVATION.json').read_text())['files']:
 assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
registry=json.loads((ROOT/'design/sunroom_stepped_storage_v1/spatial-canvas.bindings.full.json').read_text())
assert all(b['native_id'] not in soft for b in registry['bindings'])
report={'status':'PASS','registered_source_meshes_and_world_matrices_unchanged':len(registry['bindings']),'all_nonsoft_candidate_meshes_unchanged':len(baseline)-len(soft),'all_candidate_world_matrices_unchanged':len(baseline),'refined_soft_bounds_tolerance_mm':.01,'refined_soft_objects':soft,'protected_files_pass':True,'material_slots_checked':['FLOOR_LOWER','LD_Coffee_tabletop','LD_Sofa_upholstery_04'],'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'missing_images':missing,'visual_match_gate':'SEPARATE_FROM_TECHNICAL_PASS'}
(OUT/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print('APPEARANCE_V2_VERIFY_PASS',len(baseline),len(soft))
