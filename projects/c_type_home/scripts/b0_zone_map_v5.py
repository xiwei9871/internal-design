"""B0_LEVEL_ZONE_MAP_V5 + B0_CAD_TRACE_OVERLAY_V5.
Level zones traced from real CAD linework (S-S.WALL / S-楼梯 arc), not semantic rects.
Leisure hall SW corner follows the r1000 platform-edge curve on S-楼梯 layer.
"""
import json, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Hiragino Sans GB', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

ROOT = '/Users/xiwei/interior_design/projects/c_type_home'
DXF = ROOT + '/cad/freecad_import/世纪欣园FF_freecad_WORKING_v2.dxf'
ARCH = ROOT + '/design/pascal_b1/master_direct_arch_v1.json'
MODEL = ROOT + '/design/b1_blockout/b1_model.json'
OUT = ROOT + '/design/blender_b0'
OX, OY = 1298172.0, 296458.0


def load_dxf(path):
    raw = open(path, errors='ignore').read()
    lines = raw.split('\n'); ents = []; cur = None; in_e = False
    for i, l in enumerate(lines):
        v = l.strip()
        if v == 'ENTITIES': in_e = True; continue
        if v == 'ENDSEC' and in_e: in_e = False
        if not in_e: continue
        if v in ('LINE', 'ARC', 'LWPOLYLINE', 'CIRCLE'):
            if cur: ents.append(cur)
            cur = {'type': v, 'pts': []}
        if cur is not None:
            if v == '8': cur['layer'] = lines[i + 1].strip()
            elif v == '10':
                if cur['type'] == 'LWPOLYLINE': cur['pts'].append([float(lines[i + 1]), 0])
                else: cur['x0'] = float(lines[i + 1])
            elif v == '20':
                if cur['type'] == 'LWPOLYLINE': cur['pts'][-1][1] = float(lines[i + 1])
                else: cur['y0'] = float(lines[i + 1])
            elif v == '11': cur['x1'] = float(lines[i + 1])
            elif v == '21': cur['y1'] = float(lines[i + 1])
            elif v == '40': cur['r'] = float(lines[i + 1])
            elif v == '50': cur['a0'] = float(lines[i + 1])
            elif v == '51': cur['a1'] = float(lines[i + 1])
    if cur: ents.append(cur)
    return ents


def C(p): return (p[0] - OX, p[1] + OY)


def draw_cad(ax, ents, faint=False):
    LC = {'S-S.WALL': '#111', 'F-DOOR': '#e33', 'F-FURN': '#ccc',
          'F-SAN FIT': '#9cd', 'S-楼梯': '#0a0'}
    for e in ents:
        lay = e.get('layer', '?'); col = LC.get(lay, '#ddd')
        lw = 2.2 if lay == 'S-楼梯' else (1.4 if lay == 'S-S.WALL' else .8)
        if faint: col, lw = '#ddd', .7
        if e['type'] == 'LWPOLYLINE':
            pts = [C(p) for p in e['pts']]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], lw=lw, color=col)
        elif e['type'] == 'LINE':
            a, b = C([e['x0'], e['y0']]), C([e['x1'], e['y1']])
            ax.plot([a[0], b[0]], [a[1], b[1]], lw=lw, color=col)
        elif e['type'] == 'ARC':
            cx, cy = C([e['x0'], e['y0']]); a0, a1 = e['a0'], e['a1']
            if a1 < a0: a1 += 360
            th = [math.radians(t) for t in range(int(a0), int(a1) + 1, 3)]
            ax.plot([cx + e['r'] * math.cos(t) for t in th],
                    [cy + e['r'] * math.sin(t) for t in th], lw=lw, color=col)


def leisure_poly():
    """True leisure-hall outline: wall face y4700 -> D-107 angled reveal/door ->
    corridor wall x9050 -> east wall x12900 -> north y7800 -> stair edge (7800,6600)
    -> curve arm -> r1000 arc (S-楼梯) -> (5700,5600) -> close."""
    arc = [(6700 + 1000 * math.cos(math.radians(t)),
            5600 + 1000 * math.sin(math.radians(t))) for t in range(90, 181, 3)]
    return ([(5700, 4700), (8200, 4700), (8244, 4722), (8332, 4543),
             (9095, 4919), (9200, 4971), (9050, 5120), (9050, 6300),
             (9050, 6500), (12900, 6500), (12900, 7800), (7800, 7800),
             (7800, 6600), (6700, 6600)] + arc + [(5700, 5600)])


