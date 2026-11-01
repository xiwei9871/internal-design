#!/usr/bin/env python3
"""A201 lighting V2 candidate (FUNCTIONAL_DESIGN_REVIEW, not A/B validated).
Reads data/lighting_points.json (unchanged) -> data/lighting_points_v2.{json,csv},
data/lighting_changes.csv, data/lighting_compare.csv, qa/a201_v2_lighting_qa.json.
Every original point gets an action; every new point a reason tied to a real object."""
import csv, json
from collections import Counter
from shapely.geometry import Point

from cd_common import DATA, HERE, NAMES
from lighting_review import context, checks

FL_HI = 450

# ---- actions on original points: id -> (action, new_xy or None, reason) ----
ACTIONS = {
    'L006': ('MOVE', (10400, 3650), '原位在衣柜 R3_WARDROBE(顶 2650)正上方, 吊顶已被柜体占满; 移至柜门前, 兼作衣柜照明, 并离床头(东侧 x11212)更远'),
    'L012': ('MOVE', (10750, 10100), '原位在客卧衣柜 B11_Rectangle045(顶 2650)正上方; 移至柜门前(柜面 x10418)'),
    'L029': ('MOVE', (13500, 3550), '原位在母亲房衣柜 B11_Rectangle015(顶 2650)正上方; 移至柜门前'),
    'L030': ('MOVE', (14300, 3550), '同上; 不放回 x14850 以免靠近床头(东侧 x15133)造成卧姿眩光'),
    'L040': ('MOVE', (14650, 10250), '原位在书房卧榻 STUDY_V1_DAYBED 正上方(躺卧眩光); 移至卧榻前'),
    'L047': ('MOVE', (6350, 3450), '原位在冰箱上柜 FRIDGE-OVERHEAD(顶 2410)正上方; 移至冰箱门前'),
    'L050': ('MOVE', (9717, 12150), '原位在阳光房高柜/洗衣柜冠板正上方; 移至柜面前 300'),
    'L033': ('MOVE', (10400, 5500), '原位在次主卫淋浴托盘 R3_SHOWER_TRAY 投影内; 移出淋浴区(玻璃外 ≥150), 淋浴靠透光玻璃取光'),
    'L088': ('REMOVE', None, '台面任务灯位于东侧吊柜 K-WALL-E(底 1744, 顶 2410)正上方, 光被吊柜挡住照不到台面; 由吊柜下灯带 LN-K1 替代'),
    'L089': ('REMOVE', None, '同上, 由 LN-K1 替代'),
    'L090': ('REMOVE', None, '同上, 位于油烟机段, 由油烟机自带灯 + LN-K2 替代'),
    'L023': ('CONVERT', (15700, 5536), '主卫淋浴间(玻璃 x15206 以东, 约 1.5m²)内原有 2 盏; 合并为 1 盏淋浴专用灯居中, 减少湿区灯具, 型式由电气按分区定'),
    'L024': ('REMOVE', None, '与 L023 合并(见上)'),
}
LAYER_CHANGE = {   # keep position, change layer/group only
    'L064': ('accent', 'SOFA_WALL', '位于沙发靠背(x3391)外侧 40mm, 实为西墙洗墙光; 归入"沙发墙"氛围组单独调光'),
    'L065': ('accent', 'SOFA_WALL', '同上'),
    'L066': ('accent', 'SOFA_WALL', '同上'),
    'L078': ('accent', 'TV_WALL', '位于电视柜(x7398)前 100, 实为电视墙洗墙光; 观看时可单独调暗. 反射估算: 沙发 x≈4000、坐姿眼高 1.1m、屏幕在 x≈7700 时, 顶灯镜像约在 z≈2500, 高于常见屏幕上沿; 屏幕尺寸/安装高度未建模, 待确认'),
    'L079': ('accent', 'TV_WALL', '同上'),
    'L080': ('accent', 'TV_WALL', '同上'),
    'L001': ('accent', 'TV_WALL', '次主卧电视柜(x8050-8450)上方, 电视墙洗墙光; 单独调光'),
    'L002': ('accent', 'TV_WALL', '同上'),
}
# mirror orientation from model mirror bbox: guest mirror x8026-8029/y8064-8940 -> V
ORIENT = {'L083': 'V', 'L084': 'H', 'L085': 'H'}
GROUP = {'base': 'BASE', 'task': 'TASK', 'accent': 'ACCENT', 'night': 'NIGHT'}

