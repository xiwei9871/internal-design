#!/usr/bin/env python3
"""A2 最小尺寸适配器（只读）— 对基准图 A-DIMS 做标注↔几何绑定实验。
规则：
  1. TEXT 数值 = 标注值；
  2. A-DIMS 水平线按 y 聚成尺寸行，每行线段即被量跨度的几何记录；
  3. 标签绑定：候选 = 文本 x 落入线段范围±tolerance 且 |seg_mid-tx|<800 的段；
     若最近两个候选中点距离差 <100 且长度差 >20 → UNRESOLVED（链重叠无法判）；
  4. measured_working 的原生 DIMENSION：ordinate 型(dimtype含32)单独解析，
     文字覆写 vs get_measurement 交叉校验；
  5. 输出 dimension_audit_mini.csv + 与人工标准答案对比。
"""
import ezdxf, math, csv, sys

BASE = '/Users/xiwei/interior_design/projects/c_type_home/cad/C型_原始户型数字化基准图.dxf'
MEAS = '/Users/xiwei/interior_design/projects/c_type_home/cad/measured_working.dxf'
OUT = '/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad/research/house_plan_designer_v01/dimension_audit/dimension_audit_mini.csv'

doc = ezdxf.readfile(BASE)
msp = doc.modelspace()
segs = []  # (handle, x0, x1, mid, y, len)
for e in msp:
    if e.dxf.get('layer') == 'A-DIMS' and e.dxftype() == 'LINE':
        s, en = e.dxf.start, e.dxf.end
        a = abs(math.degrees(math.atan2(en.y - s.y, en.x - s.x))) % 180
        if (a < 3 or a > 177) and math.dist((s.x, s.y), (en.x, en.y)) > 80:
            segs.append(dict(h=e.dxf.handle, x0=min(s.x, en.x), x1=max(s.x, en.x),
                             mid=(s.x + en.x) / 2, y=(s.y + en.y) / 2,
                             L=math.dist((s.x, s.y), (en.x, en.y))))
# 尺寸行聚类：线段按 y 归行；文本绑定到最近的行（文本 y 与行 y 差 <1500）
rows_y = {}
for s in segs:
    key = round(s['y'] / 200) * 200
    rows_y.setdefault(key, []).append(s)
rows = []
texts = [e for e in msp if e.dxf.get('layer') == 'A-DIMS' and e.dxftype() == 'TEXT'
         and e.dxf.text.strip().isdigit()]
for t in texts:
    tx, ty, val = t.dxf.insert.x, t.dxf.insert.y, int(t.dxf.text.strip())
    row = min(rows_y, key=lambda k: abs(k - ty))
    if abs(row - ty) > 1500:
        rows.append(dict(src='baseline', th=t.dxf.handle, label=val, seg='', seg_len='', res='',
                         cls='UNRESOLVED', note='附近无尺寸行')); continue
    # 纯位置绑定：候选 = 文本 x 严格落入线段范围的本行段（去重同端点重复段）
    cand = [s for s in rows_y[row] if s['x0'] <= tx <= s['x1']]
    uniq = {}
    for s in cand:  # 去掉端点相同的重复段
        uniq.setdefault((round(s['x0']), round(s['x1'])), s)
    cand = list(uniq.values())
    if not cand:
        rows.append(dict(src='baseline', th=t.dxf.handle, label=val, seg='', seg_len='', res='',
                         cls='UNRESOLVED', note='行内无覆盖该位置的段')); continue
    if len(cand) > 1:
        # 值辅助消歧（标注不参与审计判定，仅用于链归属；单独标记）
        vm = [s for s in cand if abs(s['L'] - val) <= 15]
        if len(vm) == 1:
            s0 = vm[0]; res = val - s0['L']
            rows.append(dict(src='baseline', th=t.dxf.handle, label=val, seg=s0['h'],
                             seg_len=round(s0['L']), res=round(res, 1),
                             cls='CONSISTENT_VALUE_ASSISTED',
                             note='位置多义，按数值一致性归入该链（辅助绑定）'))
        else:
            rows.append(dict(src='baseline', th=t.dxf.handle, label=val,
                             seg='/'.join(s['h'] for s in cand), seg_len='', res='',
                             cls='UNRESOLVED',
                             note='同行多链重叠: ' + ','.join(f"{s['h']}({s['L']:.0f})" for s in cand)))
        continue
    s0 = cand[0]
    res = val - s0['L']
    rows.append(dict(src='baseline', th=t.dxf.handle, label=val, seg=s0['h'], seg_len=round(s0['L']),
                     res=round(res, 1),
                     cls='CONSISTENT' if abs(res) <= 12 else 'DIGITIZATION_MISMATCH',
                     note='' if abs(res) <= 12 else '标注值与绘制长度不一致'))

