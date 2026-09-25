#!/usr/bin/env python3
"""Task03A QC + presentation renders. task01 coords.
RC2.2: window register overlay, wall/window conflict check, before/after
cleanup sheet, and s3 split into owner-facing presentation + QC diagnostic."""
import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from pathlib import Path

plt.rcParams['font.family'] = 'PingFang SC'
ROOT = Path(__file__).resolve().parent.parent
M = json.load(open(ROOT / 'current_existing' / 'current_existing_v1.json'))
CD = json.load(open(ROOT / 'concept' / 'concept_data.json'))
WB = json.load(open(ROOT / 'qc' / 'walls_baseline_246ff12.json'))  # RC2.1 walls
QC = ROOT / 'qc'

WCOL = {'keep': '#9aa0a6', 'noopen': '#d93025', 'remove': '#dadce0', 'new': '#188038',
        'conflict': '#e8710a', 'review': '#9334e6'}
WIN_COL = {'CONFIRMED': '#1a73e8', 'MEASURED': '#1a73e8',
           'TO_VERIFY': '#9334e6', 'PROPOSED': '#188038'}

def wcolor(w):
    cls = w['wall_class']
    if w['disposition'] != 'EXISTING':
        return WCOL['conflict'] if 'CONFLICT' in cls else WCOL['remove']
    if 'NO_DEMOLITION' in cls or 'NO_OPEN' in cls: return WCOL['noopen']
    if 'REVIEW' in cls or 'CONFLICT' in cls: return WCOL['review']
    return WCOL['keep']

def draw_walls(ax, mode='current', walls=None, presentation=False):
    for w in (walls if walls is not None else M['walls']):
        x1, y1, x2, y2 = w['rect_mm']
        if mode == 'current' and w['disposition'] != 'EXISTING':
            continue
        c = wcolor(w)
        if presentation and 'REVIEW' in w['wall_class']:
            c = WCOL['keep']          # classification dispute is QC info, not owner-facing
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor=c, edgecolor='none', zorder=2))

def draw_windows(ax, qc=False):
    """window/glazing graphics — glass lines in the wall-band gap + bay outlines."""
    for win in M.get('windows', []):
        vs = win['verification_status']
        col = WIN_COL[vs]
        r = win['opening_rect_mm']
        if win['window_type'] == 'PROPOSED_BALCONY_ENCLOSURE':
            if (r[2] - r[0]) >= (r[3] - r[1]):
                ax.plot([r[0], r[2]], [(r[1] + r[3]) / 2] * 2, color=col, lw=1.8, ls='--', zorder=4)
                tx, ty = (r[0] + r[2]) / 2, r[3] + 160
            else:
                ax.plot([(r[0] + r[2]) / 2] * 2, [r[1], r[3]], color=col, lw=1.8, ls='--', zorder=4)
                tx, ty = r[2] + 160, (r[1] + r[3]) / 2
            ax.text(tx, ty, 'PROPOSED enclosure' + (f' ({win["window_id"]})' if qc else ''),
                    fontsize=6, color=col, ha='center')
            continue
        x1, y1, x2, y2 = r
        if (x2 - x1) >= (y2 - y1):
            for i in (0.25, 0.5, 0.75):
                y = y1 + (y2 - y1) * i
                ax.plot([x1, x2], [y, y], color=col, lw=1.0, zorder=4)
        else:
            for i in (0.25, 0.5, 0.75):
                x = x1 + (x2 - x1) * i
                ax.plot([x, x], [y1, y2], color=col, lw=1.0, zorder=4)
        bay = win.get('bay')
        if bay:
            for j in bay['jambs']:
                ax.add_patch(Rectangle((j[0], j[1]), j[2] - j[0], j[3] - j[1],
                                       facecolor='none', edgecolor=col, lw=1.0, zorder=4))
            f = bay['front']
            ax.add_patch(Rectangle((f[0], f[1]), f[2] - f[0], f[3] - f[1],
                                   facecolor='none', edgecolor=col, lw=1.4, zorder=4))
        if qc:
            tag = f"{win['window_id']}\n{vs}" if vs != 'CONFIRMED' else win['window_id']
            ax.text((x1 + x2) / 2, y2 + 120, tag, fontsize=5, color=col,
                    ha='center', zorder=6)

