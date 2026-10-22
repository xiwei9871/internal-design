"""Fresh-open technical verification for whole-house model candidate."""
import bpy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'design/whole_house_model_v1'
PRES=ROOT/'renders/whole_house_final_study_v1/production_batch_v1/WHOLE_HOUSE_PRODUCTION_V1.blend'; CAND=OUT/'WHOLE_HOUSE_MODEL_V1.blend'
AUD=json.loads((OUT/'BUILD_AUDIT.json').read_text()); audit=json.loads((OUT/'SOURCE_AUDIT.json').read_text())
assert hashlib.sha256(PRES.read_bytes()).hexdigest()==AUD['source_sha256']==audit['source_sha256']
assert hashlib.sha256(CAND.read_bytes()).hexdigest()==AUD['output_sha256']
bpy.ops.wm.open_mainfile(filepath=str(CAND)); scene=bpy.context.scene; bpy.context.view_layer.update()
assert scene.get('whole_house_model_revision')=='whole-house-model-v1'
assert scene.get('source_design_sha256')==AUD['source_sha256']
assert scene.get('image2_requests')==0 and scene.get('whole_house_batch_started') is False
markers=[o for o in bpy.data.objects if o.name.startswith('MODEL_V1_')]
assert len(markers)==15,len(markers)
assert len(scene.objects)>=audit['object_count']
assert bpy.data.objects.get('B11_SITE_KITCHEN_WINDOW_MULLION_1').get('model_v1_constraint')=='VIEW_03_CORRECT_WINDOW_FAMILY'
for i in range(3): assert bpy.data.objects.get(f'B11_STEP_{i}_REVIEW_NOSING').get('model_v1_constraint')=='EXACTLY_THREE_STEPS'
for n in ['READING_5015_SHORT_SHELF_0','READING_5015_SHORT_SHELF_1','READING_5015_SHORT_SHELF_2','READING_5015_SHORT_SLIDING_CABINET']:
 assert bpy.data.objects[n].get('model_v1_constraint')=='ART_WALL_SIDE_NOT_HANDRAIL_SIDE'
for n in ['WAVE_HANDRAIL_LOWER_RETURN','WAVE_HANDRAIL_UPPER_RETURN']:
 assert bpy.data.objects[n].get('model_v1_constraint')=='PALE_WOOD_RAIL;METAL_BRACKETS_REVIEW'
assert bpy.data.objects['SUNROOM_SOFA_REAR_HIGH_CABINET'].get('model_v1_constraint').startswith('REVISED_HISTORY')
assert bpy.data.objects['BW1_MOTHER_VANITY'].get('model_v1_constraint').startswith('REPLACE_WITH_REAL_PRODUCT')
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()]
assert not missing,missing
tags=sum(1 for o in scene.objects if o.get('model_v1_material_family'))
report={'status':'PASS_TECHNICAL_ONLY','source_sha256':AUD['source_sha256'],'candidate_sha256':AUD['output_sha256'],'source_object_count':audit['object_count'],'candidate_object_count':len(scene.objects),'room_markers':len(markers),'material_family_tags':tags,'missing_images':missing,'hard_constraints':['kitchen VIEW_03 window family','exactly 3 steps','reading shelf art wall','pale wood handrail returns','revised north cabinet retained','mother vanity replacement review'],'appearance_status':'HUMAN_REVIEW_PENDING','architecture_writeback':False,'image2_requests':0,'whole_house_batch_started':False}
(OUT/'VERIFICATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n'); print('WHOLE_HOUSE_VERIFY',json.dumps(report,ensure_ascii=False))
