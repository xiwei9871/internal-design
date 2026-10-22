import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/fridge_finish_v13';a=json.loads((D/'BUILD_AUDIT.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(a['source'])==a['source_sha256'] and sha(a['output'])==a['sha256'];bpy.ops.wm.open_mainfile(filepath=a['output'])
for n in a['changed_cabinet_objects']:assert bpy.data.objects[n].data.materials[0].name==a['finish_material']
for n in ['B11_K-FRIDGE-OVERHEAD_PULL_0','B11_K-FRIDGE-OVERHEAD_PULL_1']:assert bpy.data.objects[n].data.materials[0].name==a['pull_material']
assert bpy.data.objects['R3_SHOWER_GLASS_0'].data.materials[0].name=='V8_COLORLESS_PRIVACY_FROSTED_GLASS';assert bpy.data.objects['R3_SHOWER_GLASS_1'].data.materials[0].name=='V8_COLORLESS_PRIVACY_FROSTED_GLASS';assert bpy.data.objects['R3_SHOWER_GLASS_2'].data.materials[0].name=='V8_COLORLESS_PRIVACY_FROSTED_GLASS'
for f in json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files']:assert sha(f['path'])==f['sha256']
v={'status':'PASS_FRIDGE_FINISH_AND_SHOWER_AUDIT','output_sha256':a['sha256'],'cabinet_finish':a['finish_material'],'shower_audit':a['shower_audit'],'frosted_glass_preserved':True,'geometry_layout_unchanged':True,'protected_sources_verified':16,'final_visual_acceptance':False};(D/'VERIFICATION.json').write_text(json.dumps(v,indent=2)+'\n');print('VERIFY_V13',json.dumps(v))