def draw_door_symbols(ax):
    """presentation-grade door: white gap + leaf line + swing arc."""
    import math
    for o in M['openings']:
        if o['kind'] == 'open_passage':
            continue
        x1, y1, x2, y2 = o['rect_mm']
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor='white',
                               edgecolor='none', zorder=3))
        if 'glaz' in o['kind'] or 'glass' in o['kind']:
            for i in (0.3, 0.7):
                if (x2 - x1) >= (y2 - y1):
                    x = x1 + (x2 - x1) * i
                    ax.plot([x, x], [y1, y2], color='#1a73e8', lw=1.2, zorder=4)
                else:
                    y = y1 + (y2 - y1) * i
                    ax.plot([x1, x2], [y, y], color='#1a73e8', lw=1.2, zorder=4)
        else:
            span = max(x2 - x1, y2 - y1)
            if (x2 - x1) >= (y2 - y1):   # horizontal wall: leaf swings in -y
                ax.plot([x1, x1 + span * 0.7], [y1, y1 - span * 0.7], color='#555', lw=1.0, zorder=4)
                arc = matplotlib.patches.Arc((x1, y1), 2 * span * 0.7, 2 * span * 0.7,
                                             angle=0, theta1=270, theta2=360,
                                             color='#999', lw=0.7, zorder=4)
            else:                       # vertical wall: leaf swings +x
                ax.plot([x2, x2 + span * 0.7], [y2, y2 - span * 0.7], color='#555', lw=1.0, zorder=4)
                arc = matplotlib.patches.Arc((x2, y2), 2 * span * 0.7, 2 * span * 0.7,
                                             angle=0, theta1=270, theta2=360,
                                             color='#999', lw=0.7, zorder=4)
            ax.add_patch(arc)

def draw_furn(ax, label_ids=True):
    for f in CD['furniture']:
        x1, y1, x2, y2 = f['rect']
        c = '#f9ab00' if f['layer'] == 'A-FURN-EXST-KEEP' else \
            ('#34a853' if f['layer'] == 'A-FIXT-PLUMB' else
             ('#1a73e8' if 'ACCESS' in f['layer'] else '#f4b400'))
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor=c, alpha=.35,
                               edgecolor=c, lw=1.0, zorder=3))
        if label_ids:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, f['id'], fontsize=5.5,
                    ha='center', va='center', zorder=5)

def draw_furn_presentation(ax):
    """owner-facing furniture: friendly labels, no internal IDs."""
    NICE = {'SOFA-3': '3-seat sofa', 'SOFA-2': '2-seat sofa', 'LOUNGE-1': 'lounge',
            'COFFEE-MOV': 'coffee (movable)', 'PROJ-SCREEN': 'screen wall',
            'DIN-TABLE': 'dining 1500×600', 'K-CAB': 'kitchen cabinets (keep)',
            'MB-BED': 'bed 1800×2100', 'MB-WARD': 'wardrobe (keep)',
            'SMB-BED': 'bed 1800×2100', 'SMB-WARD': 'wardrobe',
            'ST-DESK': 'desk 1700×800', 'ST-DAYBED': 'daybed', 'ST-BOOK': 'storage (keep)',
            'ST-NAS': 'NAS/printer shelf', 'GB-BUNK': 'bunk 1500×2100 (lower+optional upper)',
            'GB-DESK': 'desk', 'GB-GLASSDOOR-ZONE': None, 'GB-BALC-STEP': None,
            'NB-WD': 'W+D stacked (keep)', 'NB-PLANTS': None, 'NB-TEA': 'tea set (movable)',
            'SHOE-CAB': 'shoe cab (keep)', 'BENCH': 'bench',
            'GBATH-VANITY': 'vanity', 'GBATH-WC': 'WC', 'GBATH-SHOWER': 'shower',
            'GBATH-3KG': '3kg washer', 'MBATH-SHOWER': 'shower 1600×900',
            'MBATH-WC': 'WC', 'MBATH-VANITY': 'vanity', 'MBATH-RAD': 'radiator',
            'SMB2-SHOWER': 'shower 800×1650', 'SMB2-WC': 'WC', 'SMB2-VANITY': 'vanity',
            'RAMP': 'ramp 3000×1100 (provisional)', 'STAIR': '2 risers'}
    for f in CD['furniture']:
        x1, y1, x2, y2 = f['rect']
        nice = NICE.get(f['id'], f['id'])
        c = '#f9ab00' if f['layer'] == 'A-FURN-EXST-KEEP' else \
            ('#34a853' if f['layer'] == 'A-FIXT-PLUMB' else
             ('#1a73e8' if 'ACCESS' in f['layer'] else '#f4b400'))
        if f['layer'] == 'A-NOTE' and nice is None:
            continue
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor=c, alpha=.3,
                               edgecolor=c, lw=0.9, zorder=3))
        if nice and (x2 - x1) * (y2 - y1) > 300000:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, nice, fontsize=6,
                    ha='center', va='center', zorder=5, color='#333')

