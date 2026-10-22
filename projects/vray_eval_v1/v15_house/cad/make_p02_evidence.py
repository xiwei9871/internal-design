#!/usr/bin/env python3
"""P0.2 证据: 候选arch视图 + A103 同坐标叠加 + 天花专项图."""
import ezdxf
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

CAD = Path(__file__).resolve().parent
OUT = CAD/'step_wave_p0'
WIN = (5200, 9200, 4300, 8600)

LC = {'A-WALL':'#222','A-STAIR':'#b00020','A-STAIR-NEW':'#b00020',
      'A-STAIR-DIRECTION':'#e33','A-STAIR-AREA':'#999','A-WALL-NEW':'#2a5cff',
      'A-DOOR':'#0a8','A-WALL-RETAIN':'#222','A-CONFLICT':'#f0f','A-REVIEW':'#fa0'}

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
        out.append({'lay':lay,'pts':pts,'cl':cl,'frz':lay in frozen})
    return out

e103=ents(CAD/'A103_CONSTRUCTION_POC_V7.dxf')
img=mpimg.imread(OUT/'arch_cand_stair.png')
fig,ax=plt.subplots(figsize=(10,11))
ax.imshow(img,extent=WIN,alpha=.8)
for e in e103:
    c=LC.get(e['lay'],'#999'); p=e['pts']
    xs=[q[0] for q in p]+([p[0][0]] if e['cl'] else [])
    ys=[q[1] for q in p]+([p[0][1]] if e['cl'] else [])
    if e['frz']: ax.plot(xs,ys,ls=':',lw=.7,c='#888',alpha=.8)
    else: ax.plot(xs,ys,lw=1.4,c=c,alpha=.95)
ax.set_xlim(WIN[0],WIN[1]); ax.set_ylim(WIN[2],WIN[3])
ax.set_aspect('equal'); ax.grid(alpha=.25)
ax.set_title('P0.2 叠加: 候选ARCH视图(无吊顶) + A103实体 | 红=台阶3波 蓝=新建墙 虚线=冻结面积足迹',fontsize=9)
fig.savefig(OUT/'p02_cand_a103_overlay.png',dpi=170,bbox_inches='tight',facecolor='white')
plt.close(fig); print('wrote p02_cand_a103_overlay.png')
