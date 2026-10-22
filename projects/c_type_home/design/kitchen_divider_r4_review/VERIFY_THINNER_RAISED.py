import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Matrix
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import object_state,bounds
root=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(root/'OPTION_A_R4_PIER_AND_ANGLED_AC_REVIEW.blend'))
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
ac=bpy.data.objects['B11_K-UTILITY-WALL-AC'];allowed={o.name for o in [ac,*ac.children_recursive]}
poses={n:bpy.data.objects[n].matrix_world.copy() for n in allowed}
wall_before=bounds(bpy.data.objects['KITCHEN_DIVIDER_PIER_SITE_REVIEW'])
bpy.ops.wm.open_mainfile(filepath=str(root/'OPTION_A_R4_PIER_THINNER_AC_RAISED_REVIEW.blend'))
assert set(prior)=={o.name for o in bpy.context.scene.objects}
for n,s in prior.items():
 if n not in allowed|{'KITCHEN_DIVIDER_PIER_SITE_REVIEW'}:assert object_state(bpy.data.objects[n])==s,n
for n in allowed:
 assert object_state(bpy.data.objects[n])['mesh']==prior[n]['mesh'],n
 expected=Matrix.Translation((0,0,.3))@poses[n]
 assert max(abs(a-b) for r1,r2 in zip(bpy.data.objects[n].matrix_world,expected) for a,b in zip(r1,r2))<1e-5,n
wall=bounds(bpy.data.objects['KITCHEN_DIVIDER_PIER_SITE_REVIEW']);assert abs(wall[0][0]-wall_before[0][0]-.05)<1e-5
assert all(abs(wall[i][j]-wall_before[i][j])<1e-5 for i in range(2) for j in range(3) if (i,j)!=(0,0))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for path,s in json.loads((root/'PIER_AND_AC_QA.json').read_text())['frozen_files_unchanged'].items():
 p=Path(path);assert sha(p)==s['sha256'] and p.stat().st_size==s['size'] and str(p.stat().st_mtime_ns)==s['mtime_ns'],path
packet=json.loads((root/'proxy-thinner-raised/pier.context.json').read_text())
assert packet['source']['revision']=='r4-pier-ac-review-4' and packet['source']['sha256']==sha(root/'OPTION_A_R4_PIER_THINNER_AC_RAISED_REVIEW.blend')
assert packet['entities'][0]['global_id']=='ent_b1bbaaf28737516b9c695b249f0d7ea5'
assert packet['hit']['entity_id']==packet['entities'][0]['global_id']
assert packet['source']['bindings']['sha256']==sha(root/'spatial-canvas.bindings.thinner-raised.json')
report={'status':'PASS','fresh_reopen':True,'other_objects_unchanged':True,'wall_reduction_m':.05,'ac_translation_m':.3,'ac_meshes_unchanged':True,'frozen_files_hash_size_mtime_unchanged':True,'browser_pointer_packet_verified':True}
(root/'THINNER_RAISED_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