def draw_openings(ax):
    for o in M['openings']:
        x1, y1, x2, y2 = o['rect_mm']
        c = '#9334e6' if 'glaz' in o.get('kind', '') or 'glass' in o.get('kind', '') else '#188038'
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor='none',
                               edgecolor=c, lw=1.6, ls='--', zorder=4))
        ax.text((x1 + x2) / 2, y2 + 90, o['id'], fontsize=5, ha='center', color=c, zorder=5)

def draw_new(ax):
    for r in CD['new_walls']:
        ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor=WCOL['new'], zorder=4))
    for r in CD['new_doors']:
        ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='#9334e6', zorder=4))

def base(title):
    fig, ax = plt.subplots(figsize=(13, 14), dpi=130)
    ax.set_xlim(0, 16800); ax.set_ylim(-900, 15200); ax.set_aspect('equal')
    ax.set_title(title, fontsize=13); ax.grid(alpha=.15)
    return fig, ax

def save(fig, name):
    fig.savefig(QC / name, bbox_inches='tight', facecolor='white')
    fig.savefig(QC / name.replace('.png', '.pdf'), bbox_inches='tight', facecolor='white')
    plt.close(fig); print(name)

QC_LEGEND = [
    Line2D([], [], color=WCOL['keep'], lw=6, label='existing wall (modifiable)'),
    Line2D([], [], color=WCOL['noopen'], lw=6, label='owner-declared no-opening / exterior wall'),
    Line2D([], [], color=WCOL['remove'], lw=6, label='demolished / absent wall'),
    Line2D([], [], color=WCOL['new'], lw=6, label='NEW wall'),
    Line2D([], [], color=WIN_COL['CONFIRMED'], lw=2, label='existing window (3-line glazing)'),
    Line2D([], [], color=WIN_COL['PROPOSED'], lw=2, ls='--', label='proposed glazing (N balcony)'),
    Line2D([], [], color='#1a73e8', lw=1.5, label='existing glass door'),
    Line2D([], [], color='#f4b400', lw=6, alpha=.5, label='furniture (proposed)'),
    Line2D([], [], color='#f9ab00', lw=6, alpha=.5, label='furniture/cabinet KEEP'),
    Line2D([], [], color='#34a853', lw=6, alpha=.5, label='plumbing fixture'),
    Line2D([], [], color='#e8710a', lw=1.5, ls=':', label='door-swing envelope'),
    Line2D([], [], color='#188038', lw=1.5, ls='-.', label='clear circulation zone/path'),
    Line2D([], [], color='#9334e6', lw=1.5, ls='--', label='TO_VERIFY geometry/opening'),
]

# ================================================================ S1 current existing
fig, ax = base('Task03A · Current Existing Plan (measured DWG)')
draw_walls(ax, 'current'); draw_windows(ax, qc=True); draw_openings(ax)
for k in M['keep_items']:
    x1, y1, x2, y2 = k['rect_mm']
    ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor='#f9ab00', alpha=.3, edgecolor='#f9ab00', zorder=3))
    ax.text((x1 + x2) / 2, (y1 + y2) / 2, k['id'], fontsize=5.5, ha='center')
st = M['split_level']['zone_mm']
ax.add_patch(Rectangle((st[0], st[1]), st[2]-st[0], st[3]-st[1], facecolor='#1a73e8', alpha=.4, zorder=3))
ax.text(st[0]-400, st[3]+150, '2 risers, delta LEVEL_TO_VERIFY', fontsize=7, color='#1a73e8')
ax.text(7900, 14100, 'N BALCONY: OPEN now; enclosure PROPOSED', fontsize=7, color='#188038')
ax.text(2600, 1300, 'LIFE BALCONY parapet\n(real, measured)', fontsize=6, color='#666')
ax.legend(handles=QC_LEGEND, fontsize=6, loc='lower left', ncol=2)
save(fig, 'task03a_s1_current_existing.png')

