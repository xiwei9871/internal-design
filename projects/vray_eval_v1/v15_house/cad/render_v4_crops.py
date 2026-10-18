#!/usr/bin/env python3
"""4 张局部对比裁剪: V3淡/V4实 + 对象标注"""
import ezdxf, matplotlib
matplotlib.use('Agg'); matplotlib.rcParams['font.family']='Heiti TC'
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
COL={'A-WALL':'#000','A-DOOR':'#b60','A-WINDOW':'#08c','A-DIMS':'#080','A-TEXT':'#333',
     'A-FURN':'#c8a','A-FIXT':'#49c','A-DESIGN':'#d22','A-DEMO':'#f00','A-UNCERTAIN':'#fa0'}

def entities(path):
    doc=ezdxf.readfile(path)
    frozen={l.dxf.name for l in doc.layers if l.is_off()}
    out=[]
    for e in doc.modelspace():
        if e.dxf.layer in frozen: continue
        try: xd=[v for c,v in e.get_xdata('DEVINSRC')]
        except Exception: xd=[]
        out.append((e,xd))
    dg=[]
    for e in doc.modelspace():
        if e.dxftype()=='DIMENSION':
            for v in e.virtual_entities(): dg.append((v,[]))
    return out+dg

def draw(ax,path,alpha=1.0,label=False,lim=None):
    for e,xd in entities(path):
        lay=e.dxf.layer; t=e.dxftype()
        try:
            if t=='LWPOLYLINE':
                pts=[(float(a[0]),float(a[1])) for a in e.get_points('xy')]
                ax.add_patch(MplPoly(pts,closed=bool(e.closed),fill=False,
                    edgecolor=COL.get(lay,'#999'),lw=(2.0 if lay=='A-WALL' else 1.1)*alpha,alpha=alpha))
                if label and xd and lim:
                    cx=sum(p[0] for p in pts)/len(pts); cy=sum(p[1] for p in pts)/len(pts)
                    if lim[0]<cx<lim[1] and lim[2]<cy<lim[3]:
                        nm=xd[0].split('#')[0][:26]
                        st=xd[-1] if xd[-1].isupper() else xd[-2] if len(xd)>1 else ''
                        ax.text(cx,cy,nm,fontsize=4.2,color='#666',
                                ha='center',va='center',alpha=0.9)
            elif t=='LINE':
                q,w=e.dxf.start,e.dxf.end
                ax.plot([q.x,w.x],[q.y,w.y],color=COL.get(lay,'#888'),lw=1.0*alpha,alpha=alpha)
            elif t=='ARC':
                import matplotlib.patches as mp
                c=e.dxf.center
                ax.add_patch(mp.Arc((c.x,c.y),e.dxf.radius*2,e.dxf.radius*2,
                    theta1=e.dxf.start_angle,theta2=e.dxf.end_angle,
                    edgecolor=COL.get(lay,'#888'),lw=1.0*alpha,alpha=alpha))
            elif t=='TEXT':
                ax.text(e.dxf.insert.x,e.dxf.insert.y,e.dxf.text[:18],fontsize=5,
                        color=COL.get(lay,'#333'),alpha=alpha,rotation=getattr(e.dxf,'rotation',0))
        except Exception: pass

CROPS={
 'kitchen':   (5000,8300,600,4700,'厨房拆改+门洞'),
 'stair':     (7100,9700,4300,8000,'错层台阶+扶手'),
 'bath2':     (8600,11800,4300,6800,'次卫新隔墙 vs 旧衣帽间'),
 'nbalcony':  (7800,13200,12400,14300,'北阳台拟建封窗'),
}
for tag,(x0,x1,y0,y1,title) in CROPS.items():
    fig,ax=plt.subplots(figsize=(13,11))
    draw(ax,'A103_CONSTRUCTION_POC_V3.dxf',alpha=0.35)
    draw(ax,'A103_CONSTRUCTION_POC_V4.dxf',alpha=1.0,label=True,lim=(x0,x1,y0,y1))
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal')
    ax.set_title(f'{title} — V3淡/V4实',fontsize=9)
    fig.savefig(f'A103_V4_crop_{tag}.png',dpi=170,bbox_inches='tight',facecolor='white')
    plt.close(fig); print('crop',tag)
