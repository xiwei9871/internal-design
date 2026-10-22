"""Schedules the existing Image2 edit CLI. No custom provider or HTTP integration."""
import json,time,os,subprocess,hashlib,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/whole_house_final_study_v1';M=OUT/'00_MANIFEST'
CLI='/Users/xiwei/.codex/skills/codex-image2/scripts/image2.py'
manifest=json.loads((M/'WHOLE_HOUSE_ROOM_MANIFEST_V1.json').read_text());cams=json.loads((M/'CAMERA_REGISTER_V1.json').read_text())['cameras']
jobs=[]
for room in manifest['rooms']:
 for c in [c for c in cams if c['room_id']==room['room_id']]:
  for level in ['02_designer','03_creative']:
   dir=OUT/room['room_id']/level;dir.mkdir(parents=True,exist_ok=True);v=c['view_id'];base=OUT/room['room_id']/'01_faithful'/(v+'.png');geo=OUT/room['room_id']/'00_camera_gate'/(v+'_preview.png')
   notes=' '.join(room['key_furniture'])
   style=('Professionaldesigner refinement: retainmajorfurniture topology/number andplacements,refinewhite-ashjoinery,softedges,quietlinen,subtlelightingfixtures,restrainedceramics/softtextiles.Sparsecomposition.' if level=='02_designer' else
    'Distinctivesculptural residential refinement: bolderbutplausiblewhite-ashformlanguage,subtlecurvededge detailing,selectivecreamlimestone accents,sculpturallighting andcarefullycuratedart.Texturalandeditorial,butquietandlivable—neverhotel,allstone,wabisabithemepark orfuturistic.')
   prompt=f'''Create a photorealistic interior design comparison image, {level}, room {room['display_name']} ({room['room_id']}), camera {v}. Image1 is the exact-camera Blender geometry/base render, primary authority. Image2 is same-camera clay geometry evidence. Do not reconstruct a new room from text. Keep exact viewpoint, framing, perspective, vertical lines and crop. Do not zoom, turn, widen, or change lens.\nARCHITECTURE LOCK: same walls, columns, ceiling height, openings, glass partition positions, doors, windows, mullions, floor levels and split-level steps. Never add/remove/relocate a window or door, skylight, wall or ceiling opening. Objects behindcamera muststaybehindcamera. Do not remove critical built-ins. Preserve current major furniture locations/counts and room functions: {notes}. All visible elements must correspond to the source images. Hidden elements must not appear merely because mentioned.\nSTYLE: {style}\nONE-HOME LANGUAGE: warm minimal naturalwood, Asian/Japandi residential references; pale solid white ash, restrained visible grain, mattefinish, simplejoinery andlightvisualmass. Warmoffwhitewalls;ivory/flax/taupe textiles withsparsesage;quietcreamstone;nickel/warmneutralmetal accents. Dryroom floors are light matte wood; kitchen/bath/service wetzones warmgreige tile. Northsunroom is alreadyenclosed in thislatestsource; retainexistingglazing. Softneutraldaylight,2700–3000K practicallights, notorange/yellowcast. BasedonMuJiaMuYi ashfurniturecatalog: lightwoodframes,2016/2030lowbed character,5015open/closedjoinery,naturaledge1310console,restrained3125woodchairs. These are form/materialanalogues only,never add catalog furniture absent in source.\nNopeople,nolettering,no watermark,no clutter,no randomextra chair/sofa/bed/cabinet,no heavyblackmetal,no dominantdarkwalnut/orangeoak ordramaticmarble. Maintain all circulation gaps. Keep major furniture dimensions plausible within same envelopes. Real fabricsoftness,woodgrain,ceramic,glass andreflections; do not hide bad geometry with blur orlighting. Do not turn any opaque wardrobecabinet into glass. Keep existingmirror shape (round insecondarybath). Same gentle daylightfamily as image1. Output onlythefinished roomphoto.\n'''
   pp=dir/(v+'.prompt.txt');pp.write_text(prompt)
   jobs.append({'room_id':room['room_id'],'view_id':v,'level':level,'base':str(base),'geometry':str(geo),'prompt_file':str(pp),'out':str(dir/(v+'.png'))})
(M/'IMAGE2_JOBS.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2))
if '--prepare-only' in sys.argv:print('IMAGE2_JOBS_PREPARED',len(jobs));raise SystemExit(0)
def run(j):
 if Path(j['out']).exists():return {'job':j,'status':'CACHE_UNREVIEWED'}
 cmd=[sys.executable,CLI,'edit','--image',j['base'],'--image',j['geometry'],'--prompt-file',j['prompt_file'],'--size','1920x1080','--quality','medium','--max-attempts','2','--timeout','180','--out',j['out']]
 t=time.time();p=subprocess.run(cmd,capture_output=True,text=True);key=os.environ.get('CODEX_API_KEY','');log=p.stdout+'\n'+p.stderr
 if key:log=log.replace(key,'[redacted]')
 Path(j['out']).with_suffix('.cli.log').write_text(log)
 r={'job':j,'status':'GENERATED_UNREVIEWED' if p.returncode==0 and Path(j['out']).exists() else 'API_FAILED','returncode':p.returncode,'seconds':time.time()-t,
 'base_sha256':hashlib.sha256(Path(j['base']).read_bytes()).hexdigest(),'model':'gpt-image-2','quality':'medium','requested_size':'1920x1080','logical_retry_count':0}
 with (M/'IMAGE2_EVENTS.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
 print('IMAGE2_DONE',j['room_id'],j['view_id'],j['level'],r['status'],round(r['seconds'],1),flush=True);return r
pending=list(jobs);active={};done=[];start=time.time();circuit_open=False
with ThreadPoolExecutor(max_workers=2) as pool:
 while pending or active:
  for future in list(active):
   if future.done():done.append(future.result());del active[future]
  if len(done)>=3 and all(r['status']=='API_FAILED' for r in done[-3:]):
   circuit_open=True
   print('PROVIDER_CIRCUIT_OPEN_3_FAILURES',len(pending),flush=True)
  if circuit_open and not active:break
  while len(active)<2 and not circuit_open:
   ready=next((j for j in pending if Path(j['base']).exists() and Path(j['geometry']).exists()),None)
   if ready is None:break
   pending.remove(ready);active[pool.submit(run,ready)]=ready
  (M/'IMAGE2_PROGRESS.json').write_text(json.dumps({'completed':len(done),'active':len(active),'waiting_for_base':len(pending),'provider_circuit_open':circuit_open,'elapsed_seconds':time.time()-start,'statuses':{x:sum(r['status']==x for r in done) for x in ['GENERATED_UNREVIEWED','API_FAILED','CACHE_UNREVIEWED']}}))
  if time.time()-start>18000:print('TIME_BOUND_REACHED',len(pending),flush=True);break
  time.sleep(2)
(M/'IMAGE2_RUN_SUMMARY.json').write_text(json.dumps(done,ensure_ascii=False,indent=2));print('IMAGE2_QUEUE_COMPLETE',len(done),flush=True)
