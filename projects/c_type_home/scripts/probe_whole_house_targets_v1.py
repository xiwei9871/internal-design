import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];PRES=ROOT/'renders/whole_house_final_study_v1/production_batch_v1/WHOLE_HOUSE_PRODUCTION_V1.blend';OUT=ROOT/'design/whole_house_model_v1'
bpy.ops.wm.open_mainfile(filepath=str(PRES));bpy.context.view_layer.update()
terms=['SOFA','COUCH','SEAT','BACK','KITCHEN_WINDOW','SUNROOM_SOFA','READING_5015','WAVE_HANDRAIL','STEP_','MOTHER_VANITY','R3_VANITY','STUDY_V1','B11_SITE_KITCHEN_WINDOW']
def rec(o):
 p=[o.matrix_world@v.co for v in o.data.vertices];return {'name':o.name,'bounds':[[min(x[i] for x in p) for i in range(3)],[max(x[i] for x in p) for i in range(3)]],'dims':[max(x[i] for x in p)-min(x[i] for x in p) for i in range(3)],'materials':[m.name for m in o.data.materials]}
rows=[rec(o) for o in bpy.data.objects if o.type=='MESH' and any(t in o.name.upper() for t in terms)]
(OUT/'TARGET_OBJECT_AUDIT.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print('TARGET_OBJECT_AUDIT',len(rows));print(json.dumps(rows,ensure_ascii=False))
