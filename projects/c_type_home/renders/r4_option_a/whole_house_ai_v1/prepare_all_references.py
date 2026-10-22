import subprocess,json,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT));from room_plan import ROOMS;from room_package import package
records=[]
for room in ROOMS[2:]:
 D=OUT/room['folder'];reg=D/'reports/CAMERA_REGISTER.json'
 if not reg.exists():
  print('REFERENCE_START '+room['id'],flush=True)
  r=subprocess.run(['rtk','proxy','/Applications/Blender.app/Contents/MacOS/Blender','--background','--factory-startup','--disable-autoexec','--python-exit-code','1','--python',str(OUT/'render_room.py'),'--',room['id']],capture_output=True,text=True,timeout=180)
  (OUT/'00_manifest/logs'/(room['id']+'_reference.log')).write_text(r.stdout+'\n'+r.stderr)
  if r.returncode!=0:records.append(dict(room=room['id'],status='FAILED',error=r.stderr[-900:]));print('REFERENCE_FAILED '+room['id'],flush=True);continue
 cams=json.loads(reg.read_text());package(room);records.append(dict(room=room['id'],status='REFERENCES_READY',views=len(cams),warnings=[c['id'] for c in cams if c.get('reference_camera_QA','').startswith('WARNING')]));print('REFERENCE_DONE '+room['id']+' '+str(len(cams)),flush=True)
 (OUT/'00_manifest/REFERENCE_PREPARATION_PROGRESS.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print('ALL_REMAINING_REFERENCE_EXPORTS_FINISHED',flush=True)
