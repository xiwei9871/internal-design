"""A small review gallery explains render contrast without changing geometry."""
import hashlib,html,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'design/sofa_soft_pilot_v8';RUN=SRC/'render_diagnosis';OLD=ROOT/'design/sofa_soft_pilot_v7/local_final'
OUT=ROOT/'renders/whole_house_final_study_v1/sofa_render_diagnosis_v8';OUT.mkdir(exist_ok=True)
a=json.loads((RUN/'DIAGNOSIS_MANIFEST.json').read_text());verify=json.loads((RUN/'VERIFICATION.json').read_text());delivery=json.loads((RUN/'DELIVERY_MANIFEST.json').read_text())
assert verify['status']=='PASS_UNCHANGED_GEOMETRY_AND_MATERIALS'
assert a['candidate_sha256']==verify['candidate_sha256']==delivery['source_sha256']
records=[]
def jpeg(source,name,edge=1500):
    source=Path(source)
    with Image.open(source) as im:
        size=list(im.size);im=im.convert('RGB');im.thumbnail((edge,edge));dest=OUT/(name+'.jpg');im.save(dest,quality=89)
    records.append({'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_size':size,'web_name':dest.name,'web_bytes':dest.stat().st_size})
labels={'V6_THREE_QUARTER':'斜视','V6_FRONT':'正面','V6_SIDE':'侧面'}
for camera in labels:
    jpeg(OLD/'fabric'/('V7_'+camera+'.png'),'original_'+camera)
    jpeg(RUN/('directional_fabric_'+camera+'.png'),'directional_'+camera)
jpeg(a['original_workbench'],'workbench-gray')
jpeg(RUN/'cycles_neutral_V6_THREE_QUARTER.png','cycles-gray')
jpeg(SRC/'references/OWNER_RELAXED_COVER.png','owner-reference')
for name,path in [('original',OLD/'fabric/V7_V6_THREE_QUARTER.png'),('directional',RUN/'directional_fabric_V6_THREE_QUARTER.png')]:
    with Image.open(path) as im:im.crop((280,290,1170,850)).convert('RGB').save(RUN/(name+'_native_crop.jpg'),quality=92)
    jpeg(RUN/(name+'_native_crop.jpg'),name+'-native')
