#!/usr/bin/env python3
"""Style-only POC: A102/A103 -> *_STYLE_POC.dxf
仅允许: 图层样式/线宽/文字样式/标注表达/轴线与门窗编号/图框标题栏/纸空间设置。
禁止改动: 任何现有实体的几何、门窗洞口、台阶、拆改语义、XDATA、registry 引用。
所有新增实体登记到 style_poc_manifest.json（均为非几何标注）。
"""
import ezdxf, json, math, sys, hashlib
from ezdxf import colors

CAD = '/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad'
OUT = CAD + '/research/house_plan_designer_v01/dxf_style'

# 目标线宽（1/100mm），按 GB 习惯: 主墙0.50 新建0.50 拆除0.35 门窗0.25 尺寸0.13 家具0.13 文字0.25 轴线0.13
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

def linename(i):  # 1,2,3... / A,B,C...
    return str(i)

def make_axis_grid(doc, msp, manifest, wall_layers):
    """从现有墙中线推导轴网: 取跨度>3m的墙中线位置为轴线候选，去重编号。
    纯标注: 在 AXIS/AXIS-NUM 层新增 CENTER 线 + 圈号，不动任何墙体。"""
    # 收集墙中线
    vx, hy = [], []
    for e in msp.query('LWPOLYLINE'):
        if e.dxf.get('layer') not in wall_layers: continue
        pts = [(v[0], v[1]) for v in e.get_points('xy')]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        w, h = max(xs)-min(xs), max(ys)-min(ys)
        if w > 3000 and h < 500:  # 横向长墙
            hy.append((min(ys)+max(ys))/2)
        elif h > 3000 and w < 500:  # 竖向长墙
            vx.append((min(xs)+max(xs))/2)
        elif w > 3000 and h > 3000:  # 大轮廓(外圈)
            vx += [min(xs), max(xs)]; hy += [min(ys), max(ys)]
    def dedupe(vals, tol=400):
        vals = sorted(vals); out = []
        for v in vals:
            if not out or v - out[-1] > tol: out.append(v)
        return out
    vx, hy = dedupe(vx), dedupe(hy)
    if not vx or not hy: return
    x0, x1, y0, y1 = min(vx)-1500, max(vx)+1500, min(hy)-1500, max(hy)+1500
    EXT = 1800  # 轴线伸出图外长度
    for i, x in enumerate(vx, 1):
        msp.add_line((x, y0-EXT), (x, y1+EXT), dxfattribs={'layer': 'AXIS'})
        msp.add_circle((x, y0-EXT), 350, dxfattribs={'layer': 'AXIS-NUM'})
        msp.add_text(str(i), dxfattribs={'layer': 'AXIS-NUM', 'height': 350}).set_placement(
            (x, y0-EXT), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        manifest['added'].append(dict(layer='AXIS-NUM', type='axis_v', at=round(x,1), label=str(i)))
    for i, y in enumerate(hy):
        lab = chr(ord('A')+i)
        msp.add_line((x0-EXT, y), (x1+EXT, y), dxfattribs={'layer': 'AXIS'})
        msp.add_circle((x0-EXT, y), 350, dxfattribs={'layer': 'AXIS-NUM'})
        msp.add_text(lab, dxfattribs={'layer': 'AXIS-NUM', 'height': 350}).set_placement(
            (x0-EXT, y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        manifest['added'].append(dict(layer='AXIS-NUM', type='axis_h', at=round(y,1), label=lab))

def number_openings(doc, msp, manifest):
    """给现有门窗块参照加编号文字（不改块）。M=门 W=窗"""
    nd = nw = 0
    for e in msp.query('INSERT'):
        if e.dxf.name == 'SYM-DOOR-LEAF':
            nd += 1; lab, lay = f'M{nd}', 'A-DOOR-NUM'
        elif e.dxf.name == 'SYM-WIN-SPAN':
            nw += 1; lab, lay = f'W{nw}', 'A-WIN-NUM'
        else: continue
        x, y = e.dxf.insert.x, e.dxf.insert.y
        msp.add_text(lab, dxfattribs={'layer': lay, 'height': 250}).set_placement(
            (x+300, y+300), align=ezdxf.enums.TextEntityAlignment.BOTTOM_LEFT)
        manifest['added'].append(dict(layer=lay, type='opening_num', ref=e.dxf.name,
                                      handle=e.dxf.handle, label=lab, at=[round(x,1), round(y,1)]))

def enrich_title(doc, manifest, fields):
    """纸空间标题栏字段（纯标注）。"""
    psp = doc.paperspace('Layout1')
    x0, y0 = 660, 40   # A1 右下角区域, mm
    for i, (k, v) in enumerate(fields):
        psp.add_text(f'{k}: {v}', dxfattribs={'layer': '0', 'height': 6}).set_placement((x0, y0 - i*8))
        manifest['added'].append(dict(layer='0(pspace)', type='title_field', label=f'{k}: {v}'))

def process(src, dst, wall_layers, title):
    doc = ezdxf.readfile(src)
    msp = doc.modelspace()
    manifest = {'src': src.split('/')[-1], 'src_sha': hashlib.sha256(open(src,'rb').read()).hexdigest()[:16],
                'added': []}
    # 1) 图层线宽/线型规范化
    if 'CENTER' not in [l.dxf.name for l in doc.linetypes]:
        doc.linetypes.add('CENTER', pattern='A,31.75,-6.35,6.35,-6.35', description='Center ____ _ ____ _ ____')
    for lname, lw in LINEWEIGHTS.items():
        if lname in doc.layers:
            doc.layers.get(lname).dxf.lineweight = lw
    for lname, color, lt in [('AXIS', 1, 'CENTER'), ('AXIS-NUM', 3, 'Continuous'),
                             ('A-DOOR-NUM', 2, 'Continuous'), ('A-WIN-NUM', 4, 'Continuous')]:
        if lname not in doc.layers:
            doc.layers.add(lname, color=color, linetype=lt)
        doc.layers.get(lname).dxf.lineweight = LINEWEIGHTS[lname]
    # 2) GB 标注样式（新增定义，不改现有 DIMENSION 实体）
    if 'GB' not in [s.dxf.name for s in doc.dimstyles]:
        doc.dimstyles.new('GB', dxfattribs=dict(dimtsz=140, dimtxt=180,
                                              dimexe=200, dimexo=300, dimtad=1, dimdec=0))
    # 3) 轴网 + 门窗编号（新增标注实体）
    make_axis_grid(doc, msp, manifest, wall_layers)
    number_openings(doc, msp, manifest)
    # 4) 标题栏
    enrich_title(doc, manifest, [
        ('工程名称', 'V15 全屋改造'),
        ('图    名', title),
        ('比    例', '1:50'),
        ('单    位', '毫米 mm'),
        ('图    号', src.split('/')[-1].split('_')[0] + '-POC'),
        ('日    期', '2026-10-18'),
        ('说    明', 'STYLE POC — 仅制图样式, 几何/XDATA/语义未变'),
    ])
    doc.saveas(dst)
    manifest['dst'] = dst.split('/')[-1]
    manifest['dst_sha'] = hashlib.sha256(open(dst,'rb').read()).hexdigest()[:16]
    return manifest

m1 = process(f'{CAD}/A102_WALL_DIFF_POC_V3.dxf', f'{OUT}/A102_STYLE_POC.dxf',
             wall_layers={'A-WALL-RETAIN','A-WALL-RETAIN-STRUCT','A-WALL-NEW'},
             title='墙体拆改图（样式POC）')
m2 = process(f'{CAD}/A103_CONSTRUCTION_POC_V7.dxf', f'{OUT}/A103_STYLE_POC.dxf',
             wall_layers={'A-WALL','A-COLUMN'},
             title='平面布置图（样式POC）')
json.dump([m1, m2], open(f'{OUT}/style_poc_manifest.json','w'), ensure_ascii=False, indent=1)
print('A102 added:', len(m1['added']), '| A103 added:', len(m2['added']))
EOF_MARKER = None
