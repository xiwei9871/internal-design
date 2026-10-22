import json,time,subprocess,datetime
from pathlib import Path
from PIL import Image
from zoneinfo import ZoneInfo
from prompt_rules import assemble
OUT=Path(__file__).resolve().parent
ref=OUT/'00_reference/living_A1_reference.png';assert ref.exists()
pf=OUT/'05_prompts/living_A1_faithful_v1.txt';pf.write_text(assemble('A1','faithful'))
out=OUT/'01_faithful/living_A1_faithful_v1.png';assert not out.exists()
started=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds');t=time.monotonic()
cli=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64'
try:
 p=subprocess.run(['rtk','proxy',str(cli),'edit','--image',str(ref),'--prompt-file',str(pf),'--model','gpt-image-2','--quality','high','--size','1536x1024','--n','1','--timeout','180','--max-attempts','1','--out',str(out)],capture_output=True,text=True,timeout=200)
 log=p.stdout+'\n'+p.stderr;(OUT/'06_reports/logs/A1_MINIMAL_TEST.log').write_text(log)
 status='FAILED';size=None
 if p.returncode==0 and out.is_file():im=Image.open(out);im.load();size=list(im.size);status='GENERATED' if im.size==(1536,1024) else 'FAILED_SIZE'
 err=log[-900:] if status!='GENERATED' else None
except subprocess.TimeoutExpired:status='FAILED_TIMEOUT';size=None;err='bounded180s API test exceeded wall-time limit; downstream not started'
report=dict(status=status,image_id='living_A1_faithful_v1',camera_id='A1',variant='faithful',source_reference=str(ref),prompt_file=str(pf),output=str(out),started=started,seconds=round(time.monotonic()-t,2),actual_size=size,model='gpt-image-2',quality='high',endpoint_route='configured dotenv images/edits',error=err)
(OUT/'06_reports/A1_API_TEST.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if status!='GENERATED':(OUT/'06_reports/LIVING_API_FAILURE_REPORT.md').write_text('# API preflight失败，已立即停止\n\nA1白模和最小提示词已保存；没有下游批量、PBR或Cycles工作。\n\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False),flush=True)
