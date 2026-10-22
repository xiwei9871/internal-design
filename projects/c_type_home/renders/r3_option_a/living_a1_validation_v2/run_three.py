import subprocess,json,time,concurrent.futures,datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from PIL import Image
OUT=Path(__file__).resolve().parent;JOBS=json.loads((OUT/'A1_JOBS.json').read_text());CLI=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64';RESULTS=[]
stamp=lambda:datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
def run(j):
 started=stamp();t=time.monotonic();print('START '+j['id']+' '+started,flush=True)
 if Path(j['output']).exists():return dict(**j,status='PRESERVED_EXISTS',seconds=0)
 try:
  p=subprocess.run(['rtk','proxy',str(CLI),'edit','--image',j['input'],'--prompt-file',j['prompt_file'],'--model','gpt-image-2','--quality','high','--size','1536x1024','--n','1','--timeout','180','--max-attempts','1','--out',j['output']],capture_output=True,text=True,timeout=200)
  log=p.stdout+'\n'+p.stderr;(OUT/(j['id']+'.log')).write_text(log);status='FAILED';actual=None
  if p.returncode==0 and Path(j['output']).is_file():im=Image.open(j['output']);im.load();actual=list(im.size);status='GENERATED' if im.size==(1536,1024) else 'FAILED_OUTPUT_SIZE'
  result=dict(**j,status=status,started=started,finished=stamp(),seconds=round(time.monotonic()-t,2),actual_size=actual,error=log[-600:] if status!='GENERATED' else None)
 except subprocess.TimeoutExpired:result=dict(**j,status='FAILED_TIMEOUT',started=started,finished=stamp(),seconds=round(time.monotonic()-t,2),error='single bounded request timed out; no Blender fallback material work')
 print('DONE '+j['id']+' '+result['status']+' '+str(result['seconds'])+'s',flush=True);return result
start=time.monotonic()
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for f in concurrent.futures.as_completed([pool.submit(run,j) for j in JOBS]):
  RESULTS.append(f.result());(OUT/'A1_GENERATION_RESULTS.json').write_text(json.dumps(RESULTS,ensure_ascii=False,indent=2)+'\n');print('PROGRESS '+str(len(RESULTS))+'/3',flush=True)
summary=dict(generated=sum(r['status']=='GENERATED' for r in RESULTS),target=3,total_seconds=round(time.monotonic()-start,2),scope='ONLY_A1_STOP_AT_REVIEW',model='gpt-image-2',quality='high',concurrency=3)
(OUT/'A1_GENERATION_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
if summary['generated']!=3:
 (OUT/'LIVINGROOM_A1_FAILURE_REPORT.md').write_text('# A1图像生成失败\n\n已保存白模和完整prompt pack。没有继续做Blender高质量材质。\n\n'+json.dumps(RESULTS,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary),flush=True)
