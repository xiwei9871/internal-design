import bpy,json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'renders/r3_option_a';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'design/secondary_bath_options/r3/OPTION_A_SLIDING_R3.blend'
m=json.loads((SOURCE.parent/'OPTION_A_MANIFEST.json').read_text())
h=hashlib.sha256(SOURCE.read_bytes()).hexdigest();assert h==m['model_sha256']
BRANCH=OUT/'OPTION_A_SLIDING_R3_RENDER_V1.blend'
if not BRANCH.exists():shutil.copy2(SOURCE,BRANCH)
else:assert hashlib.sha256(BRANCH.read_bytes()).hexdigest()==h,'Existing render branch; preserve it'
shutil.copy2('/Users/xiwei/.codex/attachments/a378b707-69bd-4a3a-8333-b6ed44a43d0f/Pasted text.txt',OUT/'USER_RENDER_TASK_BRIEF.txt')
bpy.ops.wm.open_mainfile(filepath=str(BRANCH));bpy.context.view_layer.update()
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.hide_render or o.hide_viewport:continue
 vs=[o.matrix_world@v.co for v in o.data.vertices]
 if not vs:continue
 lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
 if lo[0]<8.2 and hi[0]>2.5 and lo[1]<14 and hi[1]>7.5:
  rows.append(dict(name=o.name,lo=lo,hi=hi,materials=[s.material.name if s.material else None for s in o.material_slots],collections=[c.name for c in o.users_collection]))
write=dict(source=str(SOURCE),source_sha256=h,branch=str(BRANCH),blender=bpy.app.version_string,active_living_area=rows,cameras=[dict(name=o.name,pos=list(o.location),lens=o.data.lens,type=o.data.type) for o in bpy.data.objects if o.type=='CAMERA' and ('LIVING' in o.name or 'LIV_' in o.name)])
(OUT/'TEST_PREFLIGHT.json').write_text(json.dumps(write,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(source_hash='PASS',branch=str(BRANCH),active_local_objects=len(rows),objects=[dict(name=r['name'],lo=r['lo'],hi=r['hi']) for r in rows if r['name'].startswith(('LIVING_FIX_BAY','R3_HOUSE','B11_Rectangle046','B11_Rectangle047','B11_Rectangle048','B11_Rectangle049'))]),ensure_ascii=False))