# measured_working 原生 DIMENSION
# dimtype 位: 低3位=基础类型(0线性旋转/1对齐/2角度/3直径/4半径/5三角度/6坐标/7默认坐标X),
# bit4(16)=用户指定文字位, bit5(32)=块参照(非类型!), bit6(64)=默认文字位?, bit7(128)=纸空间。
BASE_NAMES = {0: 'linear', 1: 'aligned', 2: 'angular', 3: 'diameter',
              4: 'radius', 5: 'angular3pt', 6: 'ordinate', 7: 'ordinate_x'}

def dim_base(dimtype):
    return dimtype & 7

def is_ordinate(dimtype):
    return dim_base(dimtype) == 6

def geometric_measure(e):
    """按基础类型取正确的几何测量:
    base0 线性/旋转: p2→p3 在 dim 角度方向上的投影(界线方向);
    base1 对齐: |p2-p3| 直线距;
    base6 ordinate: 返回 None(坐标值,不可当跨度)。"""
    base = dim_base(e.dxf.get('dimtype', 0))
    p2, p3 = e.dxf.get('defpoint2'), e.dxf.get('defpoint3')
    if base == 6 or p2 is None or p3 is None:
        return None, 'ordinate' if base == 6 else 'no-defpoints'
    dx, dy = p3.x - p2.x, p3.y - p2.y
    if base == 1:
        return math.hypot(dx, dy), 'aligned:dist(p2,p3)'
    if base == 0:
        a = math.radians(e.dxf.get('angle', 0.0))
        proj = abs(dx * math.cos(a) + dy * math.sin(a))
        return proj, f'linear:proj@{e.dxf.get("angle", 0.0)}deg'
    return math.hypot(dx, dy), f'base{base}:dist(p2,p3)'

d2 = ezdxf.readfile(MEAS)
for e in d2.modelspace().query('DIMENSION'):
    dimt = e.dxf.get('dimtype', 0)
    p2, p3 = e.dxf.get('defpoint2'), e.dxf.get('defpoint3')
    meas = e.get_measurement()
    txt = (e.dxf.get('text', '') or '').strip()
    overridden = txt if txt and txt != '<>' else ''
    geom, method = geometric_measure(e)
    base = dim_base(dimt)
    if overridden and meas is not None:
        try:
            cls = 'OVERRIDE_MISMATCH' if abs(float(overridden) - meas) > 1 else 'CONSISTENT'
            note = f'覆写{overridden} vs 测量{meas:.0f} ({BASE_NAMES[base]})'
        except ValueError:
            cls, note = 'UNRESOLVED', f'非数值覆写 {overridden!r}'
    elif base == 6:
        cls, note = 'ORDINATE', f'ordinate标注 值{meas:.0f}=轴坐标,非跨度'
    elif geom is not None:
        res = (meas or 0) - geom
        cls = 'CONSISTENT' if abs(res) <= 2 else 'GEOM_GT_LABEL'
        note = f'dimtype={dimt}({BASE_NAMES[base]}+flag{dimt&~7}) {method} 残差{res:+.1f}'
    else:
        cls, note = 'UNRESOLVED', f'dimtype={dimt} 无法确定几何测量'
    rows.append(dict(src='measured', th=e.dxf.handle, label=txt or (f'{meas:.0f}' if meas else ''),
                     seg=f'{p2.x:.0f},{p2.y:.0f}->{p3.x:.0f},{p3.y:.0f}' if p2 and p3 else '',
                     seg_len=round(geom) if geom is not None else '',
                     res=round((meas or 0)-geom, 1) if geom is not None else '',
                     cls=cls, note=note))

with open(OUT, 'w', newline='') as fo:
    w = csv.DictWriter(fo, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
from collections import Counter
print(Counter(r['cls'] for r in rows))
print('wrote', OUT)
