"""Create numbered kitchen review pictures, an index and a camera/footprint map."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon

OUT=Path(__file__).resolve().parent;SITE=OUT.parent;ROOT=SITE.parents[1]
manifest=json.loads((OUT/'RENDER_MANIFEST_FULL.json').read_text())
assert len(manifest)==9
font_path='/System/Library/Fonts/STHeiti Medium.ttc'
def font(size):return ImageFont.truetype(font_path,size)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
source=SITE/'B1_1_SITE_CORRECTED_V2.blend'
expected=manifest[0]['source_sha256'];assert digest(source)==expected

files=[];panels=[]
for v in manifest:
    raw=OUT/v['path'];im=Image.open(raw).convert('RGB');assert im.size==(2000,1500)
    w,h=im.size;page=Image.new('RGB',(w,h+170),'#f6f8f9');page.paste(im,(0,105));d=ImageDraw.Draw(page)
    d.text((30,14),f"{v['id']}  {v['name']}",font=font(35),fill='#263e4d')
    camera_info='轴测/俯视' if v['projection']=='ORTHO' else f"室内透视 · 视点高 {v['pos'][2]*1000:.0f} mm · {v['lens']} mm"
    d.text((30,62),f"Blender V2 模型检查 · {camera_info}",font=font(23),fill='#5a6b75')
    d.text((30,h+125),'审阅材质；墙体临时剖切，天花与玻璃面暂隐以观察柜体。原始 V2 模型保持不变。',font=font(22),fill='#5a6b75')
    destination=OUT/f"KITCHEN_{v['id']}_{v['slug']}.png";page.save(destination)
    files.append(dict(id=v['id'],name=v['name'],file=destination.name,raw_file=raw.name,
                      image_size=list(page.size),sha256=digest(destination)))
    small=page.copy();small.thumbnail((780,652));panel=Image.new('RGB',(800,670),'#f6f8f9');panel.paste(small,((800-small.width)//2,5));panels.append(panel)
sheet=Image.new('RGB',(2400,3*670+70),'#d8e1e7');d=ImageDraw.Draw(sheet)
d.text((24,17),'厨房多角度检查 · V2 · 01–09',font=font(34),fill='#2b4352')
for n,p in enumerate(panels):sheet.paste(p,((n%3)*800,70+(n//3)*670))
sheet.save(OUT/'KITCHEN_MULTIVIEW_CONTACT_SHEET.png')

# Plan-map uses frozen architecture bounds and current component bounds only.
plt.rcParams['font.sans-serif']=['Arial Unicode MS','Heiti TC','DejaVu Sans']
fig,ax=plt.subplots(figsize=(8.0,9.0));ax.set_facecolor('#e6f0f3')
snapshot=json.loads((ROOT/'design/blender_b1_1/SOURCE_SCENE_SNAPSHOT.json').read_text())['branch']['objects']
for o in snapshot:
    if not o['name'].startswith('W_wall_') or not o['bounds']:continue
    lo,hi=o['bounds']
    if hi[0]<4.65 or lo[0]>8.1 or hi[1]<-.3 or lo[1]>4.75:continue
    ax.add_patch(Rectangle((lo[0],lo[1]),hi[0]-lo[0],hi[1]-lo[1],facecolor='#79858c',edgecolor='#59666d',lw=.7))
reg=json.loads((SITE/'B1_1_SITE_ASSET_REGISTER.json').read_text())
selected=['K-FRIDGE','K-TALL-L','K-NARROW-OUTER-320','K-RUN-E','K-RUN-S','K-ISLAND-PDF-C','K-ISLAND-CONNECTOR','K-UTILITY-TALL-600']
for item in reg['items']:
    if item['source_name'] not in selected:continue
    lo,hi=item['target_bounds_m'];ax.add_patch(Rectangle((lo[0],lo[1]),hi[0]-lo[0],hi[1]-lo[1],facecolor='#c1d1d7',edgecolor='#56717f',lw=1.0))
    ax.text((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,item['source_name'].replace('K-','').replace('UTILITY-TALL-','CAB-'),
            fontsize=5.5,ha='center',va='center',color='#294350',rotation=90 if hi[1]-lo[1]>hi[0]-lo[0] else 0)
colors=['#be503c','#3e72ae','#518744','#9e6d28','#8763a8','#387f7f']
for index,v in enumerate([v for v in manifest if v['projection']=='PERSP']):
    pos=np.array(v['pos'][:2]);target=np.array(v['target'][:2]);delta=target-pos;delta/=np.linalg.norm(delta)
    phi=math.atan2(delta[1],delta[0]);half=math.atan(36/(2*v['lens']));rays=[]
    for a in [phi-half,phi+half]:rays.append(pos+1.0*np.array([math.cos(a),math.sin(a)]))
    ax.add_patch(Polygon([pos,*rays],closed=True,facecolor=colors[index],alpha=.07))
    ax.annotate('',xy=pos+delta*.52,xytext=pos,arrowprops=dict(arrowstyle='->',color=colors[index],lw=1.5))
    ax.scatter(*pos,s=36,color=colors[index],zorder=10)
    ax.text(pos[0]+.035,pos[1]+.065,v['id'],color=colors[index],fontsize=10,fontweight='bold')
ax.set_xlim(4.60,8.15);ax.set_ylim(-.30,4.85);ax.set_aspect('equal');ax.grid(alpha=.2)
ax.set_xlabel('CAD X / m');ax.set_ylabel('CAD Y / m');ax.set_title('Kitchen V2: camera 03–08 and component footprints')
fig.tight_layout();fig.savefig(OUT/'KITCHEN_REVIEW_CAMERA_MAP.png',dpi=180);plt.close(fig)

index='''# 厨房多角度检查 — V2

同一 V2 模型，9 张 Blender 检查渲染；原始渲染 2000 × 1500 px。室内视点、轴测和俯视均使用简单审阅材质。墙体临时剖切、天花和玻璃面暂隐用于观察柜体，未改动 V2 几何。

[九宫格总览](KITCHEN_MULTIVIEW_CONTACT_SHEET.png) · [室内相机位置](KITCHEN_REVIEW_CAMERA_MAP.png) · [Blender 相机文件](KITCHEN_REVIEW_CAMERA_SET.blend)

可按图片编号指出需要调整的部分。

| 编号 | 检查视角 |
|---|---|
'''
for item in files:index+=f"| {item['id']} | [{item['name']}]({item['file']}) |\n"
index+='\n渲染引擎：Blender Workbench；Blender 5.2.1 LTS；Standard 色彩管理；32 次抗锯齿采样。材质/墙体处理为检查显示设置。原始视图和完整参数见 `RENDER_MANIFEST_FULL.json`；相机与几何保存文件保持未剖切的原模型。\n'
(OUT/'KITCHEN_REVIEW_INDEX.md').write_text(index)
qa=dict(status='DELIVERED_FOR_HUMAN_REVIEW',view_count=len(files),raw_resolution=[2000,1500],
        source_V2_sha256=expected,source_V2_unchanged=digest(source)==expected,
        renderer='BLENDER_WORKBENCH',blender_version=manifest[0]['blender_version'],
        total_render_seconds=round(sum(v['duration_seconds'] for v in manifest),3),
        material_stage='REVIEW',source_geometry_modified=False,
        visual_inspection='PENDING_FINAL_CONTACT_SHEET_OPEN',images=files,
        generated_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat())
(OUT/'KITCHEN_MULTIVIEW_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
print(json.dumps({'view_count':len(files),'raw_resolution':[2000,1500],'total_render_seconds':qa['total_render_seconds'],
                  'contact_sheet':str(OUT/'KITCHEN_MULTIVIEW_CONTACT_SHEET.png')},ensure_ascii=False,indent=2))
