#!/usr/bin/env python3
"""Style-only POC v2: A102/A103 -> *_STYLE_POC.dxf  (Gate B1-B3 修正版)
仅允许: 图层样式/线宽/文字样式/标注表达/控制线/图框标题栏/纸空间设置。
禁止改动: 任何现有实体的几何、门窗洞口、台阶、拆改语义、XDATA、registry 引用。
关键修正:
- B1: 轴网不再逐图推导。两图共用 axis_basis.json（以 A103 墙体外包为单一
  定位基准），只发 4 条经验证的外包控制线，编号 1/2 + A/B，灰细点划线。
- B2: 门窗编号绑定稳定对象 handle，附 DEVINPOC XDATA 指针;窗按 A-WINDOW
  开口线逐条编号（W1..W6），不再只数块。
- 所有新增实体登记 style_poc_manifest.json（均为非几何标注）。
"""
import ezdxf, json, math, hashlib

CAD = '/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad'
OUT = CAD + '/research/house_plan_designer_v01/dxf_style'

LINEWEIGHTS = {
    'A-WALL': 50, 'A-WALL-RETAIN': 50, 'A-WALL-RETAIN-STRUCT': 50, 'A-WALL-REMODELED': 50,
    'A-WALL-NEW': 50, 'A-STAIR-NEW': 35, 'A-SOFFIT-NEW': 25, 'A-MISC-NEW': 25,
    'A-WALL-DEMO-DESIGN': 35, 'A-DEMO': 35,
    'A-WALL-HOLD': 35, 'A-WALL-REVIEW': 25, 'A-CONFLICT': 25, 'A-REVIEW': 25,
    'A-DOOR': 25, 'A-WINDOW': 25, 'A-COLUMN': 50, 'A-SHAFT': 25,
    'A-STAIR': 30, 'A-STAIR-DIRECTION': 25,
    'A-DIMS': 13, 'A-DIMS-LEGACY': 13, 'A-TEXT': 25, 'A-NOTE': 18,
    'A-FURN': 13, 'A-FIXT': 18, 'A-STRUCT-UNDERLAY': 9, 'A-SOFFIT': 18, 'A-DESIGN': 30,
    'AXIS': 13, 'AXIS-NUM': 18, 'A-DOOR-NUM': 18, 'A-WIN-NUM': 18,
}

# ---------- 共享定位基准：仅从 A103 生成一次，两图共用 ----------
def build_axis_basis():
    doc = ezdxf.readfile(f'{CAD}/A103_CONSTRUCTION_POC_V7.dxf')
    xs, ys = [], []
    for e in doc.modelspace().query('LWPOLYLINE'):
        if e.dxf.get('layer') in ('A-WALL', 'A-COLUMN'):
            for p in e.get_points('xy'):
                xs.append(p[0]); ys.append(p[1])
    basis = {'source': 'A103_CONSTRUCTION_POC_V7 墙系外包(A-WALL/A-COLUMN)',
             'v': [float(min(xs)), float(max(xs))], 'h': [float(min(ys)), float(max(ys))],
             'labels': {'v': ['1', '2'], 'h': ['A', 'B']}}
    json.dump(basis, open(f'{OUT}/axis_basis.json', 'w'), ensure_ascii=False, indent=1)
    return basis

def build_opening_basis():
    """开口编号基准: 从 A103 取门/窗规范位置一次, 两图共用编号。
    门 = SYM-DOOR-LEAF 插入点(M1..M9), 窗 = A-WINDOW 开口线中心(W1..W6)。"""
    doc = ezdxf.readfile(f'{CAD}/A103_CONSTRUCTION_POC_V7.dxf')
    msp = doc.modelspace()
    doors = sorted([e for e in msp.query('INSERT') if e.dxf.name == 'SYM-DOOR-LEAF'],
                   key=lambda e: (-e.dxf.insert.y, e.dxf.insert.x))
    wins = sorted([e for e in msp.query('LWPOLYLINE') if e.dxf.get('layer') == 'A-WINDOW'],
                  key=lambda e: (-min(p[1] for p in e.get_points('xy')),
                                 min(p[0] for p in e.get_points('xy'))))
    basis = {'source': 'A103_CONSTRUCTION_POC_V7',
             'doors': [{'label': f'M{i+1}', 'at': [float(e.dxf.insert.x), float(e.dxf.insert.y)]}
                       for i, e in enumerate(doors)],
             'windows': [{'label': f'W{i+1}',
                          'at': [float((min(p[0] for p in e.get_points('xy')) +
                                       max(p[0] for p in e.get_points('xy'))) / 2),
                                 float((min(p[1] for p in e.get_points('xy')) +
                                       max(p[1] for p in e.get_points('xy'))) / 2)]}
                         for i, e in enumerate(wins)]}
    json.dump(basis, open(f'{OUT}/opening_basis.json', 'w'), ensure_ascii=False, indent=1)
    return basis

