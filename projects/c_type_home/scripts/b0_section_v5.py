"""B0_SPLIT_LEVEL_SECTION_V5 — section through LOWER nook -> 3x150 stairs ->
fan leisure UPPER. Cut along y=7300 (CAD mm): crosses nook (Z0), stair zone
(7200-7800), leisure platform (+450). Heights from Z_DATUM_SPEC v2.
"""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Hiragino Sans GB',
                                   'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

ROOT = '/Users/xiwei/interior_design/projects/c_type_home'
A = json.load(open(f'{ROOT}/design/pascal_b1/master_direct_arch_v1.json'))
M = json.load(open(f'{ROOT}/design/b1_blockout/b1_model.json'))
OUT = f'{ROOT}/design/blender_b0'

YCUT = 7300  # mm — crosses nook(0) -> stairs -> leisure(+450)

fig, ax = plt.subplots(figsize=(14, 7))

# walls the cut passes through -> vertical bands in section
for w in A['walls']:
    r = w.get('rect_mm')
    if not r: continue
    if r[1] < YCUT < r[3] and 5400 < r[0] < 9500:
        # wall vertical span depends on side it bounds; draw to its class top
        ax.add_patch(Rectangle((r[0], -300), r[2]-r[0], 3550, fc='#9a9a9a',
                               ec='#555', lw=.6, alpha=.9))

# floors (from level field): nook 0 | steps | leisure 450
ax.add_patch(Rectangle((5500, -100), 1700, 100, fc='#a9cdec', ec='none'))
for sx0, sy0, sx1, sy1, h in M['stairs']['steps']:
    ax.add_patch(Rectangle((sx0, 0), sx1-sx0, h, fc='#7ec87e', ec='#3a7d3a',
                           lw=.8))
ax.add_patch(Rectangle((7800, 0), 1700, 450, fc='#f2b878', ec='none'))

# ceilings: nook lower 2800 | stair void + leisure upper 3250
ax.plot([5500, 7200], [2800, 2800], color='#036', lw=2)
ax.plot([7200, 9500], [3250, 3250], color='#a40', lw=2)
# ceiling fascia at nook|stair boundary x7200
ax.plot([7200, 7200], [2800, 3250], color='#a40', lw=2, ls='--')
ax.text(7160, 3020, 'ceiling fascia\n450mm', fontsize=8, ha='right',
        color='#a40')

# datum lines + labels
for z, lab, c in [(0, 'Z 0  LOWER FFL', '#036'), (150, 'Z +150', '#3a7d3a'),
                  (300, 'Z +300', '#3a7d3a'), (450, 'Z +450  UPPER FFL', '#a40'),
                  (2800, 'Z +2800  LOWER CEILING', '#036'),
                  (3250, 'Z +3250  UPPER CEILING', '#a40')]:
    ax.axhline(z, color=c, lw=.5, ls=':', alpha=.6)
    ax.text(9570, z, lab, fontsize=8, va='center', color=c)

# clear-height callouts
ax.annotate('', xy=(6300, 0), xytext=(6300, 2800),
            arrowprops=dict(arrowstyle='<->', color='#036'))
ax.text(6300, 1450, 'LOWER CLEAR\nHEIGHT 2800', fontsize=8, ha='center',
        color='#036', weight='bold')
ax.annotate('', xy=(8600, 450), xytext=(8600, 3250),
            arrowprops=dict(arrowstyle='<->', color='#a40'))
ax.text(8600, 1900, 'UPPER CLEAR\nHEIGHT 2800', fontsize=8, ha='center',
        color='#a40', weight='bold')

# zone labels
ax.text(6300, -450, '楼梯前厅 nook\nLOWER  Z0', ha='center', fontsize=9,
        color='#036', weight='bold')
ax.text(7500, -450, 'EXISTING_STAIRS\n3×150', ha='center', fontsize=9,
        color='#3a7d3a', weight='bold')
ax.text(8650, -450, '扇形休闲厅 leisure\nUPPER  +450', ha='center', fontsize=9,
        color='#a40', weight='bold')
ax.text(7500, 120, '剖切线 y=7300', fontsize=7, color='#888')

ax.set_xlim(5300, 10500); ax.set_ylim(-800, 3900)
ax.set_aspect('equal')
ax.set_xlabel('CAD X (mm) — west → east')
ax.set_ylabel('Z (mm)')
ax.grid(alpha=.2)
ax.set_title('B0 SPLIT-LEVEL SECTION V5 — cut @ y=7300: '
             'LOWER nook → 3×150 stairs → fan leisure UPPER (+450)')
plt.tight_layout()
plt.savefig(f'{OUT}/B0_SPLIT_LEVEL_SECTION_V5.png', dpi=140)
print('section saved')
