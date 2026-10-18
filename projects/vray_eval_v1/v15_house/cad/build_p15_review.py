#!/usr/bin/env python3
"""P1.5.1-C 审图包: 全部从最终 DXF 直读生成(不再从JSON平行重绘).
每张图标题含 DXF sha256 短码, 与生成文件一一对应.
→ review_packages/P1_5_1/."""
import json, hashlib
from pathlib import Path
import ezdxf, matplotlib
matplotlib.use('Agg'); matplotlib.rcParams['font.family']='Heiti TC'
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
from shapely.geometry import Polygon

CAD = Path(__file__).resolve().parent
OUT = CAD/'review_packages'/'P1_5_1'; OUT.mkdir(parents=True, exist_ok=True)
F102 = CAD/'A102_WALL_DIFF_POC_V3.dxf'
F103 = CAD/'A103_CONSTRUCTION_POC_V7.dxf'
SHA = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:10] for p in (F102,F103)}

ACI = {1:'#e22',2:'#cc0',3:'#0b0',4:'#0cc',5:'#24c',6:'#c0c',7:'#111',
       8:'#888',9:'#bbb',30:'#f80',140:'#c00',250:'#666'}

def ents(path):
    doc = ezdxf.readfile(path)
    frozen = {l.dxf.name for l in doc.layers if l.dxf.flags & 1}
    rows = []
    for e in doc.modelspace():
        lay = e.dxf.layer
        if lay in frozen: continue
        if e.dxftype() == 'LWPOLYLINE':
            pts = [(p[0],p[1]) for p in e.get_points('xy')]
            if len(pts) < 2: continue
            lc = doc.layers.get(lay).dxf.color if lay in doc.layers else 7
            rows.append((lay, pts, ACI.get(lc,'#444')))
        elif e.dxftype() in ('TEXT','MTEXT'):
            try: txt = e.dxf.text[:14]
            except Exception: txt = ''
            try: ins = tuple(e.dxf.insert)[:2]
            except Exception: ins = None
            if ins and txt.strip(): rows.append((lay, ins, txt))
    return rows

def draw(ax, rows, title):
    for lay, pts, c in rows:
        if isinstance(pts, tuple):
            ax.annotate(pts if False else '', pts); continue
    for lay, item, extra in rows:
        if isinstance(item, tuple) and isinstance(extra, str):   # TEXT
            ax.annotate(extra, item, fontsize=7, color='#345')
        else:
            pts, c = item, extra
            ax.add_patch(MP(pts, closed=True, fill=False, edgecolor=c,
                            lw=0.9 if lay in ('A-FURN','A-FIXT','A-SOFFIT','A-STAIR') else 1.4))
    ax.set_aspect('equal'); ax.autoscale(); ax.set_axis_off()
    ax.set_title(title, fontsize=11)

r102, r103 = ents(F102), ents(F103)

