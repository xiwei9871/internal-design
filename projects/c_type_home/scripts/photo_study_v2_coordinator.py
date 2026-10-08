"""Serial restartable room generation with a visual gate, bounded calls and no source promotion."""
import json, os, subprocess, sys, time
from pathlib import Path
from photo_study_v2 import OUT,M,SPECS,LEVELS,ROOT
PY='/Users/xiwei/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
logs=OUT/'logs';logs.mkdir(exist_ok=True);state={'status':'RUNNING','pid':os.getpid(),'started':time.time(),'expected_images':210,'visual_qa':'ROOM_HERO_GATE_REQUIRED'}
def save(): (M/'BATCH_STATE.json').write_text(json.dumps(state,indent=2))
def gallery():
    with (logs/'gallery.log').open('a') as f:subprocess.run([PY,str(ROOT/'scripts/photo_study_v2_gallery.py')],stdout=f,stderr=subprocess.STDOUT)
def run(room,phase):
    state.update({'current_room':room,'phase':phase});save()
    with (logs/(room+'_'+phase+'.log')).open('a') as log:p=subprocess.run([sys.executable,str(ROOT/'scripts/photo_study_v2.py'),'--room',room,'--phase',phase],stdout=log,stderr=subprocess.STDOUT)
    gallery();return p.returncode
def failure_present(room,views):
    for view in views:
        for level in LEVELS:
            meta=OUT/room/level/(view+'.json')
            if meta.exists():
                r=json.loads(meta.read_text())
                if r['status'].startswith('API_FAILED'):
                    state.update({'status':'API_FAILURE_REQUIRES_BOUNDED_REVIEW','failed_job':r.get('job'),'error':r.get('error'),'room':room});save();return True
    return False
save();guard=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
order=['living','dining','mother_bedroom','couple_bedroom','study','guest_bedroom','master_bath','secondary_bath','guest_bath','north_sunroom','service_balcony','reading_transition','entry','hallway']
for room in order:
    if not all((OUT/room/level/'VIEW_01.png').exists() for level in LEVELS):
        if run(room,'hero') or failure_present(room,['VIEW_01']):break
    gate=OUT/room/'HERO_QA.json'
    if gate.exists() and json.loads(gate.read_text())['status']=='PASS_FOR_PROPAGATION':
        if run(room,'followup') or failure_present(room,[f'VIEW_{i:02d}' for i in range(2,6)]):break
    else:
        state.setdefault('heroes_waiting_for_visual_review',[]).append(room);save()
    time.sleep(10)
else:state['status']='HERO_REVIEW_OR_FOLLOWUP_COMPLETE'
gallery();state['finished_this_run']=time.time();save();print('PHOTO_V2_COORDINATOR_STOP',json.dumps(state),flush=True)
