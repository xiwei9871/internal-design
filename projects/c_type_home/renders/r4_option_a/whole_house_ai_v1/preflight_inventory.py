import bpy,json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
SRC=ROOT/'design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend';BRANCH=OUT/'00_manifest/R4_WHOLE_HOUSE_AI_REFERENCE_V1.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for d in ['00_manifest','00_manifest/logs','00_manifest/proxies']:(OUT/d).mkdir(parents=True,exist_ok=True)
m=json.loads((SRC.parent/'R4_OPTION_A_MANIFEST.json').read_text());assert sha(SRC)==m['model_sha256']
if not BRANCH.exists():shutil.copy2(SRC,BRANCH)
shutil.copy2('/Users/xiwei/.codex/attachments/86f88e22-8b23-4234-9bf5-fc4e37e03e44/Pasted text.txt',OUT/'00_manifest/USER_OVERNIGHT_TASK_BRIEF.txt')
bpy.ops.wm.open_mainfile(filepath=str(BRANCH));bpy.context.view_layer.update()
rows=[]
for o in bpy.data.objects:
 if o.type=='MESH':
  vs=[o.matrix_world@v.co for v in o.data.vertices]
  if not vs:continue
  lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
 else:lo=list(o.location);hi=list(o.location)
 props={k:str(o[k])[:1000] for k in o.keys() if any(x in k.lower() for x in ['room','zone','label','role','source','semantic','id','purpose','ffl'])}
 rows.append(dict(name=o.name,type=o.type,lo=lo,hi=hi,hidden=[o.hide_render,o.hide_viewport,o.hide_get()],collections=[c.name for c in o.users_collection],materials=[s.material.name if s.material else None for s in o.material_slots] if o.type=='MESH' else [],props=props))
collections=[dict(name=c.name,objects=len(c.objects),hide_render=c.hide_render,hide_viewport=c.hide_viewport) for c in bpy.data.collections]
pref=dict(status='PASS_OPENED_R4',source_path=str(SRC),sha256=sha(SRC),object_count=len(bpy.data.objects),collection_count=len(bpy.data.collections),working_copy=str(BRANCH),blender=bpy.app.version_string,source_unchanged=True)
(OUT/'00_manifest/R4_WHOLE_HOUSE_PREFLIGHT.json').write_text(json.dumps(pref,ensure_ascii=False,indent=2)+'\n')
(OUT/'00_manifest/R4_ACTUAL_OBJECT_INVENTORY.json').write_text(json.dumps(dict(objects=rows,collections=collections,scene_properties={k:str(bpy.context.scene[k])[:1500] for k in bpy.context.scene.keys()}),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(preflight='PASS',objects=pref['object_count'],collections=pref['collection_count'],source_sha256=pref['sha256'],room_objects=[r['name'] for r in rows if any(x in r['name'].upper() for x in ['ROOM','ZONE','LABEL','SPACE'])]),ensure_ascii=False))
