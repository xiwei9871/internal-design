#!/usr/bin/env python3
"""P0_STEP_WAVE_AUTHORITY_BREAK 证据图 02/03/04 — 错层窗 (5200-9200, 4300-8600).
全部从真实 DXF/渲染直出, 无手工修补."""
import ezdxf
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

CAD = Path(__file__).resolve().parent
OUT = CAD/'step_wave_p0'
WIN = (5200, 9200, 4300, 8600)

LC = {'A-WALL':'#222','A-WALL-RETAIN':'#222','A-WALL-RETAIN-STRUCT':'#222',
      'A-WALL-REMODELED':'#888','A-WALL-NEW':'#2a5cff','A-WALL-REVIEW':'#ff9c00',
      'A-WALL-DEMO-DESIGN':'#e33','A-WALL-HOLD':'#d0d','A-DOOR':'#0a8',
      'A-STAIR':'#b00020','A-STAIR-NEW':'#b00020','A-STAIR-DIRECTION':'#b00020',
      'A-SOFFIT':'#888','A-SOFFIT-NEW':'#888','A-STRUCT-UNDERLAY':'#bbb',
      'A-CONFLICT':'#f0f','A-REVIEW':'#ff9c00','A-MISC-NEW':'#ff9c00',
      'A-DESIGN':'#666','A-FURN':'#ccc','A-FIXT':'#ccc','A-ROOM':'#ddd',
      'A-DIMS':'#3a3','A-TEXT':'#777','A-STAIR-AREA':'#bbb'}

def ents(path):
    doc=ezdxf.readfile(path); frozen={l.dxf.name for l in doc.layers if l.dxf.flags&1}
    out=[]
    for e in doc.modelspace():
        t=e.dxftype(); lay=e.dxf.layer; pts=None; cl=False
        if t=='LWPOLYLINE': pts=[(p[0],p[1]) for p in e.get_points('xy')]; cl=e.closed
        elif t=='POLYLINE': pts=[(v.dxf.location.x,v.dxf.location.y) for v in e.vertices]
        elif t=='LINE': pts=[(e.dxf.start.x,e.dxf.start.y),(e.dxf.end.x,e.dxf.end.y)]
        if not pts: continue
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        if max(xs)<WIN[0] or min(xs)>WIN[1] or max(ys)<WIN[2] or min(ys)>WIN[3]: continue
        xd=[]
        try: xd=[v[1] for v in e.get_xdata('DEVINSRC') if v[0]==1000]
        except Exception: pass
        out.append({'h':e.dxf.handle,'lay':lay,'pts':pts,'cl':cl,
                    'frz':lay in frozen,'xd':xd,'t':t})
    return out

def draw(ax, es, lw=1.3, frozen_style=True, labels=None):
    for e in es:
        c=LC.get(e['lay'],'#999')
        p=e['pts']
        if e['frz']:
            if not frozen_style: continue
            ax.plot([q[0] for q in p]+([p[0][0]] if e['cl'] else []),
                    [q[1] for q in p]+([p[0][1]] if e['cl'] else []),
                    ls=':',lw=.6,c='#bbb',alpha=.8)
        else:
            ax.plot([q[0] for q in p]+([p[0][0]] if e['cl'] else []),
                    [q[1] for q in p]+([p[0][1]] if e['cl'] else []),
                    lw=lw,c=c,alpha=.95)
        if labels and 'STAIR' in e['lay']:
            cx=sum(q[0] for q in p)/len(p); cy=sum(q[1] for q in p)/len(p)
            tag = e['xd'][0] if e['xd'] else '-'
            ax.annotate(f"{e['h']} {e['lay']}\n{tag}",(cx,cy),fontsize=6,
                        color='#b00020',ha='center',
                        bbox=dict(fc='white',ec='#b00020',lw=.4,alpha=.85))

def frame(ax, title):
    ax.set_xlim(WIN[0],WIN[1]); ax.set_ylim(WIN[2],WIN[3])
    ax.set_aspect('equal'); ax.grid(alpha=.25); ax.set_title(title,fontsize=9)

e102=ents(CAD/'A102_WALL_DIFF_POC_V3.dxf')
e103=ents(CAD/'A103_CONSTRUCTION_POC_V7.dxf')

# --- 02: CAD 实体图(左A102 右A103, 冻结足迹虚线) ---
fig,axs=plt.subplots(1,2,figsize=(17,9))
draw(axs[0],e102); frame(axs[0],'A102 错层区 — 可见: 开放轮廓(3波=3级踢面)+2踢面线 | 虚线=冻结面积足迹')
draw(axs[1],e103); frame(axs[1],'A103 错层区 — 同上')
fig.savefig(OUT/'step_wave_evidence_02_cad.png',dpi=170,bbox_inches='tight',facecolor='white')
plt.close(fig); print('wrote 02')

# --- 03: Blender底图 + CAD 叠加 ---
img=mpimg.imread(OUT/'step_wave_evidence_01_blender.png')
fig,ax=plt.subplots(figsize=(10,11))
ax.imshow(img,extent=WIN,alpha=.85)
draw(ax,e103,lw=1.5)
frame(ax,'G2叠加: 新渲Blender俯视 + 修复A103实体 | 地坪弧=当前blend几何, 3波=台阶')
fig.savefig(OUT/'step_wave_evidence_03_overlay.png',dpi=170,bbox_inches='tight',facecolor='white')
plt.close(fig); print('wrote 03')

# --- 04: 对象ID标注图(A103, 台阶相关实体标 handle+DEVINSRC) ---
fig,ax=plt.subplots(figsize=(10,11))
ax.imshow(img,extent=WIN,alpha=.5)
draw(ax,e103,lw=1.4,labels=True)
draw(ax,e102,lw=.8)
frame(ax,'对象ID标注: 台阶实体 handle+DEVINSRC | 红=台阶层 蓝=新建墙 灰=保留')
fig.savefig(OUT/'step_wave_evidence_04_objid.png',dpi=170,bbox_inches='tight',facecolor='white')
plt.close(fig); print('wrote 04')
