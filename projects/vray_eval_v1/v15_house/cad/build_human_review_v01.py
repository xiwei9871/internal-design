#!/usr/bin/env python3
"""HUMAN_CAD_REVIEW_V01 — 两组同坐标审图包, 全部从最终文件直读.
组1: measured_working.dxf(偏移-AX,-AY) vs A102_WALL_DIFF_POC_V3.dxf
组2: blender_ortho_top.png(V15_WORK.blend 正交俯视) vs A103_CONSTRUCTION_POC_V7.dxf
门窗/尺寸/弧/文字经 virtual_entities 展开, 不画墙线了事.
→ review_packages/HUMAN_CAD_REVIEW_V01/"""
import json, hashlib
from pathlib import Path
import ezdxf, matplotlib
matplotlib.use('Agg'); matplotlib.rcParams['font.family']='Heiti TC'
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import Polygon as MP
from matplotlib.collections import LineCollection

CAD = Path(__file__).resolve().parent
OUT = CAD/'review_packages'/'HUMAN_CAD_REVIEW_V01'; OUT.mkdir(parents=True, exist_ok=True)
F102 = CAD/'A102_WALL_DIFF_POC_V3.dxf'
F103 = CAD/'A103_CONSTRUCTION_POC_V7.dxf'
FMEA = CAD.parents[3]/'projects/c_type_home/cad/measured_working.dxf'
AX, AY = 1298172.0, -296458.0
SHA = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:10]
       for p in (F102, F103, FMEA)}

ACI = {0:'#888',1:'#e22',2:'#cc0',3:'#0b0',4:'#0cc',5:'#24c',6:'#c0c',7:'#111',
       8:'#888',9:'#bbb',30:'#f80',108:'#7ab',140:'#c00',250:'#666',256:None}

def col_of(e, doc, default='#555'):
    try:
        tc = e.dxf.get('true_color', 0)
        if tc and tc > 0:
            return '#%06x' % (tc & 0xFFFFFF)
        c = e.dxf.color
        if c in (0, 256):                    # BYBLOCK/BYLAYER
            c = doc.layers.get(e.dxf.layer).dxf.color if e.dxf.layer in doc.layers else 7
        return ACI.get(abs(c), default)
    except Exception:
        return default

def each_geom(path, offset=(0.0,0.0)):
    """yield (layer, kind, payload, color). 展开 DIMENSION/INSERT 虚拟实体."""
    doc = ezdxf.readfile(path)
    frozen = {l.dxf.name for l in doc.layers if l.dxf.flags & 1}
    ox, oy = offset
    for e in doc.modelspace():
        if e.dxf.layer in frozen: continue
        col = col_of(e, doc)
        def put(ee, cc):
            t = ee.dxftype()
            if t in ('LINE',):
                yield (ee.dxf.layer,'line',[(ee.dxf.start.x+ox,ee.dxf.start.y+oy),
                       (ee.dxf.end.x+ox,ee.dxf.end.y+oy)],cc)
            elif t == 'LWPOLYLINE':
                yield (ee.dxf.layer,'poly',[(p[0]+ox,p[1]+oy) for p in
                       ee.get_points('xy')],cc)
            elif t == 'CIRCLE':
                yield (ee.dxf.layer,'circle',
                       ((ee.dxf.center.x+ox,ee.dxf.center.y+oy),ee.dxf.radius),cc)
            elif t == 'ARC':
                yield (ee.dxf.layer,'arc',
                       ((ee.dxf.center.x+ox,ee.dxf.center.y+oy),ee.dxf.radius,
                        ee.dxf.start_angle,ee.dxf.end_angle),cc)
            elif t in ('TEXT','MTEXT'):
                try: ins = (ee.dxf.insert.x+ox, ee.dxf.insert.y+oy)
                except Exception: return
                txt = (ee.dxf.text if t=='TEXT' else ee.plain_text())[:20]
                yield (ee.dxf.layer,'text',(ins,txt),cc)
            elif t == 'SPLINE':
                try:
                    pts = [(p.x+ox,p.y+oy) for p in ee.approximate(20)]
                    yield (ee.dxf.layer,'line',pts,cc)
                except Exception: pass
        if e.dxftype() in ('DIMENSION','INSERT'):
            try:
                for ve in e.virtual_entities():
                    yield from put(ve, col)
            except Exception:
                yield from put(e, col)
        else:
            yield from put(e, col)

