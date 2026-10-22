import json,hashlib,re,collections
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent
m=json.loads((OUT/'LIVING_LAYOUT_MANIFEST_V2.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();errors=[];count=0

def ck(test,note):
 global count
 count+=1
 if not test:errors.append(note)
ck(sha(m['source'])==m['source_sha256'],'R4 changed')
for p,h in m['freecad_source_hashes'].items():ck(sha(p)==h,'FreeCAD changed '+p)
ck(not list(OUT.rglob('*.blend')) and not list(OUT.rglob('*.FCStd')),'unexpected model writeback')
ck(len(m['images'])==15,'image count');ck(len({r['image_id'] for r in m['images']})==15,'duplicate ids')
ck(m['winner'] is None and m['selected_DNA'] is None and m['all_candidates_unselected'],'unrequested selection')
ck({k:sum(r['layout']==k for r in m['images']) for k in ['A','B','C']}=={'A':5,'B':5,'C':5},'per scheme count')
ck({r['camera'] for r in m['images']}=={'L1','L2','L3','L4','L5'},'camera coverage')
ck(sum(r['retry_count'] for r in m['images'])==7,'bounded correction count')
for r in m['images']:
 id=r['image_id'];ck(r['retry_count'] in [0,1],id+' retry cap');ck(r['visual_review']=='COMPLETE',id+' pending visual QA')
 for key,hkey in [('output','image_sha256'),('reference','reference_sha256'),('prompt','prompt_sha256')]:
  ck(Path(r[key]).exists(),id+' missing '+key);ck(sha(r[key])==r[hkey],id+' hash mismatch '+key)
 im=Image.open(r['output']);im.load();ck(im.size==(1536,1024),id+' wrong size');im.close()
 im=Image.open(r['reference']);im.load();ck(im.size==(1536,1024),id+' wrong reference size');im.close()
 if r.get('style_anchor'):ck(Path(r['style_anchor']).exists(),id+' missing style anchor');ck(sha(r['style_anchor'])==r['style_anchor_sha256'],id+' incorrect style anchor hash')
 if r.get('raw_correction'):ck(sha(r['raw_correction'])==r['image_sha256'],id+' correction archive mismatch');ck(Path(r['initial_image']).exists(),id+' lost initial image')
 expected='living_layout'+r['layout']+'_'+r['slug']+'_'+r['camera']+'.png';ck(Path(r['output']).name==expected,id+' wrong canonical name')
 if r['camera']=='L5':ck(r['camera_pose']['pos']==[7.05,11.55,1.55] and r['camera_pose']['lens']==32,id+' L5 position/lens drift')
for k in ['A','B','C']:
 for name in ['LIVING_LAYOUT_'+k+'_CONTACT_SHEET.png','LIVING_LAYOUT_'+k+'_REFERENCE_SHEET.png']:
  p=OUT/'contact_sheet'/name;ck(p.exists(),name+' missing');im=Image.open(p);im.load();ck(im.size==(1800,970),name+' bad sheet size');im.close()
folder=OUT/'contact_sheet/LIVING_LAYOUT_ABC_COMPARISON.png';im=Image.open(folder);im.load();ck(im.size==(1800,2325),'comparison sheet size');im.close()
required=['LIVING_LAYOUT_IMAGE_INDEX_V2.md','LIVING_LAYOUT_REVIEW_V2.md','LIVING_LAYOUT_PROMPT_PACK_V2.md','LIVING_LAYOUT_MANIFEST_V2.json','reports/LAYOUT_PLAN_CAMERA_ENVELOPES.png','reports/ARCHITECTURE_LOCK.json','reports/VISUAL_QA_V2.json']
for name in required:ck((OUT/name).exists(),name+' missing')
for name in ['LIVING_LAYOUT_IMAGE_INDEX_V2.md','LIVING_LAYOUT_REVIEW_V2.md']:
 for target in re.findall(r'\]\(([^)]+)\)',(OUT/name).read_text()):
  if target.startswith('/'):ck(Path(target).exists(),name+' broken link '+target)
pack=(OUT/'LIVING_LAYOUT_PROMPT_PACK_V2.md').read_text()
for r in m['images']:ck(Path(r['prompt']).read_text().strip() in pack,r['image_id']+' effective prompt absent')
locks=m['architecture_lock'];ck(len(locks)==3 and all(l['protected_geometry_and_authored_pose']=='PASS_UNCHANGED' for l in locks),'protected original states changed')
result=dict(status='PASS' if not errors else 'FAIL',checks=count,errors=errors,formal_images=15,reference_images=15,scheme_contact_sheets=3,source_sha256=sha(m['source']),source_unchanged=True,freecad_files_unchanged=len(m['freecad_source_hashes']),no_model_writeback=True,furniture_pose_warning_images=[r['image_id'] for r in m['images'] if r['layout_execution'].startswith('WARNING')],delivery_status=m['status'],all_candidates_unselected=True)
(OUT/'reports/DELIVERY_INTEGRITY_V2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False));raise SystemExit(1 if errors else 0)
