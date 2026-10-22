import json,subprocess,time,concurrent.futures,datetime,threading
from pathlib import Path
from PIL import Image
from zoneinfo import ZoneInfo
OUT=Path(__file__).resolve().parent;J=json.loads((OUT/'05_prompts/LIVING_JOBS.json').read_text());TEST=json.loads((OUT/'06_reports/A1_API_TEST.json').read_text());assert TEST['status']=='GENERATED'
CLI=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64';stop=threading.Event();results=[]
stamp=lambda:datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
def run(j):
 if j['image_id']==TEST['image_id']:return dict(**j,status='GENERATED_PREFLIGHT_REUSED',seconds=TEST['seconds'],started=TEST['started'],actual_size=TEST['actual_size'])
 if stop.is_set():return dict(**j,status='SKIPPED_INTERFACE_ERROR',seconds=0)
 if Path(j['output']).exists():return dict(**j,status='EXISTS_PRESERVED',seconds=0)
 print('START '+j['image_id'],flush=True);t=time.monotonic();started=stamp()
 try:
  p=subprocess.run(['rtk','proxy',str(CLI),'edit','--image',j['source_reference'],'--prompt-file',j['prompt_file'],'--model','gpt-image-2','--quality','high','--size','1536x1024','--n','1','--timeout','180','--max-attempts','1','--out',j['output']],capture_output=True,text=True,timeout=200)
  log=p.stdout+'\n'+p.stderr;(OUT/'06_reports/logs'/(j['image_id']+'.log')).write_text(log);status='FAILED';size=None
  if p.returncode==0 and Path(j['output']).exists():im=Image.open(j['output']);im.load();size=list(im.size);status='GENERATED' if im.size==(1536,1024) else 'GENERATED_SIZE_VARIATION'
  else:stop.set()
  r=dict(**j,status=status,started=started,completed=stamp(),seconds=round(time.monotonic()-t,2),actual_size=size,error=log[-800:] if status=='FAILED' else None)
 except subprocess.TimeoutExpired:stop.set();r=dict(**j,status='FAILED_TIMEOUT',started=started,completed=stamp(),seconds=round(time.monotonic()-t,2),error='bounded API request timed out')
 print('DONE '+j['image_id']+' '+r['status']+' '+str(r['seconds'])+'s',flush=True);return r
start=time.monotonic()
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for f in concurrent.futures.as_completed([pool.submit(run,j) for j in J]):
  results.append(f.result());(OUT/'06_reports/GENERATION_RESULTS.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');done=sum(r['status'].startswith('GENERATED') or r['status']=='EXISTS_PRESERVED' for r in results);print('PROGRESS '+str(done)+'/15',flush=True)
summary=dict(generated=sum(r['status'].startswith('GENERATED') or r['status']=='EXISTS_PRESERVED' for r in results),target=15,batch_seconds=round(time.monotonic()-start,2),minimal_test_seconds=TEST['seconds'],model='gpt-image-2',concurrency=3,interface_error=stop.is_set())
(OUT/'06_reports/GENERATION_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary),flush=True)
if stop.is_set():(OUT/'06_reports/LIVING_GENERATION_FAILURE_REPORT.md').write_text('# 图像接口失败\n\n已停止未启动的请求，保留完成图、全部白模和prompt。不转向Blender高精材质。\n\n'+json.dumps(results,ensure_ascii=False,indent=2)+'\n')
