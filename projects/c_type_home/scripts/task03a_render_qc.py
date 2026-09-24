#!/usr/bin/env python3
"""Task03A QC renders — 6 sheets. task01 coords."""
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
QC = ROOT / 'qc'

WCOL = {'keep': '#9aa0a6', 'noopen': '#d93025', 'remove': '#dadce0', 'new': '#188038',
        'conflict': '#e8710a', 'review': '#9334e6'}

def wcolor(w):
    cls = w['wall_class']
    if w['disposition'] != 'EXISTING':
        return WCOL['conflict'] if 'CONFLICT' in cls else WCOL['remove']
    if 'NO_DEMOLITION' in cls or 'NO_OPEN' in cls: return WCOL['noopen']
    if 'REVIEW' in cls or 'CONFLICT' in cls: return WCOL['review']
    return WCOL['keep']

def draw_walls(ax, mode='current'):
    for w in M['walls']:
        x1, y1, x2, y2 = w['rect_mm']
        if mode == 'current' and w['disposition'] != 'EXISTING':
            continue
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor=wcolor(w), edgecolor='none', zorder=2))

def draw_furn(ax):
    for f in CD['furniture']:
        x1, y1, x2, y2 = f['rect']
        c = '#f9ab00' if f['layer'] == 'A-FURN-EXST-KEEP' else \
            ('#34a853' if f['layer'] == 'A-FIXT-PLUMB' else
             ('#1a73e8' if 'ACCESS' in f['layer'] else '#f4b400'))
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor=c, alpha=.35,
                               edgecolor=c, lw=1.0, zorder=3))
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, f['id'], fontsize=5.5, ha='center', va='center', zorder=5)

def draw_openings(ax):
    for o in M['openings']:
        x1, y1, x2, y2 = o['rect_mm']
        c = '#9334e6' if 'GLAZ' in o.get('kind', '') or 'glaz' in o.get('kind', '') else '#188038'
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor='none',
                               edgecolor=c, lw=1.6, ls='--', zorder=4))
        ax.text((x1 + x2) / 2, y2 + 90, o['id'], fontsize=5, ha='center', color=c, zorder=5)

def base(title):
    fig, ax = plt.subplots(figsize=(13, 14), dpi=130)
    ax.set_xlim(0, 16800); ax.set_ylim(-600, 15200); ax.set_aspect('equal')
    ax.set_title(title, fontsize=13); ax.grid(alpha=.15)
    return fig, ax

def save(fig, name):
    fig.savefig(QC / name, bbox_inches='tight', facecolor='white')
    fig.savefig(QC / name.replace('.png', '.pdf'), bbox_inches='tight', facecolor='white')
    plt.close(fig); print(name)

# S1 current existing
fig, ax = base('Task03A · Current Existing Plan(measured DWG)')
draw_walls(ax, 'current'); draw_openings(ax)
for k in M['keep_items']:
    x1, y1, x2, y2 = k['rect_mm']
    ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor='#f9ab00', alpha=.3, edgecolor='#f9ab00', zorder=3))
    ax.text((x1 + x2) / 2, (y1 + y2) / 2, k['id'], fontsize=5.5, ha='center')
st = M['split_level']['zone_mm']
ax.add_patch(Rectangle((st[0], st[1]), st[2]-st[0], st[3]-st[1], facecolor='#1a73e8', alpha=.4, zorder=3))
ax.text(st[0]-400, st[3]+150, '2 risers, delta LEVEL_TO_VERIFY', fontsize=7, color='#1a73e8')
ax.text(7900, 13900, 'N BALCONY: OPEN now; enclosure PROPOSED', fontsize=7, color='#188038')
ax.legend(handles=[Line2D([], [], color=WCOL['noopen'], lw=6, label='NO-OPEN (owner rule/exterior)'),
                   Line2D([], [], color=WCOL['keep'], lw=6, label='existing wall (modifiable/review)'),
                   Line2D([], [], color='#9334e6', lw=2, ls='--', label='glazing/door')], fontsize=7, loc='lower left')
save(fig, 'task03a_s1_current_existing.png')

# S2 demolition / keep / new
fig, ax = base('Task03A · Demolition / Keep / New')
draw_walls(ax, 'all'); draw_openings(ax)
# new walls (bath W)
ax.add_patch(Rectangle((8950, 4650), 100, 1800, facecolor=WCOL['new'], zorder=4))
ax.add_patch(Rectangle((9050, 6300), 2250, 100, facecolor=WCOL['new'], zorder=4))
ax.text(9400, 6000, 'NEW bath walls\n(former cloakroom)', fontsize=6, color=WCOL['new'])
ax.legend(handles=[Line2D([], [], color=WCOL['noopen'], lw=6, label='NO-OPEN (owner rule/exterior)'),
                   Line2D([], [], color=WCOL['keep'], lw=6, label='keep / modifiable'),
                   Line2D([], [], color=WCOL['remove'], lw=6, label='demolished/absent'),
                   Line2D([], [], color=WCOL['conflict'], lw=6, label='CLASSIFICATION_CONFLICT (white-class but demolished)'),
                   Line2D([], [], color=WCOL['new'], lw=6, label='new wall')], fontsize=7, loc='lower left')
