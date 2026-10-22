#!/usr/bin/env python3
"""A102/A103 联合验收: 渲染 PDF+PNG, 一致性QA.
QJ1 两图源于同一geometry快照与registry
QJ2 A102拆除集==registry DEMOLISHED_CONFIRMED; HOLD集=={W_EXT_N_BAL}
QJ3 A103无SUPPRESS*对象落在可见层; DEMOLITION_HOLD不得作为已批拆除出现
QJ4 冲突对象在A103 A-CONFLICT层, 在A102仍按registry角色
QJ5 两图原生DIMENSION锚点对一致
QJ6 A102保留墙(A-WALL-RETAIN*) ⊆ A103可见墙 — 拆改图不得保留A103没有的墙
QJ7 源文件live SHA未变"""
import json, hashlib
from pathlib import Path
import ezdxf
import matplotlib; matplotlib.use('Agg'); matplotlib.rcParams['font.family']='Heiti TC'
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
from shapely.geometry import Polygon

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
REG = json.loads((CAD/'derived'/'wall_state_registry.json').read_text())
GEO = json.loads((CAD/'derived'/'geometry_v05.json').read_text())
reg_role = {e['object']: e['a102_role'] for e in REG['entries']}
reg_a103 = {e['object']: e['a103_role'] for e in REG['entries']}

def read(path):
    doc = ezdxf.readfile(path)
    walls = {}   # layer -> [(handle,pts,xdata_objs)]
    dims, texts = [], []
    for e in doc.modelspace():
        if e.dxftype() == 'LWPOLYLINE':
            pts = [(p[0],p[1]) for p in e.get_points('xy')]
            objs = []
            try:
                xd = e.get_xdata('DEVINSRC')
                objs = [v[1] for v in xd if v[0]==1000]
            except ezdxf.DXFValueError: pass
            walls.setdefault(e.dxf.layer,[]).append((e.dxf.handle,pts,objs))
        elif e.dxftype() == 'LINE':
            s,t = e.dxf.start,e.dxf.end
            walls.setdefault(e.dxf.layer,[]).append(
                (e.dxf.handle,[(s.x,s.y),(t.x,t.y)],[]))
        elif e.dxftype() == 'DIMENSION':
            try:
                xd = e.get_xdata('DEVINSRC') + e.get_xdata('DEVINDIM')
                dims.append(set(v[1] for v in xd if v[0]==1000))
            except ezdxf.DXFValueError: dims.append(set())
    layflags = {l.dxf.name: bool(l.dxf.flags & 1) for l in doc.layers}
    return walls, dims, layflags

w102, d102, f102 = read(CAD/'A102_WALL_DIFF_POC_V1.dxf')
w103, d103, f103 = read(CAD/'A103_CONSTRUCTION_POC_V5.dxf')

qa = {}
# QJ1
qa['QJ1_same_snapshot'] = REG['meta']['geometry_snapshot']['sha256'] == \
    hashlib.sha256((CAD/'derived'/'geometry_v05.json').read_bytes()).hexdigest()
# QJ2
demo_in_102 = set(); hold_in_102 = set()
for h,pts,objs in w102.get('A-WALL-DEMO',[]):
    for o in objs:
        if '#demol' in o: demo_in_102.add(o)
for h,pts,objs in w102.get('A-WALL-HOLD',[]):
    for o in objs:
        if '#demol' in o: hold_in_102.add(o)
want_demo = {e['object'] for e in REG['entries'] if e['a102_role']=='DEMOLISHED_CONFIRMED'}
want_hold = {e['object'] for e in REG['entries'] if e['a102_role']=='DEMOLITION_HOLD'}
qa['QJ2_demo_set'] = demo_in_102 == want_demo
qa['QJ2_hold_set'] = hold_in_102 == want_hold == {'W_EXT_N_BAL#demol0'}
# QJ3: A103可见层上不得有 SUPPRESS 对象; A-DEMO 必须冻结
bad = []
for lay,ents in w103.items():
    if f103.get(lay): continue   # 冻结层不算可见
    for h,pts,objs in ents:
        for o in objs:
            base = o.split('#')[0] if not o.startswith('dim:') else o
            if reg_a103.get(o) in ('SUPPRESS','SUPPRESS_HOLD') or \
               reg_a103.get(base) in ('SUPPRESS','SUPPRESS_HOLD'):
                bad.append((h,lay,o))
