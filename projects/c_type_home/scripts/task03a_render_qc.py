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

def draw_new(ax):
    for r in CD['new_walls']:
        ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor=WCOL['new'], zorder=4))
    for r in CD['new_doors']:
        ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='#9334e6', zorder=4))

# S2 demolition / keep / new
fig, ax = base('Task03A · Demolition / Keep / New')
draw_walls(ax, 'all'); draw_openings(ax); draw_new(ax)
ax.text(9200, 5400, 'NEW bath enclosure:\nsouth partition + annex walls\n(shell N/W/E kept)', fontsize=6, color=WCOL['new'])
ax.legend(handles=[Line2D([], [], color=WCOL['noopen'], lw=6, label='NO-OPEN (owner rule/exterior)'),
                   Line2D([], [], color=WCOL['keep'], lw=6, label='keep / modifiable'),
                   Line2D([], [], color=WCOL['remove'], lw=6, label='demolished/absent'),
                   Line2D([], [], color=WCOL['conflict'], lw=6, label='CLASSIFICATION_CONFLICT (white-class but demolished)'),
                   Line2D([], [], color=WCOL['new'], lw=6, label='new wall')], fontsize=7, loc='lower left')
save(fig, 'task03a_s2_demolition.png')

# S3 furniture plan
fig, ax = base('Task03A · Proposed Furniture Plan')
draw_walls(ax, 'current'); draw_furn(ax); draw_openings(ax); draw_new(ax)
# door-swing envelopes (dashed) so swing/fixture conflicts are visible
for s in CD['door_swings']:
    r = s['rect']
    ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='none',
                           edgecolor='#e8710a', lw=1.2, ls=':', zorder=4))
    ax.text(r[0], r[3]+80, 'swing '+s['door'], fontsize=5, color='#e8710a')
# guest-room continuous path entry -> balcony (RC2.1, >=800 throat)
for i, r in enumerate(CD['guest_path']):
    ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='none',
                           edgecolor='#188038', lw=1.2, ls='-.', zorder=4))
ax.text(11800, 9600, 'path >=800\nentry->balcony', fontsize=5, color='#188038', ha='center')
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
ac = CD['level']['area_comparison']
ax.text(3500, 4400, f"AREA ACCOUNT: returned platform {ac['returned_platform_m2']}m2\n"
                    f"vs ramp footprint {ac['ramp_footprint_m2']}m2 -> net +{ac['net_unobstructed_public_gain_m2']}m2\n"
                    f"value = regular living rectangle + step-free route (PROVISIONAL)", fontsize=7, color='#b06000')
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
draw_new(ax)
for s in CD['door_swings']:
    if s['door'] in ('D-SMB2-S', 'D-MB'):
        r = s['rect']
        ax.add_patch(Rectangle((r[0], r[1]), r[2]-r[0], r[3]-r[1], facecolor='none',
                               edgecolor='#e8710a', lw=1.2, ls=':', zorder=4))
# SMB2 shower glass partition + real entry opening (RC2.1)
gp = CD['smb']['shower_glass']['panel']
ax.add_patch(Rectangle((gp[0], gp[1]), gp[2]-gp[0], gp[3]-gp[1], facecolor='#9334e6', alpha=.5, zorder=5))
ax.annotate('glass panel; 750 entry\nsouth of it; aisle 800', xy=(10450, 5800),
            xytext=(7600, 6800), fontsize=6, color='#9334e6',
            arrowprops=dict(arrowstyle='->', color='#9334e6'))
ax.set_xlim(7000, 16800); ax.set_ylim(3400, 11500)
save(fig, 'task03a_s5_bathrooms.png')

# S6 W vs S comparison
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
        # W needs a cut in retained CLK-W (white-class); sliding leaf
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
