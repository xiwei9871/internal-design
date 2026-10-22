"""Read B1 candidate, add registered/draft cameras and references, preserve all geometry."""
from pathlib import Path
import bpy
import hashlib
import json
from mathutils import Matrix

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
SOURCE=ROOT/'design/blender_b1_1/B1_1_DESIGN_MODEL_V1.blend'
MODEL=OUT/'B1_1_SITE_REGISTERED_V1.blend'
manifest=json.loads((ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
for key,expected in manifest['sha256'].items():
    assert hashlib.sha256((ROOT/manifest['files'][key]).read_bytes()).hexdigest()==expected,'B0 integrity mismatch'
report=json.loads((OUT/'PHOTO_REGISTRATION_REPORT.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
col=bpy.data.collections.new('COL_SITE_PHOTO_REGISTRATION');bpy.context.scene.collection.children.link(col)
col['physical_ground_truth']=False;col['geometry_authority']=False
for r in report['photos']:
    name=r['camera_name'];camera=bpy.data.cameras.new(name);obj=bpy.data.objects.new(name,camera);col.objects.link(obj)
    params=r['camera_parameters'];R=Matrix(params['camera_cv_rotation_rows'])
    rot=R.transposed()@Matrix.Diagonal((1,-1,-1));matrix=rot.to_4x4()
    matrix.translation=params['position_m'];obj.matrix_world=matrix
    camera.type='PERSP';camera.sensor_fit='HORIZONTAL';camera.sensor_width=36
    camera.lens=36*params['focal_preview_px']/r['preview_size'][0]
    camera.clip_start=.025;camera.clip_end=100
    camera.show_background_images=True;bg=camera.background_images.new()
    bg.image=bpy.data.images.load(str(OUT/'originals'/f"{r['photo_id']}.jpg"),check_existing=True)
    bg.image.pack();bg.alpha=.50;bg.display_depth='BACK';bg.frame_method='FIT'
    obj['photo_id']=r['photo_id'];obj['registration_confidence']=r['confidence']
    obj['usable_for_dimension_estimation']=False
    obj['mean_reprojection_error_px']=r['mean_reprojection_error_px'] if r['mean_reprojection_error_px'] is not None else -1
    obj['max_reprojection_error_px']=r['max_reprojection_error_px'] if r['max_reprojection_error_px'] is not None else -1
    obj['reference_basis']=r['basis'];obj['status']='HUMAN_REVIEW_DRAFT_NOT_METRIC_ACCEPTED'
scene=bpy.context.scene;scene['B1_SITE_CORRECTION']='HUMAN_REVIEW'
scene['site_model_geometry_correction']='NOT_APPLIED_REGISTRATION_GATE_NOT_PASSED'
scene['old_pdf_role']='INITIAL_INSTALLATION; CURRENT_SITE_DETAILS_MUST_USE_PHOTO_EVIDENCE'
scene['site_photo_count']=6;scene.camera=bpy.data.objects['SITE_CAM_KITCHEN_001']
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))
print(json.dumps({'registered_scene':str(MODEL),'geometry_modified':False,'camera_count':6,
                  'metric_gate':'NOT_PASSED','B0_INTEGRITY':'PASS'},indent=2))