# ================================================================ S2 demolition / keep / new
fig, ax = base('Task03A · Demolition / Keep / New')
draw_walls(ax, 'all'); draw_windows(ax, qc=True); draw_openings(ax); draw_new(ax)
ax.text(9200, 5400, 'NEW bath enclosure:\nsouth partition + annex walls\n(shell N/W/E kept)', fontsize=6, color=WCOL['new'])
ax.legend(handles=QC_LEGEND, fontsize=6, loc='lower left', ncol=2)
save(fig, 'task03a_s2_demolition.png')

# ================================================================ S3 PRESENTATION (owner-facing)
fig, ax = base('Task03A · Proposed Furniture Plan — PRESENTATION')
draw_walls(ax, 'current', presentation=True); draw_windows(ax); draw_door_symbols(ax)
draw_furn_presentation(ax); draw_new(ax)
ROOMS = [('FLEX FAMILY ROOM 客厅', 4200, 10600), ('DINING 餐厅', 3700, 6600),
         ('KITCHEN 厨房', 6200, 2500), ('LIFE BALC 生活阳台', 2600, 1500),
         ('MASTER BED 主卧', 12500, 2800), ('SEC MASTER BED 次主卧', 9000, 2800),
         ('SEC MASTER BATH 次主卫', 9200, 5600), ('MASTER BATH 主卫', 14200, 5500),
         ('STUDY 书房', 14000, 10000), ('GUEST BED 客卧', 11750, 9900),
         ('GUEST BATH 客卫', 8200, 9600), ('N BALCONY 北阳台', 9800, 12200),
         ('LANDING/FOYER 平台', 8000, 6800)]
for t, x, y in ROOMS:
    ax.text(x, y, t, fontsize=8, fontweight='bold', color='#202124', zorder=6)
# key dimensions only
for txt, x, y in [('living clear ~4850×4850 (provisional)', 4300, 9000),
                  ('sec-master bath ~5.0m²', 9050, 3500),
                  ('level delta TO_VERIFY ≤350/~400', 7200, 7900)]:
    ax.text(x, y, txt, fontsize=6, color='#666', style='italic')
ax.legend(handles=[Line2D([], [], color=WCOL['keep'], lw=6, label='existing wall'),
                   Line2D([], [], color=WCOL['noopen'], lw=6, label='exterior / no-opening wall'),
                   Line2D([], [], color=WCOL['new'], lw=6, label='new wall'),
                   Line2D([], [], color='#1a73e8', lw=2, label='window / glass door'),
                   Line2D([], [], color='#188038', lw=2, ls='--', label='proposed balcony glazing'),
                   Line2D([], [], color='#f4b400', lw=6, alpha=.5, label='furniture'),
                   Line2D([], [], color='#34a853', lw=6, alpha=.5, label='bathroom fixture'),
                   Line2D([], [], color='#1a73e8', lw=6, alpha=.4, label='stairs / ramp')],
          fontsize=6, loc='lower left')
save(fig, 'task03a_s3_furniture_presentation.png')

# ================================================================ S3 QC (diagnostic)
fig, ax = base('Task03A · Proposed Furniture Plan — QC')
draw_walls(ax, 'current'); draw_windows(ax, qc=True); draw_furn(ax)
draw_openings(ax); draw_new(ax)
for s in CD['door_swings']:
    r = s['rect']
    ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='none',
                           edgecolor='#e8710a', lw=1.2, ls=':', zorder=4))
    ax.text(r[0], r[3]+80, 'swing '+s['door'], fontsize=5, color='#e8710a')
for r in CD['guest_path']:
    ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='none',
                           edgecolor='#188038', lw=1.2, ls='-.', zorder=4))
ax.text(11800, 9600, 'path >=800\nentry->balcony', fontsize=5, color='#188038', ha='center')
ax.legend(handles=QC_LEGEND, fontsize=5.5, loc='lower left', ncol=2)
save(fig, 'task03a_s3_furniture_qc.png')

