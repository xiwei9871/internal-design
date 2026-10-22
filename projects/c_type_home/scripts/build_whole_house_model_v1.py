"""Build an isolated whole-house presentation candidate from the production scene."""
import bpy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design/whole_house_model_v1'; OUT.mkdir(exist_ok=True)
SOURCE=ROOT/'renders/whole_house_final_study_v1/production_batch_v1/WHOLE_HOUSE_PRODUCTION_V1.blend'
AUDIT=OUT/'SOURCE_AUDIT.json'; DEC=ROOT/'render_config/whole_house_model_v1/ROOM_DECISIONS.json'; dest=OUT/'WHOLE_HOUSE_MODEL_V1.blend'
assert SOURCE.exists() and AUDIT.exists() and DEC.exists()
audit=json.loads(AUDIT.read_text()); decisions=json.loads(DEC.read_text())
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==audit['source_sha256']
if dest.exists(): raise SystemExit('Preserved candidate exists; use a new version directory.')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene=bpy.context.scene; bpy.context.view_layer.update()
base_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
presentation=bpy.data.collections.new('WHOLE_HOUSE_MODEL_V1_PRESENTATION'); scene.collection.children.link(presentation)
scene['whole_house_model_revision']='whole-house-model-v1'; scene['source_design_sha256']=base_hash
scene['owner_contract']='2026-10-12 confirmed room-by-room directions'; scene['architecture_authority']='production source; walls/openings/levels/stairs/plumbing unchanged'
scene['sofa_reference_workflow']='V10 supported seat core + soft jacket; channel-filled back; actual intersections checked'; scene['image2_requests']=0; scene['whole_house_batch_started']=False
def marker(room,choice):
    e=bpy.data.objects.new('MODEL_V1_'+room.upper()+'_'+choice['mode'].upper(),None); presentation.objects.link(e); e['room_id']=room; e['mode']=choice['mode']; e['notes']=choice['notes']; e['appearance_only']=True; e.hide_render=True; e.hide_viewport=True; return e
markers=[marker(r,c) for r,c in decisions['rooms'].items()]
material_tags=[]
for o in scene.objects:
    if o.type!='MESH' or not o.data.materials: continue
    n=o.name.upper(); mnames=' '.join(m.name.upper() for m in o.data.materials if m)
    if any(x in n for x in ['KITCHEN','SUNROOM','STORAGE','CABINET','SHELF','BOOK','WARDROBE','VANITY','BED','DESK','TABLE','CONSOLE']):
        o['model_v1_material_family']='PALE_ASH_OR_EXISTING_PRODUCT_MATERIAL'; material_tags.append(o.name)
    elif any(x in mnames for x in ['WOOD','ASH','RENDER_WHITE_ASH']): o['model_v1_material_family']='PALE_ASH_RETAINED'; material_tags.append(o.name)
    elif any(x in mnames for x in ['LINEN','FABRIC','IVORY']): o['model_v1_material_family']='IVORY_FLAX_RETAINED'; material_tags.append(o.name)
def tag(names,key,value):
    found=[]
    for name in names:
        o=bpy.data.objects.get(name)
        if o: o[key]=value; found.append(name)
    return found
corrections={
 'kitchen_window_family':tag(['B11_SITE_KITCHEN_WINDOW_GLASS_0','B11_SITE_KITCHEN_WINDOW_GLASS_1','B11_SITE_KITCHEN_WINDOW_MULLION_1'],'model_v1_constraint','VIEW_03_CORRECT_WINDOW_FAMILY'),
 'three_wave_steps':tag(['B11_STEP_0_REVIEW_NOSING','B11_STEP_1_REVIEW_NOSING','B11_STEP_2_REVIEW_NOSING'],'model_v1_constraint','EXACTLY_THREE_STEPS'),
 'reading_art_wall_shelf':tag(['READING_5015_SHORT_SHELF_0','READING_5015_SHORT_SHELF_1','READING_5015_SHORT_SHELF_2','READING_5015_SHORT_SLIDING_CABINET'],'model_v1_constraint','ART_WALL_SIDE_NOT_HANDRAIL_SIDE'),
 'wood_handrail':tag(['WAVE_HANDRAIL_LOWER_RETURN','WAVE_HANDRAIL_UPPER_RETURN'],'model_v1_constraint','PALE_WOOD_RAIL;METAL_BRACKETS_REVIEW'),
 'north_revised_cabinet':tag(['SUNROOM_SOFA_REAR_HIGH_CABINET','SUNROOM_INTEGRATED_UPPER_DOOR_0','SUNROOM_INTEGRATED_UPPER_DOOR_1','SUNROOM_INTEGRATED_UPPER_DOOR_2','SUNROOM_INTEGRATED_UPPER_DOOR_3','SUNROOM_INTEGRATED_UPPER_DOOR_4'],'model_v1_constraint','REVISED_HISTORY_STATE_DO_NOT_RESTORE_OLD_UPPER_CABINET'),
 'mother_vanity_review':tag(['BW1_MOTHER_VANITY','BW1_MOTHER_VANITY_CHAIR'],'model_v1_constraint','REPLACE_WITH_REAL_PRODUCT_OR_CREATIVE_VIEW05_REFERENCE')}
meta={'status':'CANDIDATE_BUILT_HUMAN_REVIEW','source':str(SOURCE),'source_sha256':base_hash,'output':str(dest),'room_decisions':decisions,'material_tagged_objects':len(material_tags),'material_tag_samples':material_tags[:80],'corrections':corrections,'architecture_objects_unchanged':audit['object_count'],'candidate_marker_count':len(markers),'unresolved':['real kitchen appliance SKU','mother vanity product/reference selection','north cabinet history provenance','room-by-room appearance acceptance'],'image2_requests':0,'whole_house_batch_started':False}
(OUT/'BUILD_AUDIT.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(dest)); meta['output_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest(); (OUT/'BUILD_AUDIT.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('WHOLE_HOUSE_MODEL_V1_BUILT',json.dumps({'output':str(dest),'output_sha256':meta['output_sha256'],'markers':len(markers),'tagged':len(material_tags)}))