# ---- new points (all PROPOSED) ----
NEW = [
    # mother: night route bed -> bedroom door -> vestibule -> master bath
    dict(id='N-M1', room='mother_bedroom', layer='night', type='NIGHT_UNDERBED_SENSOR', x=14100, y=2950, z=FL_HI + 150,
         mount='floor', cct_k=3000, reason='母亲床北侧下床处(床 y≤2916)感应低位光: 起身即亮, 不照眼', src='model:HOUSE_V1_MOTHER_mattress'),
    dict(id='N-M2', room='mother_bedroom', layer='night', type='NIGHT_WALL_LOW', x=12950, y=4350, z=FL_HI + 300,
         mount='wall', cct_k=3000, reason='卧室门(12250,4550)东侧墙面低位灯, 引导至门口', src='A103 door (12250,4550)'),
    dict(id='N-M3', room='vestibule', layer='night', type='NIGHT_WALL_LOW', x=11700, y=5300, z=FL_HI + 300,
         mount='wall', cct_k=3000, reason='前过道西墙低位感应灯, 连接卧室门与主卫门', src='A202 vestibule zone'),
    dict(id='N-M4', room='master_bath', layer='night', type='NIGHT_WALL_LOW', x=13250, y=5250, z=FL_HI + 300,
         mount='wall', cct_k=3000, reason='主卫门内低位夜灯, 夜间如厕不开主灯; 位置避开淋浴区', src='A103 door (13000,5125)'),
    # bedside reading (task) — head side from bedside cabinets
    dict(id='R-M1', room='mother_bedroom', layer='task', type='WALL_READING', x=15250, y=1040, z=FL_HI + 1200,
         mount='wall', cct_k=3000, reason='床头柜 HOUSE_V2_MOTHER_0 上方床头阅读灯(床头朝东)', src='model:HOUSE_V2_MOTHER_0_case_panel'),
    dict(id='R-M2', room='mother_bedroom', layer='task', type='WALL_READING', x=15250, y=3190, z=FL_HI + 1200,
         mount='wall', cct_k=3000, reason='床头柜 HOUSE_V2_MOTHER_1 上方', src='model:HOUSE_V2_MOTHER_1_case_panel'),
    dict(id='R-C1', room='couple_bedroom', layer='task', type='WALL_READING', x=11350, y=830, z=FL_HI + 1200,
         mount='wall', cct_k=3000, reason='床头柜 HOUSE_V2_COUPLE_0 上方(床头朝东)', src='model:HOUSE_V2_COUPLE_0_case_panel'),
    dict(id='R-C2', room='couple_bedroom', layer='task', type='WALL_READING', x=11350, y=3340, z=FL_HI + 1200,
         mount='wall', cct_k=3000, reason='床头柜 HOUSE_V2_COUPLE_1 上方', src='model:HOUSE_V2_COUPLE_1_case_panel'),
    dict(id='R-G1', room='guest_bedroom', layer='task', type='WALL_READING', x=12850, y=9450, z=FL_HI + 1200,
         mount='wall', cct_k=3000, reason='客卧床头(床头板 x12764)北侧阅读灯', src='model:HOUSE_V2_GUEST_head_panel'),
    dict(id='N-C1', room='couple_bedroom', layer='night', type='NIGHT_WALL_LOW', x=8100, y=4250, z=FL_HI + 300,
         mount='wall', cct_k=3000, reason='次主卧门(8625,4550)旁低位夜灯, 夜间去次主卫', src='A103 door (8625,4550)'),
    dict(id='R-M3', room='mother_bedroom', layer='task', type='MIRROR_LIGHT', x=11760, y=660, z=1760,
         mount='wall', cct_k=3500, reason='梳妆镜 HOUSE_V2_Vanity_mirror_glass(z1303-1713)上沿镜前灯; 现方案梳妆位无面光, 顶灯 L025 在其北侧 500 会在脸上投影',
         src='model:HOUSE_V2_Vanity_mirror_glass', orient='V'),
    # kitchen under-cabinet (replaces L088-L090)
    dict(id='LN-K1', room='kitchen', layer='task', type='LED_UNDER_CABINET', x=7440, y=1460, z=1744,
         mount='under_cabinet', cct_k=4000, reason='东侧吊柜底板(z1744)下灯带, y535-2380, 直接照台面 B11_K-RUN-E_COUNTER',
         src='model:B11_K-WALL-E_BASE', path=[[7440, 560], [7440, 2380]]),
    dict(id='LN-K2', room='kitchen', layer='task', type='LED_UNDER_CABINET', x=7440, y=3525, z=1744,
         mount='under_cabinet', cct_k=4000, reason='油烟机北侧吊柜下灯带 y3320-3730; 油烟机段由烟机自带灯', src='model:B11_K-WALL-E_BASE',
         path=[[7440, 3320], [7440, 3730]]),
]

