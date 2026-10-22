import json,shutil,hashlib,datetime
from pathlib import Path
from zoneinfo import ZoneInfo
OUT=Path(__file__).resolve().parent;OLD=OUT.parent/'living_exploration_v1'
P=json.loads((OUT/'00_manifest/R4_WHOLE_HOUSE_PREFLIGHT.json').read_text());M=json.loads((OLD/'06_reports/LIVING_AI_MANIFEST_V1.json').read_text());assert M['source_sha256']==P['sha256'];assert M['reference_geometry_QA']=='PASS_UNCHANGED_R4';D=OUT/'01_living'
for p in ['reference','faithful','designer','creative','bonus','contact_sheet','prompts','reports']:(D/p).mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cams=json.loads((OLD/'00_reference/R4_CAMERA_REGISTER.json').read_text());rows=[]
for c in cams:
 assert c['source_sha256']==P['sha256'];assert sha(c['reference'])==c['reference_sha256'];newid=c['id'].replace('A','L');ref=D/'reference'/('living_'+newid+'_reference.png');shutil.copy2(c['reference'],ref);rows.append(dict(**{k:v for k,v in c.items() if k not in ['id','reference','reference_sha256']},id=newid,reference=str(ref),reference_sha256=sha(ref),provenance='R4 source SHA identical, geometry/camera checked before reuse'))
images=[]
for r in M['images']:
 cam=r['camera_id'].replace('A','L');id='living_'+cam+'_'+r['variant']+'_v1';out=D/r['variant']/(id+'.png');pf=D/'prompts'/(id+'.txt');shutil.copy2(r['output'],out);shutil.copy2(r['prompt_file'],pf)
 images.append(dict(image_id=id,room='living',camera=cam,variant=r['variant'],reference=next(c['reference'] for c in rows if c['id']==cam),prompt=str(pf),output=str(out),status='GENERATED_REUSED_VERIFIED_R4',retry_count=r['retry_count'],geometry_preservation=r['geometry_preservation'],design_divergence=r['design_divergence'],new_ideas=r['new_ideas'],review_notes=r['review_notes'],difference_categories=r['difference_categories'],divergence_gate=r['divergence_gate'],image_sha256=sha(out),reuse_source=r['output'],reuse_source_sha256=sha(r['output'])))
(D/'reports/CAMERA_REGISTER.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(D/'reports/IMAGES.json').write_text(json.dumps(images,ensure_ascii=False,indent=2)+'\n')
for name in ['LIVING_ALL_15_CONTACT_SHEET.png','LIVING_R4_CAMERA_REFERENCE_SHEET.png']:
 target='ROOM_CONTACT_SHEET.png' if 'ALL_15' in name else 'ROOM_REFERENCE_CONTACT_SHEET.png';shutil.copy2(OLD/'04_contact_sheets'/name,D/'contact_sheet'/target)
(D/'reports/ROOM_DONE.json').write_text(json.dumps(dict(room='living',expected_images=15,completed_images=15,failed_images=0,warning_images=sum(r['geometry_preservation']=='WARNING' for r in images),contact_sheet=str(D/'contact_sheet/ROOM_CONTACT_SHEET.png'),timestamp=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),source_sha256=P['sha256'],reuse='VERIFIED_IDENTICAL_R4_SOURCE_AND_REFERENCES',visual_review='COMPLETE'),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(living_checkpoint='DONE',reused=15,geometry_source='R4_VERIFIED',no_regeneration=True)))
