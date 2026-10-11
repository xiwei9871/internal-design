"""Small JPEG review site; original Blender renders and caches stay local."""
import hashlib, html, json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT/'design/sofa_soft_pilot_v7'
RUN = SRC/'local_final'
OUT = ROOT/'renders/whole_house_final_study_v1/sofa_soft_pilot_v7'
OUT.mkdir(exist_ok=True)
audit=json.loads((RUN/'SOLVE_AUDIT.json').read_text())
verify=json.loads((RUN/'VERIFICATION.json').read_text())
assert verify['status']=='PASS_TECHNICAL_ONLY'
assert verify['sha256']==audit['output_sha256']
records=[]

def jpeg(source, name, edge=1500):
    source=Path(source)
    with Image.open(source) as im:
        original=list(im.size);im=im.convert('RGB');im.thumbnail((edge,edge));dest=OUT/(name+'.jpg');im.save(dest,quality=88)
    records.append({'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_size':original,'web_name':dest.name,'web_bytes':dest.stat().st_size})

for stage in ['fabric','clay']:
    manifest=json.loads((RUN/stage/'render-manifest.json').read_text())
    assert len(manifest['images'])==6
    assert manifest['source_sha256']==audit['output_sha256']
    for entry in manifest['images']:
        jpeg(entry['path'],stage+'_'+entry['family']+'_'+entry['camera'])
jpeg(ROOT/'design/sofa_soft_pilot_v6/references/REFERENCE_SHAPE_CONTACT.jpg','reference')
for rejected in ['solve1','solve2']:
    jpeg(SRC/rejected/'CLAY_COMPARE.jpg',rejected+'-rejected')
with Image.open(RUN/'fabric/V7_V6_THREE_QUARTER.png') as im:
    # Native pixels, not magnified by resampling; shows sewing and fabric together.
    im.crop((280,290,1170,850)).convert('RGB').save(RUN/'FABRIC_NATIVE_CROP.jpg',quality=92)
jpeg(RUN/'FABRIC_NATIVE_CROP.jpg','native-fabric')

def card(name,label):
    return f'<article><h3>{html.escape(label)}</h3><a href="{name}.jpg" target="_blank"><img src="{name}.jpg" alt="{html.escape(label)}" loading="lazy"></a></article>'

