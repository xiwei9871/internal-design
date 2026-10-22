import json,sys,subprocess,time,concurrent.futures,hashlib,threading
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT))
from layout_spec import *
CLI=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64'
REG=OUT/'reports/CAMERA_REGISTER.json';FILE=OUT/'reports/IMAGES.json';fatal=threading.Event()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
MASTER='''任务：R4住宅客厅二次活动家具布局探索，室内杂志级专业住宅效果图，真实可落地的设计候选。第一张输入是当前机位的R4建筑+本方向家具布局clay参考。它对建筑、相机和座位布局优先级最高。允许把临时家具代理转化成成熟家具外观，不允许再重新排列座位或改变A/B/C指定种类。若有第二张输入，它只提供本方向主视角的家具家族、茶几、边几、布艺、帘、画、木色和灯具一致性，禁止把第二张机位的墙/窗/门移植到第一张。\n\n硬锁：墙体位置与厚度、房间尺度、门洞/门套、玻璃开口、窗框主分格、北侧外挑飘窗、450mm窗台、三阶150mm台阶与+450错层曲线平台、原平整连续地坪、原低媒体柜和固定柜体。不得加门窗、修改门宽、恢复斜门、删普通门、扩客厅、抹错层、加斜坡、增台阶、添加墙/柱/窗柜，不可把低飘窗做成高柜、落地窗或把阳台吞入客厅。所有座椅都在室内原FFL0地坪，不能悬浮或爬上450mm窗台。玻璃是透明玻璃，不是木墙。白模上部白背景是正常室内平顶，不能是露天、天窗或不完整屋顶。\n\n重要：正方形封闭抽屉角几/床头柜必须全部消失；不许换成圆角四方抽屉柜糊弄。使用420mm级小圆开放式白蜡木三腿边几，无抽屉无整块封闭侧板。茶几是一大一小两张低茶几：主桌980x620的椭圆暖浅石面+轻白蜡木腿，高370；副桌570x520的近圆暖浅石面+木腿，高440，两桌略套叠，位置跟参考。不要把两茶几合为一个普通小方桌，不用粗黑金属底、不做大厚石墩。保留自然室内透视、真实家具尺度与通道。日间自然柔光、清晰织物和木纹、透窗不过曝、干净克制、完整成熟设计感，不是白模简单上色。'''
def prompt(cam,correction=''):
 l=LAYOUTS[cam['layout']]
 text=MASTER+'\n\n[统一风格]\n'+STYLE+'\n\n[本方向：'+l['name']+']\n'+l['description']+'\n明确座位家族：'+l['sofa']+'\n同一方向三个视角统一：'+l['rug']+'；'+l['lighting']+'；'+l['art']+'。沙发为浅米色亚麻厚实软包、轻浅木底；A/B保留原三人位数量和位置，C是单一L型模块家族。窗帘只用薄米白自然织物/暖白轻透帘，不遮光成暗空间，不因帘改窗分格。软装密度少。\n\n[机位 '+cam['camera']+']\n相机位置'+str(cam['pos'])+'、目标'+str(cam['target'])+'、'+str(cam['lens'])+'mm。保留第一图裁切/透视。可见：'+cam['visible']+'。不可见/禁止移入：'+cam['hidden']+'。'
 if cam['camera']=='L1':text+='\n主视角朝北窗：A/B前方窗边是独立1700x900贵妃躺椅，不是双人沙发；三人位在左侧。A内侧双人位位于镜头后方/侧后，不能为了显示它又造一张放北窗。B必须没有双人位；内侧只有单椅，在本取景可能不完整入画。C必须明确一体L型转角轮廓，转角/北回转段朝室内；窗边只有一张轻观景椅。'
 if cam['camera']=='L2':text+='\n反向视角：原北窗在镜头后方，前方必须是原实墙低媒体柜、准确三阶和曲线平台、普通直门/右公共区玻璃开口，不能新增大窗。A原双人位在内侧南区朝北，后背可能朝镜头，不能再画躺椅放内侧；贵妃椅在镜头后方北窗边。B内侧只有轻木单椅加小圆边几，没有两人沙发。C前景可裁切同一个L沙发近腿，不能分解成多张独立沙发。没有大黑电视墙，低柜保持。'
 if cam['camera']=='L5':text+='\n窗边近景：已只将原L5目标下调至新窗前座位，位置和32mm镜头不变。必须明确A/B是一张可伸腿的贵妃躺椅，C是一件轻木观景休闲躺靠椅；不能沿用原北窗双人沙发。椅落FFL0室内地坪，窗台仍450mm低平台，椅后窗/侧返玻璃按clay裁切，不强迫主沙发或茶几从画外入画。边几是小圆开放腿，无抽屉。落地灯不遮满窗、不能变巨大灯罩。'
 if cam['camera']=='L3':text+='\n只表现本方向同一套沙发/两茶几近景，A/B窗前贵妃椅可局部入画，C须保留原L转角轮廓；不加第三张茶几，不把裁切外的内侧座椅拉到前景。'
 if cam['camera']=='L4':text+='\n公共区联动：原玻璃开口、三阶/曲边和低媒体柜保持，同方向内侧座位只按参考位置出现。原次主卧直门被墙遮住则继续遮住，不造前景门或改变玻璃门洞。镜头背后是北窗，前方不能新增北窗或吞阳台。'
 if correction:text+='\n\n[单次技术修正]\n'+correction
 return text

