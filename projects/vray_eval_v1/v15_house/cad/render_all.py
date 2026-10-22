#!/usr/bin/env python3
import ezdxf, matplotlib, glob
matplotlib.rcParams['font.family']='Heiti TC'
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
COL={'A-WALL':'#000','A-DOOR':'#b60','A-WINDOW':'#08c','A-COLUMN':'#000','A-SHAFT':'#999','A-DIMS':'#080','A-TEXT':'#333','A-FURN':'#c8a','A-FIXT':'#49c','A-DESIGN':'#d22',
'A-PLUM-C':'#36c','A-PLUM-H':'#e33','A-PLUM-D':'#90c','A-NOTE':'#333','A-ELEC-SOC':'#d22','A-ELEC-SW':'#c80','A-ELEC-NET':'#08c','A-HATCH-WOOD':'#c9a','A-HATCH-TILE':'#9ad','A-CEIL':'#f0f','A-DEMO':'#f00'}
for p in sorted(glob.glob('cad/A*.dxf')):
    name=p[:-4]
    doc=ezdxf.readfile(p)
    frozen={l.dxf.name for l in doc.layers if l.is_off()}
    fig,ax=plt.subplots(figsize=(17,17))
    for e in doc.modelspace():
        lay=e.dxf.layer
        if lay in frozen: continue
        t=e.dxftype()
        try:
            if t=='LWPOLYLINE':
                pts=[(float(a[0]),float(a[1])) for a in e.get_points('xy')]
                ls='--' if lay=='A-DEMO' else '-'
                ax.add_patch(Polygon(pts,closed=bool(e.closed),fill=False,edgecolor=COL.get(lay,'#999'),lw=1.6 if lay=='A-WALL' else 0.9,linestyle=ls))
            elif t=='LINE':
                q,w=e.dxf.start,e.dxf.end; ax.plot([q.x,w.x],[q.y,w.y],color=COL.get(lay,'#888'),lw=0.8)
            elif t=='CIRCLE':
                c=e.dxf.center; ax.add_patch(plt.Circle((c.x,c.y),e.dxf.radius,fill=False,edgecolor=COL.get(lay,'#888'),lw=0.9))
            elif t=='ARC':
                import matplotlib.patches as mp
                c=e.dxf.center
                ax.add_patch(mp.Arc((c.x,c.y),e.dxf.radius*2,e.dxf.radius*2,theta1=e.dxf.start_angle,theta2=e.dxf.end_angle,edgecolor=COL.get(lay,'#888'),lw=0.9))
            elif t=='TEXT':
                ax.text(e.dxf.insert.x,e.dxf.insert.y,e.dxf.text[:18],fontsize=4.5,color=COL.get(lay,'#333'),rotation=getattr(e.dxf,'rotation',0))
        except: pass
    ax.set_aspect('equal'); ax.autoscale(); ax.set_axis_off()
    out=name+'_preview.png'
    fig.savefig(out,dpi=140,bbox_inches='tight',facecolor='white')
    plt.close(fig); print(out)
