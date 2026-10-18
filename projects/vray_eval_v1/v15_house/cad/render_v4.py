#!/usr/bin/env python3
"""V4 预览 + V3/V4 叠差图 + 局部放大"""
import ezdxf, matplotlib
matplotlib.use('Agg'); matplotlib.rcParams['font.family']='Heiti TC'
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
COL={'A-WALL':'#000','A-DOOR':'#b60','A-WINDOW':'#08c','A-COLUMN':'#000','A-SHAFT':'#999',
     'A-DIMS':'#080','A-TEXT':'#333','A-FURN':'#c8a','A-FIXT':'#49c','A-DESIGN':'#d22',
     'A-DEMO':'#f00','A-UNCERTAIN':'#fa0'}

def draw(ax, path, alpha=1.0, only_layers=None, lw_scale=1.0):
    doc=ezdxf.readfile(path)
    frozen={l.dxf.name for l in doc.layers if l.is_off()}
    dim_geom=[]
    for e in doc.modelspace():
        if e.dxftype()=='DIMENSION':
            for v in e.virtual_entities(): dim_geom.append(v)
    for e in list(doc.modelspace())+dim_geom:
        lay=e.dxf.layer
        if lay in frozen or (only_layers and lay not in only_layers): continue
        t=e.dxftype()
        try:
            if t=='LWPOLYLINE':
                pts=[(float(a[0]),float(a[1])) for a in e.get_points('xy')]
                ax.add_patch(MplPoly(pts,closed=bool(e.closed),fill=False,
                    edgecolor=COL.get(lay,'#999'),lw=(1.6 if lay=='A-WALL' else 0.9)*lw_scale,alpha=alpha))
            elif t=='LINE':
                q,w=e.dxf.start,e.dxf.end
                ax.plot([q.x,w.x],[q.y,w.y],color=COL.get(lay,'#888'),lw=0.8*lw_scale,alpha=alpha)
            elif t=='ARC':
                import matplotlib.patches as mp
                c=e.dxf.center
                ax.add_patch(mp.Arc((c.x,c.y),e.dxf.radius*2,e.dxf.radius*2,
                    theta1=e.dxf.start_angle,theta2=e.dxf.end_angle,
                    edgecolor=COL.get(lay,'#888'),lw=0.9*lw_scale,alpha=alpha))
            elif t=='TEXT':
                ax.text(e.dxf.insert.x,e.dxf.insert.y,e.dxf.text[:18],fontsize=4,
                        color=COL.get(lay,'#333'),alpha=alpha,
                        rotation=getattr(e.dxf,'rotation',0))
        except Exception: pass

fig,ax=plt.subplots(figsize=(17,17))
draw(ax,'A103_CONSTRUCTION_POC_V4.dxf')
ax.set_aspect('equal'); ax.autoscale(); ax.set_axis_off()
fig.savefig('A103_CONSTRUCTION_POC_V4_preview.png',dpi=140,bbox_inches='tight',facecolor='white')
plt.close(fig); print('preview ok')

fig,ax=plt.subplots(figsize=(17,17))
draw(ax,'A103_CONSTRUCTION_POC_V3.dxf',alpha=0.45,only_layers={'A-WALL','A-DESIGN'})
draw(ax,'A103_CONSTRUCTION_POC_V4.dxf',alpha=1.0,only_layers={'A-WALL','A-DESIGN','A-DOOR'})
ax.set_aspect('equal'); ax.autoscale(); ax.set_axis_off()
ax.set_title('V3(淡) vs V4(实) 墙体叠差')
fig.savefig('A103_V3_V4_overlay.png',dpi=140,bbox_inches='tight',facecolor='white')
plt.close(fig); print('overlay ok')

# 局部放大: 厨房门洞区 + 台阶区
for name,lim in (('kitchen',(4500,7500,800,4300)),('stair',(7200,9600,4200,7600)):
    fig,ax=plt.subplots(figsize=(12,12))
    draw(ax,'A103_CONSTRUCTION_POC_V4.dxf')
    ax.set_xlim(lim[0],lim[1]); ax.set_ylim(lim[2],lim[3])
    ax.set_aspect('equal'); ax.set_axis_off()
    fig.savefig(f'A103_V4_zoom_{name}.png',dpi=160,bbox_inches='tight',facecolor='white')
    plt.close(fig); print('zoom',name,'ok')
