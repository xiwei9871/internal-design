"""Render one bounded Workbench preview per room using the approved cameras."""
import bpy, json, hashlib, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'design/whole_house_model_v1'; REND=OUT/'preview'; REND.mkdir(exist_ok=True)
CAND=OUT/'WHOLE_HOUSE_MODEL_V1.blend'; CAM=ROOT/'renders/whole_house_final_study_v1/00_MANIFEST/CAMERA_REGISTER_REVIEW_V3.json'
bpy.ops.wm.open_mainfile(filepath=str(CAND)); scene=bpy.context.scene; reg=json.loads(CAM.read_text()); rooms=[]; seen=set(); decisions=json.loads((ROOT/'render_config/whole_house_model_v1/ROOM_DECISIONS.json').read_text())
scene.render.engine='BLENDER_WORKBENCH'; scene.render.resolution_x=960; scene.render.resolution_y=540; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'; scene.render.threads_mode='FIXED'; scene.render.threads=2
s=scene.display.shading; s.light='STUDIO'; s.color_type='MATERIAL'; s.show_shadows=True; s.show_cavity=False; s.show_specular_highlight=False
for c in reg['cameras']:
 if c['room_id'] in seen: continue
 seen.add(c['room_id']); cam=bpy.data.objects.get(c['camera_name']); assert cam, c['camera_name']; scene.camera=cam
 out=REND/(c['room_id']+'_VIEW_01.png'); t=time.time(); scene.render.filepath=str(out); bpy.ops.render.render(write_still=True)
 rooms.append({'room_id':c['room_id'],'camera':c['camera_name'],'path':str(out),'size':[960,540],'seconds':round(time.time()-t,2),'mode':decisions['rooms'][c['room_id']]['mode']})
manifest={'status':'PREVIEW_RENDERED','source':str(CAND),'source_sha256':hashlib.sha256(CAND.read_bytes()).hexdigest(),'engine':'BLENDER_WORKBENCH','cavity':False,'images':rooms,'image2_requests':0,'whole_house_batch_started':False}
(OUT/'PREVIEW_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'); print('WHOLE_HOUSE_PREVIEW',len(rooms))
