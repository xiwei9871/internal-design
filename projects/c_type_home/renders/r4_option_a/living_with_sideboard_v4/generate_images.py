import sys,json,subprocess,time,hashlib,concurrent.futures
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent;OLD=OUT.parent/'living_light_seating_v3';CLI=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64';cams=json.loads((OUT/'reports/CAMERA_REGISTER.json').read_text());FILE=OUT/'reports/IMAGES.json';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
MASTER='''本轮只做“有轻边柜”版本，与已有“无柜+轻单椅”版本比较。必须真正新增一只清楚可辨认的轻边柜，不能再只画椅和圆边几。柜的位置由用户图3蓝色高亮带规定：主沙发的南侧/侧后方、客厅下层平地，不是曲线错层平台上。柜中心R4坐标X4.45/Y7.81m，长方向东西向；占地X3.75–5.15/Y7.65–7.97m，全部落FFL0。前门朝北会客区。\n边柜精确候选包络1400长x320浅进深x650总高mm，细腿高度200mm，离地上部仅450mm柜箱，轻白蜡木、两扇简洁柜门、薄台面/薄侧板、纤细木腿和克制细拉手；是一只轻侧柜，不是厚重2200x400x700柜、床头柜、巨储物墙、三米长柜、厚石台或新电视墙。台面最多放一件小花器或两本书，不堆摆件。必须画出柜门和落地细腿，不能画成无柜门长桌，也不能悬浮在空中。\n硬锁：墙、全部门窗/门套、窗框分格、飘窗、三步台阶、+450曲线错层平台、餐厅玻璃门、原通道、现有主沙发/窗边贵妃/轻单椅/圆边几/主副茶几和原低媒体柜都不改。只能新增所指定柜。平台顶、侧面和台阶完全是原建筑，绝不能把平台木/石立面画成柜门、在平台上放柜或把柜脚落在+450台面；柜脚必须落客厅FFL0地面。不要为露出柜子搬单椅或沙发、拓宽房间或新建墙。自然遮挡允许，另有柜体细节图展示全柜。\n家具/材质/软装完全延续已有图：暖白、浅白蜡木、米白燕麦亚麻、细腿、轻日式/北欧、明亮柔和日光。保持相同地毯、两张木腿浅石茶几、挂画、窗帘、采光与整洁陈设；不能换一套家具或风格。玻璃透明，平顶正常，无新增梁、天窗、复杂吊顶或大黑电视。'''

def run(c):
 id='LIVING_WITH_SIDEBOARD_'+c['id'];output=OUT/'images'/(id+'.png');pf=OUT/'prompts'/(id+'.txt')
 if c['id'] in ['HERO','SPACE']:
  base=OLD/'images'/('LIVING_LIGHT_'+c['id']+'.png');inputs=[str(base),c['reference']];note='第一输入是无柜原效果图，原图的相机、建筑和其它家具绝对保持。第二输入是同机位R4 clay，新增的柜位置/深度/柜门/四脚清楚，请将它以白蜡木材质植入第一图对应处。透明mask只许可改柜及接触阴影的局部；原椅、前景沙发、平台和玻璃不得重画。柜投影范围约'+str(c['cabinet_projected_bbox_px'])+'像素，位于原图椅后右方靠下处，与用户黄框位置相符。';mask=c['mask']
 else:
  base=OUT/'images/LIVING_WITH_SIDEBOARD_HERO.png';inputs=[c['reference'],str(base)];mask=None;note='第一图是柜体细节的新机位R4 clay，第二图仅作同方案柜门、细腿和材质外观参考。保留第一图机位与结构，清楚表现全柜浅进深、两柜门、200mm腿下净空、FFL0地面和前方原单椅关系；不是新放柜的位置。'
 pf.write_text(MASTER+'\n\n[机位输入]\n'+note+'\n相机'+str(c['pos'])+'，目标'+str(c['target'])+'，'+str(c['lens'])+'mm。')
 args=['rtk','proxy',str(CLI),'edit']
 for f in inputs:args+=['--image',f]
 if mask:args+=['--mask',mask]
 args+=['--prompt-file',str(pf),'--model','gpt-image-2','--quality','high','--size','1536x1024','--n','1','--timeout','180','--max-attempts','1','--out',str(output)]
 t=time.monotonic();print('IMAGE_START '+c['id'],flush=True)
 try:r=subprocess.run(args,capture_output=True,text=True,timeout=200);code=r.returncode;log=r.stdout+'\n'+r.stderr
 except subprocess.TimeoutExpired:code=124;log='TIMEOUT_200s'
 lp=OUT/'reports/logs'/(id+'.log');lp.write_text(log);status='GENERATED' if code==0 and output.exists() else 'FAILED'
 if output.exists():Image.open(output).verify()
 result=dict(image_id=id,camera=c['id'],reference=c['reference'],reference_sha256=sha(c['reference']),inputs=inputs,input_sha256=[sha(f) for f in inputs],mask=mask,output=str(output),prompt=str(pf),status=status,seconds=round(time.monotonic()-t,2),request_log=str(lp),retry_count=0,image_sha256=sha(output) if output.exists() else None,error=None if status=='GENERATED' else log[-900:]);print('IMAGE_'+status+' '+c['id']+' '+str(result['seconds'])+'s',flush=True);return result
rows=json.loads(FILE.read_text()) if FILE.exists() else [];mode=sys.argv[1];selected=[c for c in cams if (c['id']=='DETAIL')==(mode=='detail')];done={r['camera'] for r in rows}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for r in pool.map(run,[c for c in selected if c['id'] not in done]):rows.append(r);FILE.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print('PHASE_DONE '+mode,flush=True)