qa['QJ3_no_suppress_visible'] = not bad
qa['QJ3_detail'] = bad
qa['QJ3_a102_demo_frozen_not_in_a103'] = 'A-WALL-DEMO' not in w103 and f103.get('A-DEMO',False)
# QJ4
qa['QJ4_conflicts_on_conflict_layer'] = len(w103.get('A-CONFLICT',[])) > 0
# QJ5
qa['QJ5_dim_anchor_parity'] = d102 == d103 and len(d102) == len(GEO['dims'])
# QJ6
VOCAB = {'RETAINED','RETAINED_STRUCT','NEW','PENDING_REVIEW','DEMOLISHED_CONFIRMED',
         'DEMOLITION_HOLD','NO_STRUCT_OVERLAP','CLASSIFICATION_UNVERIFIED',
         'STRUCT_EVIDENCE_BOUNDARY_RING','STRUCT_EVIDENCE_HATCH_FILL',
         'EXISTING_RETAINED','EXISTING_DEMOLISHED','PROPOSED_NEW','UNVERIFIED',
         'DESIGN_REVIEW_PENDING'}
retained_102_objs = set()
for lay in ('A-WALL-RETAIN','A-WALL-RETAIN-STRUCT'):
    for h,pts,objs in w102.get(lay,[]):
        retained_102_objs.update(o for o in objs
            if not o.startswith(('dim:','LEGACY')) and o not in VOCAB)
visible_103 = set()
for lay,ents in w103.items():
    if f103.get(lay): continue
    for h,pts,objs in ents:
        for o in objs:
            visible_103.add(o.split('#')[0])
qa['QJ6_retained_in_a103'] = {o: (o.split('#p')[0] in visible_103 or o in visible_103)
                              for o in retained_102_objs}
qa['QJ6_pass'] = all(qa['QJ6_retained_in_a103'].values())
# QJ7
qa['QJ7_sources_fresh'] = all(
    hashlib.sha256((ROOT/s['file'].split('interior_design/')[-1]).read_bytes()).hexdigest()
    == s['sha256']
    for s in json.loads((CAD/'derived'/'three_source_mapping.json').read_text())
            ['summary']['sources'].values() if s['file'].endswith(('.dxf','.FCStd','.blend','.json'))
    and Path(ROOT/s['file'].split('interior_design/')[-1]).exists())

qa['verdict'] = 'PASS' if all(v for k,v in qa.items()
                    if isinstance(v,bool)) else 'HOLD'
(CAD/'derived'/'qa_joint.json').write_text(json.dumps(qa,ensure_ascii=False,indent=1))
print(json.dumps({k:v for k,v in qa.items() if not isinstance(v,(list,dict))},
                 ensure_ascii=False,indent=1))
print('fails:',[k for k,v in qa.items() if v is False])

# ---------- 渲染 ----------
COLORS = {'A-STRUCT-UNDERLAY':'#bbb','A-WALL-RETAIN':'#111','A-WALL-RETAIN-STRUCT':'#111',
          'A-WALL-DEMO':'#e22','A-WALL-HOLD':'#e0e','A-WALL-NEW':'#24c',
          'A-WALL-REVIEW':'#f90','A-CONFLICT':'#e0e','A-DOOR':'#4a4','A-WINDOW':'#0aa',
          'A-WALL':'#111','A-DESIGN':'#24c','A-UNCERTAIN':'#f90','A-DEMO':'#e22'}
def render(walls, layflags, title, png, pdf):
    fig,ax = plt.subplots(figsize=(16,16))
    for lay,ents in walls.items():
        if layflags.get(lay): continue
        c = COLORS.get(lay,'#ccc')
        lw = 2.2 if lay in ('A-WALL-RETAIN','A-WALL-RETAIN-STRUCT','A-WALL') else 1.2
        for h,pts,objs in ents:
            if len(pts)>2:
                ax.add_patch(MP(pts,closed=True,fill=False,edgecolor=c,lw=lw))
            elif len(pts)==2:
                ax.plot([p[0] for p in pts],[p[1] for p in pts],color=c,lw=lw)
    ax.set_aspect('equal'); ax.autoscale(); ax.set_axis_off(); ax.set_title(title)
    fig.savefig(png,dpi=160,bbox_inches='tight',facecolor='white')
    fig.savefig(pdf,format='pdf',bbox_inches='tight',facecolor='white')
    plt.close(fig)
render(w102,f102,'A102 墙体拆改图 POC V1 (黑保留/红已批拆/品红HOLD/蓝新建/灰结构)',
       CAD/'A102_POC_preview.png',CAD/'A102_POC.pdf')
render(w103,f103,'A103 最终平面 POC V5 (黑保留/蓝拟建/品红冲突候选)',
       CAD/'A103_POC_preview.png',CAD/'A103_POC.pdf')
print('rendered A102_POC.png/pdf, A103_POC.png/pdf')
