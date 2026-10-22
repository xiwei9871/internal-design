import json,time,subprocess,threading,concurrent.futures,datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from PIL import Image
OUT=Path(__file__).resolve().parent
CLI=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64'
JOBS=json.loads((OUT/'working/prompts/jobs.json').read_text());RESULTS=[];LOCK=threading.Lock();STOP=threading.Event()
def stamp():return datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
def save():
 (OUT/'logs/GENERATION_RESULTS.json').write_text(json.dumps(RESULTS,ensure_ascii=False,indent=2)+'\n')
def run(j):
 if STOP.is_set():return dict(**j,status='SKIPPED_INTERFACE_FALLBACK',start_time=stamp(),duration_seconds=0)
 start=stamp();t=time.monotonic();print('START '+j['id']+' '+start,flush=True)
 out=Path(j['output'])
 if out.exists():return dict(**j,status='EXISTS_PRESERVED',start_time=start,duration_seconds=0)
 args=['rtk','proxy',str(CLI),'edit','--image',j['input'],'--prompt-file',j['prompt_file'],'--model',j['model'],'--size',j['size'],'--quality',j['quality'],'--n','1','--timeout','180','--max-attempts','2','--out',j['output']]
 try:
  p=subprocess.run(args,capture_output=True,text=True,timeout=390)
  log=(p.stdout+'\n'+p.stderr).strip();(OUT/'logs'/(j['id']+'.log')).write_text(log+'\n')
  status='FAILED';size=None
  if p.returncode==0 and out.is_file():
   im=Image.open(out);im.load();size=list(im.size);status='GENERATED' if im.size==(1536,1024) else 'GENERATED_SIZE_VARIATION'
  elif any(x in log for x in ['HTTP 400','HTTP 401','HTTP 403','HTTP 404','HTTP 422','configuration error']):STOP.set()
  result=dict(**j,status=status,start_time=start,completion_time=stamp(),duration_seconds=round(time.monotonic()-t,2),actual_size=size,exit_code=p.returncode,error=log[-800:] if status=='FAILED' else None)
 except subprocess.TimeoutExpired:
  STOP.set();result=dict(**j,status='FAILED_TIMEOUT_FALLBACK',start_time=start,completion_time=stamp(),duration_seconds=round(time.monotonic()-t,2),error='bounded timeout; fallback assets already prepared')
 print('DONE '+j['id']+' '+result['status']+' '+str(result['duration_seconds'])+'s',flush=True);return result
started=stamp();begin=time.monotonic()
for mode in ['strict','design','explore']:
 if STOP.is_set():
  RESULTS.extend(dict(**j,status='SKIPPED_INTERFACE_FALLBACK',start_time=stamp(),duration_seconds=0) for j in JOBS if j['version']==mode);save();continue
 print('STAGE '+mode+' concurrency=3',flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(run,j) for j in JOBS if j['version']==mode]
  for f in concurrent.futures.as_completed(futures):
   RESULTS.append(f.result());save();done=sum(r['status'].startswith('GENERATED') or r['status']=='EXISTS_PRESERVED' for r in RESULTS);print('PROGRESS '+str(done)+'/15',flush=True)
summary=dict(start_time=started,end_time=stamp(),duration_seconds=round(time.monotonic()-begin,2),concurrency=3,generated=sum(r['status'].startswith('GENERATED') or r['status']=='EXISTS_PRESERVED' for r in RESULTS),target=15,interface_fallback=STOP.is_set())
(OUT/'logs/BATCH_GENERATION_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False),flush=True)
