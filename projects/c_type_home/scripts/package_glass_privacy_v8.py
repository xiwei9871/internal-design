"""Publish lightweight glass/privacy review evidence without overwriting old versions."""
import json,html,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];D=R/'design/glass_privacy_v8'
a=json.loads((D/'BUILD_AUDIT.json').read_text());v=json.loads((D/'VERIFICATION.json').read_text())
assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==v['sha256']
O=R/'renders/whole_house_final_study_v1/glass_privacy_v8';O.mkdir(exist_ok=True)
assert not (O/'review_gallery.html').exists()
for n in ['living','master_bath','secondary_bath','guest_bath','guest_balcony']:
    im=Image.open(D/'review_final'/(n+'.png')).convert('RGB')
    im.thumbnail((1600,900));im.save(O/(n+'.jpg'),quality=88)
im=Image.open(R/'design/pale_ash_review_v7/review_final/after_living.png').convert('RGB')
im.thumbnail((1600,900));im.save(O/'living_v7.jpg',quality=88)
sheet=Image.new('RGB',(1500,900),'#eee8dc');draw=ImageDraw.Draw(sheet)
for i,(n,label) in enumerate([('master_bath','Master bath: frosted shower / timber entry'),('secondary_bath','Secondary bath: frosted shower + slider'),('guest_bath','Guest bath: frosted shower / timber entry'),('guest_balcony','Guest bedroom -> north balcony: frosted double slider')]):
    im=Image.open(O/(n+'.jpg'));im.thumbnail((735,414));x=i%2*750;y=i//2*450;sheet.paste(im,(x,y+24));draw.text((x+8,y+5),label,fill='#302b25')
sheet.save(D/'PRIVACY_CONTACT.jpg',quality=85)
cards=[]
for title,images in [('普通玻璃：同机位V7 / V8',['living_v7','living']),('主卫与次主卫',['master_bath','secondary_bath']),('客卫与客房阳台门',['guest_bath','guest_balcony'])]:
    cards.append('<section><h2>'+title+'</h2><div class="pair">'+''.join('<figure><figcaption>'+n+'</figcaption><img src="'+n+'.jpg"></figure>' for n in images)+'</div></section>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type 透明与磨砂玻璃 V8</title><style>body{font:16px/1.7 system-ui;background:#f3efe7;color:#302b25;margin:0}main{max-width:1600px;padding:24px;margin:auto}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0}img{width:100%;border-radius:7px}section{padding:20px 0;border-top:1px solid #d4c7b3}td,th{padding:10px;text-align:left;border-bottom:1px solid #d4c7b3}.note{background:#fff0d3;padding:15px}code{overflow-wrap:anywhere}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style><main><h1>C-Type · 透明 / 隐私磨砂玻璃 V8</h1><p>按你确认的用途分类，沿用V7浅白蜡木、家具、门框与去顶查看模式。</p><table><tr><th>位置</th><th>采用</th></tr><tr><td>普通采光窗、非隐私区玻璃门</td><td>无色透明玻璃</td></tr><tr><td>三个卫生间淋浴玻璃</td><td>无色磨砂玻璃</td></tr><tr><td>次主卫推拉门</td><td>磨砂玻璃</td></tr><tr><td>客房通北阳台双扇推拉门</td><td>磨砂玻璃（已确认是客房门）</td></tr><tr><td>主卫、客卫入口</td><td>保留木门</td></tr></table><p class="note">透明玻璃的底色已统一为无色，不加茶色/墨色吸收；深色或茶色景物的反射仍可能让某些角度看起来偏暗。室外环境保持V7，以便比较本轮材质。磨砂散射光线，近距离贴近玻璃或夜间强背光时仍可能见轮廓，实际采购需看样品。</p>'''
page+=''.join(cards)
page+='<section><h2>模型与检查</h2><p>'+html.escape(a['output'])+'<br>SHA256 <code>'+a['sha256']+'</code></p>'
page+='''<p>31个非隐私玻璃物件为透明、16个隐私玻璃物件为磨砂。原有物件网格、位置和渲染可见性保持；主卫/客卫木门、深色家电舱门和灯罩保持。16保护源哈希保持；天花450mm高差与查看模式保持。没有使用Image2，当前外观待人工评审。</p><details><summary>渲染与材质记录</summary><p>5张实际Cycles1600×900、96samples、MetalGPU / OIDNHighAccurate；V7客厅对照图复用同相机1600×900、128samples。无色BaseColor1、Metallic0、Transmission1、IOR1.45，透明roughness.015，磨砂.68；窗玻璃沿用V7已验证的shadow-ray采光近似，camera/reflection仍为正常透明/磨砂表面；这是表现材质，不能代替玻璃产品隐私测试。</p></details><p><a href="verification.json">核验记录</a> · <a href="../pale_ash_review_v7/review_gallery.html">返回V7</a></p></section></main></html>'''
(O/'review_gallery.html').write_text(page);(O/'verification.json').write_text(json.dumps(v,indent=2)+'\n')
print('GLASS_PRIVACY_GALLERY',str(O/'review_gallery.html'))
