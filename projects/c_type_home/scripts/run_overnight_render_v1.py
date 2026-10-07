"""Durable local batch process: Blender, Image2 CLI, progress gallery; no AI authority promotion."""
import json,os,time,subprocess,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];S=ROOT/'scripts';OUT=ROOT/'renders/whole_house_final_study_v1/production_batch_v1';M=OUT/'00_MANIFEST';PYTHON='/Users/xiwei/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';logs=OUT/'logs';logs.mkdir(exist_ok=True)
state={'pid':os.getpid(),'started':time.time(),'status':'RUNNING','expected_faithful':75,'expected_image2':150,'expected_total':225,'visual_qa':'PENDING'}
def save(): (M/'BATCH_STATE.json').write_text(json.dumps(state,indent=2))
def spawn(name,cmd):
 f=(logs/(name+'.log')).open('a');p=subprocess.Popen(cmd,cwd=ROOT.parents[1],stdout=f,stderr=subprocess.STDOUT,start_new_session=True);f.close();state[name+'_pid']=p.pid;save();return p
save();guard=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
gallery=spawn('gallery',[PYTHON,str(S/'update_render_review_gallery_v1.py'),'--watch'])
image2=spawn('image2',[sys.executable,str(S/'run_approved_image2_v1.py')])
# Do not duplicate the initial five-view live Blender process.
initial_wait_start=time.time()
while not (OUT/'living/01_faithful/VIEW_05.render.json').exists() and time.time()-initial_wait_start<1800:
 state['blender_phase']='waiting_for_initial_living_process';save();time.sleep(15)
blender=spawn('blender',['/opt/homebrew/bin/blender','--background','--factory-startup','--threads','2','--python-exit-code','1','--python',str(S/'render_approved_batch_v1.py'),'--','final']);state['blender_phase']='all_rooms_cached_living';save()
while blender.poll() is None:
 state['elapsed_seconds']=time.time()-state['started'];save();time.sleep(30)
state['blender_exit_code']=blender.returncode;(M/'BLENDER_QUEUE_COMPLETE.json').write_text(json.dumps({'exit_code':blender.returncode,'timestamp':time.time()}));save()
while image2.poll() is None:
 state['elapsed_seconds']=time.time()-state['started'];save();time.sleep(30)
state['image2_exit_code']=image2.returncode
subprocess.run([PYTHON,str(S/'update_render_review_gallery_v1.py')],cwd=ROOT.parents[1],stdout=(logs/'gallery-final.log').open('w'),stderr=subprocess.STDOUT)
register=json.loads((M/'RENDER_REGISTER.json').read_text());state['counts']=register['summary'];state['status']='GENERATED_PENDING_VISUAL_QA' if register['summary']['actual_generated']==225 else 'PARTIAL';state['finished']=time.time();reg=json.loads((M/'CAMERA_REGISTER.json').read_text());state['source_hash_unchanged']=hashlib.sha256(Path(reg['source_design']).read_bytes()).hexdigest()==reg['source_sha256'];save()
print('OVERNIGHT_BATCH_FINISHED',json.dumps(state),flush=True)