def draw_geoms(ax, geoms, alpha=1.0, scale_lw=1.0,
               only_layers=None, force_color=None, text=True):
    for lay, kind, pl, c in geoms:
        if only_layers and lay not in only_layers: continue
        cc = force_color or c
        if kind in ('line','poly'):
            xs=[p[0] for p in pl]; ys=[p[1] for p in pl]
            ax.add_line(plt.Line2D(xs,ys,color=cc,lw=0.8*scale_lw,alpha=alpha))
            if kind=='poly' and len(pl)>2:
                ax.add_line(plt.Line2D([pl[-1][0],pl[0][0]],[pl[-1][1],pl[0][1]],
                            color=cc,lw=0.8*scale_lw,alpha=alpha))
        elif kind=='circle':
            from matplotlib.patches import Circle
            ax.add_patch(Circle(pl[0],pl[1],fill=False,edgecolor=cc,lw=.7,alpha=alpha))
        elif kind=='arc':
            from matplotlib.patches import Arc
            ax.add_patch(Arc(pl[0],pl[1]*2,pl[1]*2,theta1=pl[2],theta2=pl[3],
                             edgecolor=cc,lw=.7,alpha=alpha))
        elif kind=='text' and text:
            ins,txt = pl
            if txt.strip(): ax.annotate(txt,ins,fontsize=5,color=cc,alpha=alpha)

def full_fig(path, geoms, title, name, facecolor='white'):
    fig,ax=plt.subplots(figsize=(18,18))
    draw_geoms(ax,geoms)
    ax.set_aspect('equal'); ax.autoscale(); ax.set_axis_off()
    ax.set_title(title,fontsize=12)
    fig.savefig(OUT/name,dpi=170,bbox_inches='tight',facecolor=facecolor)
    plt.close(fig); print('wrote',name)

CROPS = {'kitchen':(5200,7200,1400,4300),'bath2':(8500,12000,5400,8400),
         'nbalc':(7400,13400,12400,14200),'step':(5200,9200,4300,8600)}

def crop_figs(tag, layersets, name_t, crops=CROPS):
    for cname,(x0,x1,y0,y1) in crops.items():
        fig,ax=plt.subplots(figsize=(13,11))
        for geoms,kw in layersets: draw_geoms(ax,geoms,**kw)
        ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal')
        ax.grid(alpha=.25)
        ax.set_title(name_t.format(c=cname),fontsize=10)
        fig.savefig(OUT/f'{tag}_{cname}.png',dpi=170,bbox_inches='tight',
                    facecolor='white'); plt.close(fig)
        print('wrote',f'{tag}_{cname}.png')

# ============ 组1: 实测CAD vs A102 ============
g_mea  = list(each_geom(FMEA, offset=(-AX,-AY)))
g_102  = list(each_geom(F102))
full_fig(None, g_mea, f'现状测绘CAD(measured_working, 模型坐标) sha:{SHA[FMEA.name]}',
         'g1_measured_full.png')
full_fig(None, g_102, f'A102拆改图 sha:{SHA[F102.name]}', 'g1_a102_full.png')

fig,ax=plt.subplots(figsize=(18,18))
draw_geoms(ax,g_mea,alpha=.55,force_color='#999')                    # 现状灰
draw_geoms(ax,[g for g in g_102 if g[0] not in ('A-TEXT','Defpoints')],scale_lw=1.3)
ax.set_aspect('equal'); ax.autoscale(); ax.set_axis_off()
ax.set_title(f'G1叠加: 灰=现状测绘 | 黑=保留 红=拟拆(设计确认) 品红=HOLD 蓝=新建 橙=待裁 绿=尺寸 | sha102:{SHA[F102.name]}',fontsize=11)
fig.savefig(OUT/'g1_overlay.png',dpi=170,bbox_inches='tight',facecolor='white')
plt.close(fig); print('wrote g1_overlay.png')
crop_figs('g1',[(g_mea,{'alpha':.5,'force_color':'#999'}),
                (g_102,{'scale_lw':1.3})],
          'G1 {c} 叠加: 灰=现状 sha102:'+SHA[F102.name])

