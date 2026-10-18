#!/usr/bin/env python3
"""P1.3.3 业主可视化裁决包: A/B/C/D 四视图 + 证据放大 + 索引 + PDF"""
import json, csv
from pathlib import Path
import ezdxf, matplotlib
matplotlib.use('Agg'); matplotlib.rcParams['font.family']='Heiti TC'
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Rectangle
from matplotlib.backends.backend_pdf import PdfPages
from shapely.geometry import Polygon as SP, box

CAD = Path(__file__).resolve().parent
PKG = CAD / 'review_packages' / 'P1_3_3'; PKG.mkdir(parents=True, exist_ok=True)
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())
BASE_DXF = CAD/'A103_平面布置图.dxf'   # 含基准墙线的现图
ORIG_DXF = CAD.parents[3]/'projects/c_type_home/cad/C型_原始户型数字化基准图.dxf'
V5 = CAD/'A103_CONSTRUCTION_POC_V5.dxf'

# ---------- 案例定义: 物理墙段×房间 ----------
CASES = [
 dict(rid='R1_BATH2_CLK', title='次卫新隔墙 vs 旧衣帽间隔墙',
      region=(8500,11900,4200,6900),
      focus={'W_INT_CLK_N','W_INT_CLK_E','W_INT_CLK_W','R3_COMPLETE_PARTITION_WALLS',
             'VIEW_WALL_R3_WEST_PARTITION','VIEW_WALL_R3_SOUTH_POCKET_PARTITION',
             'D107_V3_RED_SIDE_50MM_WALL','DOOR_V2_D107_RIGHT_RETURN_WALL','W_INT_COR_N_STUB'},
      q='旧衣帽间三面隔墙(CLK_N/E/W)与次卫新建隔墙: 拆除/保留/错位?' ),
 dict(rid='R2_KITCHEN', title='厨房开放式拆改 + 残墙/门垛',
      region=(5400,8300,1400,4800),
      focus={'W_INT_X5800','KITCHEN_DIVIDER_PIER_SITE_REVIEW','W_wall_md_0009','W_wall_md_0010',
             'DOOR_V2_D107_LEFT_RETURN_WALL','W_INT_Y4500_a','W_INT_Y4500_bc','W_wall_md_0044'},
      q='西墙中段拆除范围 y1800-3800、残墙与门垛位置是否正确?'),
 dict(rid='R3_STAIR', title='走廊西墙开口(楼梯敞开) + 错层台阶',
      region=(7000,9800,4400,8300),
      focus={'W_INT_X7900_U','W_INT_X7900_L','W_wall_md_0015'},
      q='走廊西墙 y5000-7800 开口与台阶边界?'),
 dict(rid='R4_NBALC', title='北阳台拟建封窗 + 阳光房北带拆除',
      region=(7700,13300,12300,14300),
      focus={'W_EXT_N_BAL','W_wall_md_0062','W_wall_md_0016','W_wall_md_0026',
             'VIEW_WALL_DOOR_V2_NBALC_NORTH_FULL_WALL_PIER','VIEW_WALL_DOOR_V2_NBALC_SOLID_ABOVE_DOOR',
             'W_wall_md_0061','W_INT_X13000'},
      q='北带整拆+矮墙封窗方案与外墙关系?', section=True),
 dict(rid='R5_BED_STUDY', title='卧室/书房/客卧新隔墙 vs 原内墙',
      region=(9500,13300,4300,11800),
      focus={'VIEW_WALL_V4_D-MB_COMPLETE_HOST_WALL','VIEW_WALL_V4_D-STUDY_COMPLETE_HOST_WALL',
             'VIEW_WALL_V4_D-GUEST-ROOM_COMPLETE_HOST_WALL','W_INT_X13000','W_INT_X9800',
             'W_INT_STD_S','W_wall_md_0019','W_wall_md_0024','W_wall_md_0025','W_wall_md_0064',
             'VIEW_WALL_LIVING_FIX_GUEST_BATH_FULL_WALL'},
      q='FC 原内墙与模型新隔墙重合/错位关系?'),
 dict(rid='R6_ENT_WEST', title='玄关/西侧外墙及入口墙段',
      region=(2300,6000,2200,6600),
      focus={'W_EXT_W','VIEW_WALL_V4_ENT-1_COMPLETE_HOST_WALL','W_BALC_W','W_wall_md_0004',
             'W_wall_md_0005','W_wall_md_0006','VIEW_WALL_V4_G_DIN_LIV_RIGHT_PIER'},
      q='西外墙与入口墙段的重合双候选?'),
 dict(rid='R7_BAY', title='客厅飘窗头部/下部墙组合',
      region=(3400,7300,12500,14000),
      focus={'W_BAY_F','VIEW_WALL_LIVING_FIX_BAY_SOFFIT','VIEW_WALL_LIVING_FIX_BAY_SOLID_PLATFORM_CORE',
             'VIEW_WALL_LIVING_FIX_BAY_FRONT_HEAD','VIEW_WALL_LIVING_FIX_BAY_FRONT_UNDER_WALL',
             'VIEW_WALL_LIVING_FIX_BAY_INNER_HEAD','VIEW_WALL_LIVING_FIX_BAY_INNER_UNDER_WALL',
             'VIEW_WALL_LIVING_FIX_BAY_LEFT_HEAD','VIEW_WALL_LIVING_FIX_BAY_LEFT_UNDER_WALL',
             'VIEW_WALL_LIVING_FIX_BAY_RIGHT_HEAD','VIEW_WALL_LIVING_FIX_BAY_RIGHT_UNDER_WALL','W_wall_md_0063'},
      q='飘窗上下构件与 FC 飘窗墙重叠关系?'),
]