def job(cam,anchor=None,correction='',retry=False):
 key=cam['layout'];l=LAYOUTS[key];id='living_layout'+key+'_'+l['slug']+'_'+cam['camera'];suffix='_retry' if retry else '';pf=OUT/'prompts'/(id+suffix+'.txt');output=OUT/l['folder']/(id+suffix+'.png');pf.write_text(prompt(cam,correction));j=dict(image_id=id,layout=key,slug=l['slug'],camera=cam['camera'],reference=cam['reference'],prompt=str(pf),output=str(output),style_anchor=anchor)
 if output.exists():Image.open(output).verify();return dict(**j,status='GENERATED_EXISTING',seconds=0,retry_count=int(retry),image_sha256=sha(output))
 if fatal.is_set():return dict(**j,status='SKIPPED_FATAL',retry_count=int(retry))
 args=['rtk','proxy',str(CLI),'edit','--image',cam['reference']]
 if anchor:args+=['--image',anchor]
 args+=['--prompt-file',str(pf),'--model','gpt-image-2','--quality','high','--size','1536x1024','--n','1','--timeout','180','--max-attempts','1','--out',str(output)]
 print('IMAGE_START '+id+suffix,flush=True);t=time.monotonic()
 try:r=subprocess.run(args,capture_output=True,text=True,timeout=200);code=r.returncode;log=r.stdout+'\n'+r.stderr
 except subprocess.TimeoutExpired:code=124;log='NETWORK_TIMEOUT_200s'
 lp=OUT/'reports/logs'/(id+suffix+'.log');lp.write_text(log);elapsed=round(time.monotonic()-t,2)
 if any(e in log for e in ['HTTP 400','HTTP 401','HTTP 403','HTTP 404','HTTP 422','configuration error']):fatal.set()
 status='GENERATED' if code==0 and output.exists() else 'FAILED'
 if status=='GENERATED':im=Image.open(output);im.load();size=list(im.size)
 else:size=None
 print('IMAGE_'+status+' '+id+suffix+' '+str(elapsed)+'s',flush=True)
 return dict(**j,status=status,seconds=elapsed,retry_count=int(retry),actual_size=size,request_log=str(lp),image_sha256=sha(output) if output.exists() else None,error=None if status=='GENERATED' else log[-700:])
def main():
 assert sha(SRC)==SOURCE_SHA;cams=json.loads(REG.read_text());rows=json.loads(FILE.read_text()) if FILE.exists() else [];old={i['image_id']:i for i in rows}
 for views in [['L1'],['L2','L5'],['L3','L4']]:
  jobs=[c for c in cams if c['camera'] in views]
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   fs=[]
   for c in jobs:
    l=LAYOUTS[c['layout']];id='living_layout'+c['layout']+'_'+l['slug']+'_'+c['camera']
    if id in old:continue
    anchor=str(OUT/l['folder']/('living_layout'+c['layout']+'_'+l['slug']+'_L1.png')) if c['camera']!='L1' else None
    if anchor and not Path(anchor).exists():rows.append(dict(image_id=id,layout=c['layout'],camera=c['camera'],status='SKIPPED_MISSING_ANCHOR',output=str(OUT/l['folder']/(id+'.png')),retry_count=0));continue
    fs.append(pool.submit(job,c,anchor))
   for f in concurrent.futures.as_completed(fs):
    r=f.result();rows.append(r);old[r['image_id']]=r;dump(FILE,rows)
    if r['status']=='FAILED' and not fatal.is_set():
     c=next(c for c in cams if c['layout']==r['layout'] and c['camera']==r['camera']);r2=job(c,r.get('style_anchor'),retry=True);r2['initial_attempt']=r;rows=[r2 if x['image_id']==r['image_id'] else x for x in rows];old[r['image_id']]=r2;dump(FILE,rows)
  if fatal.is_set():break
 dump(OUT/'reports/GENERATION_DONE.json',dict(status='BLOCKED_EXTERNAL_SERVICE' if fatal.is_set() else 'GENERATION_COMPLETE_PENDING_VISUAL_QA',generated=sum(Path(r['output']).exists() for r in rows),expected=len(cams),source_unchanged=sha(SRC)==SOURCE_SHA))
 print('BATCH_DONE '+str(len(rows)),flush=True)
if __name__=='__main__':main()
