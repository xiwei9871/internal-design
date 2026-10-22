import json,sys,subprocess,time,hashlib,concurrent.futures
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent;CLI=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64';REG=OUT/'reports/CAMERA_REGISTER.json';FILE=OUT/'reports/IMAGES.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
MASTER='''请根据第一张R4客厅clay几何图生成一张专业住宅室内效果图。本轮只有一个已指定方向：维持主沙发现状、窗边贵妃椅/躺椅、空位轻单椅+小边几，不做A/B/C发散。第一张负责建筑、相机、家具位置，若有第二张，它只负责本轮同一个客厅的材质、家具外观和光色一致性，不能移植相机。\n建筑硬锁：墙体、全部门洞/门套、窗洞及主要窗框分格、450mm外挑飘窗、曲线错层平台、+450mm高差、原3x150mm台阶、原餐厅玻璃门和主通道宽度、原固定柜体与低媒体柜全部保持。白模上方是正常平顶，不是露天、天窗或新增梁。玻璃透明，不能画成木墙。原卧室直门保留，不能恢复斜门或删门。\n必须彻底取消上一版错误：不能在错层平台或台阶上放任何大柜/厚重低柜！不许2200x400x700mm深柜，不许一整条深边柜、巨大储物墙、黑色电视/黑洞、额外高柜、岛台、带抽屉方床头柜。错层平台上保持参考图的原建筑表面和净空，绝不以新柜体冒充平台。\n主沙发严格保留R4三人位2300x900的原西侧位置和朝向，不改L型，不更换主布局。窗前独立1700x900贵妃躺椅保持低矮亚麻软包+白蜡木细腿，放客厅原FFL0地坪，不放在450mm窗台上。新增只有一张800x780x820mm白蜡木开放框架轻休闲椅，位于客厅平地、台阶西北侧会客区内缘，中心X5.15/Y8.95m，朝向会客中心略转10°；旁边一张直径420mm、高510mm的圆开放式三腿边几，中心X5.95/Y8.85m。参考已经给出位置，不能挪到高平台，不再加第二张单椅/小沙发。\n本版不需要新side cabinet或console；宁可留弹性空位，不为了填满画面再加柜。如窗侧已有同类小圆边几，只保留参考位置。保留当前一主一副木腿+暖浅石茶几系统，不增第三张茶几，不换普通小方桌。\n风格：明亮、清爽、干净、轻暖的日式/北欧住宅，浅白蜡木/自然木色、暖白墙、米白/燕麦亚麻布艺、浅暖石台面、薄自然织毯、自然日间柔和光影、少量柔软靠垫、细腿家具与克制植物，材质真实细腻。不深色豪华、不重奶油/侘寂、不复杂吊顶/夸张灯带、不装满台面。墙上只可保留一幅克制艺术，兼容未来壁画电视/投影，不在这轮画巨大黑电视。空间有生活感但不满，原通道要完整。'''
NOTES={
'HERO':'主视角沿用R4 L2反向机位。北窗在镜头背后，不凭空加到正前方。重点表现低层轻单椅+圆边几、原主沙发一角、三阶台阶/原曲平台、原直门与餐厅玻璃关系。不得在高平台放柜。',
'SPACE':'整体辅助视角沿用R4 L4公共区机位。保持近景左侧实墙和原低媒体柜、原三阶和曲平台、原餐厅玻璃门与正常直门位置，不能把近景暗墙误读为黑色大屏/新门。单椅必须落下层平地，过道净宽保持。',
'WINDOW_LINK':'窗边/新单椅关系辅助视角，从R4 L1原位置以24mm自然视角向内微调目标。必须在同一真实空间里表现北窗附近贵妃躺椅与会客区内侧新增轻单椅/边几关系，允许局部家具被自然裁切，不把原架构拉长以求所有物品完整入画。落地椅与450mm窗台层次清楚，原主沙发位置不动。'}
def run(c,anchor=None):
 id='LIVING_LIGHT_'+c['id'];pf=OUT/'prompts'/(id+'.txt');pf.write_text(MASTER+'\n\n[当前机位]\n'+NOTES[c['id']]+'\n相机位置'+str(c['pos'])+'、目标'+str(c['target'])+'、焦距'+str(c['lens'])+'mm。');out=OUT/'images'/(id+'.png');args=['rtk','proxy',str(CLI),'edit','--image',c['reference']]
 if anchor:args+=['--image',anchor]
 args+=['--prompt-file',str(pf),'--model','gpt-image-2','--quality','high','--size','1536x1024','--n','1','--timeout','180','--max-attempts','1','--out',str(out)]
 t=time.monotonic();print('IMAGE_START '+c['id'],flush=True)
 try:r=subprocess.run(args,capture_output=True,text=True,timeout=200);log=r.stdout+'\n'+r.stderr;code=r.returncode
 except subprocess.TimeoutExpired:log='NETWORK_TIMEOUT_200s';code=124
 lp=OUT/'reports/logs'/(id+'.log');lp.write_text(log);status='GENERATED' if code==0 and out.exists() else 'FAILED'
 if status=='GENERATED':Image.open(out).verify()
 row=dict(image_id=id,camera=c['id'],reference=c['reference'],reference_sha256=c['reference_sha256'],prompt=str(pf),output=str(out),style_anchor=anchor,style_anchor_sha256=sha(anchor) if anchor else None,status=status,seconds=round(time.monotonic()-t,2),retry_count=0,image_sha256=sha(out) if out.exists() else None,request_log=str(lp));print('IMAGE_'+status+' '+c['id']+' '+str(row['seconds'])+'s',flush=True);return row
rows=json.loads(FILE.read_text()) if FILE.exists() else [];cams=json.loads(REG.read_text());mode=sys.argv[1]
selected=[c for c in cams if (c['id']=='HERO')==(mode=='hero')];old={r['camera'] for r in rows}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 fs=[pool.submit(run,c,None if c['id']=='HERO' else str(OUT/'images/LIVING_LIGHT_HERO.png')) for c in selected if c['id'] not in old]
 for f in concurrent.futures.as_completed(fs):rows.append(f.result());FILE.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print('PHASE_DONE '+mode,flush=True)
