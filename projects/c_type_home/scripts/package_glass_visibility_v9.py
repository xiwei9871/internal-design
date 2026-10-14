"""Before/after evidence for actual viewport refraction and exterior readability."""
import json,hashlib,html
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];D=R/'design/glass_visibility_v9'
a=json.loads((D/'BUILD_AUDIT.json').read_text());v=json.loads((D/'VERIFICATION.json').read_text())
assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==v['sha256']
O=R/'renders/whole_house_final_study_v1/glass_visibility_v9';O.mkdir(exist_ok=True)
assert not (O/'review_gallery.html').exists()
sources={'living_before':R/'design/glass_privacy_v8/review_final/living.png','living_after':D/'review/living.png','bedroom_after':D/'review/bedroom.png','privacy_after':D/'review/privacy.png','viewport_before':D/'eevee_trace_off.png','viewport_after':D/'review/viewport_check.png','no_glass_control':D/'no_clear_glass.png'}
for n,p in sources.items():
    im=Image.open(p).convert('RGB');im.thumbnail((1600,900));im.save(O/(n+'.jpg'),quality=88)
sheet=Image.new('RGB',(1500,910),'#eee8dc');draw=ImageDraw.Draw(sheet)
for i,(n,label) in enumerate([('viewport_before','Before: EEVEE transmission unavailable'),('viewport_after','After: raytraced transmission reveals the room'),('living_before','Before: dark exterior / dominant reflection'),('living_after','After: exterior exposure calibrated')]):
    im=Image.open(O/(n+'.jpg'));im.thumbnail((735,414));x=i%2*750;y=i//2*455;sheet.paste(im,(x,y+24));draw.text((x+8,y+5),label,fill='#302b25')
sheet.save(D/'FINAL_COMPARE.jpg',quality=85)
cards=[]
for title,ns in [('查看模式：同森林环境、同窗口、同机位',['viewport_before','viewport_after']),('最终渲染：客厅同机位前后',['living_before','living_after']),('普通卧室窗与保留的隐私磨砂门',['bedroom_after','privacy_after'])]:
    cards.append('<section><h2>'+title+'</h2><div class="pair">'+''.join('<figure><figcaption>'+n+'</figcaption><img src="'+n+'.jpg"></figure>' for n in ns)+'</div></section>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type 玻璃可见性修正 V9</title><style>body{margin:0;background:#f3efe7;color:#302b25;font:16px/1.7 system-ui}main{max-width:1600px;margin:auto;padding:24px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0}img{width:100%;border-radius:7px}section{border-top:1px solid #d8cabb;padding:20px 0}.note{background:#fff0d3;padding:15px}code{overflow-wrap:anywhere}@media(max-width:780px){.pair{grid-template-columns:1fr}}</style><main><h1>C-Type · 玻璃可见性修正 V9</h1><p>上一版玻璃表面虽设为无色，查看模式与摄影背景仍有问题。这次分别修正EEVEE透射和过暗的窗外背景，保留真正的玻璃反射、全部尺寸及隐私区磨砂分类。</p><p class="note">请打开下方新的V9模型：已保存场景光线追踪＋玻璃材质折射开关，默认仍为去顶查看模式。旧V8文件的查看设置不会随网页更新。</p>'''
page+=''.join(cards)
page+='''<section><h2>改了什么</h2><p>查看模式原先使用forest.exr但光线追踪关闭。这里的外侧窗口对照用相同森林环境模拟Material Preview：关闭时是黑色环境反射，开启后可见沙发、地毯和台阶。这是实际EEVEE渲染对照，不是从用户电脑截取的UI画面。</p><p>Cycles中窗外的独立显示/透射曝光原先过低，使室内倒影压过外景；已校准这部分背景曝光，原有室内灯能量和环境漫射光保持。外景仍是已登记的示意HDRI，并非现场照片。没有用删除玻璃、IOR设1或取消全部反射来伪装透明。</p><details><summary>无玻璃诊断对照与技术记录</summary><p>移除普通玻璃后的控制图：室外仍暗，室内反射消失。窗口中心射线只命中一块8mm玻璃，闭合网格/法线检查未发现本窗口重复叠片。此诊断图不用于交付模型。</p><img src="no_glass_control.jpg"><p>普通玻璃与磨砂的V8表面参数保持；EEVEE光线追踪SCREEN、use_raytrace_refraction、SLAB8mm预览厚度近似开启。Cycles按原真实几何厚度渲染。可见/透射外景强度0.6→3.6，漫射背景0.22保持。3张Cycles1600×900/96samples；EEVEE同视角查看对照。0Image2。</p></details></section><section><h2>模型与核验</h2><p>'''
page+=html.escape(a['output'])+'<br>SHA256 <code>'+a['sha256']+'</code></p>'
page+='''<p>3473个原对象网格、位置、材质槽和可见性保持；原灯能量、家具尺寸、天花450mm高差保持。16处隐私磨砂分类、木门及黑色家电舱门保持。旧V8与全部控制图保留，当前外观待人工评审。</p><p><a href="verification.json">核验记录</a> · <a href="../glass_privacy_v8/review_gallery.html">返回V8</a></p></section></main></html>'''
(O/'review_gallery.html').write_text(page);(O/'verification.json').write_text(json.dumps(v,indent=2)+'\n')
print('V9_GALLERY',str(O/'review_gallery.html'))
