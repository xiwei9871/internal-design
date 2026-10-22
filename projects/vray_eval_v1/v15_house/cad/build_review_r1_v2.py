#!/usr/bin/env python3
"""R1_BATH2_CLK V2 业主审图样张 — 单页裁决"""
import json
from pathlib import Path
import ezdxf, matplotlib
matplotlib.use('Agg'); matplotlib.rcParams['font.family']='Heiti TC'
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Rectangle, FancyArrow

CAD=Path(__file__).resolve().parent
PKG=CAD/'review_packages'/'P1_3_3'
ORIG=CAD.parents[3]/'projects/c_type_home/cad/C型_原始户型数字化基准图.dxf'
orig=ezdxf.readfile(ORIG)

# 颜色规范 (全程统一): 黑=现状保留 红=拟拆 蓝=新建 橙=待确认 灰=背景
C_RET='#111'; C_DEM='#e22'; C_NEW='#1a66cc'; C_PEN='#f58020'; C_BG='#c9c9c9'

# ---- 墙段定义 (mm) ----
CLK = {  # 旧衣帽间三面墙 (基准图标注为存疑)
 'N': dict(num='①',name='北侧旧墙',rect=(9050,6300,11400,6500)),
 'E': dict(num='②',name='东侧旧墙',rect=(11300,4500,11400,6300)),
 'W': dict(num='③',name='西侧旧墙',rect=(8950,4500,9050,6300)),
}
NEW = {  # 设计模型中的目标隔墙
 'N': dict(rect=(9200,6450,11400,6600),rel='错位替换 · 新墙整体北移约150mm, 西端缩进至x9200'),
 'E': dict(rect=(11400,4700,11600,6400),rel='错位外扩 · 新墙向东移, 位于旧墙外侧(加厚至200mm)'),
 'W': dict(rect=(9059,4507,9209,6507),rel='错位替换 · 新隔墙东移约110mm(含150mm墙厚)'),
 'S': dict(rect=(9988,4524,11400,4823),rel='新增 · 原衣帽间位置无南墙, 本次新建'),
}
R=(8400,12300,4000,7100)

def rect_pts(r): x0,y0,x1,y1=r; return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
def poly(ax,r,color,lw=1.6,fill=False,ls='-',z=3,alpha=1.0):
    ax.add_patch(MplPoly(rect_pts(r),closed=True,fill=fill,edgecolor=color,lw=lw,ls=ls,zorder=z,alpha=alpha))

fig=plt.figure(figsize=(16.5,11.7))
gs=fig.add_gridspec(3,3,height_ratios=[2.6,1.5,1.0],width_ratios=[1.25,1.0,1.0],
                  hspace=0.28,wspace=0.18)
fig.suptitle('次卫 / 原衣帽间隔墙裁决样张 V2  —  颜色统一: 黑=现状保留 红=拟拆 蓝=新建 橙=待确认(旧墙)',fontsize=13)

# ====== 左: 叠加对照图 ======
ax=fig.add_subplot(gs[0:2,0])
ax.set_title('① 原户型 + 目标设计 叠加  (橙=旧衣帽间墙, 蓝=目标新隔墙)',fontsize=10)
# 背景: 基准墙线(灰) + 房间
for e in orig.modelspace():
    if e.dxftype()!='LWPOLYLINE' or e.dxf.layer not in ('A-WALL','A-ROOM','A-DOOR'): continue
    pts=[(p[0],p[1]) for p in e.get_points('xy')]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    if max(xs)<R[0] or min(xs)>R[1] or max(ys)<R[2] or min(ys)>R[3]: continue
    ax.add_patch(MplPoly(pts,closed=True,fill=False,edgecolor=C_BG,lw=1.0,zorder=1))
# 周边保留墙 (黑)
for rr in [(12900,4630,13100,13600),(7800,4670,7900,13550),(9050,4450,12900,4650),(11400,6300,12100,6500)]:
    poly(ax,rr,C_RET,2.0,z=2)
# CLK 旧墙 橙色 + ①②③
for k,d in CLK.items():
    poly(ax,d['rect'],C_PEN,3.0,fill=True,z=4,alpha=0.55)
    x0,y0,x1,y1=d['rect']
    ax.text((x0+x1)/2,(y0+y1)/2,d['num'],fontsize=17,color='#c33',ha='center',va='center',
            zorder=10,fontweight='bold')
# 新隔墙 蓝
for k,d in NEW.items():
    poly(ax,d['rect'],C_NEW,2.2,z=5)
# 门洞(基准 D107 x8250-9000 侧)
poly(ax,(8250,4450,9000,4650),'#b60',1.2,z=3)
# 房间名
ax.text(10250,5550,'目标次卫',fontsize=12,color=C_NEW,ha='center',zorder=9)
ax.text(9600,6700,'走  廊',fontsize=9,color='#888',ha='center')
ax.text(7400,3800,'客  厅',fontsize=9,color='#888',ha='center')
ax.text(11800,5300,'书  房',fontsize=9,color='#888',ha='center',rotation=90)
ax.set_xlim(R[0],R[1]); ax.set_ylim(R[2],R[3]); ax.set_aspect('equal'); ax.set_axis_off()

