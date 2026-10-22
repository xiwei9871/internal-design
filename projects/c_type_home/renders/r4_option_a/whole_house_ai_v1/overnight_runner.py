"""Resumable ordered whole-house generation. Per-room checkpoint before next room."""
import json,subprocess,time,concurrent.futures,datetime,hashlib,sys,threading,importlib
from pathlib import Path
from zoneinfo import ZoneInfo
from PIL import Image
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT))
from room_plan import ROOMS
from prompt_system import assemble
import prompt_system
from room_package import package
CLI=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64'
PY=Path('/Users/xiwei/interior_design/.venv/bin/python');BLENDER='/Applications/Blender.app/Contents/MacOS/Blender'
P=json.loads((OUT/'00_manifest/R4_WHOLE_HOUSE_PREFLIGHT.json').read_text());assert json.loads((OUT/'00_manifest/WHOLE_HOUSE_API_PREFLIGHT.json').read_text())['status']=='PASS'
stop=threading.Event();stamp=lambda:datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def request(j):
 if stop.is_set():return dict(**j,status='SKIPPED_GLOBAL_FATAL',retry_count=0,geometry_preservation='WARNING',design_divergence='LOW',new_ideas=[])
 if Path(j['output']).exists():
  try:Image.open(j['output']).load();return dict(**j,status='GENERATED_EXISTING_RESUME',retry_count=0,geometry_preservation='WARNING',design_divergence='LOW',new_ideas=[],review_notes='Existing output preserved; visual QA pending')
  except Exception:Path(j['output']).rename(Path(j['output']).with_suffix('.incomplete.png'))
 attempts=[];retry=0
 for attempt in range(2):
  t=time.monotonic();print('IMAGE_START '+j['image_id']+' attempt'+str(attempt+1),flush=True)
  args=['rtk','proxy',str(CLI),'edit','--image',j['reference'],'--prompt-file',j['prompt'],'--model','gpt-image-2','--quality','high','--size','1536x1024','--n','1','--timeout','180','--max-attempts','1','--out',j['output']]
  try:
   r=subprocess.run(args,capture_output=True,text=True,timeout=200);log=r.stdout+'\n'+r.stderr;code=r.returncode
  except subprocess.TimeoutExpired:log='NETWORK_TIMEOUT bounded200s';code=124
  logfile=Path(j['output']).parents[1]/'reports'/(j['image_id']+'_attempt'+str(attempt+1)+'.log');logfile.write_text(log)
  elapsed=round(time.monotonic()-t,2);attempts.append(dict(attempt=attempt+1,seconds=elapsed,log=str(logfile),exit_code=code))
  if code==0 and Path(j['output']).exists():
   im=Image.open(j['output']);im.load();print('IMAGE_DONE '+j['image_id']+' '+str(elapsed)+'s',flush=True)
   return dict(**j,status='GENERATED',retry_count=retry,geometry_preservation='WARNING',design_divergence='LOW',new_ideas=[],actual_size=list(im.size),image_sha256=sha(j['output']),completed=stamp(),attempts=attempts,review_notes='PENDING_VISUAL_GEOMETRY_AND_DIVERGENCE_QA')
  if any(x in log for x in ['HTTP 400','HTTP 401','HTTP 403','HTTP 404','HTTP 422','configuration error']):stop.set();break
  retry=1
 result=dict(**j,status='FAILED',retry_count=min(retry,1),geometry_preservation='FAIL',design_divergence='LOW',new_ideas=[],completed=stamp(),attempts=attempts,error=log[-1000:]);print('IMAGE_FAILED '+j['image_id'],flush=True);return result
