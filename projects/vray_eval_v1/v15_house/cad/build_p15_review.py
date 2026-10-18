#!/usr/bin/env python3
"""P1.5 审图包: 差异叠加 + 4处局部图 + 异常清单页 → review_packages/P1_5/."""
import json
from pathlib import Path
import ezdxf, matplotlib
matplotlib.use('Agg'); matplotlib.rcParams['font.family']='Heiti TC'
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
from shapely.geometry import Polygon

CAD = Path(__file__).resolve().parent
OUT = CAD/'review_packages'/'P1_5'; OUT.mkdir(parents=True, exist_ok=True)
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())
NC  = json.loads((CAD/'derived'/'new_construction_v1.json').read_text())
REG = json.loads((CAD/'derived'/'wall_state_registry.json').read_text())

def role(o):
    for e in REG['entries']:
        if e['object']==o: return e['a102_role']
    return None

def draw_spec(ax, m, nc_row=None):
    st = m['design_status']
    col = {'EXISTING_RETAINED':'#111','EXISTING_DEMOLISHED':'#e22',
           'PROPOSED_NEW':'#24c','UNVERIFIED':'#f90',
           'DESIGN_REVIEW_PENDING':'#f90'}.get(st,'#888')
    lw = 1.8 if m['source']=='fcstd' else 1.2
    for p in m['parts']:
        ax.add_patch(MP(p['exterior'],closed=True,fill=False,edgecolor=col,lw=lw))
    for p in m.get('demolished_parts',[]):
        ax.add_patch(MP(p,closed=True,facecolor='#e22',alpha=.25,edgecolor='#e22',lw=1.2))

# --- 叠加图: 现状(黑/红/橙) + 实际新建(蓝) ---
fig,ax = plt.subplots(figsize=(17,17))
for m in GEO['managed_entities']:
    draw_spec(ax,m)
# 实际新建差集段 (蓝, 粗)
for r in NC['rows']:
    for pts in r['new_geoms']:
        ax.add_patch(MP(pts,closed=True,fill=False,edgecolor='#05c',lw=2.0))
ax.set_aspect('equal'); ax.autoscale(); ax.set_axis_off()
ax.set_title('P1.5 叠加: 黑=保留 红=拟拆(设计确认) 蓝=实际新建 橙=待裁 — N_BAL HOLD',fontsize=13)
fig.savefig(OUT/'overlay_a102a103.png',dpi=150,bbox_inches='tight',facecolor='white')
plt.close(fig)

# --- 4 局部图 ---
CROPS = {
 'crop1_kitchen':   (5200,7200,1400,4300,'厨房: X5800拆除段(红) + 门洞 + 残墙'),
 'crop2_bath2':     (8500,12000,5400,8400,'次卫/旧衣帽间: CLK橙(待裁) + 新隔墙蓝'),
 'crop3_nbalc':     (7400,13400,12400,14200,'北阳台: 品红=N_BAL HOLD 蓝=封窗新墙'),
 'crop4_step':      (7000,9600,3600,6200,'错层台阶: 蓝波浪台阶 + 红拆段 + 周边'),
}
for name,(x0,x1,y0,y1,title) in CROPS.items():
    fig,ax=plt.subplots(figsize=(13,11))
    for m in GEO['managed_entities']:
        draw_spec(ax,m)
    for r in NC['rows']:
        for pts in r['new_geoms']:
            ax.add_patch(MP(pts,closed=True,fill=False,edgecolor='#05c',lw=2.2))
    # 标注该窗内对象
    for m in GEO['managed_entities']:
        for p in m['parts']:
            g=Polygon(p['exterior']); bx=g.bounds
            cx,cy=(bx[0]+bx[2])/2,(bx[1]+bx[3])/2
            if x0<=cx<=x1 and y0<=cy<=y1:
                st=m['design_status']
                tag={'EXISTING_RETAINED':'保留','EXISTING_DEMOLISHED':'拟拆',
                     'PROPOSED_NEW':'新建','UNVERIFIED':'待裁',
                     'DESIGN_REVIEW_PENDING':'待裁'}.get(st,st)
                ax.annotate(tag,(cx,cy),fontsize=8,color='#555',ha='center')
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal')
    ax.grid(alpha=.2); ax.set_title(title,fontsize=11)
    fig.savefig(OUT/f'{name}.png',dpi=150,bbox_inches='tight',facecolor='white')
    plt.close(fig)

# --- 异常/待核实清单页 ---
reg = json.loads((CAD/'derived'/'wall_state_registry.json').read_text())
lines = ['P1.5 异常与专业待核实清单','='*40,'']
lines.append('■ DEMOLITION_HOLD (实施待批):')
for e in reg['entries']:
    if e['a102_role']=='DEMOLITION_HOLD':
        lines.append(f"  {e['object']}  bbox={e['bbox']}  {e['note']}")
lines.append(''); lines.append('■ PENDING_REVIEW (设计待裁):')
for e in reg['entries']:
    if e['a102_role']=='PENDING_REVIEW':
        lines.append(f"  {e['object']}  bbox={e['bbox']}")
lines.append(''); lines.append('■ 拟建与结构层重叠待核实 (UNVERIFIED_STRUCT_OVERLAP):')
for e in reg['entries']:
    if e.get('overlap_class'):
        lines.append(f"  {e['object']}  {e['overlap_class']} ratio={e['struct_ratio']}")
lines.append(''); lines.append('■ CLASSIFICATION_UNVERIFIED (映射不到开发商黑白语义):')
for e in reg['entries']:
    if e['classification']=='CLASSIFICATION_UNVERIFIED':
        lines.append(f"  {e['object']}  {e['a102_role']}")
lines.append(''); lines.append('■ 专业HOLD(不变): 结构核验 / 现场复尺 / 封窗合规 / 专业编辑器打印')
fig,ax=plt.subplots(figsize=(14,18)); ax.set_axis_off()
ax.text(0.02,0.98,'\n'.join(lines),family='Heiti TC',fontsize=8.5,va='top')
fig.savefig(OUT/'anomaly_list.png',dpi=140,bbox_inches='tight',facecolor='white')
print('review pack ->', OUT)