seat=verify['shells']['V7_SEAT_COMPLETE_COVER']['bounds_m']
back=verify['shells']['V7_BACK_COMPLETE_COVER']['bounds_m']
seat_dims=[(seat[1][i]-seat[0][i])*1000 for i in range(3)]
back_dims=[(back[1][i]-back[0][i])*1000 for i in range(3)]
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type 软包 V7 · 松软感试点</title>
<style>body{margin:0;background:#f4f0e8;color:#302e28;font-family:system-ui,sans-serif}main{max-width:1450px;margin:auto;padding:28px}h1{font-size:29px}h2{font-size:23px;margin-top:38px}h3{font-size:16px}p,li{line-height:1.8}article{padding:14px;background:#fff;border-radius:10px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:16px 0}img{display:block;width:100%;height:auto}aside{background:#e6ddcc;border-radius:10px;padding:18px;line-height:1.8}nav{display:flex;gap:22px;flex-wrap:wrap;margin:20px 0}a{color:#695432}table{width:100%;border-collapse:collapse;background:white}th,td{text-align:left;padding:12px;border-bottom:1px solid #ded8cd}summary{cursor:pointer;font-size:19px}code{overflow-wrap:anywhere}.status{font-size:13px;letter-spacing:.1em;color:#7b633e}@media(max-width:800px){.pair{grid-template-columns:1fr}main{padding:16px}}</style>
<main><p class="status">2026-10-11 · 一组坐包＋背包 · 待人工评审</p><h1>V7：保留厚度，检查松软感</h1>
<p>您对 V6 的反馈是“体积变大、变厚，像沙发了，但蓬松感、松软感还没做到”。本轮延续同一组软包、白蜡木和亚麻布艺，固定正面、侧面、斜视作比较。</p>
<aside>V7 增加较宽缓的填充下沉、收束的缝口及少量沿缝边的褶皱，并弯曲原来偏平直的坐包侧围。改善主要在局部，正常材质下的松软变化仍不够明显。自评尚不足替代 V6，保留 V6 基线，V7 仅供评审。木色、布艺材质、相机、灯光与曝光保持一致；全屋模型没有写回。</aside>
<nav><a href="#fabric">实渲对比</a><a href="#clay">灰模形体</a><a href="#detail">布艺近景</a><a href="#reference">图册与参考</a><a href="#method">试验记录</a><a href="#sizes">尺寸与检查</a></nav>
<h2 id="fabric">相同布艺与灯光 · 每组左 V6 / 右 V7</h2><p>先看靠包下缘与肩部、坐包冠部下沉和侧围曲线；本轮没有靠换色或加柔光制造区别。</p>'''
labels={'V6_FRONT':'正面','V6_SIDE':'侧面','V6_THREE_QUARTER':'斜视'}
for camera,label in labels.items():
    page+='<div class="pair">'+card('fabric_V6_'+camera,'V6 · '+label)+card('fabric_V7_'+camera,'V7 · '+label)+'</div>'
page+='<h2 id="clay">灰模 · 排除材质对形体判断的干扰</h2>'
for camera,label in labels.items():
    page+='<div class="pair">'+card('clay_V6_'+camera,'V6 · '+label)+card('clay_V7_'+camera,'V7 · '+label)+'</div>'
page+='<h2 id="detail">原生布艺近景</h2>'+card('native-fabric','V7 · 原生裁图，未放大插值')
page+='''<p>织物仍沿用 V5 的原生 4K 亚麻。木色有人工正向反馈；布样、光泽和目标的柔软观感尚未全部验收。形体与布艺质感需要分别判断。</p><h2 id="reference">同一套实物与外观依据</h2>'''+card('reference','业主图册第 4 / 8 页与已选 A 效果图')
page+='''<p>以图册的白蜡木框、海绵坐包、麻棉布套、羽绒＋丝棉靠包为有依据的定制构造。尚未确定准确采购 SKU；没有借用别款软包拼入旧木架。A 图限定外观，不提供建筑或施工尺寸。</p>
<h2 id="method">采用方法与保留的失败试验</h2><p>两轮真实布套模拟均完成坐包、背包各 55 帧磁盘烘焙，重开后缓存能复现。第一轮全表面细皱明显；第二轮收紧布套余量、提高抗弯和约束，仍像罩布，均不采用。</p>
<p>交付 V7 为参考约束的静态塑形：较宽的填充变化、缝边局部凹陷和侧围弧度，借鉴前轮查证的局部 height-alpha 方法。模型保留 Basis 和软包塑形 Shape Key，可编辑；最终形体未使用这两轮模拟结果，也未声称执行成功的原生雕刻笔刷或认证填充物力学。</p>
<details><summary>查看未采用的模拟结果</summary>'''+card('solve1-rejected','模拟 1 · 满面细皱，未采用')+card('solve2-rejected','模拟 2 · 细皱仍多，未采用')+'</details>'
page+=f'''<h2 id="sizes">实际尺寸与验证</h2><table><tr><th>项目</th><th>V7 实际</th><th>评审边界</th></tr>
<tr><td>坐包外包络</td><td>{seat_dims[0]:.0f} × {seat_dims[1]:.0f} × {seat_dims[2]:.0f} mm</td><td>宽深不变；冠部最高约 {seat[1][2]*1000:.0f} mm，比 V6 低约 8 mm</td></tr>
<tr><td>背包外包络</td><td>{back_dims[0]:.0f} × {back_dims[1]:.0f} × {back_dims[2]:.0f} mm</td><td>含原有后倾，不等同于展开板片规格</td></tr>
<tr><td>总高</td><td>约 {back[1][2]*1000:.0f} mm</td><td>V6 约 814 mm；仍高于旧 700 mm 预留约 {back[1][2]*1000-700:.0f} mm，尚未批准最终适配</td></tr>
<tr><td>静态支撑</td><td>坐包底 z=285 mm；背包最低间距约 {verify['minimum_back_seat_gap_mm']:.1f} mm</td><td>两软包与背架无表面穿插；不认证舒适度或真实承载</td></tr></table>
<p>两个软包闭合、正体积，无零长边 / 微小碎面；缝边附着于实际曲面。10 项受保护源文件哈希不变，V6 对照及木架网格、材质、相机、灯光与色彩管理保持；{verify['packed_images']} 张贴图打包无缺失。固定三视角实渲 1500×1200、Cycles / Metal / 64 samples；灰模 1000×800。原图、模拟缓存和前版均保留。</p>
<p>V6 的体积改善不等于最终坐高或采购规格获批。本轮最高坐面约 {seat[1][2]*1000:.0f} mm，也需要结合实际木架与受压坐高重新评估。未运行 Image2、全屋队列或操作用户正在使用的 Blender。</p>
<p>下一步由您判断 V7 的松软变化是否足够明显。外观未认可前，这个试点不进入全屋或成品模型库。</p></main></html>'''
(OUT/'review_gallery.html').write_text(page)
(OUT/'WEB_ARTIFACTS.json').write_text(json.dumps({'status':'HUMAN_REVIEW','records':records},indent=2)+'\n')
sheet=Image.new('RGB',(1500,850),'#f4f0e8');draw=ImageDraw.Draw(sheet)
for i,(family,camera) in enumerate((f,c) for f in ['V6','V7'] for c in labels):
    im=Image.open(OUT/f'fabric_{family}_{camera}.jpg');im.thumbnail((490,390))
    sheet.paste(im,(i%3*500+(500-im.width)//2,i//3*425+28));draw.text((i%3*500+10,i//3*425+8),family+' '+camera,fill='#222')
sheet.save(SRC/'PILOT_REVIEW_CONTACT.jpg',quality=84)
print(OUT/'review_gallery.html')
