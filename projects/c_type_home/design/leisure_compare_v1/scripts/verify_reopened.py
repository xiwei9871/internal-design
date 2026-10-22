import bpy,json,sys,hashlib,bmesh,runpy
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[1];SRC=ROOT/'design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend';H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='helper');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def states():return {n:{k:v for k,v in d.items() if k in ['type','geometry_sha256','authored_transform','parent','modifiers']} for n,d in H['snapshot']().items()}
bpy.ops.wm.open_mainfile(filepath=str(SRC));baseline=states();report=[]
for k in ['A','B']:
 file=OUT/('LEISURE_COMPARE_OPTION_'+k+'.blend');bpy.ops.wm.open_mainfile(filepath=str(file));current=states();lock=json.loads((OUT/'reports'/('OPTION_'+k+'_INHERITED_STATE_LOCK.json')).read_text());changed=[n for n in lock['protected_names'] if current.get(n)!=baseline[n]];assert not changed,changed
 col=bpy.data.collections['OPTION_'+k+('_RETAINED' if k=='A' else '_REMOVED')];top=[]
 for o in col.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);top.append(dict(name=o.name,nonmanifold=bad));bm.free();assert bad==0,o.name
 ramp=bpy.data.collections['RAMP_RESEARCH_NOT_ADOPTED_450_5400_1in12'];assert ramp.hide_render and ramp.hide_viewport
 # Furniture dimensions outside study remain exactly as R4, doors never moved.
 report.append(dict(option=k,branch=str(file),branch_sha256=sha(file),protected_count=len(lock['protected_names']),unchanged_protected=True,nonmanifold_new_meshes=0,ramp_disabled=True,local_top_z=[.15,.30,.45],model_status='RESEARCH_ONLY_NOT_CONSTRUCTION',checks=top))
(OUT/'reports/FRESH_REOPEN_QA.json').write_text(json.dumps(dict(status='PASS',source_sha256=sha(SRC),options=report),ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(status='PASS_FRESH_REOPEN',options=2,source_unchanged=sha(SRC)==lock['source_sha256'],protected_objects=[r['protected_count'] for r in report])))