def apply_axis_basis(doc, msp, manifest, basis):
    EXT = 1500
    x0, x1 = basis['v']; y0, y1 = basis['h']
    for i, x in enumerate(basis['v']):
        msp.add_line((x, y0-EXT), (x, y1+EXT), dxfattribs={'layer': 'AXIS'})
        for yy in (y0-EXT,):
            msp.add_circle((x, yy), 350, dxfattribs={'layer': 'AXIS-NUM'})
            t = msp.add_text(basis['labels']['v'][i],
                             dxfattribs={'layer': 'AXIS-NUM', 'height': 300})
            t.set_placement((x, yy), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        manifest['added'].append(dict(layer='AXIS', type='control_axis_v', at=x,
                                      label=basis['labels']['v'][i], basis='axis_basis.json'))
    for i, y in enumerate(basis['h']):
        msp.add_line((x0-EXT, y), (x1+EXT, y), dxfattribs={'layer': 'AXIS'})
        msp.add_circle((x0-EXT, y), 350, dxfattribs={'layer': 'AXIS-NUM'})
        t = msp.add_text(basis['labels']['h'][i],
                         dxfattribs={'layer': 'AXIS-NUM', 'height': 300})
        t.set_placement((x0-EXT, y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        manifest['added'].append(dict(layer='AXIS', type='control_axis_h', at=y,
                                      label=basis['labels']['h'][i], basis='axis_basis.json'))

def _tag_label(text_ent, ref_handle):
    text_ent.set_xdata('DEVINPOC', [(1000, 'ANNOTATION'), (1005, ref_handle)])

def _cent(e):
    if e.dxftype() == 'LWPOLYLINE':
        pts = [(p[0], p[1]) for p in e.get_points('xy')]
        return ((min(p[0] for p in pts)+max(p[0] for p in pts))/2,
                (min(p[1] for p in pts)+max(p[1] for p in pts))/2)
    return (e.dxf.insert.x, e.dxf.insert.y)

def _nearest(objs, pos, tol=1200):
    best, bd = None, tol
    for e in objs:
        c = _cent(e); d = math.dist(c, pos)
        if d < bd: best, bd = e, d
    return best, bd

def number_openings(doc, msp, manifest, basis):
    """按共享 opening_basis 编号: 在每个文件内找距基准位置最近的同类对象,
    编号文字以 DEVINPOC XDATA(1005) 绑定本地对象 handle —— 跨图编号一致。"""
    if 'DEVINPOC' not in doc.appids:
        doc.appids.new('DEVINPOC')
    local_doors = [e for e in msp.query('INSERT') if e.dxf.name == 'SYM-DOOR-LEAF'] or \
                  [e for e in msp.query('LWPOLYLINE') if e.dxf.get('layer') == 'A-DOOR']
    local_wins = [e for e in msp.query('LWPOLYLINE') if e.dxf.get('layer') == 'A-WINDOW']
    manifest['opening_count'] = {'door_candidates': len(local_doors),
                                 'window_candidates': len(local_wins)}
    manifest['unmatched'] = []
    for item in basis['doors']:
        e, d = _nearest(local_doors, item['at'])
        if e is None:
            manifest['unmatched'].append(item['label']); continue
        c = _cent(e)
        t = msp.add_text(item['label'], dxfattribs={'layer': 'A-DOOR-NUM', 'height': 220})
        t.set_placement((c[0]+260, c[1]+260), align=ezdxf.enums.TextEntityAlignment.BOTTOM_LEFT)
        _tag_label(t, e.dxf.handle)
        manifest['added'].append(dict(layer='A-DOOR-NUM', type='door_num', label=item['label'],
                                      ref_handle=e.dxf.handle, basis_at=item['at'],
                                      match_dist=round(d, 1),
                                      at=[round(c[0], 1), round(c[1], 1)]))
        local_doors.remove(e)
    for item in basis['windows']:
        e, d = _nearest(local_wins, item['at'])
        if e is None:
            manifest['unmatched'].append(item['label']); continue
        c = _cent(e)
        t = msp.add_text(item['label'], dxfattribs={'layer': 'A-WIN-NUM', 'height': 220})
        t.set_placement((c[0], c[1]+260), align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)
        _tag_label(t, e.dxf.handle)
        manifest['added'].append(dict(layer='A-WIN-NUM', type='win_num', label=item['label'],
                                      ref_handle=e.dxf.handle, basis_at=item['at'],
                                      match_dist=round(d, 1),
                                      at=[round(c[0], 1), round(c[1], 1)]))
        local_wins.remove(e)

def enrich_title(doc, manifest, fields):
    """纸空间标题栏: 置于图框右下角, 现有图名文字(y35/55)上方, 右对齐 x=795。"""
    psp = doc.paperspace('Layout1')
    for i, (k, v) in enumerate(fields):
        psp.add_text(f'{k}: {v}', dxfattribs={'layer': '0', 'height': 5}).set_placement(
            (795, 75 + i * 9), align=ezdxf.enums.TextEntityAlignment.RIGHT)
        manifest['added'].append(dict(layer='0(pspace)', type='title_field', label=f'{k}: {v}'))

def process(src, dst, basis, obasis, title):
    doc = ezdxf.readfile(src)
    msp = doc.modelspace()
    manifest = {'src': src.split('/')[-1], 'src_sha': hashlib.sha256(open(src, 'rb').read()).hexdigest()[:16],
                'added': []}
    if 'CENTER' not in [l.dxf.name for l in doc.linetypes]:
        doc.linetypes.add('CENTER', pattern='A,31.75,-6.35,6.35,-6.35', description='Center ____ _ ____ _ ____')
    for lname, lw in LINEWEIGHTS.items():
        if lname in doc.layers:
            doc.layers.get(lname).dxf.lineweight = lw
    for lname, color, lt in [('AXIS', 8, 'CENTER'), ('AXIS-NUM', 8, 'Continuous'),
                             ('A-DOOR-NUM', 2, 'Continuous'), ('A-WIN-NUM', 4, 'Continuous')]:
        if lname not in doc.layers:
            doc.layers.add(lname, color=color, linetype=lt)
        doc.layers.get(lname).dxf.lineweight = LINEWEIGHTS[lname]
    if 'GB' not in [s.dxf.name for s in doc.dimstyles]:
        doc.dimstyles.new('GB', dxfattribs=dict(dimtsz=140, dimtxt=180,
                                              dimexe=200, dimexo=300, dimtad=1, dimdec=0))
    apply_axis_basis(doc, msp, manifest, basis)
    number_openings(doc, msp, manifest, obasis)
    enrich_title(doc, manifest, [
        ('工程名称', 'V15 全屋改造'),
        ('图    名', title),
        ('比    例', '1:50'), ('单    位', '毫米 mm'),
        ('图    号', src.split('/')[-1].split('_')[0] + '-POC'),
        ('日    期', '2026-10-18'),
        ('说    明', 'STYLE POC — 仅制图样式, 几何/XDATA/语义未变'),
    ])
    doc.saveas(dst)
    manifest['dst'] = dst.split('/')[-1]
    manifest['dst_sha'] = hashlib.sha256(open(dst, 'rb').read()).hexdigest()[:16]
    return manifest

basis = build_axis_basis()
obasis = build_opening_basis()
m1 = process(f'{CAD}/A102_WALL_DIFF_POC_V3.dxf', f'{OUT}/A102_STYLE_POC.dxf', basis, obasis, '墙体拆改图（样式POC）')
m2 = process(f'{CAD}/A103_CONSTRUCTION_POC_V7.dxf', f'{OUT}/A103_STYLE_POC.dxf', basis, obasis, '平面布置图（样式POC）')
json.dump([m1, m2], open(f'{OUT}/style_poc_manifest.json', 'w'), ensure_ascii=False, indent=1)
print('axis basis:', basis['v'], basis['h'])
print('A102 added:', len(m1['added']), 'unmatched:', m1.get('unmatched'),
      '| A103 added:', len(m2['added']), 'unmatched:', m2.get('unmatched'))
print('openings:', m1['opening_count'], m2['opening_count'])
