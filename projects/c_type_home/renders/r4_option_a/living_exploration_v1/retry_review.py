"""Exactly one targeted generation per image selected by documented review."""
import json,subprocess,time,concurrent.futures,shutil
from pathlib import Path
from PIL import Image
from prompt_rules import assemble
OUT=Path(__file__).resolve().parent;J=json.loads((OUT/'05_prompts/LIVING_JOBS.json').read_text());R=json.loads((OUT/'06_reports/REVIEW_RETRY_REQUESTS.json').read_text())
CLI=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64';rejected=OUT/'06_reports/rejected_initials';rejected.mkdir(exist_ok=True)
def run(req):
 j=next(j for j in J if j['image_id']==req['image_id']);pf=OUT/'05_prompts'/(j['image_id']+'_review_retry.txt');pf.write_text(assemble(j['camera_id'],j['variant'],req['correction']))
 candidate=Path(j['output']).with_name(Path(j['output']).stem+'_review_retry.png');logpath=OUT/'06_reports/logs'/(j['image_id']+'_review_retry.log')
 if candidate.exists():return dict(**req,status='EXISTING_RETRY',candidate=str(candidate),prompt_file=str(pf))
 t=time.monotonic();print('RETRY_START '+j['image_id']+' '+req['reason'],flush=True)
 try:
  p=subprocess.run(['rtk','proxy',str(CLI),'edit','--image',j['source_reference'],'--prompt-file',str(pf),'--model','gpt-image-2','--quality','high','--size','1536x1024','--n','1','--timeout','180','--max-attempts','1','--out',str(candidate)],capture_output=True,text=True,timeout=200);logpath.write_text(p.stdout+'\n'+p.stderr);status='RETRY_FAILED'
  if p.returncode==0 and candidate.exists():im=Image.open(candidate);im.load();status='RETRY_GENERATED' if im.size==(1536,1024) else 'RETRY_SIZE_WARNING'
 except subprocess.TimeoutExpired:status='RETRY_TIMEOUT'
 result=dict(**req,status=status,candidate=str(candidate),prompt_file=str(pf),seconds=round(time.monotonic()-t,2));print('RETRY_DONE '+j['image_id']+' '+status,flush=True);return result
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for f in concurrent.futures.as_completed([pool.submit(run,r) for r in R]):results.append(f.result());(OUT/'06_reports/REVIEW_RETRY_RESULTS.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(retries=len(results),generated=sum(r['status']=='RETRY_GENERATED' for r in results),no_further_retries=True)))