# ============ 组2: Blender俯视 vs A103 ============
g_103 = list(each_geom(F103))
full_fig(None,g_103,f'A103平面图 sha:{SHA[F103.name]}','g2_a103_full.png')

img = mpimg.imread(OUT/'blender_ortho_top.png')
EXT = (500,15800,-1000,15200)      # blender_ortho_top 输出范围(mm)
fig,ax=plt.subplots(figsize=(18,18))
ax.imshow(img,extent=EXT,alpha=.85)
draw_geoms(ax,[g for g in g_103 if g[0] in
           ('A-WALL','A-DESIGN','A-STAIR','A-SOFFIT','A-MISC-NEW','A-REVIEW',
            'A-CONFLICT','A-STRUCT-UNDERLAY','A-WALL-NEW')],scale_lw=1.4)
ax.set_xlim(EXT[0],EXT[1]); ax.set_ylim(EXT[2],EXT[3]); ax.set_aspect('equal')
ax.set_axis_off()
ax.set_title(f'G2叠加: Blender正交俯视底 + A103墙体轮廓 | blend_sha:feaeed380c a103_sha:{SHA[F103.name]}',fontsize=11)
fig.savefig(OUT/'g2_overlay.png',dpi=170,bbox_inches='tight',facecolor='white')
plt.close(fig); print('wrote g2_overlay.png')
crop_figs('g2',[(g_103,{'only_layers':{'A-WALL','A-DESIGN','A-STAIR','A-SOFFIT',
                'A-MISC-NEW','A-REVIEW','A-CONFLICT','A-STRUCT-UNDERLAY'},
                'scale_lw':1.4})],
          'G2 {c}: A103墙层叠加俯视底 sha103:'+SHA[F103.name],
          )
# crop 也带俯视底
for cname,(x0,x1,y0,y1) in CROPS.items():
    fig,ax=plt.subplots(figsize=(13,11))
    ax.imshow(img,extent=EXT,alpha=.85)
    draw_geoms(ax,[g for g in g_103 if g[0] in
               ('A-WALL','A-DESIGN','A-STAIR','A-SOFFIT','A-MISC-NEW','A-REVIEW',
                'A-CONFLICT','A-STRUCT-UNDERLAY')],scale_lw=1.6)
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.grid(alpha=.25)
    ax.set_title(f'G2 {cname}: 俯视底+A103 sha103:{SHA[F103.name]}',fontsize=10)
    fig.savefig(OUT/f'g2_{cname}.png',dpi=170,bbox_inches='tight',facecolor='white')
    plt.close(fig)

# ============ 说明页 ============
lines = ['HUMAN_CAD_REVIEW_V01 — 人工审图包','='*50,'',
 f'组1 现状 vs A102:  g1_measured_full / g1_a102_full / g1_overlay / g1_*crop',
 f'组2 俯视 vs A103:  blender_ortho_top / g2_a103_full / g2_overlay / g2_*crop','',
 '源 sha256(前10):']
for k,v in SHA.items(): lines.append(f'  {k}  {v}')
lines += [f'  V15_WORK.blend  feaeed380c (权威哈希未变)','',
 '注意: blender_ortho_top 为 Workbench 俯视, 渲染严格遵循文件内 hide_render 状态(未改blend).',
 '台阶平面图语义: 3级=3条踢面线. WAVE_STEP_3_ARRIVAL 为+450到达平台,',
 'A102/A103 中已并入 STEP_2 轮廓(XDATA: merged_arrival), 不再显示为第4级.',
 'g2 叠加中俯视底图色深=实体, A103轮廓线=墙体层.',
 '本包为人工审图资料, 非正式施工图; 专业CAD编辑验证仍 NOT_RUN.']
(OUT/'README.txt').write_text('\n'.join(lines),encoding='utf-8')
print('done ->',OUT)