def main():
 sourcehash=sha(P['source_path']);assert sourcehash==P['sha256'];started=stamp();completed=[]
 for room in ROOMS:
  D=OUT/room['folder'];done=D/'reports/ROOM_DONE.json'
  if done.exists():
   cp=json.loads(done.read_text())
   if cp['completed_images']+cp['failed_images']==cp['expected_images'] and cp.get('source_sha256',sourcehash)==sourcehash:print('ROOM_SKIP_CHECKPOINT '+room['id'],flush=True);completed.append(room['id']);continue
  if stop.is_set():break
  print('ROOM_START '+room['id']+' '+stamp(),flush=True)
  reg=D/'reports/CAMERA_REGISTER.json'
  if not reg.exists():
   proc=subprocess.run(['rtk','proxy',BLENDER,'--background','--factory-startup','--disable-autoexec','--python-exit-code','1','--python',str(OUT/'render_room.py'),'--',room['id']],capture_output=True,text=True,timeout=180)
   (OUT/'00_manifest/logs'/(room['id']+'_reference.log')).write_text(proc.stdout+'\n'+proc.stderr)
   if proc.returncode!=0:raise RuntimeError('R4_REFERENCE_FAILURE '+room['id'])
  cams=json.loads(reg.read_text());jobs=[]
  importlib.reload(prompt_system)
  for cam in cams:
   for v in ['faithful','designer','creative']:
    id=room['id']+'_'+cam['id']+'_'+v+'_v1';pf=D/'prompts'/(id+'.txt');output=D/v/(id+'.png')
    if not output.exists():pf.write_text(prompt_system.assemble(room,cam,v))
    jobs.append(dict(image_id=id,room=room['id'],camera=cam['id'],variant=v,reference=cam['reference'],prompt=str(pf),output=str(output)))
  results=[];ip=D/'reports/IMAGES.json';old=json.loads(ip.read_text()) if ip.exists() else [];oldmap={r['image_id']:r for r in old}
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   fs=[]
   for j in jobs:
    if j['image_id'] in oldmap and Path(j['output']).exists():results.append(oldmap[j['image_id']])
    else:fs.append(pool.submit(request,j))
   for f in concurrent.futures.as_completed(fs):
    results.append(f.result());ip.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print('ROOM_PROGRESS '+room['id']+' '+str(len(results))+'/'+str(len(jobs)),flush=True)
  ip.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');cs=package(room);success=sum(Path(r['output']).exists() for r in results);failed=len(jobs)-success
  checkpoint=dict(room=room['id'],expected_images=len(jobs),completed_images=success,failed_images=failed,warning_images=sum(r['geometry_preservation']=='WARNING' for r in results),contact_sheet=cs,timestamp=stamp(),source_sha256=sourcehash,visual_review='PENDING_MODEL_INSPECTION',room_generation_complete=True)
  done.write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n');completed.append(room['id']);assert sha(P['source_path'])==sourcehash
  (OUT/'00_manifest/LIVE_PROGRESS.json').write_text(json.dumps(dict(status='RUNNING' if not stop.is_set() else 'BLOCKED_EXTERNAL_SERVICE',started=started,latest_checkpoint=room['id'],completed_rooms=completed,generated_images=sum(json.loads((OUT/r['folder']/'reports/ROOM_DONE.json').read_text())['completed_images'] for r in ROOMS if (OUT/r['folder']/'reports/ROOM_DONE.json').exists()),target_images=144,source_sha256=sourcehash),ensure_ascii=False,indent=2)+'\n')
  print('ROOM_DONE '+room['id']+' '+str(success)+'/'+str(len(jobs)),flush=True)
 if stop.is_set():status='BLOCKED_EXTERNAL_SERVICE'
 else:status='GENERATION_COMPLETE_PENDING_VISUAL_QA'
 (OUT/'00_manifest/GENERATION_RUN_DONE.json').write_text(json.dumps(dict(status=status,completed_rooms=completed,source_sha256=sourcehash,finished=stamp(),global_fatal=stop.is_set()),ensure_ascii=False,indent=2)+'\n');print('OVERNIGHT_RUN '+status,flush=True)
if __name__=='__main__':main()