def card(name,label):return f'<article><h3>{html.escape(label)}</h3><a href="{name}.jpg" target="_blank"><img src="{name}.jpg" alt="{html.escape(label)}" loading="lazy"></a></article>'
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type V8 · 同模型光照诊断</title>
<style>body{margin:0;background:#f4f0e8;color:#302d27;font-family:system-ui,sans-serif}main{max-width:1440px;margin:auto;padding:28px}h1{font-size:29px}h2{font-size:23px;margin-top:38px}h3{font-size:16px}p,li{line-height:1.8}aside{padding:18px;background:#e6ddcc;border-radius:10px;line-height:1.8}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:16px 0}article{padding:14px;background:#fff;border-radius:10px}img{display:block;width:100%;height:auto}a{color:#685430}nav{display:flex;flex-wrap:wrap;gap:22px;margin:20px 0}summary{cursor:pointer;font-size:18px}table{width:100%;border-collapse:collapse;background:#fff}th,td{text-align:left;padding:12px;border-bottom:1px solid #ded8cd}@media(max-width:800px){.grid{grid-template-columns:1fr}main{padding:16px}}</style>
<main><p>2026-10-11 · 仅一组坐包＋背包 · 人工评审</p><h1>为什么灰模松软，实渲却紧绷？</h1>
<p>您指出 V7 灰模已经有点松，实渲却显得紧绷。本轮暂停继续松化网格，用同一份 V7 形体隔离检查渲染。</p>
<aside>同一网格换成 Cycles 灰材质，在原柔光下仍显得平。保留原布艺，只改变主光方向和补光强度，浅褶皱便更可见。证据支持：Workbench 的凹凸增强与原环绕柔光，是这次视觉落差的重要来源。右图不是更松的新模型；形体、材料、镜头、曝光和色彩管理都没有改变。</aside>
<nav><a href="#compare">三机位同模对比</a><a href="#diagnosis">四格诊断</a><a href="#detail">原生近景</a><a href="#reference">目标参考</a><a href="#limits">范围与核验</a></nav>
<h2 id="compare">左：原 V7 柔光 · 右：同模型方向光</h2><p>方向光减少从各方向填平阴影的补光，恢复靠包下缘、肩部和坐包浅褶皱的明暗变化。没有添加褶皱、改布料颜色或后期压暗来产生差异。</p>'''
for camera,label in labels.items():page+='<div class="grid">'+card('original_'+camera,'原灯光 · '+label)+card('directional_'+camera,'方向光候选 · '+label)+'</div>'
page+='''<h2 id="diagnosis">同一 V7 网格的四格诊断</h2><div class="grid">'''
page+=card('workbench-gray','Workbench 灰模 · 含凹凸 / 腔体增强')+card('cycles-gray','Cycles 18% 灰 · 原灯光')+card('original_V6_THREE_QUARTER','原布艺 · 原灯光')+card('directional_V6_THREE_QUARTER','同一布艺 · 方向光')+'</div>'
page+='''<p>Workbench 的增强能帮助找表面细节，但会放大褶皱印象；它不是布料在真实光照下的保证。灰材质实渲也偏平，说明不能把问题全部归咎于布艺 shader。最后一格仅改变光照，因此它直接展示了光照对浅褶皱的影响。</p>
<h2 id="detail">布艺与缝边 · 同范围原生裁图</h2><div class="grid">'''+card('original-native','原灯光 · 原生裁图')+card('directional-native','方向光 · 原生裁图')+'</div>'
page+='''<p>完整 V5 原生 4K 亚麻 shader 保持，含织纹、粗糙度、方向与反射。没有临时增加 bump / sheen 或换色。更明显的阴影不等于布样、软包形态或 1:1 参考复现已经获批。</p>
<h2 id="reference">您提供的松弛感参考</h2>'''+card('owner-reference','目标：饱满填充上有余量的布套、宽浅不等距褶皱')
page+='''<p>参考限定外观，不提供施工尺寸。V8 的更松形体试验已暂停、未采用；本页全部对比都使用 V7 网格。现在先评审实际光照下的观感，再决定是否还需要改形体。</p>
<h2 id="limits">本轮范围与核验</h2><p>独立重开比较：全部模型网格、评价后网格、UV、Shape Key、曲线、家具变换和相机一致；布艺与木材 shader、曝光和色彩管理一致。只允许主光的位置 / 朝向 / 尺寸 / 功率、补光与轮廓光功率、World 强度和渲染设置改变。11 项受保护源文件哈希不变，18 张图像打包无缺失。</p>
<p>当前仍是约 810 mm 总高、483 mm 坐包冠部的 V7 试点，尺寸、采购规格与本户最终坐高均未批准。方向光用于独立诊断，尚未按住宅窗位和现场照度校准；房间模型和原 V7 文件未写回。</p>
<details><summary>查看诊断设置</summary><table><tr><th>项目</th><th>原灯光</th><th>方向光候选</th></tr><tr><td>主光</td><td>420 W，2.5 m 大光源</td><td>320 W，1 m 侧向光源</td></tr><tr><td>补光 / 轮廓光</td><td>180 / 220 W</td><td>55 / 80 W</td></tr><tr><td>World 强度</td><td>0.35</td><td>0.18</td></tr><tr><td>相机 / 曝光 / 色彩</td><td colspan="2">同镜头；AgX Medium High Contrast；曝光 0</td></tr><tr><td>实渲</td><td colspan="2">原生 1500×1200，Cycles / Metal / 64 samples，OIDN High Accurate</td></tr></table></details>
<p>没有运行 Image2、全屋队列或操作正在使用的 Blender。原图、旧版与中途试验保留；候选尚待人工评审，不自动替换全屋。</p></main></html>'''
(OUT/'review_gallery.html').write_text(page)
(OUT/'WEB_ARTIFACTS.json').write_text(json.dumps({'status':'HUMAN_REVIEW','records':records},indent=2)+'\n')
sheet=Image.new('RGB',(1500,650),'#f4f0e8');draw=ImageDraw.Draw(sheet)
for i,name in enumerate(['original_V6_THREE_QUARTER','directional_V6_THREE_QUARTER']):
    im=Image.open(OUT/(name+'.jpg'));im.thumbnail((730,600));sheet.paste(im,(i*750+(750-im.width)//2,30));draw.text((i*750+12,8),['V7 original lights','Same V7 mesh/material, side light'][i],fill='#222')
sheet.save(SRC/'SAME_MESH_LIGHT_COMPARE.jpg',quality=85)
print(OUT/'review_gallery.html')
