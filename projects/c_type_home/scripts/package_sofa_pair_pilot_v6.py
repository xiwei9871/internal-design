"""One pair, fixed V5/V6 cameras: image/data review without house propagation."""
import hashlib,html,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'design/sofa_soft_pilot_v6';OUT=ROOT/'renders/whole_house_final_study_v1/sofa_soft_pilot_v6';OUT.mkdir(exist_ok=True)
audit=json.loads((SRC/'DETAIL_AUDIT.json').read_text());verify=json.loads((SRC/'VERIFICATION.json').read_text());assert verify['status']=='PASS' and verify['output_sha256']==audit['output_sha256']
records=[]
def jpeg(source,name,edge=1500):
    with Image.open(source) as im:
        size=list(im.size);im=im.convert('RGB');im.thumbnail((edge,edge));p=OUT/(name+'.jpg');im.save(p,quality=92)
    records.append({'source':str(source),'sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),'source_size':size,'web_name':p.name,'web_bytes':p.stat().st_size})
for source_stage,prefix in [('detail_fabric_delivery','detail_fabric'),('detail_clay_contact','detail_clay_contact')]:
    manifest=json.loads((SRC/source_stage/'render-manifest.json').read_text());assert len(manifest['images'])==6
    for r in manifest['images']:jpeg(r['path'],prefix+'_'+r['family']+'_'+r['camera'])
jpeg(SRC/'references/REFERENCE_SHAPE_CONTACT.jpg','reference-shape')
jpeg(SRC/'FABRIC_NATIVE_CROP.jpg','native-fabric')
def card(name,label):return f'<article><h3>{html.escape(label)}</h3><a href="{name}.jpg" target="_blank"><img alt="{html.escape(label)}" src="{name}.jpg" loading="lazy"></a></article>'
height=audit['pair_bounds_m'][1][2]*1000;conflict=audit['trial_height_conflict_mm'];seatheight=(audit['seat_bounds_m'][1][2]-audit['seat_bounds_m'][0][2])*1000
page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type 坐包＋背包 · V6 试点</title>
<style>body{{margin:0;background:#f4f0e8;color:#272722;font-family:system-ui,sans-serif}}main{{max-width:1500px;margin:auto;padding:28px}}h1{{font-size:28px}}h2{{font-size:23px;margin-top:36px}}h3{{font-size:16px}}p,li{{line-height:1.8}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}.pair{{grid-template-columns:repeat(2,minmax(0,1fr))}}article{{padding:14px;background:white;border-radius:10px}}img{{width:100%;height:auto;display:block}}aside{{padding:18px;background:#e8dfcf;border-radius:10px}}a{{color:#635133}}nav{{display:flex;gap:22px;flex-wrap:wrap;margin:20px 0}}table{{width:100%;border-collapse:collapse;background:white}}td,th{{padding:12px;text-align:left;border-bottom:1px solid #ddd5c5}}@media(max-width:850px){{.grid,.pair{{grid-template-columns:1fr}}main{{padding:16px}}}}</style>
<main><h1>一组坐包＋背包 · V6 试点</h1><p>2026-10-11 · 正面、侧面与斜视固定对照。木材和布艺沿用 V5，本轮重点评审软包形体。</p>
<aside>坐包重新建立有支撑的冠部、侧围和布套；背包按柔软填充袋单独塑形，沿缝口收束并贴合坐包及木架。
这是独立的定制构造试点，尚未装入全屋模型，也不是原厂型号精确副本。当前总高约 {height:.0f} mm，比旧 700 mm 预留高约 {conflict:.0f} mm，必须单独确认适配。</aside>
<nav><a href="#fabric">布艺对照</a><a href="#clay">灰材质形体</a><a href="#reference">参考</a><a href="#fit">尺寸与限制</a></nav>
<h2 id="fabric">相同灯光与材质 · 上排 V5，下排 V6</h2><div class="grid">'''
labels={'V6_FRONT':'正面','V6_SIDE':'侧面','V6_THREE_QUARTER':'斜视'}
for family in ['V5','V6']:
    for camera,label in labels.items():page+=card('detail_fabric_'+family+'_'+camera,family+' · '+label)
page+='''</div><p>观察中心冠部、侧围厚度、背包圆润轮廓、缝边与支撑关系。材质没有为新版本重新加亮或换色，也没有添加装饰抱枕。</p>
<h2 id="clay">灰材质 · 形体与受压检查</h2><div class="grid">'''
for family in ['V5','V6']:
    for camera,label in labels.items():page+=card('detail_clay_contact_'+family+'_'+camera,family+' · '+label+'（灰材质）')
page+='''</div><p>这组图片用于判断形体是否真的改变。局部褶皱根据参考的缝口 / 受力位置塑形，保留大面积平顺表面；不是把随机褶皱铺满软包。</p>
<h2 id="reference">图册与已选效果图</h2>'''+card('reference-shape','业主图册与 A 参考 · 构造 / 轮廓依据')+'''
<p>业主图册第 4 页 1020 的木框 / 软包关系、第 8 页明确的白蜡木、海绵、麻棉、羽绒＋丝棉条目是构造依据。
A 效果图约束外观，不据图片推算施工尺寸。试点的内部泡棉、包覆层和背包分仓保存在可编辑模型中，可查看构造示意。</p>
<h2 id="fit">实际尺寸与需要确认的差异</h2><table><tr><th>项目</th><th>本轮实际 / 设计范围</th><th>含义</th></tr>
<tr><td>坐包</td><td>约 1033×898×'''+f'{seatheight:.0f}'+''' mm；底部 z=285 mm，中心顶部约 491 mm</td><td>侧围与冠部重建；尺寸为定制试验，非采购规格</td></tr>
<tr><td>背包</td><td>展开板片 1027×365 mm；带中央填充鼓起和后倾</td><td>与 V5 的 296 mm 旧板片高度不同；保留实际形体，不压回旧厚度</td></tr>
<tr><td>总高</td><td>约 '''+f'{height:.0f}'+''' mm，较旧 700 mm 增加约 '''+f'{conflict:.0f}'+''' mm</td><td>图册类似木框沙发约 800–820 mm；尚未确认本户最终产品和摆位</td></tr>
<tr><td>支撑</td><td>背包与坐包最低间距约 0.8 mm；坐包底部与木承托接触</td><td>静态接触检查通过，填充承载和舒适度未认证</td></tr></table>
<p>当前坐面未受压的最高点约 491 mm，比 V5 的约 440 mm 高约 51 mm；采用前需结合真实坐高、受压状态与木架尺寸一起确定。</p>
<h2>原生布艺近景与剩余问题</h2>'''+card('native-fabric','V6 布艺、侧围与缝口 · 原生裁图')+'''
<p>当前坐包比 V5 更有体积、背包更圆润，但座包仍偏规整；织纹、松弛外套与真实受压细节是否接近目标，仍由人工评审。
本版没有使用原生笔刷来完成雕刻：后台笔刷执行崩溃后，使用可编辑板片曲面与沿缝口的局部静态塑形。没有将工具失败包装为成功。</p>
<p>独立重开验证：两个软包闭合、无零长边 / 小碎面、正体积；坐包 / 背包和背架均无三角面穿插。
九项模型 / 建筑 Ground Truth / 图册哈希保持；18 张贴图打包，无缺失。六张 1500×1200 实渲采用 Cycles / Metal / 64 samples / OIDN High Accurate；灰材质六张 1000×800。
旧模型、失败候选和原图保留，未运行 Image2 或全屋队列。</p>
<p>下一步先判断这一组的松软形体是否明显改善，再决定是否调整本户沙发高度 / 内部尺寸和推广其它模块。当前不自动写回客厅或全屋。</p></main></html>'''
(OUT/'review_gallery.html').write_text(page)
(OUT/'WEB_ARTIFACTS.json').write_text(json.dumps({'status':'HUMAN_REVIEW','records':records},indent=2)+'\n')
sheet=Image.new('RGB',(1500,840),'#f3f0e8');d=ImageDraw.Draw(sheet)
for i,(family,camera) in enumerate([(f,c) for f in ['V5','V6'] for c in labels]):
    im=Image.open(OUT/('detail_fabric_'+family+'_'+camera+'.jpg'));im.thumbnail((480,375));x=i%3*500+(500-im.width)//2;y=i//3*420+28;sheet.paste(im,(x,y));d.text((i%3*500+8,i//3*420+8),family+' '+camera,fill='#222222')
sheet.save(SRC/'PILOT_REVIEW_CONTACT.jpg',quality=84)
print(OUT/'review_gallery.html')
