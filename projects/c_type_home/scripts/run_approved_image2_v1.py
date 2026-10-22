"""Persistent bounded Image2 queue through the user-installed CLI only."""
import json,time,os,subprocess,sys,hashlib,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/whole_house_final_study_v1/production_batch_v1';M=OUT/'00_MANIFEST';CLI=Path.home()/'.codex/skills/codex-image2/scripts/image2.py';jobs=json.loads((M/'IMAGE2_JOBS.json').read_text());probe='--probe' in sys.argv
if probe:jobs=jobs[:1]
if '--resume-unattempted' in sys.argv:jobs=[j for j in jobs if not Path(j['out']).exists() and not Path(j['out']).with_suffix('.image2.json').exists()]
events=M/'IMAGE2_EVENTS.jsonl';results=[];consecutive=0;start=time.time();pending=list(jobs);active={};limit=28800
# Native CLI suppresses provider bodies/headers; capture only sanitized output.
def run(j):
 out=Path(j['out']);meta=out.with_suffix('.image2.json')
 if not out.exists() and meta.exists():return {**json.loads(meta.read_text()),'status':'SKIPPED_PREVIOUS_FAILURE_REQUIRES_REVIEW'}
 if out.exists() and meta.exists():return {**json.loads(meta.read_text()),'status':'CACHE_GENERATED_UNREVIEWED'}
 t=time.time();cmd=[sys.executable,str(CLI),'edit','--image',j['base'],'--image',j['geometry'],'--prompt-file',j['prompt_file'],'--size','1920x1080','--quality','medium','--max-attempts','2','--timeout','240','--out',str(out)]
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=540);log=p.stdout+'\n'+p.stderr
 # No key is passed to CLI argv or kept in project state.
 key=os.environ.get('CODEX_API_KEY','')
 if key:log=log.replace(key,'[redacted]')
 out.with_suffix('.cli.log').write_text(log)
 record={'job':j,'status':'GENERATED_UNREVIEWED' if p.returncode==0 and out.exists() else 'API_FAILED','returncode':p.returncode,'seconds':time.time()-t,'base_sha256':hashlib.sha256(Path(j['base']).read_bytes()).hexdigest(),'requested_size':'1920x1080','quality':'medium','model':'gpt-image-2','logical_retry_count':0,'human_visual_qc':'PENDING'}
 meta.write_text(json.dumps(record,ensure_ascii=False,indent=2));return record
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 while pending or active:
  for f in list(active):
   if not f.done():continue
   j=active.pop(f)
   try:r=f.result()
   except Exception as exc:r={'job':j,'status':'API_FAILED','error_type':type(exc).__name__,'human_visual_qc':'PENDING'}
   results.append(r)
   with events.open('a') as h:h.write(json.dumps(r,ensure_ascii=False)+'\n')
   print('IMAGE2_DONE',j['room_id'],j['view_id'],j['level'],r['status'],round(r.get('seconds',0),1),flush=True)
   consecutive=consecutive+1 if r['status']=='API_FAILED' else 0
  circuit=consecutive>=3
  if circuit and not active:print('CIRCUIT_OPEN_3_FAILURES',len(pending),flush=True);break
  while len(active)<2 and pending and not circuit:
   j=next((j for j in pending if Path(j['base']).exists() and Path(j['base']).with_suffix('.render.json').exists()),None)
   if j is None:break
   pending.remove(j);active[pool.submit(run,j)]=j
  progress={'elapsed_seconds':time.time()-start,'expected_jobs':len(jobs),'completed':len(results),'active':len(active),'pending':len(pending),'circuit_open':circuit,'generated':sum(r['status'] in ['GENERATED_UNREVIEWED','CACHE_GENERATED_UNREVIEWED'] for r in results),'failed':sum(r['status']=='API_FAILED' for r in results),'qa':'Visual review pending'}
  (M/'IMAGE2_PROGRESS.json').write_text(json.dumps(progress,indent=2))
  if time.time()-start>limit:print('TIME_LIMIT_STOP',len(pending),flush=True);break
  if pending and not active and (M/'BLENDER_QUEUE_COMPLETE.json').exists() and not any(Path(j['base']).exists() for j in pending):print('MISSING_BASES_STOP',len(pending),flush=True);break
  time.sleep(2)
(M/('IMAGE2_PROBE_RESULTS.json' if probe else 'IMAGE2_RUN_RESULTS.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2));print('IMAGE2_QUEUE_FINISHED',len(results),'of',len(jobs),flush=True)

if not probe:(M/'IMAGE2_QUEUE_COMPLETE.json').write_text(json.dumps({'completed':len(results),'expected':len(jobs),'timestamp':time.time(),'status':'GENERATED_PENDING_VISUAL_QA' if len(results)==len(jobs) else 'PARTIAL'}))

if not probe:
 final=json.loads((M/'IMAGE2_PROGRESS.json').read_text());final.update({'completed':len(results),'active':0,'pending':len(pending),'generated':sum(Path(j['out']).exists() for j in jobs),'failed':sum(r['status'] in ['API_FAILED','SKIPPED_PREVIOUS_FAILURE_REQUIRES_REVIEW'] for r in results)});(M/'IMAGE2_PROGRESS.json').write_text(json.dumps(final,indent=2))
