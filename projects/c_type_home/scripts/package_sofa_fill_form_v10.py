"""Small JPEG review site for differentiated filling forms, originals retained."""
import hashlib,html,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'design/sofa_fill_form_v10';RUN=SRC/'delivery';OUT=ROOT/'renders/whole_house_final_study_v1/sofa_fill_form_v10';OUT.mkdir(exist_ok=True)
a=json.loads((RUN/'BUILD_AUDIT.json').read_text());v=json.loads((RUN/'VERIFICATION.json').read_text())
assert v['status']=='PASS_TECHNICAL_ONLY' and v['output_sha256']==a['output_sha256']
records=[];image_paths={}
def jpeg(source,name,edge=1500):
    source=Path(source)
    with Image.open(source) as im:
        size=list(im.size);im=im.convert('RGB');im.thumbnail((edge,edge));p=OUT/(name+'.jpg');im.save(p,quality=89)
    records.append({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_size':size,'web_name':p.name,'web_bytes':p.stat().st_size})
for stage in ['fabric','clay']:
    manifest=json.loads((RUN/stage/'render-manifest.json').read_text());assert len(manifest['images'])==6 and manifest['source_sha256']==a['output_sha256']
    for r in manifest['images']:
        image_paths[(stage,r['family'],r['camera'])]=r['path']
        jpeg(r['path'],stage+'_'+r['family']+'_'+r['camera'])
jpeg(ROOT/'design/sofa_soft_pilot_v8/references/OWNER_RELAXED_COVER.png','owner-reference')
for family in ['V7','V10']:
    with Image.open(image_paths[('fabric',family,'V6_THREE_QUARTER')]) as im:im.crop((270,250,1190,850)).convert('RGB').save(RUN/(family+'_NATIVE_CROP.jpg'),quality=92)
    jpeg(RUN/(family+'_NATIVE_CROP.jpg'),family+'-native')
def card(name,label):return f'<article><h3>{html.escape(label)}</h3><a href="{name}.jpg" target="_blank"><img src="{name}.jpg" alt="{html.escape(label)}" loading="lazy"></a></article>'
labels={'V6_THREE_QUARTER':'斜视','V6_FRONT':'正面','V6_SIDE':'侧面'}
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type V10 · 坐垫支撑与靠包松填充</title>
<style>body{margin:0;background:#f4f0e8;color:#302d27;font-family:system-ui,sans-serif}main{max-width:1440px;margin:auto;padding:28px}h1{font-size:29px}h2{font-size:23px;margin-top:36px}h3{font-size:16px}p,li{line-height:1.8}aside{padding:18px;background:#e6ddcc;border-radius:10px;line-height:1.8}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:16px 0}article{padding:14px;background:#fff;border-radius:10px}img{display:block;width:100%;height:auto}a{color:#685430}table{width:100%;border-collapse:collapse;background:#fff}th,td{text-align:left;padding:12px;border-bottom:1px solid #ded8cd}nav{display:flex;gap:22px;flex-wrap:wrap;margin:20px 0}summary{cursor:pointer;font-size:18px}@media(max-width:800px){.pair{grid-template-columns:1fr}main{padding:16px}th,td{padding:8px}}</style>
<main><p>2026-10-11 · 一组坐垫＋靠包 · 待人工评审</p><h1>V10：坐垫保留支撑，靠包重做填充轮廓</h1>
<aside>材质测试没有解决蓬松感，本轮恢复原布艺，重点改变填充大形。坐垫缩短直立侧围，让软包覆绕过泡棉芯的边缘；靠包做更圆的填充鼓起、肩部轻微垂落与下部支撑变形。自评靠包的丰满度有可见变化，但布套仍偏规整，参考图的自然松弛感尚未确认达标。保持同一木架、灯光、相机与曝光，褶皱仍为原来的四组缝边，没有增加数量。</aside>
<nav><a href="#fabric">实渲对照</a><a href="#detail">近景</a><a href="#clay">灰模</a><a href="#reference">目标参考</a><a href="#sizes">尺寸与核验</a></nav>
<h2 id="fabric">左：V7 形体 · 右：V10 填充形体候选</h2><p>两边都使用 V8 的同一方向光和原生 V5 亚麻材质。请分别看坐垫边缘是否仍有支撑、靠包是否更圆且更有柔软填充感；有褶皱和更圆不自动等于完成目标。</p>'''
for camera,label in labels.items():page+='<div class="pair">'+card('fabric_V7_'+camera,'V7 · '+label)+card('fabric_V10_'+camera,'V10 · '+label)+'</div>'
page+='<h2 id="detail">相同范围 · 原生裁图</h2><div class="pair">'+card('V7-native','V7 · 原生近景')+card('V10-native','V10 · 原生近景')+'</div>'
page+='''<h2 id="clay">灰模 · 本轮关闭凹凸增强</h2><p>灰模只辅助检查轮廓和支撑，以实渲作为布艺观感依据。本轮两边的 Workbench Cavity 都关闭，减少灰模夸大褶皱反差。</p>'''
for camera,label in labels.items():page+='<div class="pair">'+card('clay_V7_'+camera,'V7 · '+label)+card('clay_V10_'+camera,'V10 · '+label)+'</div>'
page+='<h2 id="reference">您指定的目标参考</h2>'+card('owner-reference','饱满填充、自然垂落与宽浅褶皱')
page+='''<p>业主图册第 4 / 8 页和已核查的厂家坐芯＋柔软包覆、分仓松填充靠包构造作为依据；图中材质与轮廓用于外观，不据此推定尺寸。本模型属于有依据的定制试点，尚未绑定准确采购 SKU。</p>
<p>可编辑模型另有隐藏的泡棉芯、柔软包覆层和三仓靠包填充示意，用于查看构造。它们是试验示意尺寸，不是厂家剖面。外观采用静态曲面塑形，没有声称真实模拟海绵或羽绒的回弹、硬度与承载。</p>'''
sb=v['shells']['V10_SEAT_COMPLETE_COVER']['bounds_m'];bb=v['shells']['V10_BACK_COMPLETE_COVER']['bounds_m']
page+=f'''<h2 id="sizes">实际尺寸与核验</h2><table><tr><th>项目</th><th>V10 实际</th><th>与旧版的关系</th></tr>
<tr><td>坐垫占地</td><td>{(sb[1][0]-sb[0][0])*1000:.0f}×{(sb[1][1]-sb[0][1])*1000:.0f} mm</td><td>保持原占地和木承托</td></tr>
<tr><td>坐垫标高</td><td>底部 285 mm；冠部最高 {v['seat_crown_mm']:.1f} mm</td><td>最高点比 V7 高约 1.1 mm；不是最终推荐坐高</td></tr>
<tr><td>靠包轮廓</td><td>底部最低 {(bb[0][2])*1000:.1f} mm；顶部 {v['total_height_mm']:.1f} mm</td><td>顶部比 V7 低约 3.9 mm；下缘局部贴合坐垫，最低点较 V7 低约 31 mm，整包没有整体下移</td></tr>
<tr><td>总高预留</td><td>{v['total_height_mm']:.1f} mm</td><td>仍高于旧 700 mm 预留约 {v['old700mm_conflict_mm']:.0f} mm；适配未批准</td></tr>
<tr><td>静态接触</td><td>背包最低顶点间距约 {v['minimum_back_to_seat_vertex_gap_mm']:.1f} mm</td><td>坐垫 / 靠包、软包 / 木架无穿透；坐垫底面与木承托接触</td></tr></table>
<details><summary>技术证据与本轮限制</summary><p>两个软包闭合、正体积，无零长边 / 微小碎面。70 个基线对象、14 个木架副本、原 shader、相机、灯光、World、曝光和色彩保持；13 项保护哈希不变，18 张贴图打包无缺失。原始版、失败候选与所有原图保留。</p>
<p>第一版顶点间距正常，但粗侧围面片穿过凸起坐垫；已保留失败记录。修正侧围细分、接触余量和后缘支撑后，独立重开验证无面片穿插。木承托的共面接触是有意支撑，检查没有坐垫沉入木板。</p>
<p>最终 6 张实渲均原生 1500×1200，Cycles / Metal / 64 samples / OIDN GPU High Accurate；灰模 1000×800。只评审这一组，没有调用 Image2、全屋队列、购买资产或操作用户正在使用的 Blender。棚拍灯光未按本户窗位 / 现场照度校准。</p></details>
<p>本轮交付为候选；松软感、准确布样、最终坐高与整件家具适配仍需人工判断。当前不写回全屋。<a href="../sofa_material_pilot_v9/review_gallery.html">材质测试记录</a></p></main></html>'''
(OUT/'review_gallery.html').write_text(page);(OUT/'WEB_ARTIFACTS.json').write_text(json.dumps({'status':'HUMAN_REVIEW','records':records},indent=2)+'\n')
sheet=Image.new('RGB',(1500,850),'#f4f0e8');draw=ImageDraw.Draw(sheet)
for i,(family,camera) in enumerate((f,c) for f in ['V7','V10'] for c in ['V6_FRONT','V6_SIDE','V6_THREE_QUARTER']):
    im=Image.open(OUT/('fabric_'+family+'_'+camera+'.jpg'));im.thumbnail((490,390));sheet.paste(im,(i%3*500+(500-im.width)//2,i//3*425+28));draw.text((i%3*500+10,i//3*425+8),family+' '+camera,fill='#222')
sheet.save(SRC/'FINAL_REVIEW_CONTACT.jpg',quality=85);print(OUT/'review_gallery.html')