SCENES = {
    'mother_bedroom': '门口+床头双控 BASE; 床头 TASK 各自开关; NIGHT 组 = 床下感应 + 过道/主卫感应, 定时熄灭',
    'couple_bedroom': '门口+床头双控 BASE; TV_WALL 调光; 床头 TASK; NIGHT 门旁感应',
    'guest_bedroom': 'BASE 门口单控(门位 H4 待定); 床头 TASK',
    'living': 'ENTRY / DINING(吊灯) / LIVING BASE / SOFA_WALL / TV_WALL 分组, 观影场景只留 SOFA_WALL 低亮',
    'kitchen': 'BASE 与吊柜下灯带分开控制',
    'study': 'BASE 分两组(书桌区/卧榻区) + 书桌 TASK',
    'master_bath': 'BASE + 镜前灯 + 淋浴灯分控; NIGHT 感应',
    'secondary_bath': 'BASE + 镜前灯分控',
    'guest_bath': 'BASE + 镜前灯分控',
    'hallway': 'BASE 两地控制 + 跌级灯带单独',
}


def build():
    pts, ctx = context()
    v2, changes = [], []
    for p in pts:
        q = dict(p)
        act, xy, why = ACTIONS.get(p['id'], ('KEEP', None, ''))
        if p['id'] in LAYER_CHANGE:
            lay, grp, why = LAYER_CHANGE[p['id']]
            q['layer'] = lay; q['group'] = grp; act = 'KEEP_REGROUP'
        if act == 'REMOVE':
            changes.append({'id': p['id'], 'room': p['room'], 'action': act, 'from': [p['x'], p['y']], 'to': None,
                            'type_from': p['type'], 'type_to': None, 'reason': why}); continue
        if xy: q['x'], q['y'] = xy
        if act == 'CONVERT': q['type'] = 'SHOWER_LIGHT'; q['note'] = '淋浴区灯具: 型式/电压/IP 由电气按 GB 55024 第4.6.6条分区确定'
        if q['type'] == 'MIRROR_LIGHT':
            q['orient'] = ORIENT.get(p['id'], 'H')
            if p['id'] == 'L083' and act == 'KEEP': q['note'] = '镜子 CBM_GUEST_MIRROR 沿 y 方向, 图示改为竖向(V1 图示方向有误)'
        q.setdefault('group', GROUP.get(q['layer'], q['layer'].upper()))
        q['action'] = act
        q['status'] = 'PROPOSED' if act != 'KEEP' else 'OWNER_REVIEW'
        q['reason'] = why
        q['circuit'] = f"C-{q['room']}-{q['group']}"
        v2.append(q)
        changes.append({'id': p['id'], 'room': p['room'], 'action': act, 'from': [p['x'], p['y']],
                        'to': [q['x'], q['y']], 'type_from': p['type'], 'type_to': q['type'], 'reason': why})
    for n in NEW:
        q = {'id': n['id'], 'room': n['room'], 'room_name': NAMES.get(n['room'], n['room']), 'layer': n['layer'],
             'type': n['type'], 'x': n['x'], 'y': n['y'], 'z_abs': n['z'], 'mount': n['mount'], 'cct_k': n['cct_k'],
             'beam_deg': None, 'lumen': None, 'group': GROUP[n['layer']], 'circuit': f"C-{n['room']}-{GROUP[n['layer']]}",
             'switch_id': f"SW-{n['room']}", 'source': n['src'], 'status': 'PROPOSED', 'action': 'ADD',
             'reason': n['reason'], 'note': ''}
        if 'path' in n: q['path'] = n['path']
        if n['type'] == 'MIRROR_LIGHT': q['orient'] = n.get('orient', 'H')
        v2.append(q)
        changes.append({'id': n['id'], 'room': n['room'], 'action': 'ADD', 'from': None, 'to': [n['x'], n['y']],
                        'type_from': None, 'type_to': n['type'], 'reason': n['reason']})
    return pts, v2, changes, ctx