# ================================================================ window register overlay
fig, ax = base('Task03A · Window Register Overlay')
draw_walls(ax, 'current'); draw_windows(ax, qc=True)
for win in M.get('windows', []):
    r = win['opening_rect_mm']
    col = WIN_COL[win['verification_status']]
    ax.add_patch(Rectangle((r[0]-60, r[1]-60), r[2]-r[0]+120, r[3]-r[1]+120,
                           facecolor='none', edgecolor=col, lw=1.0, ls=':', zorder=5))
ax.legend(handles=[Line2D([], [], color=WIN_COL['CONFIRMED'], lw=2, label='CONFIRMED / MEASURED'),
                   Line2D([], [], color=WIN_COL['TO_VERIFY'], lw=2, label='TO_VERIFY'),
                   Line2D([], [], color=WIN_COL['PROPOSED'], lw=2, ls='--', label='PROPOSED')],
          fontsize=7, loc='lower left')
save(fig, 'window_register_overlay.png')

# ================================================================ wall/window conflict check
fig, ax = base('Task03A · Wall-Through-Window Conflict Check')
draw_walls(ax, 'current'); draw_windows(ax, qc=True)
conflicts = []
for win in M.get('windows', []):
    if win['window_type'] == 'PROPOSED_BALCONY_ENCLOSURE':
        continue
    op = win['opening_rect_mm']
    hit = [w['id'] for w in M['walls'] if w['disposition'] == 'EXISTING'
           and not (w['rect_mm'][2] <= op[0] or w['rect_mm'][0] >= op[2] or
                    w['rect_mm'][3] <= op[1] or w['rect_mm'][1] >= op[3])]
    col = '#d93025' if hit else '#188038'
    ax.add_patch(Rectangle((op[0]-40, op[1]-40), op[2]-op[0]+80, op[3]-op[1]+80,
                           facecolor='none', edgecolor=col, lw=1.6, zorder=6))
    ax.text(op[0], op[1]-320, f"{win['window_id']}: {'CONFLICT '+str(hit) if hit else 'clear'}",
            fontsize=5.5, color=col, zorder=6)
    conflicts += hit
ax.text(600, 14700, f'solid-wall-through-window conflicts: {len(conflicts)}', fontsize=9,
        color='#d93025' if conflicts else '#188038')
save(fig, 'wall_window_conflict_check.png')

# ================================================================ cleanup before/after
AREAS = [('bottom-left phantom L (parapet)', (500, 6600), (-300, 3000)),
         ('top floating red (living bay)', (2400, 8200), (12400, 14600)),
         ('right floating red (study NE bay)', (12800, 16800), (10400, 12600)),
         ('south windows', (4400, 16000), (-1400, 2200))]
fig, axs = plt.subplots(4, 2, figsize=(16, 22), dpi=120)
for row, (name, (xa, xb), (ya, yb)) in enumerate(AREAS):
    for col, (walls, wins, tag) in enumerate(((WB['walls'], [], 'BEFORE'),
                                             (M['walls'], M['windows'], 'AFTER'))):
        ax = axs[row][col]
        ax.set_xlim(xa, xb); ax.set_ylim(ya, yb); ax.set_aspect('equal')
        ax.set_title(f'{tag} — {name}', fontsize=9); ax.grid(alpha=.12)
        for w in walls:
            if w['disposition'] != 'EXISTING':
                continue
            x1, y1, x2, y2 = w['rect_mm']
            ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1, facecolor=wcolor(w), zorder=2))
        for win in wins:
            r = win['opening_rect_mm']
            colr = WIN_COL[win['verification_status']]
            if win['window_type'] == 'PROPOSED_BALCONY_ENCLOSURE':
                if (r[2]-r[0]) >= (r[3]-r[1]):
                    ax.plot([r[0], r[2]], [(r[1]+r[3])/2]*2, color=colr, lw=1.6, ls='--', zorder=4)
                else:
                    ax.plot([(r[0]+r[2])/2]*2, [r[1], r[3]], color=colr, lw=1.6, ls='--', zorder=4)
                continue
            x1, y1, x2, y2 = r
            if (x2-x1) >= (y2-y1):
                for i in (0.25, 0.5, 0.75):
                    ax.plot([x1, x2], [y1+(y2-y1)*i]*2, color=colr, lw=1.0, zorder=4)
            else:
                for i in (0.25, 0.5, 0.75):
                    ax.plot([x1+(x2-x1)*i]*2, [y1, y2], color=colr, lw=1.0, zorder=4)
            bay = win.get('bay')
            if bay:
                for j in bay['jambs']:
                    ax.add_patch(Rectangle((j[0], j[1]), j[2]-j[0], j[3]-j[1],
                                           facecolor='none', edgecolor=colr, lw=1.0, zorder=4))
                f = bay['front']
                ax.add_patch(Rectangle((f[0], f[1]), f[2]-f[0], f[3]-f[1],
                                       facecolor='none', edgecolor=colr, lw=1.3, zorder=4))