# 1) 全图各一张
for rows, name, tag in ((r102,'a102_full','A102 拆改图'),(r103,'a103_full','A103 平面图')):
    fig,ax = plt.subplots(figsize=(17,17))
    draw(ax, rows, f'{tag} | {name} sha:{SHA["A102_WALL_DIFF_POC_V3.dxf" if "102" in name else "A103_CONSTRUCTION_POC_V7.dxf"]}')
    fig.savefig(OUT/f'{name}.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)

# 2) 叠加: A103可见墙(黑/蓝按层) + A102拆除红/品红HOLD + 冻结不画
fig,ax = plt.subplots(figsize=(17,17))
for lay, item, extra in r103:
    if isinstance(item, tuple): continue
    ax.add_patch(MP(item, closed=True, fill=False, edgecolor=extra, lw=1.1))
for lay, item, extra in r102:
    if isinstance(item, tuple): continue
    if lay == 'A-WALL-DEMO-DESIGN':
        ax.add_patch(MP(item, closed=True, fill=False, edgecolor='#e22', lw=2.0))
    elif lay == 'A-WALL-HOLD':
        ax.add_patch(MP(item, closed=True, fill=False, edgecolor='#c0c', lw=2.0))
ax.set_aspect('equal'); ax.autoscale(); ax.set_axis_off()
ax.set_title(f'P1.5.1叠加: A103全色底 + A102红=拟拆/品红=HOLD | sha102:{SHA[F102.name]} sha103:{SHA[F103.name]}',fontsize=11)
fig.savefig(OUT/'overlay_a102a103.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)

# 3) 四局部 (A103为准, 叠加A102拆除/HOLD)
CROPS = {
 'crop1_kitchen':   (5200,7200,1400,4300,'厨房: X5800拆除段+新隔墙+门洞'),
 'crop2_bath2':     (8500,12000,5400,8400,'次卫/衣帽间: 待裁墙+新隔墙+门洞'),
 'crop3_nbalc':     (7400,13400,12400,14200,'北阳台: 品红HOLD+封窗新墙+上部构件'),
 'crop4_step':      (7000,9600,3600,6200,'错层: 台阶+拆除段+周边墙'),
}
for name,(x0,x1,y0,y1,title) in CROPS.items():
    fig,ax=plt.subplots(figsize=(13,11))
    for lay, item, extra in r103:
        if isinstance(item, tuple):
            if x0<=item[0]<=x1 and y0<=item[1]<=y1:
                ax.annotate(extra, item, fontsize=7, color='#345')
            continue
        ax.add_patch(MP(item, closed=True, fill=False, edgecolor=extra, lw=1.2))
    for lay, item, extra in r102:
        if isinstance(item, tuple): continue
        if lay == 'A-WALL-DEMO-DESIGN':
            ax.add_patch(MP(item, closed=True, fill=False, edgecolor='#e22', lw=2.0))
        elif lay == 'A-WALL-HOLD':
            ax.add_patch(MP(item, closed=True, fill=False, edgecolor='#c0c', lw=2.0))
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal')
    ax.grid(alpha=.2); ax.set_title(f'{title} | sha103:{SHA[F103.name]}', fontsize=10)
    fig.savefig(OUT/f'{name}.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)

# 4) 异常清单(数据源标注)
reg = json.loads((CAD/'derived'/'wall_state_registry.json').read_text())
lines = ['P1.5.1 异常与专业待核实清单','='*44,'']
lines.append('■ DEMOLITION_HOLD (实施待批):')
for e in reg['entries']:
    if e['a102_role']=='DEMOLITION_HOLD':
        lines.append(f"  {e['object']}  {e['note'][:60]}")
lines += ['', '■ PENDING_REVIEW (设计待裁):']
for e in reg['entries']:
    if e['a102_role']=='PENDING_REVIEW': lines.append(f"  {e['object']}")
lines += ['', '■ UNVERIFIED_STRUCT_OVERLAP (拟建骑结构层):']
for e in reg['entries']:
    if e.get('overlap_class'): lines.append(f"  {e['object']}  {e['overlap_class']}")
lines += ['', '■ CLASSIFICATION_UNVERIFIED:']
for e in reg['entries']:
    if e['classification']=='CLASSIFICATION_UNVERIFIED': lines.append(f"  {e['object']}  {e['a102_role']}")
lines += ['', '■ 专业HOLD(不变): 结构核验 / 现场复尺 / 封窗合规 / 专业CAD编辑器打印(NOT_RUN)',
          '', f"sha102:{SHA[F102.name]}  sha103:{SHA[F103.name]}"]
fig,ax=plt.subplots(figsize=(14,18)); ax.set_axis_off()
ax.text(0.02,0.98,'\n'.join(lines),family='Heiti TC',fontsize=8.5,va='top')
fig.savefig(OUT/'anomaly_list.png',dpi=140,bbox_inches='tight',facecolor='white')
print('review pack ->',OUT,'| sha:',SHA)
