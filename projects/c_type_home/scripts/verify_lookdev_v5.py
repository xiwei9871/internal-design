"""Fresh-open preservation, camera/light control, soft-envelope and material checks."""
import bpy,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/lookdev_v5';OLD=ROOT/'design/product_rebuild_v4/LIVING_DINING_PRODUCT_REBUILD_V4.blend'
def shot_state(scene):
    return {'cameras':{o.name:[o.data.lens,[float(x) for row in o.matrix_world for x in row]] for o in scene.objects if o.type=='CAMERA'},
            'lights':{o.name:[o.data.energy,list(o.data.color),[float(x) for row in o.matrix_world for x in row]] for o in scene.objects if o.type=='LIGHT'},
            'color':[scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure],
            'world':scene.world.name,'ceilings':[(o.name,o.hide_render) for o in scene.objects if o.name.startswith('CEILING_')]}
bpy.ops.wm.open_mainfile(filepath=str(OLD));before=shot_state(bpy.context.scene)
audit=json.loads((OUT/'BUILD_AUDIT.json').read_text());dest=Path(audit['output']);assert hashlib.sha256(dest.read_bytes()).hexdigest()==audit['output_sha256']
bpy.ops.wm.open_mainfile(filepath=str(dest));scene=bpy.context.scene;assert shot_state(scene)==before,'room light/camera/color state changed'
def fingerprint(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
    for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return {'sha256':h.hexdigest(),'matrix_world':[float(v) for row in o.matrix_world for v in row]}
baseline=json.loads((OUT/'UNCHANGED_GEOMETRY.json').read_text())
for n,s in baseline.items():assert fingerprint(bpy.data.objects[n])==s,n
for o in scene.objects:
    if o.type=='MESH':o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
def points(o):
    e=o.evaluated_get(deps);me=e.to_mesh();p=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();return p
def bounds(objects):
    p=[v for o in objects for v in points(o)];return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
constraints={'V4_LIVING_SOFA_COMPLETE':[[3.4,7.95,0],[5.2,11.25,.7]],'V4_WINDOW_CHAISE_COMPLETE':[[4.671625,11.05522,0],[6.371625,11.95522,.8]]};envelopes={}
for name,wanted in constraints.items():
    b=bounds([o for o in bpy.data.objects[name].children_recursive if o.type in ['MESH','CURVE'] and not o.hide_render]);assert all(b[0][i]>=wanted[0][i]-.003 and b[1][i]<=wanted[1][i]+.003 for i in range(3)),(name,b)
    envelopes[name]=b
seat=[bounds([bpy.data.objects[n]]) for n in ['V4_Sofa_chaise_upholstery','V4_Sofa_seat_middle','V4_Sofa_seat_north']];gaps=[(seat[i+1][0][1]-seat[i][1][1])*1000 for i in range(2)];assert all(0<=v<15 for v in gaps),gaps
support_gaps=[(b[0][2]-.285)*1000 for b in seat];assert all(-3<=v<=3 for v in support_gaps),support_gaps
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()];assert not missing,missing
protected=json.loads((OUT/'PRESERVATION.json').read_text())['files']
for f in protected:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
report={'status':'PASS','fresh_reopen':True,'preserved_meshes':len(baseline),'changed_soft_meshes':audit['changed_soft_meshes'],'room_camera_lights_color_unchanged':True,'protected_hashes_pass':len(protected),'envelopes':envelopes,'seat_gaps_mm':gaps,'seat_bottom_to_deck_top_mm':support_gaps,'missing_images':missing,'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'output_sha256':audit['output_sha256'],'visual_acceptance':'OWNER_REVIEW_REQUIRED','not_certified':'exactproductSKU,fillingmechanics,constructionorhumanergonomics'}
(OUT/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print('V5_VERIFY_PASS',len(baseline),gaps,support_gaps)
