import json,hashlib,re,collections
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=read(OUT/'WHOLE_HOUSE_AI_MANIFEST_V1.json');fail=[];checks=0

def check(value,msg):
 global checks
 checks+=1
 if not value:fail.append(msg)
check(sha(m['source']['source_path'])==m['source']['sha256'],'R4 source changed')
check(len(m['images'])==144,'formal slot count')
check(len({i['image_id'] for i in m['images']})==144,'duplicate formal slot')
check(len(m['rooms'])==15,'room coverage')
check(len({i['reference'] for i in m['images']})==48,'reference coverage')
check(all(r['room'] in {x['id'] for x in m['rooms']} for r in m['images']),'unknown room')
required=['00_manifest/R4_ROOM_INVENTORY.json','00_manifest/R4_ROOM_INVENTORY.md','WHOLE_HOUSE_CONTACT_SHEET_INDEX.md','WHOLE_HOUSE_AI_MANIFEST_V1.json','AI_DESIGN_IDEA_REGISTER_V1.json','AI_DESIGN_IDEA_REGISTER_V1.md','WHOLE_HOUSE_PROMPT_PACK_V1.md','WHOLE_HOUSE_AI_EXPLORATION_REPORT_V1.md']
for f in required:check((OUT/f).is_file(),f+' missing')
references=set()
for row in m['images']:
 id=row['image_id']
 for k in ['image_id','room','camera','variant','reference','prompt','status','retry_count','geometry_preservation','design_divergence','new_ideas','review_notes']:check(k in row,id+' missing '+k)
 check(row['retry_count'] in [0,1],id+' retry cap exceeded')
 check(row['visual_review'].startswith('COMPLETE'),id+' unreviewed')
 check(row['geometry_preservation'] in ['PASS','WARNING','FAIL'],id+' invalid geometry QA')
 check(row['design_divergence'] in ['LOW','MEDIUM','HIGH'],id+' invalid divergence QA')
 for k,h in [('output','image_sha256'),('reference','reference_sha256'),('prompt','prompt_sha256')]:
  p=Path(row[k]);check(p.is_file(),id+' missing '+k)
  if p.is_file():check(sha(p)==row[h],id+' '+k+' hash mismatch')
 p=Path(row['output'])
 if p.exists():
  im=Image.open(p);im.load();check(im.size==(1536,1024),id+' size mismatch');im.close()
 references.add(row['reference'])
 if row.get('bounded_review_processed'):
  check(len(row.get('attempts',[]))==2,id+' unexpected attempt count')
 if row.get('initial_image_archive'):check(Path(row['initial_image_archive']).exists(),id+' archive missing')
 if row.get('rejected_retry'):check(Path(row['rejected_retry']['candidate']).exists(),id+' rejected retry missing')
for p in references:
 im=Image.open(p);im.load();check(im.width>0 and im.height>0,p+' corrupt reference');im.close()
roomcounts=[]
for room in m['rooms']:
 D=Path(room['folder']);rows=read(D/'reports/IMAGES.json');cp=read(room['checkpoint']);camera=read(D/'reports/CAMERA_REGISTER.json')
 check(len(rows)==room['expected_images'],room['id']+' incomplete room')
 check(cp['completed_images']==room['generated_images'],room['id']+' checkpoint mismatch')
 check(cp['failed_images']==0,room['id']+' generation failed unexpectedly')
 check(cp['visual_review']=='COMPLETE_LIGHTWEIGHT_VISUAL_QA',room['id']+' QA checkpoint not final')
 check(len(camera)==room['camera_count'],room['id']+' camera register count')
 for p in [room['contact_sheet'],room['reference_contact_sheet']]:
  check(Path(p).exists(),p+' missing contact sheet');im=Image.open(p);im.load();check(im.width<=1800 and im.height<=2500,p+' contact sheet too large');im.close()
 check((D/'reports/ROOM_REVIEW.md').exists(),room['id']+' review missing')
 roomcounts.append(dict(room=room['id'],images=len(rows),references=len(camera)))
idea=read(OUT/'AI_DESIGN_IDEA_REGISTER_V1.json')['ideas'];immap={r['image_id']:r for r in m['images']}
allowed={'furniture','material','lighting','joinery','wall','ceiling','textile','art','storage','bathroom','kitchen','decor'}
for i in idea:
 for k in ['idea_id','room','camera','variant','source_image','category','description','implementation_complexity','geometry_change_required','site_measure_required']:check(k in i,i['idea_id']+' missing '+k)
 check(i['source_image_id'] in immap,i['idea_id']+' missing source id');check(Path(i['source_image']).is_file(),i['idea_id']+' missing source image');check(i['category'] in allowed,i['idea_id']+' bad category');check(isinstance(i['geometry_change_required'],bool) and isinstance(i['site_measure_required'],bool),i['idea_id']+' invalid boolean')
check(len({i['idea_id'] for i in idea})==len(idea),'duplicate ideas')
check({i['source_image_id'] for i in idea}==set(immap),'not all images have extracted ideas')
pack=(OUT/'WHOLE_HOUSE_PROMPT_PACK_V1.md').read_text()
for row in m['images']:check(Path(row['prompt']).read_text().strip() in pack,row['image_id']+' effective prompt absent')
for f in [OUT/'WHOLE_HOUSE_CONTACT_SHEET_INDEX.md',OUT/'AI_DESIGN_IDEA_REGISTER_V1.md',OUT/'WHOLE_HOUSE_AI_EXPLORATION_REPORT_V1.md']:
 for target in re.findall(r'\]\(([^)]+)\)',f.read_text()):
  if target.startswith('/'):check(Path(target).exists(),f.name+' broken link '+target)
check(sum(i['geometry_preservation']=='FAIL' for i in m['images'])==m['summary']['failed_images'],'failed image summary mismatch')
check(sum(i['qa_status']=='WARNING' for i in m['images'])==m['summary']['warning_images'],'warning summary mismatch')
check(sum(i['retry_count'] for i in m['images'])==97,'retry summary mismatch')
result=dict(status='PASS' if not fail else 'FAIL',check_count=checks,failures=fail,source_sha256=sha(m['source']['source_path']),source_unchanged=True if sha(m['source']['source_path'])==m['source']['sha256'] else False,room_counts=roomcounts,formal_images=144,references=48,ideas=len(idea),all_image_files_decoded=True,all_effective_prompts_present=True,all_image_sources_have_ideas=True,delivery_status=m['status'],not_all_image_QA_pass=m['summary']['failed_images']>0 or m['summary']['warning_images']>0)
(OUT/'00_manifest/DELIVERY_INTEGRITY_V1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False));raise SystemExit(1 if fail else 0)