fig.tight_layout()
save(fig, 'window_cleanup_before_after.png')

# ================================================================ S4 split-level study
fig, ax = base('Task03A · Split-Level Accessibility Study(2 risers + ramp)')
draw_walls(ax, 'current'); draw_windows(ax)
for r in CD['level']['landing_kept_mm']:
    ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='#fce8b2', edgecolor='#f9ab00', zorder=2))
r = CD['level']['returned_to_L1_mm']
ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='#ceead6', edgecolor='#188038', zorder=2))
s = CD['level']['stair_mm']
ax.add_patch(Rectangle((s[0], s[1]), s[2]-s[0], s[3]-s[1], facecolor='#1a73e8', alpha=.5, zorder=3))
rp = CD['level']['ramp']['rect_mm']
ax.add_patch(Rectangle((rp[0], rp[1]), rp[2]-rp[0], rp[3]-rp[1], facecolor='#d2e3fc', edgecolor='#1a73e8', hatch='//', zorder=3))
ax.annotate('', xy=(rp[2]-100, (rp[1]+rp[3])/2), xytext=(rp[0]+100, (rp[1]+rp[3])/2), arrowprops=dict(arrowstyle='->', color='#1a73e8'))
ax.text(6000, 8100, 'STAIR: 2 risers, delta LEVEL_TO_VERIFY\n(owner <=350 vs CAD ~400)', fontsize=7)
ax.text(3500, 5100, 'RAMP: 3000 run x1100, climb +x onto open passage\nslope 1:7.5-1:8.6 PROVISIONAL — ASSISTED WHEELCHAIR\nFUTURE PROVISION (not code claim)', fontsize=7, color='#1a73e8')
ac = CD['level']['area_comparison']
ax.text(3500, 4400, f"AREA ACCOUNT: returned platform {ac['returned_platform_m2']}m2\n"
                    f"vs ramp footprint {ac['ramp_footprint_m2']}m2 -> net +{ac['net_unobstructed_public_gain_m2']}m2\n"
                    f"value = regular living rectangle + step-free route (PROVISIONAL)", fontsize=7, color='#b06000')
ax.text(7950, 6500, 'kept UPPER landing\n+ suite foyer', fontsize=7, color='#b06000')
ax.text(5950, 7200, 'platform arm\nreturned to L1\n→ bigger living/dining', fontsize=7, color='#188038')
ax.set_xlim(2500, 13500); ax.set_ylim(4000, 11000)
save(fig, 'task03a_s4_splitlevel.png')

# ================================================================ S5 bathroom study
fig, ax = base('Task03A · Bathroom Layout Study')
draw_walls(ax, 'current'); draw_windows(ax, qc=True)
for f in CD['furniture']:
    if any(k in f['id'] for k in ('BATH', 'SMB2', 'MBATH', 'GBATH')):
        x1, y1, x2, y2 = f['rect']
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor='#34a853', alpha=.3, edgecolor='#34a853', zorder=3))
        ax.text((x1+x2)/2, (y1+y2)/2, f['id']+'\n'+f['note'][:38], fontsize=5, ha='center', va='center')
draw_new(ax)
for s in CD['door_swings']:
    if s['door'] in ('D-SMB2-S', 'D-MB'):
        r = s['rect']
        ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='none',
                               edgecolor='#e8710a', lw=1.2, ls=':', zorder=4))
gp = CD['smb']['shower_glass']['panel']
ax.add_patch(Rectangle((gp[0], gp[1]), gp[2]-gp[0], gp[3]-gp[1], facecolor='#9334e6', alpha=.5, zorder=5))
ax.annotate('glass panel; 750 entry\nsouth of it; aisle 800', xy=(10450, 5800),
            xytext=(7600, 6800), fontsize=6, color='#9334e6',
            arrowprops=dict(arrowstyle='->', color='#9334e6'))