def qa(pts, v2, changes, ctx):
    res = []
    for p in v2:
        for sev, code, det in checks(p, ctx):
            res.append({'id': p['id'], 'room': p['room'], 'severity': sev, 'code': code, 'detail': str(det)})
    acted = {c['id'] for c in changes}
    missing = [p['id'] for p in pts if p['id'] not in acted]
    if missing: res.append({'id': ','.join(missing), 'severity': 'FAIL', 'code': 'UNTRACED_ORIGINAL', 'detail': ''})
    route = {'mother_bedroom', 'vestibule', 'master_bath'}
    have = {p['room'] for p in v2 if p['layer'] == 'night'}
    if not route <= have:
        res.append({'id': '-', 'severity': 'FAIL', 'code': 'NIGHT_ROUTE_GAP', 'detail': str(route - have)})
    if any(p.get('photometry_claim') for p in v2):
        res.append({'id': '-', 'severity': 'FAIL', 'code': 'PHOTOMETRY_CLAIM', 'detail': ''})
    fails = [r for r in res if r['severity'] == 'FAIL']
    flags = [r for r in res if r['severity'] == 'FLAG']
    explained = {'L023'}            # shower light kept by design, zone decided by electrical
    unexplained_flags = [f for f in flags if f['id'] not in explained]
    return {'result': 'PASS' if not fails and not unexplained_flags else 'FAIL', 'fails': fails, 'flags': flags,
            'unexplained_flags': unexplained_flags, 'counts': {'original': len(pts), 'v2': len(v2),
            'actions': dict(Counter(c['action'] for c in changes))},
            'scope': 'FUNCTIONAL_DESIGN_REVIEW: geometry/data checks only; no illuminance or glare compliance claimed'}


def compare(pts, v2):
    rooms = sorted({p['room'] for p in pts} | {p['room'] for p in v2})
    rows = []
    for r in rooms:
        a = Counter(p['layer'] for p in pts if p['room'] == r)
        b = Counter(p['layer'] for p in v2 if p['room'] == r)
        rows.append({'room': r, 'room_name': NAMES.get(r, r), 'v1_total': sum(a.values()), 'v2_total': sum(b.values()),
                     **{f'v1_{k}': a.get(k, 0) for k in ('base', 'task', 'accent', 'night')},
                     **{f'v2_{k}': b.get(k, 0) for k in ('base', 'task', 'accent', 'night')},
                     'scene_control': SCENES.get(r, '')})
    return rows


def main():
    pts, v2, changes, ctx = build()
    q = qa(pts, v2, changes, ctx)
    (DATA / 'lighting_points_v2.json').write_text(json.dumps(
        {'status': 'CANDIDATE_PROPOSED (not owner-approved)', 'review': 'FUNCTIONAL_DESIGN_REVIEW; A/B NOT_RUN',
         'units': 'mm', 'z': 'absolute (lower floor ±0)', 'cct_range_k': [3000, 4000], 'base_file': 'lighting_points.json (unchanged)',
         'points': v2, 'scenes': SCENES}, ensure_ascii=False, indent=1))
    keys = ['id', 'room', 'room_name', 'layer', 'group', 'type', 'x', 'y', 'z_abs', 'mount', 'cct_k', 'circuit',
            'switch_id', 'action', 'status', 'source', 'reason', 'note']
    with open(DATA / 'lighting_points_v2.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore', lineterminator='\n'); w.writeheader(); w.writerows(v2)
    with open(DATA / 'lighting_changes.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'room', 'action', 'from', 'to', 'type_from', 'type_to', 'reason'],
                           lineterminator='\n'); w.writeheader(); w.writerows(changes)
    rows = compare(pts, v2)
    with open(DATA / 'lighting_compare.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
    (HERE / 'qa').mkdir(exist_ok=True)
    (HERE / 'qa' / 'a201_v2_lighting_qa.json').write_text(json.dumps(q, ensure_ascii=False, indent=1))
    print(json.dumps({k: q[k] for k in ('result', 'counts')}, ensure_ascii=False), 'fails', q['fails'], 'flags', q['flags'])
    return q


if __name__ == '__main__':
    main()