# ---------- 数据加载 ----------
orig = ezdxf.readfile(ORIG_DXF)
orig_walls = [e for e in orig.modelspace() if e.dxftype()=='LWPOLYLINE' and e.dxf.layer=='A-WALL']
orig_unc   = [e for e in orig.modelspace() if e.dxftype()=='LWPOLYLINE' and e.dxf.layer=='A-UNCERTAIN']
orig_rooms = [e for e in orig.modelspace() if e.dxftype()=='LWPOLYLINE' and e.dxf.layer=='A-ROOM']
orig_open  = [e for e in orig.modelspace() if e.dxftype()=='LWPOLYLINE' and e.dxf.layer=='A-DOOR']
v5doc = ezdxf.readfile(V5)
v5frozen = {l.dxf.name for l in v5doc.layers if l.is_off()}
spec_by_obj = {}
for m in GEO['managed_entities']:
    for o in m['objects']: spec_by_obj[o] = m

def draw_poly(ax,pts,color,lw=1.4,ls='-',fill=False,alpha=1.0,z=2):
    ax.add_patch(MplPoly(pts,closed=True,fill=fill,edgecolor=color,lw=lw,linestyle=ls,alpha=alpha,zorder=z))

def clip_region(ax,R):
    ax.set_xlim(R[0],R[1]); ax.set_ylim(R[2],R[3])
    ax.set_aspect('equal'); ax.set_axis_off()

def draw_orig(ax,R,color='#999'):
    for e in orig_rooms:
        pts=[(p[0],p[1]) for p in e.get_points('xy')]
        draw_poly(ax,pts,'#e8e8e8',0.7,z=1)
    for e in orig_walls:
        pts=[(p[0],p[1]) for p in e.get_points('xy')]
        draw_poly(ax,pts,color,1.4,z=2)
    for e in orig_unc:
        pts=[(p[0],p[1]) for p in e.get_points('xy')]
        draw_poly(ax,pts,'#f90',1.1,z=3)   # 基准图本就标注存疑
    for e in orig_open:
        pts=[(p[0],p[1]) for p in e.get_points('xy')]
        ax.add_patch(MplPoly(pts,closed=True,fill=False,edgecolor='#c90',lw=0.9))

def draw_specs(ax,R,mode='V5'):
    """按 spec 状态着色: 保留黑/拟建蓝/拆除红虚/存疑橙/冲突品红"""
    cc={'EXISTING_RETAINED':'#000','PROPOSED_NEW':'#24c','EXISTING_DEMOLISHED':'#e22',
        'UNVERIFIED':'#f90','DESIGN_REVIEW_PENDING':'#f90'}
    for m in GEO['managed_entities']:
        st=m['design_status']; col=cc.get(st,'#999')
        ls='--' if st=='EXISTING_DEMOLISHED' else '-'
        for p in m['demolished_parts']:
            draw_poly(ax,p,'#e22',1.3,'--',z=3)
        for p in m['parts']:
            draw_poly(ax,p['exterior'],col,1.7 if st!='PROPOSED_NEW' else 1.5,ls,z=4)
            for h in p['holes']: draw_poly(ax,h,col,1.0,ls,z=4)
    for c in GEO.get('conflicts',[]):
        for nm in (c['a'],c['b']):
            m=spec_by_obj.get(nm)
            if m:
                for p in m['parts']: draw_poly(ax,p['exterior'],'#f0f',2.0,':',z=6)

