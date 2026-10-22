import subprocess,time,sys,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;deadline=time.monotonic()+210
while time.monotonic()<deadline:
 lines=subprocess.run(['/bin/ps','-axo','pid=,command='],capture_output=True,text=True).stdout.splitlines();active=[]
 for line in lines:
  if 'codex-image2-darwin-arm64.native edit ' in line and '/whole_house_ai_v1/05_main_bedroom/' in line:active.append(int(line.strip().split(maxsplit=1)[0]))
 if not active:break
 time.sleep(1)
print('RESUME_PRESERVING_COMPLETED_AND_ORPHAN_FINISHED_OUTPUTS',flush=True)
r=subprocess.run(['rtk','proxy',sys.executable,str(OUT/'overnight_runner.py')]);sys.exit(r.returncode)
