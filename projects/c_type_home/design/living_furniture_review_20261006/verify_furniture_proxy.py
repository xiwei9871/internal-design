import bpy,json,sys
from pathlib import Path
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import bounds,sha
r=Path(__file__).parent;q=json.loads((r/'LIVING_FURNITURE_QA.json').read_text())
bpy.ops.import_scene.gltf(filepath=str(r/'proxy/interaction_proxy.glb'))
objects={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('native_object_id')};assert len(objects)==1017
for name,target in q['after'].items():
 actual=bounds(objects[name]);assert max(abs(actual[i][j]-target[i][j]) for i in range(2) for j in range(3))<2e-5,(name,actual,target)
for path,v in q['frozen_files_unchanged'].items():
 p=Path(path);assert sha(p)==v['sha256'] and p.stat().st_size==v['size'] and str(p.stat().st_mtime_ns)==v['mtime_ns']
report={'status':'PASS','fresh_glb_import':True,'entity_count':1017,'three_target_bounds_correct':True,'frozen_sources_unchanged':True};(r/'PROXY_FURNITURE_QA.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
