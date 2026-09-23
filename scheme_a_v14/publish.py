"""Assemble a review package only after every view and CAD sheet is version-consistent."""
from pathlib import Path
import json
import hashlib
import shutil
import html
import sys
import importlib.metadata
import numpy as np
from PIL import Image
import OpenEXR
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from design_model import design_hash
from scheme_a_v14.validate import validate
KEYS={'living':'客餐厅','kitchen':'厨房与服务墙','master':'主卧','child':'儿童房','elder':'老人房','main_bath':'主卫','secondary_bath':'次卫'}
DEST=ROOT.parent/'deliverables/v14'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def extract_passes(path,out,key):
    f=OpenEXR.File(str(path)); parts={p.name():p for p in f.parts}
    expected=['ViewLayer.Depth','ViewLayer.Normal','ViewLayer.CryptoObject00','ViewLayer.CryptoMaterial00']
    if any(k not in parts for k in expected): raise ValueError('Required EXR passes missing: '+str(path))
    depth=next(iter(parts['ViewLayer.Depth'].channels.values())).pixels.astype(np.float32)
    normal=np.stack([parts['ViewLayer.Normal'].channels['ViewLayer.Normal.'+k].pixels for k in 'XYZ'],axis=-1).astype(np.float32)
    valid=np.isfinite(depth)&(depth<1e6)&(depth>0)
    distance=np.where(valid,np.minimum(depth,15)/15,1)
    Image.fromarray((distance*65535).astype(np.uint16)).save(out/f'{key}_depth.png')
    Image.fromarray(np.clip((normal*.5+.5)*255,0,255).astype(np.uint8)).save(out/f'{key}_normal.png')
    edge=np.zeros(depth.shape,dtype=bool)
    edge[:,1:] |= (np.abs(distance[:,1:]-distance[:,:-1])>.015)|(np.linalg.norm(normal[:,1:]-normal[:,:-1],axis=2)>.35)
    edge[1:,:] |= (np.abs(distance[1:,:]-distance[:-1,:])>.015)|(np.linalg.norm(normal[1:,:]-normal[:-1,:],axis=2)>.35)
    Image.fromarray(np.where(edge,0,255).astype(np.uint8)).save(out/f'{key}_surface_edges.png')
    return {'parts':list(parts),'depth_range_m':[float(depth[valid].min()),float(depth[valid].max())] if valid.any() else [],'geometry_pass_note':'First visible surface; glass transmission and mirrors need manual semantic review. Workbench is schematic only.'}

