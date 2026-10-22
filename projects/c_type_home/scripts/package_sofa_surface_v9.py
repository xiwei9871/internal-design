"""Material A/B and sourced filling facts; no adoption of an unsuccessful test."""
import hashlib,html,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'design/sofa_material_pilot_v9';RUN=SRC/'surface_test';OUT=ROOT/'renders/whole_house_final_study_v1/sofa_material_pilot_v9';OUT.mkdir(exist_ok=True)
a=json.loads((RUN/'RENDER_MANIFEST.json').read_text());v=json.loads((RUN/'VERIFICATION.json').read_text())
assert v['status']=='PASS_MATERIAL_ONLY' and v['candidate_sha256']==a['candidate_sha256']
records=[]
def jpeg(source,name):
    source=Path(source)
    with Image.open(source) as im:
        original=list(im.size);im=im.convert('RGB');im.thumbnail((1500,1500));p=OUT/(name+'.jpg');im.save(p,quality=90)
    records.append({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_size':original,'web_name':p.name,'web_bytes':p.stat().st_size})
for r in a['images']:jpeg(r['path'],r['case']+'_'+r['camera'])
jpeg(ROOT/'design/sofa_soft_pilot_v8/references/OWNER_RELAXED_COVER.png','owner-reference')
def card(name,label):return f'<article><h3>{html.escape(label)}</h3><a href="{name}.jpg" target="_blank"><img src="{name}.jpg" alt="{html.escape(label)}" loading="lazy"></a></article>'
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type V9 · 布艺材质与填充构造测试</title>
<style>body{margin:0;background:#f4f0e8;color:#302d27;font-family:system-ui,sans-serif}main{max-width:1440px;margin:auto;padding:28px}h1{font-size:29px}h2{font-size:23px;margin-top:38px}h3{font-size:16px}p,li{line-height:1.8}aside{padding:18px;background:#e6ddcc;border-radius:10px;line-height:1.8}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:16px 0}article{padding:14px;background:#fff;border-radius:10px}img{display:block;width:100%;height:auto}a{color:#685430}table{width:100%;border-collapse:collapse;background:#fff}th,td{text-align:left;padding:12px;border-bottom:1px solid #ded8cd}nav{display:flex;gap:22px;flex-wrap:wrap;margin:20px 0}summary{cursor:pointer;font-size:18px}@media(max-width:800px){.pair{grid-template-columns:1fr}main{padding:16px}th,td{padding:8px}}</style>
<main><p>2026-10-11 · 一组坐包＋靠包 · 材质单项测试</p><h1>表面更柔和，是否就会显得蓬松？</h1>
<p>按您要求，先查一般沙发的坐垫 / 靠包填充，再固定同一模型、同一灯光，验证只改布套材质是否有用。本轮没有继续增加褶皱或松量。</p>
<aside>本轮结果：增强微纤维反射后，布面更亮、反射更柔和；蓬松体积没有明显改善，部分浅褶皱反而被淡化。当前保留原布艺，B 不自动采用。这个对照只验证了表面纤维层调整；它没有改变内部填充的硬度、回弹或下沉。</aside>
<nav><a href="#filling">坐垫与靠包填充</a><a href="#compare">材质对照</a><a href="#detail">近景</a><a href="#reference">目标参考</a><a href="#method">方法与核验</a></nav>
<h2 id="filling">厂家常见构造：外套与填充是两层问题</h2><table><tr><th>部位</th><th>常见材料 / 组合</th><th>决定什么</th></tr>
<tr><td>坐垫内部</td><td>聚氨酯泡棉 / 海绵芯，外包聚酯纤维；更柔软的产品另加羽毛 / 羽绒 / 纤维混合外套，也有弹簧芯方案</td><td>支撑、回弹、表面包覆与受压形状。泡棉密度不能单独代表硬度</td></tr>
<tr><td>靠包内部</td><td>较松的聚酯纤维、超细纤维或羽毛 / 羽绒 / 纤维混合填充，常用分仓防止堆积；具体产品可能另含泡棉</td><td>较容易塌陷、堆积与回弹的轮廓；不是一块处处同样规整的硬芯</td></tr>
<tr><td>可见布套</td><td>棉麻、聚酯混纺等家具布；本项目沿用麻棉 / 米白亚麻方向</td><td>颜色、织纹、反光、纤维感。表面材质参数不等于内部填充力学</td></tr></table>
<p><a href="https://www.vanguardfurniture.com/CushionOptions" target="_blank">Vanguard 官方 Cushion Options</a> 明确区分多个坐芯与靠包方案，包括泡棉＋包覆层、分仓纤维 / 羽毛靠包。业主图册第 8 页也写有“海绵坐包、麻棉、羽绒＋丝棉”；本户准确采购型号、丝棉成分和泡棉硬度尚未确定。表中是常见实例，不是本户已批准配方。</p>
<h2 id="compare">同模型、同方向光 · 左 A 原布艺 / 右 B 微纤维层测试</h2><div class="pair">'''+card('A_original_V6_THREE_QUARTER','A · 原 4K 亚麻材质')+card('B_microfiber_V6_THREE_QUARTER','B · 同材质，增强微纤维层')+'</div>'
page+='''<p>模型、UV、贴图、布色参数、相机、灯光、曝光与色彩管理相同。B 改变的是纤维反射，因此即使布色参数不变，视觉亮度仍会变化。这个变化没有创造填充蓬松感。</p>
<h2 id="detail">相同近景相机 · 原生 1500×1200</h2><div class="pair">'''+card('A_original_V9_FABRIC_CLOSEUP','A · 原布艺近景')+card('B_microfiber_V9_FABRIC_CLOSEUP','B · 微纤维层近景')+'</div>'
page+='''<p>织纹仍来自同一完整供应商亚麻材质。B 更柔和、更白，也削弱了部分局部起伏；自评尚不能称优化了目标的松软感。这不证明所有材质方法都无效，只说明这次有控制的表面调整不足以解决核心问题。</p>
<h2 id="reference">您提供的目标</h2>'''+card('owner-reference','目标：饱满填充、宽浅不等距褶皱与自然垂落')
page+='''<p>后续若继续，应分别处理坐垫的支撑芯 / 柔软包覆轮廓与靠包的松填充 / 分仓轮廓，并在同材质、同光照下判断。局部布面有褶皱，不代表整体填充已经柔软；当前不自动进入新形体制作。</p>
<h2 id="method">本次方法与核验</h2><p>复用项目已验证的 Poly Haven rough_linen 原生 Blender shader 与完整 4K 贴图，保留物理纹理尺度和现有浅色方向。另查棉织物资产，Fabric Pattern 05 为卡其 / 蓝格纹，不符合素色布艺，因此未下载或替换。</p>
<p><a href="https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/principled.html#sheen" target="_blank">Blender 5.2 官方 Sheen 说明</a> 将其定义为微小表面纤维的反射层。B 仅将 Sheen Weight 从 0.2 改为 0.5，Sheen Roughness 从 0.5 改为 0.8；这些是公开声明的测试值，不是厂家实测硬度或通用棉麻配方。SSS、Coat、Transmission 保持 0。</p>
<p>独立重开确认 70 个原对象、54 个网格及评价后几何保持；两个布套材料槽换到副本，副本仅两项输入不同。灯光、World、已有相机、曝光、色彩与所有原材质保持。12 项保护哈希不变，18 张贴图打包无缺失。三个新实渲＋一个复用基线，Cycles / Metal / 64 samples / OIDN High Accurate。</p>
<p>模型仍是 V7 的独立试点：冠部最高约 483 mm、总高约 810 mm，采购、坐高与全屋适配尚未批准。未改全屋或 Ground Truth，未使用 Image2，未操作正在使用的 Blender。B 为失败的待评审试验，原模型、原材质与所有候选保留。</p>
<p><a href="../sofa_render_diagnosis_v8/review_gallery.html">上一轮同模光照诊断</a> · 先核对灰模 / 实渲差异，再分别判断布套表面与填充大形。</p></main></html>'''
(OUT/'review_gallery.html').write_text(page)
(OUT/'WEB_ARTIFACTS.json').write_text(json.dumps({'status':'HUMAN_REVIEW_RETAIN_ORIGINAL_MATERIAL','records':records},indent=2)+'\n');print(OUT/'review_gallery.html')