def draw_v5(ax,R,labels=True):
    cmap={'A-WALL':'#000','A-DOOR':'#b60','A-WINDOW':'#08c','A-DESIGN':'#d22',
          'A-DEMO':'#e22','A-UNCERTAIN':'#f90','A-CONFLICT':'#f0f','A-FURN':'#caa','A-FIXT':'#9ad'}
    for e in v5doc.modelspace():
        lay=e.dxf.layer
        if lay in v5frozen: continue
        if e.dxftype()=='LWPOLYLINE':
            pts=[(p[0],p[1]) for p in e.get_points('xy')]
            ls='--' if lay=='A-DEMO' else '-'
            draw_poly(ax,pts,cmap.get(lay,'#ccc'),2.0 if lay in('A-WALL','A-CONFLICT') else 1.0,ls,z=4)
            if labels:
                try: xd=[v for c,v in e.get_xdata('DEVINSRC')]
                except Exception: xd=[]
                if xd:
                    cx=sum(p[0] for p in pts)/len(pts); cy=sum(p[1] for p in pts)/len(pts)
                    if R[0]<cx<R[1] and R[2]<cy<R[3]:
                        ax.text(cx,cy,str(xd[0]).split('#')[0][:24],fontsize=4.6,color='#555',
                                ha='center',va='center',clip_on=True,zorder=8)
        elif e.dxftype()=='LINE':
            q,w=e.dxf.start,e.dxf.end
            ax.plot([q.x,w.x],[q.y,w.y],color=cmap.get(lay,'#ccc'),lw=0.8)

def draw_section(ax,R,case):
    """x-z 高度示意: 沿区域中线的对象高度条 (封窗/错层)"""
    objs=[]
    import json as _j
    bl=_j.loads((CAD/'derived'/'blender_geom_raw.json').read_text())
    fc={o['name']:o for o in _j.loads((CAD/'derived'/'fc_objects_raw.json').read_text())}
    for o in case['focus']:
        if o in bl: objs.append((o,bl[o]['bbox'],bl[o]['z']))
        elif o in fc: objs.append((o,fc[o]['bbox'],fc[o]['z']))
    ax.set_title('高度示意 (x-z)',fontsize=8)
    for o,b,z in objs:
        ax.add_patch(Rectangle((b[0],z[0]),max(b[2]-b[0],80),z[1]-z[0],
                     fill=False,edgecolor='#24c' if o in bl else '#000',lw=1.2))
        ax.text(b[0],z[1]+60,o[:22],fontsize=4)
    ax.set_xlim(R[0],R[1]); ax.set_ylim(0,2900)
    ax.axhline(450,color='#c60',lw=0.7,ls=':'); ax.axhline(1150,color='#0a0',lw=0.7,ls=':')
    ax.text(R[0]+50,480,'+450 上层地面',fontsize=4,color='#c60')
    ax.text(R[0]+50,1180,'剖切线1150',fontsize=4,color='#0a0')
    ax.set_xticks([]); ax.set_yticks([0,450,1150,2000,2800])
    ax.tick_params(labelsize=4)
    for s in ax.spines.values(): s.set_visible(True)