def main():
    result=validate()
    if result['issues']: raise ValueError(result['issues'])
    cad=json.loads((DEST/'cad/manifest.json').read_text())
    if cad['design_sha256']!=design_hash(): raise ValueError('Stale CAD package')
    sys.path.insert(0,str(ROOT.parent/'construction'))
    from build_all import verify_package
    verify_package()
    scene=json.loads((ROOT/'scene_manifest.json').read_text())
    if scene['build_script_sha256']!=sha(ROOT/'build_scene.py'): raise ValueError('Rebuild scene after generator edit')
    images=DEST/'images'; images.mkdir(parents=True,exist_ok=True)
    passes=ROOT/'passes'; passes.mkdir(exist_ok=True)
    rows=[]
    for key,label in KEYS.items():
        meta=json.loads((ROOT/'renders'/f'{key}.json').read_text())
        if meta['design_sha256']!=design_hash() or meta['build_script_sha256']!=scene['build_script_sha256']: raise ValueError('Stale view '+key)
        png=ROOT/'renders'/f'{key}.png'
        if sha(png)!=meta['sha256']: raise ValueError('PNG changed after render '+key)
        exr=ROOT/'renders'/f'{key}_passes.exr'
        info=extract_passes(exr,passes,key)
        shutil.copy2(png,images/f'{key}.png')
        shutil.copy2(ROOT.parent/'scheme_a_v13'/f'realfurn_{key}.png',images/f'{key}_before.png')
        rows.append(dict(meta,label=label,passes=info,exr_sha256=sha(exr),before_sha256=sha(images/f'{key}_before.png'),camera_parameters=scene['camera_anchors'][key]))
    release={'revision':'A14-20260918','design_sha256':design_hash(),'scene':scene,'views':rows,'validation':result,'cad_manifest':cad,'client_approval':'pending_review','ai_generation_used':False,'notes':['Current images are direct physical renders from approved layout; appearance update requires client review.','Site measurements, product SKUs and MEP coordination remain pending.']}
    release['cad_file_sha256']={p.name:sha(p) for p in sorted((DEST/'cad').iterdir()) if p.suffix in ['.pdf','.dxf']}
    release['optional_surface_experiments']={p.stem:json.loads(p.read_text()) for p in (ROOT/'surface_edits').glob('*_status.json')}
    release['dependencies']={p:importlib.metadata.version(p) for p in ['ezdxf','numpy','scipy','Pillow','shapely','matplotlib','PyMuPDF','OpenEXR']}
    (DEST/'release_manifest.json').write_text(json.dumps(release,ensure_ascii=False,indent=2))
    sections=[]
    for key,label in KEYS.items():
        if key=='main_bath':
            sections.append(f'''<section id="{key}"><div class="section-head"><span class="num">06</span><h2>{label}</h2><a href="images/{key}.png" target="_blank">查看原图 ↗</a></div><p>主卫机位移入门内以避开打开的门扇；以下并列查看，不作像素对齐比较。</p><div class="bath-pair"><figure><img src="images/{key}_before.png" alt="原主卫底图"><figcaption>原机位</figcaption></figure><figure><img src="images/{key}.png" alt="新版主卫"><figcaption>A14 · 修正机位</figcaption></figure></div></section>''')
            continue
        sections.append(f'''<section id="{key}"><div class="section-head"><span class="num">{list(KEYS).index(key)+1:02}</span><h2>{label}</h2><a href="images/{key}.png" target="_blank">查看原图 ↗</a></div>
<div class="compare"><img src="images/{key}.png" alt="新版{label}"><div class="before"><img src="images/{key}_before.png" alt="原底图{label}"></div><span class="old-tag">原底图</span><span class="new-tag">A14 · 同模渲染</span><div class="divider"></div></div><label class="slider-label">拖动比较<input type="range" min="0" max="100" value="35" aria-label="{label}前后对比"></label></section>''')
    links=''.join(f'<a href="#{k}">{v}</a>' for k,v in KEYS.items())
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>学道街44号 · A14 方案复核</title><style>
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f3f0e9;color:#282c29;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}header,main{max-width:1280px;margin:auto;padding:48px 48px 16px}small,.eyebrow{letter-spacing:3px;font-size:12px;color:#627264}h1{font-size:42px;letter-spacing:-1px;margin:18px 0}p{line-height:1.8;color:#646860;max-width:900px}.toolbar{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}.button{background:#344b3f;color:#fff;padding:14px 20px;border-radius:4px;text-decoration:none}.button.secondary{background:#e1e5db;color:#344b3f}nav{position:sticky;top:0;background:#f3f0e9f2;backdrop-filter:blur(10px);z-index:5;display:flex;gap:24px;flex-wrap:wrap;padding:18px 48px;border-top:1px solid #d9d9cf;border-bottom:1px solid #d9d9cf;justify-content:center}nav a{font-size:14px;color:#3d4a40;text-decoration:none}section{margin:24px 0 64px;scroll-margin-top:100px}.section-head{display:flex;align-items:center;gap:18px;margin-bottom:20px}.section-head h2{font-weight:500;font-size:26px;margin:0}.section-head a{margin-left:auto;color:#526653;font-size:13px}.num{color:#8b998b;font-size:15px}.compare{position:relative;aspect-ratio:2500/1727;background:#e5e4df;overflow:hidden}.compare>img,.before img{width:100%;height:100%;object-fit:cover;display:block}.before{position:absolute;inset:0;clip-path:inset(0 65% 0 0)}.divider{position:absolute;left:35%;top:0;bottom:0;border-left:2px solid #fff}.old-tag,.new-tag{position:absolute;top:20px;padding:8px 12px;background:#fffD;font-size:12px}.old-tag{left:20px}.new-tag{right:20px}.slider-label{display:flex;align-items:center;gap:24px;margin-top:12px;color:#697567;font-size:12px}input{flex:1;accent-color:#526d58}.notes{background:#e6e9e0;padding:28px 32px;border-radius:4px;margin-bottom:40px}.notes h2{font-size:20px;font-weight:500}.notes li{line-height:1.9;font-size:14px;color:#505c50}footer{padding:24px 0 60px;font-size:12px;color:#788173}a{color:#385a43}@media(max-width:700px){header,main{padding:28px 18px 12px}h1{font-size:30px}nav{padding:14px 18px;gap:14px}.section-head h2{font-size:21px}.old-tag,.new-tag{top:10px;font-size:10px;padding:5px}.old-tag{left:10px}.new-tag{right:10px}}
</style><header><div class="eyebrow">XUEDAO STREET 44 · DESIGN REVIEW</div><h1>统一尺寸，让图纸与空间对应。</h1><p>A14 方案复核版。保留已确认的功能布局，统一门型、柜体与设备尺寸，更新 CAD 图面和七个固定视角的材质、光线。以下可直接比较原底图与新版效果。</p><div class="toolbar"><a class="button" href="cad/学道街44号_v14_设计协调图册_A2.pdf" target="_blank">打开 10 页 CAD 图册</a><a class="button secondary" href="更新说明.md">查看更新与待核实事项</a></div></header><nav>''' + links + '</nav><main>' + ''.join(sections) + '''<div class="notes"><h2>本轮复核重点</h2><ul><li>次卫采用推拉门表达；门袋位置与墙体条件仍需现场确认。</li><li>儿童窗边低书柜统一为 1100 mm；服务墙按冰箱、蒸烤、洗烘三列建模。</li><li>厨房窗台、台面及窗边界存在待复尺关系，详见 CAD 图册说明。</li><li>本轮效果图为方案复核图；产品型号、机电点位和施工节点仍需深化。</li></ul></div><footer>学道街44号 · A14 · 2026.09.18　<a href="release_manifest.json">版本与检查记录</a></footer></main><script>document.querySelectorAll('section').forEach(s=>{const r=s.querySelector('input');r.addEventListener('input',()=>{s.querySelector('.before').style.clipPath=`inset(0 ${100-r.value}% 0 0)`;s.querySelector('.divider').style.left=r.value+'%';});});</script></html>'''
    page=page.replace('</style>','.bath-pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}.bath-pair figure{margin:0}.bath-pair img{width:100%;display:block}.bath-pair figcaption{font-size:12px;color:#697567;padding:12px 0}@media(max-width:700px){.bath-pair{grid-template-columns:1fr}}</style>')
    page=page.replace("const r=s.querySelector('input');r.addEventListener", "const r=s.querySelector('input');if(!r)return;r.addEventListener")
    (DEST/'index.html').write_text(page,encoding='utf-8')
    print('PUBLISHED_REVIEW_PACKAGE',len(rows),'views',DEST/'index.html')

if __name__=='__main__': main()
