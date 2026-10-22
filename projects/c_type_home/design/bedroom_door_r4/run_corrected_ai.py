import json,runpy,time,subprocess,concurrent.futures,datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/r3_option_a/living_batch_v2_door';OLD=OUT.parent/'living_batch_v1'
master=runpy.run_path(str(OLD/'prepare_jobs.py'),run_name='prompt_helpers')
cams=json.loads((OUT/'working/cameras/CORRECTED_CAMERA_REGISTER.json').read_text())
jobs=[]
for cam in cams:
 for mode in ['strict','design','explore']:
  ident=f'living_{cam["id"]}_{mode}_door_corrected_v2'
  prompt=master['MASTER']+'\n最新模型修正高于任何历史prompt：次主卧不是无门通道，而是一樘850mm普通木门，门洞东西向，朝南向卧室内平开，有完整门框门套和上方实体墙。当前输入图门为关闭状态。严禁删门、画成衣柜/墙面/窗口、放回斜门，不能因为旧AI图没有门而省略门。模型西侧隔断墙保留完整。\n当前相机实际约束：'+cam['story']+'\n版本约束：'+master['MODES'][mode]
  if cam['id']=='A2':prompt+='\n后景普通木门必须位于参考图对应的曲线平台后方、紧邻西侧隔墙，保留门框可见部分和把手。不要把该门替换成另一块挂画或木饰面，不另造大窗。'
  if cam['id']=='A4':prompt+='\n新门仅在画面左侧边缘部分可见，以真实遮挡和裁切为准；不要为展示整樘门而移动镜头或挪开墙体。'
  if cam['id']=='D1':prompt+='\n这是门位核对特写，不是完整客厅取景。只显示输入可见的完整门、门套、左右实墙、门上墙和同高地坪。材质可以用统一浅白蜡木、暖白墙和中性地面；不新增家具、大窗、挂画、艺术背景墙或灯带来填满空白。门扇保持关闭且位置尺寸与输入相同，地面应为平整连续同标高，不生成三角台阶。'
  pf=OUT/'working/prompts'/(ident+'.txt');pf.write_text(prompt)
  jobs.append(dict(id=ident,camera=cam['id'],version=mode,input=cam['clay_path'],prompt_file=str(pf),output=str(OUT/'exports/ai_outputs'/(ident+'.png'))))
(OUT/'working/prompts/DOOR_CORRECTION_JOBS.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2)+'\n')
CLI=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64';results=[];start=time.monotonic()
def stamp():return datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
def run(j):
 t=time.monotonic();s=stamp();print('START '+j['id'],flush=True)
 if Path(j['output']).exists():return dict(**j,status='EXISTS_PRESERVED',seconds=0)
 cmd=['rtk','proxy',str(CLI),'edit','--image',j['input'],'--prompt-file',j['prompt_file'],'--model','gpt-image-2','--quality','high','--size','1536x1024','--n','1','--timeout','180','--max-attempts','2','--out',j['output']]
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=390);log=p.stdout+'\n'+p.stderr;(OUT/'logs'/(j['id']+'.log')).write_text(log)
 status='FAILED'
 if p.returncode==0 and Path(j['output']).is_file():im=Image.open(j['output']);im.load();status='GENERATED' if im.size==(1536,1024) else 'GENERATED_SIZE_VARIANT'
 result=dict(**j,status=status,started=s,completed=stamp(),seconds=round(time.monotonic()-t,2),error=log[-600:] if status=='FAILED' else None);print('DONE '+j['id']+' '+status+' '+str(result['seconds'])+'s',flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for f in concurrent.futures.as_completed([pool.submit(run,j) for j in jobs]):
  results.append(f.result());(OUT/'logs/DOOR_CORRECTION_GENERATION_RESULTS.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print('PROGRESS '+str(len(results))+'/9',flush=True)
print(json.dumps(dict(generated=sum(r['status']=='GENERATED' for r in results),target=9,seconds=round(time.monotonic()-start,2)),ensure_ascii=False))