save(fig, 'task03a_s2_demolition.png')

# S3 furniture plan
fig, ax = base('Task03A · Proposed Furniture Plan')
draw_walls(ax, 'current'); draw_furn(ax); draw_openings(ax)
save(fig, 'task03a_s3_furniture.png')

# S4 split-level study
fig, ax = base('Task03A · Split-Level Accessibility Study(2 risers + ramp)')
draw_walls(ax, 'current')
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
ax.text(7950, 6500, 'kept UPPER landing\n+ suite foyer', fontsize=7, color='#b06000')
ax.text(5950, 7200, 'platform arm\nreturned to L1\n→ bigger living/dining', fontsize=7, color='#188038')
ax.set_xlim(2500, 13500); ax.set_ylim(4000, 11000)
save(fig, 'task03a_s4_splitlevel.png')

# S5 bathroom study
fig, ax = base('Task03A · Bathroom Layout Study')
draw_walls(ax, 'current')
for f in CD['furniture']:
    if any(k in f['id'] for k in ('BATH', 'SMB2', 'MBATH', 'GBATH')):
        x1, y1, x2, y2 = f['rect']
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor='#34a853', alpha=.3, edgecolor='#34a853', zorder=3))
        ax.text((x1+x2)/2, (y1+y2)/2, f['id']+'\n'+f['note'][:38], fontsize=5, ha='center', va='center')
ax.add_patch(Rectangle((8950, 4650), 100, 1800, facecolor=WCOL['new'], zorder=4))
ax.add_patch(Rectangle((9050, 6300), 2250, 100, facecolor=WCOL['new'], zorder=4))
ax.set_xlim(7000, 16800); ax.set_ylim(4000, 11500)
save(fig, 'task03a_s5_bathrooms.png')

# S6 W vs S comparison
fig, axs = plt.subplots(1, 2, figsize=(15, 9), dpi=130)
for ax, opt in zip(axs, 'WS'):
    ax.set_xlim(7000, 12500); ax.set_ylim(3500, 7500); ax.set_aspect('equal')
    ax.set_title(f'Option {opt}', fontsize=12); ax.grid(alpha=.15)
    for w in M['walls']:
        x1, y1, x2, y2 = w['rect_mm']
        if x2 > 7000 and x1 < 12500 and y2 > 3500 and y1 < 7500:
            ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1, facecolor=wcolor(w), zorder=2))
    if opt == 'W':
        ax.add_patch(Rectangle((8950, 4650), 100, 550, facecolor=WCOL['new'], zorder=4))
        ax.add_patch(Rectangle((8950, 5950), 100, 700, facecolor=WCOL['new'], zorder=4))
        ax.add_patch(Rectangle((9050, 6300), 2250, 100, facecolor=WCOL['new'], zorder=4))
        ax.add_patch(Rectangle((8950, 5200), 100, 750, facecolor='#9334e6', zorder=4))
        ax.annotate('door into suite foyer', xy=(8950, 5575), xytext=(7300, 5800),
                    fontsize=8, arrowprops=dict(arrowstyle='->'))
        ax.add_patch(Rectangle((7800, 4650), 1100, 1650, facecolor='#fce8b2', edgecolor='#f9ab00', zorder=1))
        ax.text(7850, 4750, 'foyer', fontsize=7)
        ax.text(7200, 7000, 'FEASIBLE — PREFERRED\nprivate vestibule, door not facing bed', fontsize=8, color='#188038')
    else:
        ax.add_patch(Rectangle((8950, 4650), 100, 1800, facecolor=WCOL['new'], zorder=4))
        ax.add_patch(Rectangle((9050, 6300), 2250, 100, facecolor=WCOL['new'], zorder=4))
        ax.add_patch(Rectangle((9050, 4550), 450, 100, facecolor=WCOL['new'], zorder=4))
        ax.add_patch(Rectangle((10300, 4550), 1000, 100, facecolor=WCOL['new'], zorder=4))
        ax.add_patch(Rectangle((9500, 4550), 800, 100, facecolor='#9334e6', zorder=4))
        ax.add_patch(Rectangle((10800, 4450), 600, 250, facecolor=WCOL['conflict'], alpha=.7, zorder=5))
        ax.annotate('door in NEW south wall\n(direct from bedroom)', xy=(9900, 4600), xytext=(7300, 5200),
                    fontsize=8, arrowprops=dict(arrowstyle='->'))
        ax.text(11000, 4900, 'residual stub\nTO_VERIFY', fontsize=6, color=WCOL['conflict'])
        ax.text(7200, 7000, 'FEASIBLE (conditional)\ndoor faces bed zone; stub check needed', fontsize=8, color='#188038')
fig.savefig(QC / 'task03a_s6_smb_ws.png', bbox_inches='tight', facecolor='white')
fig.savefig(QC / 'task03a_s6_smb_ws.pdf', bbox_inches='tight', facecolor='white')
print('task03a_s6_smb_ws.png')