ax.set_xlim(7000, 16800); ax.set_ylim(3400, 11500)
save(fig, 'task03a_s5_bathrooms.png')

# ================================================================ S6 W vs S comparison
fig, axs = plt.subplots(1, 2, figsize=(15, 9), dpi=130)
smb2 = [f for f in CD['furniture'] if f['id'].startswith('SMB2-')]
for ax, opt in zip(axs, 'WS'):
    ax.set_xlim(7000, 12500); ax.set_ylim(3200, 7500); ax.set_aspect('equal')
    ax.set_title(f'Option {opt}', fontsize=12); ax.grid(alpha=.15)
    for w in M['walls']:
        x1, y1, x2, y2 = w['rect_mm']
        if x2 > 7000 and x1 < 12500 and y2 > 3200 and y1 < 7500:
            ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1, facecolor=wcolor(w), zorder=2))
    for r in CD['new_walls']:
        ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor=WCOL['new'], zorder=4))
    for f in smb2:
        x1, y1, x2, y2 = f['rect']
        ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1, facecolor='#34a853', alpha=.35, edgecolor='#34a853', zorder=3))
        ax.text((x1+x2)/2, (y1+y2)/2, f['id'].replace('SMB2-',''), fontsize=6, ha='center', va='center')
    if opt == 'W':
        ax.add_patch(Rectangle((8950, 4700), 100, 700, facecolor=WCOL['conflict'], alpha=.8, zorder=5, hatch='xx'))
        ax.annotate('SLIDING door cut in RETAINED\nCLK-W (white-class wall)', xy=(8950, 5050), xytext=(7300, 5400),
                    fontsize=8, arrowprops=dict(arrowstyle='->'))
        ax.add_patch(Rectangle((7800, 4650), 1100, 1650, facecolor='#fce8b2', edgecolor='#f9ab00', zorder=1))
        ax.text(7850, 4750, 'foyer', fontsize=7)
        ax.text(7200, 7000, 'CONSTRAINED — needs owner exception\nto open white-class CLK-W;\nsliding leaf; door not facing bed', fontsize=8, color='#e8710a')
    else:
        for r in CD['new_doors']:
            ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='#9334e6', zorder=5))
        r = CD['smb']['clearances']['door_swing']
        ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='none',
                               edgecolor='#e8710a', lw=1.2, ls=':', zorder=5))
        ax.text(r[0]-150, r[3]+60, 'swing zone\n(fixture-free)', fontsize=6, color='#e8710a')
        ax.add_patch(Rectangle((10800, 4450), 600, 100, facecolor=WCOL['conflict'], alpha=.7, zorder=5))
        ax.annotate('door 750 in NEW south partition\n(hinge E, swings into annex)', xy=(9400, 3850), xytext=(7300, 4400),
                    fontsize=8, arrowprops=dict(arrowstyle='->'))
        gp = CD['smb']['shower_glass']['panel']
        ax.add_patch(Rectangle((gp[0], gp[1]), gp[2]-gp[0], gp[3]-gp[1], facecolor='#9334e6', alpha=.5, zorder=5))
        ax.text(10600, 5100, '750 entry\n(glass above)', fontsize=5, color='#9334e6')
        ma = CD['smb']['clearances']['main_aisle']
        ax.add_patch(Rectangle((ma[0], ma[1]), ma[2]-ma[0], ma[3]-ma[1], facecolor='none',
                               edgecolor='#188038', lw=1.0, ls='-.', zorder=5))
        ax.text(9730, 6000, 'aisle\n800', fontsize=6, color='#188038')
        ax.text(10900, 4200, 'stub\nTO_VERIFY', fontsize=6, color=WCOL['conflict'])
        ax.text(7200, 7000, 'FEASIBLE — RECOMMENDED\n~5.0m2 shell+annex; zero demolition;\n750 door; 800 continuous aisle', fontsize=8, color='#188038')
fig.savefig(QC / 'task03a_s6_smb_ws.png', bbox_inches='tight', facecolor='white')
fig.savefig(QC / 'task03a_s6_smb_ws.pdf', bbox_inches='tight', facecolor='white')
print('task03a_s6_smb_ws.png')