# ---------- 渲染 ----------
pdf = PdfPages(PKG/'OWNER_REVIEW.pdf')
index_boxes=[]
for case in CASES:
    R=case['region']; rid=case['rid']
    index_boxes.append((R,rid))
    fig,axes=plt.subplots(2,2,figsize=(16.5,11.7))   # A3 横版
    fig.suptitle(f'{rid} — {case["title"]}  |  XY范围 {R}',fontsize=11)
    ax=axes[0][0]; ax.set_title('A · 现状基准 (原数字化图)',fontsize=9)
    draw_orig(ax,R); clip_region(ax,R)
    ax=axes[0][1]; ax.set_title('B · 拆改意图 (红虚=已批拆除 / 橙=待裁)',fontsize=9)
    draw_orig(ax,R,'#ccc'); draw_specs(ax,R); clip_region(ax,R)
    ax=axes[1][0]; ax.set_title('C · 已确认设计目标 (模型结构)',fontsize=9)
    draw_specs(ax,R); clip_region(ax,R)
    ax=axes[1][1]; ax.set_title('D · CAD 自动生成 V5 (品红=冲突候选)',fontsize=9)
    draw_v5(ax,R); clip_region(ax,R)
    fig.tight_layout()
    fig.savefig(PKG/f'{rid}_ABCD.png',dpi=150,bbox_inches='tight',facecolor='white')
    pdf.savefig(fig); plt.close(fig)
    # 证据放大: 聚焦 focus 对象 bbox+margin
    fxs=[]; fys=[]
    for o in case['focus']:
        m=spec_by_obj.get(o)
        if m:
            b=m['outline_bbox']; fxs+=[b[0],b[2]]; fys+=[b[1],b[3]]
    if fxs:
        pad=700; ZR=(max(min(fxs)-pad,R[0]),min(max(fxs)+pad,R[1]),
                    max(min(fys)-pad,R[2]),min(max(fys)+pad,R[3]))
        fig,ax=plt.subplots(figsize=(13,11))
        draw_orig(ax,ZR,'#bbb'); draw_specs(ax,ZR); draw_v5(ax,ZR,labels=False)
        # ①②③ 标注焦点对象
        labels=sorted(case['focus'])
        notes=[]
        for i,o in enumerate(labels):
            m=spec_by_obj.get(o); 
            if not m: continue
            b=m['outline_bbox']; cx,cy=(b[0]+b[2])/2,(b[1]+b[3])/2
            if not (ZR[0]<cx<ZR[1] and ZR[2]<cy<ZR[3]): cx,cy=(b[0]+b[2])/2,min(max(cy,ZR[2]+200),ZR[3]-200)
            mk=chr(0x2460+i) if i<20 else str(i+1)
            ax.annotate(mk,(cx,cy),fontsize=13,color='#d00',ha='center',va='center',
                        fontweight='bold',zorder=10)
            st=m['design_status']; cut=m.get('cut_height') or 'FC'
            notes.append(f'{mk} {o[:34]}  [{st}|{cut}]')
        ax.text(ZR[0]+60,ZR[3]-60,'\n'.join(notes[:14]),fontsize=5.2,va='top',
                bbox=dict(fc='white',ec='#999',lw=0.5))
        clip_region(ax,ZR)
        ax.set_title(f'{rid} 证据放大 (灰色原墙/黑保留/蓝新建/红拆/橙待裁/品红冲突)',fontsize=9)
        fig.savefig(PKG/f'{rid}_ZOOM.png',dpi=170,bbox_inches='tight',facecolor='white')
        # 高度示意页 (需要时)
        if case.get('section'):
            fig2,ax2=plt.subplots(figsize=(16.5,5))
            draw_section(ax2,R,case)
            fig2.savefig(PKG/f'{rid}_SECTION.png',dpi=150,bbox_inches='tight',facecolor='white')
            pdf.savefig(fig2); plt.close(fig2)
        pdf.savefig(fig); plt.close(fig)
    print(rid,'done')
# 索引图
fig,ax=plt.subplots(figsize=(17,17))
draw_v5(ax,(0,17000,-1000,16000),labels=False)
for R,rid in index_boxes:
    ax.add_patch(Rectangle((R[0],R[2]),R[1]-R[0],R[3]-R[2],fill=False,
                 edgecolor='#e22',lw=2.0,zorder=9))
    ax.text((R[0]+R[1])/2,R[3]-300,rid,fontsize=9,color='#e22',ha='center',
            fontweight='bold',zorder=10,
            bbox=dict(fc='white',ec='#e22',lw=0.6))
clip_region(ax,(-800,17000,-1500,16200))
fig.savefig(PKG/'00_INDEX.png',dpi=140,bbox_inches='tight',facecolor='white')
pdf.savefig(fig); plt.close(fig)
pdf.close()
# 裁决表
with open(PKG/'owner_decisions.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['REVIEW_ID','位置','问题','A:模型为准','B:现状保留','C:方案调整','D:无法判断','业主选择','备注'])
    for c in CASES:
        w.writerow([c['rid'],c['title'],c['q'],'','','','','',''])
print('PKG done ->',PKG)