# ====== 右上: 目标净墙轮廓 (无家具无ID) ======
ax2=fig.add_subplot(gs[0,1:])
ax2.set_title('② 目标次卫 — 净墙轮廓 (仅空间结构)',fontsize=10)
# 目标次卫房间外壳: 西9059-9209 北9200-11400/6450-6600 东11400-11600/4700-6400 南9988-11400/4524-4823
# + 西南角 L 形补充 (9059-9209 y4507-4524)
shell=[(9059,4507,9209,6507),(9200,6450,11400,6600),(11400,4700,11600,6400),(9988,4524,11400,4823)]
for rr in shell: poly(ax2,rr,C_RET,2.6,fill=True,z=3)
# 周边保留墙黑
for rr in [(12900,4630,13100,13600),(11400,6300,12100,6500),(9050,4450,12900,4650)]:
    poly(ax2,rr,C_RET,1.6,z=2)
# 门洞位置未定死 → 标注见A103, 不猜画
ax2.text(10250,4300,'门洞位置以A103为准',fontsize=8,ha='center',color='#a55')
# 净尺寸
ax2.annotate('',xy=(9209,4700),xytext=(9209,6400),
             arrowprops=dict(arrowstyle='<->',color='#0a0',lw=1.0))
ax2.text(9350,5550,'净深 ≈1700',fontsize=8,color='#0a0')
ax2.annotate('',xy=(9300,6400),xytext=(11300,6400),
             arrowprops=dict(arrowstyle='<->',color='#0a0',lw=1.0))
ax2.text(10300,6150,'净宽 ≈2000',fontsize=8,color='#0a0',ha='center')
ax2.text(10250,5550,'次  卫',fontsize=14,color='#333',ha='center',zorder=9)
ax2.text(10500,6800,'走  廊',fontsize=9,color='#999',ha='center')
ax2.set_xlim(8400,12300); ax2.set_ylim(4000,7100)
ax2.set_aspect('equal'); ax2.set_axis_off()

# ====== 右中: 三段旧墙逐一对比 ======
ax3=fig.add_subplot(gs[1,1:])
ax3.set_title('③ 每段旧墙: 原位置 vs 目标位置',fontsize=10)
ax3.axis('off')
rows=[('① 北侧旧墙','原: y6300-6500','新: y6450-6600 (北移~150)','错位替换'),
      ('② 东侧旧墙','原: x11300-11400','新: x11400-11600 (东移, 贴旧墙外)','外扩加厚'),
      ('③ 西侧旧墙','原: x8950-9050','新: x9059-9209 (东移~110)','错位替换')]
for i,(a,b,c,tag) in enumerate(rows):
    y=0.88-i*0.34
    ax3.text(0.02,y,a,fontsize=10,color=C_PEN,transform=ax3.transAxes,fontweight='bold')
    ax3.text(0.24,y,b,fontsize=9,transform=ax3.transAxes)
    ax3.text(0.52,y,c,fontsize=9,color=C_NEW,transform=ax3.transAxes)
    ax3.text(0.02,y-0.13,f'关系: {tag}',fontsize=9,color='#333',transform=ax3.transAxes)
# 南面补充
ax3.text(0.02,0.0,'另: 南侧新增隔墙(蓝色)——原衣帽间位置本无南墙, 非拆除项',
         fontsize=9,color=C_NEW,transform=ax3.transAxes)

# ====== 底部: 三个问题 ======
ax4=fig.add_subplot(gs[2,:]); ax4.axis('off')
ax4.set_title('业主裁决 (每段勾选一个, 或圈图说明)',fontsize=10,loc='left')
qs=[('① 北侧旧墙: ','A 拆除, 按新位置建新墙    B 保留原墙    C 部分拆除(注明范围)    D 无法判断'),
    ('② 东侧旧墙: ','A 拆除, 按新位置建加厚墙  B 保留原墙    C 部分拆除(注明范围)    D 无法判断'),
    ('③ 西侧旧墙: ','A 拆除, 按新位置建隔墙    B 保留原墙    C 部分拆除(注明范围)    D 无法判断')]
for i,(q,opts) in enumerate(qs):
    ax4.text(0.02,0.78-i*0.30,q,fontsize=10.5,transform=ax4.transAxes)
    ax4.text(0.20,0.78-i*0.30,opts,fontsize=9.5,transform=ax4.transAxes,color='#333')
ax4.text(0.02,0.02,'注: 次卫位于 +450mm 上层地面(错层), 新旧墙均为同层隔墙; 结构安全与现场复尺独立核实 —— 此处仅裁决设计意图',
         fontsize=8.5,color='#a00',transform=ax4.transAxes)
fig.savefig(PKG/'R1_BATH2_CLK_V2.png',dpi=170,bbox_inches='tight',facecolor='white')
print('saved R1_BATH2_CLK_V2.png')
