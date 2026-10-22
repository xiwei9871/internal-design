import bpy,json,sys
from pathlib import Path
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import bounds
root=Path(__file__).parent;qa=json.loads((root/'DINING_CHAIRS_QA.json').read_text())
bpy.ops.import_scene.gltf(filepath=str(root/'proxy/interaction_proxy.glb'))
for name,target in {**qa['after'],qa['table']:qa['table_bounds_m']}.items():
 obj=next(o for o in bpy.context.scene.objects if o.get('native_object_id')==name);actual=bounds(obj);assert max(abs(actual[i][j]-target[i][j]) for i in range(2) for j in range(3))<1e-5,(name,actual,target)
report={'status':'PASS','fresh_glb_import':True,'four_chair_world_bounds_match':True,'table_world_bounds_unchanged':True}
(root/'EXPORTED_CHAIRS_QA.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
