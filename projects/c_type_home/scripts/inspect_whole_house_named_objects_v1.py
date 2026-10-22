import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRES=ROOT/'renders/whole_house_final_study_v1/production_batch_v1/WHOLE_HOUSE_PRODUCTION_V1.blend'
OUT=ROOT/'design/whole_house_model_v1'
bpy.ops.wm.open_mainfile(filepath=str(PRES))
bpy.context.view_layer.update()
terms=['KITCHEN','WINDOW','SUNROOM','NORTH','READING','STEP','WAVE','HANDRAIL','MOTHER','VANITY','SOFA','COUCH','DINING','BED','STUDY','BATH','CABINET','SHELF','MIRROR']
def rec(o):
    p=[o.matrix_world@v.co for v in o.data.vertices]
    return {'name':o.name,'type':o.type,'collections':[c.name for c in o.users_collection],'materials':[m.name for m in o.data.materials] if hasattr(o.data,'materials') else [],'bounds':[[min(x[i] for x in p) for i in range(3)],[max(x[i] for x in p) for i in range(3)]]}
rows=[]
for o in bpy.data.objects:
    if o.type!='MESH': continue
    u=o.name.upper()
    if any(t in u for t in terms): rows.append(rec(o))
(OUT/'NAMED_OBJECT_AUDIT.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print('NAMED_OBJECT_AUDIT',len(rows))
print(json.dumps(rows[:30],ensure_ascii=False))
