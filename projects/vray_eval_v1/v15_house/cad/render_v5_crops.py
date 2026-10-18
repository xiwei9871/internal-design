#!/usr/bin/env python3
"""局部审查裁图: 自动收紧到内容 + 状态标注"""
import ezdxf, matplotlib
matplotlib.use('Agg'); matplotlib.rcParams['font.family']='Heiti TC'
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
COL={'A-WALL':'#000','A-DOOR':'#b60','A-WINDOW':'#08c','A-DIMS':'#080','A-TEXT':'#333',
     'A-FURN':'#c8a','A-FIXT':'#49c','A-DESIGN':'#d22','A-DEMO':'#f00','A-UNCERTAIN':'#fa0',
     'A-CONFLICT':'#f0f'}

def content_bbox(path, region, pad=300):
    x0,x1,y0,y1=region
    doc=ezdxf.readfile(path); xs,ys=[],[]
    for e in doc.modelspace():
        if e.dxftype()!='LWPOLYLINE': continue
        for p in e.get_points('xy'):
            if x0<p[0]<x1 and y0<p[1]<y1: xs.append(p[0]); ys.append(p[1])
    if not xs: return region
    return (min(xs)-pad, max(xs)+pad, min(ys)-pad, max(ys)+pad)

def draw(ax,path,alpha=1.0,label=False,lim=None):
    doc=ezdxf.readfile(path)
    frozen={l.dxf.name for l in doc.layers if l.is_off()}
    ents=[(e,None) for e in doc.modelspace() if e.dxf.layer not in frozen]
    for e in doc.modelspace():
        if e.dxftype()=='DIMENSION':
            for v in e.virtual_entities(): ents.append((v,None))
    for e,_ in ents:
        lay=e.dxf.layer; t=e.dxftype()
        try:
            if t=='LWPOLYLINE':
                pts=[(float(a[0]),float(a[1])) for a in e.get_points('xy')]
                ax.add_patch(MplPoly(pts,closed=bool(e.closed),fill=False,
                    edgecolor=COL.get(lay,'#999'),lw=2.2 if lay in('A-WALL','A-CONFLICT') else 1.0,alpha=alpha))
                if label and lim:
                    try: xd=[v for c,v in e.get_xdata('DEVINSRC')]
                    except Exception: xd=[]
                    if xd:
                        cx=sum(p[0] for p in pts)/len(pts); cy=sum(p[1] for p in pts)/len(pts)
                        if lim[0]<cx<lim[1] and lim[2]<cy<lim[3]:
                            nm=str(xd[0]).split('#')[0][:30]; st=xd[-1] if xd[-1].isupper() else ''
                            ax.text(cx,cy,nm,fontsize=4.5,color='#666',ha='center',va='center',clip_on=True)
                            ax.text(cx,cy-150,st,fontsize=4,color='#b40' if st!='EXISTING_RETAINED' else '#080',
                                    ha='center',va='center',clip_on=True)
            elif t=='LINE':
                q,w=e.dxf.start,e.dxf.end
                ax.plot([q.x,w.x],[q.y,w.y],color=COL.get(lay,'#888'),lw=1.0,alpha=alpha)
            elif t=='ARC':
                import matplotlib.patches as mp
                c=e.dxf.center
                ax.add_patch(mp.Arc((c.x,c.y),e.dxf.radius*2,e.dxf.radius*2,
                    theta1=e.dxf.start_angle,theta2=e.dxf.end_angle,edgecolor=COL.get(lay,'#888'),lw=1.0,alpha=alpha))
            elif t=='TEXT':
                ax.text(e.dxf.insert.x,e.dxf.insert.y,e.dxf.text[:18],fontsize=5,
                        color=COL.get(lay,'#333'),alpha=alpha,rotation=getattr(e.dxf,'rotation',0),clip_on=True)
        except Exception: pass

CROPS={
 'kitchen':  ((5200,8000,1200,4500),'厨房拆改+门洞'),
 'stair':    ((7300,9500,4400,7800),'错层台阶+扶手'),
 'bath2':    ((8800,11600,4300,6700),'次卫新隔墙 vs 旧衣帽间'),
 'nbalcony': ((7800,13200,12500,14200),'北阳台拟建封窗'),
}
for tag,(nominal,title) in CROPS.items():
    lim=content_bbox('A103_CONSTRUCTION_POC_V5.dxf',nominal,pad=400)
    fig,ax=plt.subplots(figsize=(12,10))
    draw(ax,'A103_CONSTRUCTION_POC_V3.dxf',alpha=0.3)
    draw(ax,'A103_CONSTRUCTION_POC_V5.dxf',alpha=1.0,label=True,lim=lim)
    ax.set_xlim(lim[0],lim[1]); ax.set_ylim(lim[2],lim[3]); ax.set_aspect('equal')
    ax.set_axis_off(); ax.margins(0)
    ax.set_title(f'{title} — V3淡/V5实 品红=冲突候选 橙=存疑 红=新建',fontsize=10)
    fig.savefig(f'A103_V5_crop_{tag}.png',dpi=180,bbox_inches='tight',facecolor='white')
    plt.close(fig); print('crop',tag,'lim',[round(v) for v in lim])
