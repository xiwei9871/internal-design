import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/whole_house_model_v1';CAND=OUT/'WHOLE_HOUSE_MODEL_V1.blend'
bpy.ops.wm.open_mainfile(filepath=str(CAND));scene=bpy.context.scene
WOOD=bpy.data.materials.get('RENDER_WHITE_ASH'); CLOTH=bpy.data.materials.get('RENDER_IVORY_LINEN')
def tag(names,key,value):
 found=[]
 for n in names:
  o=bpy.data.objects.get(n)
  if o:o[key]=value;found.append(n)
 return found
for n in [o.name for o in scene.objects if o.type=='MESH' and any(x in o.name.upper() for x in ['B11_K-','KITCHEN_'])]:
 o=bpy.data.objects[n];o['house_v1_room']='kitchen';o['house_v1_style']='faithful';o['real_product_reference']='kitchen_prompt_review_v2/APPLIANCE_OFFICIAL_REFERENCES.json'
for n in ['B11_SITE_KITCHEN_WINDOW_GLASS_0','B11_SITE_KITCHEN_WINDOW_GLASS_1','B11_SITE_KITCHEN_WINDOW_MULLION_1']:
 o=bpy.data.objects.get(n)
 if o:o['house_v1_window_authority']='VIEW_03_CORRECT'
for n in ['B11_STEP_0','B11_STEP_1','B11_STEP_2']:
 o=bpy.data.objects.get(n)
 if o:o['house_v1_step_count']='THREE_STEPS'
for n in ['WAVE_HANDRAIL_LOWER_RETURN','WAVE_HANDRAIL_UPPER_RETURN']:
 o=bpy.data.objects.get(n)
 if o and WOOD:o.data.materials.clear();o.data.materials.append(WOOD);o['house_v1_finish']='pale ash wood handrail; metal bracket only'
for n in ['READING_5015_SHORT_SHELF_0','READING_5015_SHORT_SHELF_1','READING_5015_SHORT_SHELF_2','READING_5015_SHORT_SLIDING_CABINET']:
 o=bpy.data.objects.get(n)
 if o:o['house_v1_wall_role']='artwork_wall_shelf;away_from_handrail'
for n in ['SUNROOM_SOFA_REAR_HIGH_CABINET','SUNROOM_INTEGRATED_UNDERSIDE']:
 o=bpy.data.objects.get(n)
 if o:o['house_v1_revision']='current_stepped_storage_candidate;do_not_restore_old_cabinet'
old=bpy.data.objects.get('BW1_MOTHER_VANITY')
if old:old.hide_render=True;old.hide_viewport=True;old.hide_set(True);old['house_v1_replacement']='creative real-product reference pending'
for o in scene.objects:
 if o.name.startswith('V4_Sofa_') or o.name.startswith('V4_LIVING_SOFA'):
  o['house_v1_sofa_workflow']='V10 differentiated seat support and filled back; native wood/linen retained';o['house_v1_real_product_reference']='owner ash catalog p4/p8; custom whole object, SKU pending'
decisions=json.loads((ROOT/'render_config/whole_house_model_v1/ROOM_DECISIONS.json').read_text())['rooms']
for room,choice in decisions.items():
 marker=bpy.data.objects.get('MODEL_V1_'+room.upper()+'_'+choice['mode'].upper())
 if marker:marker['applied_finish']='candidate semantic lock';marker['real_reference_required']=room not in ['living','dining']
scene['whole_house_model_stage']='room_finish_candidate';scene['room_finish_applied']=True;scene['source_writeback']=False;scene['image2_requests']=0;scene['whole_house_batch_started']=False
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(CAND))
audit=json.loads((OUT/'BUILD_AUDIT.json').read_text());audit['output_sha256']=hashlib.sha256(CAND.read_bytes()).hexdigest();audit['finish_applied']=True;audit['mother_vanity_replaced']=bool(old);audit['source_writeback']=False;(OUT/'BUILD_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print('WHOLE_HOUSE_FINISH_APPLIED',bool(old))