def main():
    ents = load_dxf(DXF)
    A = json.load(open(ARCH)); M = json.load(open(MODEL))
    COL = {'lower': '#b7d7f0', 'upper': '#f4c89a'}
    LEI = leisure_poly()

    # ---- FIG 1: zone map ----
    fig, ax = plt.subplots(figsize=(15, 10.5))
    for w in A['walls']:
        r = w.get('rect_mm')
        if r: ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1],
                                    fc='#888', ec='none', alpha=.5))
    for sp in M['spaces']:
        if sp['id'] in ('R-LEISURE-W', 'R-LEISURE-E'): continue
        ax.add_patch(Polygon(sp['poly'], closed=True, fc=COL[sp['level']],
                             ec='#666', lw=1, alpha=.8))
        xs = [p[0] for p in sp['poly']]; ys = [p[1] for p in sp['poly']]
        ax.text((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
                f"{sp['name']}\n{sp['level'].upper()} FFL+{0 if sp['level'] == 'lower' else 450}",
                ha='center', va='center', fontsize=8)
    ax.add_patch(Polygon(LEI, closed=True, fc=COL['upper'], ec='#a50', lw=2, alpha=.85))
    ax.text(7050, 6200, '扇形休闲厅 LEISURE\nUPPER FFL+450', ha='center',
            fontsize=9, weight='bold')
    st = M['stairs']; r = st['zone']
    ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1],
                           fc='#7ec87e', ec='green', lw=1.5, hatch='//'))
    ax.text(7500, 8100, '台阶 STAIRS 3×150', ha='center', fontsize=8, color='green')
    r = M['ramp']['rect']
    ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1],
                           fc='none', ec='#e07000', lw=2, hatch='xx'))
    ax.text(r[0] + 50, r[1] + 150, 'FUTURE ramp (overlay only)', fontsize=8,
            color='#e07000')
    draw_cad(ax, ents)
    ax.set_xlim(800, 16700); ax.set_ylim(14200, -1200); ax.set_aspect('equal')
    ax.set_title('B0 LEVEL ZONE MAP V5 — CAD trace underlay | 扇形休闲厅=UPPER +450 '
                 '真实弧边 | ramp=future overlay')
    plt.tight_layout(); plt.savefig(OUT + '/B0_LEVEL_ZONE_MAP_V5.png', dpi=140)

    # ---- FIG 2: CAD trace overlay ----
    fig, ax = plt.subplots(figsize=(15, 10.5))
    for w in A['walls']:
        r = w.get('rect_mm')
        if r: ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1],
                                    fc='#f5f5f5', ec='#ddd', lw=.4))
    for sp in M['spaces']:
        if sp['id'] in ('R-LEISURE-W', 'R-LEISURE-E'): continue
        ax.add_patch(Polygon(sp['poly'], closed=True, fc=COL[sp['level']],
                             ec='none', alpha=.45))
    ax.add_patch(Polygon(LEI, closed=True, fc=COL['upper'], ec='#f80', lw=1.5,
                         alpha=.45))
    draw_cad(ax, ents)
    th = [math.radians(t) for t in range(90, 181, 3)]
    ax.plot([6700 + 1000 * math.cos(t) for t in th],
            [5600 + 1000 * math.sin(t) for t in th], lw=3, color='#0a0')
    ax.annotate('扇形弧边 r1000 (S-楼梯)', xy=(6100, 6100), xytext=(5200, 7200),
                fontsize=9, color='#0a0',
                arrowprops=dict(arrowstyle='->', color='green'))
    ax.annotate('D-107 斜门洞', xy=(8700, 4800), xytext=(7000, 3800), fontsize=9,
                color='#e33', arrowprops=dict(arrowstyle='->', color='red'))
    ax.set_xlim(800, 16700); ax.set_ylim(14200, -1200); ax.set_aspect('equal')
    ax.set_title('B0 CAD TRACE OVERLAY V5 — 黑=S-S.WALL 红=F-DOOR 绿=S-楼梯 '
                 '灰=F-FURN 蓝=F-SAN | 填色=level zones')
    plt.tight_layout(); plt.savefig(OUT + '/B0_CAD_TRACE_OVERLAY_V5.png', dpi=140)
    print('V5 saved')


if __name__ == '__main__':
    main()
