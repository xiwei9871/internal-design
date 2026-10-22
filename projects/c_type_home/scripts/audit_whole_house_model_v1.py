"""Read-only audit of the production whole-house blend and room authority files."""
import bpy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design/whole_house_model_v1'; OUT.mkdir(exist_ok=True)
PRES=ROOT/'renders/whole_house_final_study_v1/production_batch_v1/WHOLE_HOUSE_PRODUCTION_V1.blend'
CAM=ROOT/'renders/whole_house_final_study_v1/00_MANIFEST/CAMERA_REGISTER_REVIEW_V3.json'
ROOM=ROOT/'renders/whole_house_final_study_v1/00_MANIFEST/WHOLE_HOUSE_ROOM_MANIFEST_V1.json'
DEC=ROOT/'render_config/whole_house_model_v1/ROOM_DECISIONS.json'
assert PRES.exists() and CAM.exists() and ROOM.exists() and DEC.exists()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(PRES)); scene=bpy.context.scene; bpy.context.view_layer.update()
names={o.name for o in scene.objects}
rooms=json.loads(ROOM.read_text())['rooms']; dec=json.loads(DEC.read_text()); camera=json.loads(CAM.read_text())
missing=[c['camera_name'] for c in camera['cameras'] if c['camera_name'] not in names]
patterns={
 'kitchen_window_candidates':[n for n in names if any(x in n.upper() for x in ['KITCHEN','WINDOW','GLAZING'])],
 'north_cabinet_candidates':[n for n in names if any(x in n.upper() for x in ['NORTH','SUNROOM','CABINET','STORAGE'])],
 'reading_candidates':[n for n in names if any(x in n.upper() for x in ['READING','STEP','STAIR','WAVE','SHELF','HANDRAIL'])],
 'mother_vanity_candidates':[n for n in names if any(x in n.upper() for x in ['MOTHER','VANITY','DRESS','DRESSING'])],
 'sofa_candidates':[n for n in names if any(x in n.upper() for x in ['SOFA','COUCH','SEAT','BACK'])]
}
audit={'status':'AUDIT_COMPLETE','source':str(PRES),'source_sha256':sha(PRES),'camera_register':str(CAM),'camera_register_sha256':sha(CAM),'room_manifest':str(ROOM),'room_manifest_sha256':sha(ROOM),'room_count':len(rooms),'camera_count':len(camera['cameras']),'missing_camera_objects':missing,'collections':[c.name for c in bpy.data.collections],'object_count':len(scene.objects),'mesh_count':sum(o.type=='MESH' for o in scene.objects),'candidate_name_patterns':patterns,'room_decisions':dec,'architecture_hash_policy':'source blend unchanged; derived candidate only','unresolved':['exact kitchen appliance SKU','mother bedroom real vanity SKU','north sunroom revised cabinet history object identity','all non-living/dining owner appearance acceptance']}
(OUT/'SOURCE_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print('WHOLE_HOUSE_SOURCE_AUDIT',json.dumps({'status':audit['status'],'source_sha256':audit['source_sha256'],'camera_count':audit['camera_count'],'room_count':audit['room_count'],'object_count':audit['object_count'],'mesh_count':audit['mesh_count'],'missing_camera_objects':missing},ensure_ascii=False))
