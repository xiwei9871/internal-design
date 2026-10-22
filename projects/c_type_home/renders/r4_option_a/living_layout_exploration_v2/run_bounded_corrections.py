import sys,json,concurrent.futures
from pathlib import Path
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT))
from run_layout_images import job,dump
from layout_spec import LAYOUTS
cams=json.loads((OUT/'reports/CAMERA_REGISTER.json').read_text());phase=sys.argv[1];resultfile=OUT/'reports/CORRECTION_RESULTS.json';results=json.loads(resultfile.read_text()) if resultfile.exists() else []
if phase=='hero':selected=[c for c in cams if c['layout']=='C' and c['camera']=='L1']+[c for c in cams if c['layout'] in ['A','B'] and c['camera']=='L4']
else:selected=[c for c in cams if c['layout']=='C' and c['camera'] in ['L2','L3','L4','L5']]
def run(c):
 l=LAYOUTS[c['layout']];anchor=OUT/l['folder']/('living_layout'+c['layout']+'_'+l['slug']+'_L1'+('_retry' if phase!='hero' and c['layout']=='C' else '')+'.png')
 correction='唯一空间修正：C主副双茶几整体向南/内侧移动约270mm，以当前第一张clay位置为准；副茶几与L沙发北回转前沿净距应约436mm，不能把副桌顶回原紧贴座位的位置。保留同样椭圆主石桌/圆副石桌、木腿、L型沙发、观景椅、开放圆边几、帘/画/灯家族，不能新增第三张桌，不改变机位、窗、门、三阶、曲平台、低媒体柜。第二张旧L1仅提供家具外观，旧茶几坐标不生效。' if c['layout']=='C' else '原图错误地在近景左侧墙上新增巨大黑电视/黑洞。必须去掉所有黑屏和新增电视墙，用现有完整暖白/浅木墙面，原低媒体柜保持。近景左侧是实墙，不能是电视、落地门、黑色洞口或新玻璃。其余家具/两茶几/圆边几和原镜头、三阶平台、门套/开口都保持。仅修正这项，维持本方向L1家具外观。'
 return job(c,str(anchor),correction,retry=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for r in pool.map(run,selected):results.append(r);dump(resultfile,results)
print('CORRECTION_PHASE_DONE '+phase,flush=True)
