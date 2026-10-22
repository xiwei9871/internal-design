import json,sys,subprocess,time,concurrent.futures,hashlib,shutil
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT));from room_plan import ROOMS;from prompt_system import assemble;from room_package import package
REQ=OUT/(sys.argv[1] if len(sys.argv)>1 else '00_manifest/REVIEW_RETRY_QUEUE.json');RESULT=OUT/(sys.argv[2] if len(sys.argv)>2 else '00_manifest/REVIEW_RETRY_RESULTS.json')
CLI=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(req):
 room=next(r for r in ROOMS if r['id']==req['room']);D=OUT/room['folder'];images=json.loads((D/'reports/IMAGES.json').read_text());row=next(i for i in images if i['image_id']==req['image_id']);cams=json.loads((D/'reports/CAMERA_REGISTER.json').read_text());cam=next(c for c in cams if c['id']==row['camera'])
 if row['retry_count']>=1:return dict(**req,status='SKIP_RETRY_ALREADY_USED')
 pf=D/'prompts'/(req['image_id']+'_review_retry.txt');pf.write_text(assemble(room,cam,row['variant'],req['correction']));out=Path(row['output']).with_name(Path(row['output']).stem+'_review_retry.png')
 if out.exists():return dict(**req,status='RETRY_EXISTING',candidate=str(out),prompt=str(pf))
 t=time.monotonic();print('REVIEW_RETRY_START '+req['image_id'],flush=True)
 try:
  p=subprocess.run(['rtk','proxy',str(CLI),'edit','--image',cam['reference'],'--prompt-file',str(pf),'--model','gpt-image-2','--quality','high','--size','1536x1024','--n','1','--timeout','180','--max-attempts','1','--out',str(out)],capture_output=True,text=True,timeout=200);(D/'reports'/(req['image_id']+'_review_retry.log')).write_text(p.stdout+'\n'+p.stderr);status='RETRY_FAILED'
  if p.returncode==0 and out.exists():im=Image.open(out);im.load();status='RETRY_GENERATED' if im.size==(1536,1024) else 'RETRY_SIZE_WARNING'
 except subprocess.TimeoutExpired:status='RETRY_TIMEOUT'
 res=dict(**req,status=status,candidate=str(out),prompt=str(pf),reference=cam['reference'],seconds=round(time.monotonic()-t,2));print('REVIEW_RETRY_DONE '+req['image_id']+' '+status,flush=True);return res
requests=json.loads(REQ.read_text());previous=json.loads(RESULT.read_text()) if RESULT.exists() else [];done={r['image_id'] for r in previous};pending=[r for r in requests if r['image_id'] not in done]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for f in concurrent.futures.as_completed([pool.submit(run,r) for r in pending]):previous.append(f.result());RESULT.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(attempted=len(previous),bounded_once=True)))
