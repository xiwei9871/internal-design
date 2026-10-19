#!/usr/bin/env python3
"""原版 vs STYLE_POC 同尺度并排对比图: 全图 + 4 个局部。输出到 comparison/"""
import ezdxf, matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family'] = 'Heiti TC'
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

CAD = '/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad'
OUT = CAD + '/research/house_plan_designer_v01/dxf_style/comparison'
CROPS = {'kitchen': (5200, 7200, 1400, 4300), 'bath2': (8500, 12000, 5400, 8400),
         'nbalc': (7400, 13400, 12400, 14200), 'step': (5200, 9200, 4300, 8600)}
FULL = (-2500, 19000, -4500, 16500)

def draw(doc, ax, win):
    ax.set_axis_off(); ax.set_aspect('equal')
    ctx = RenderContext(doc)
    for l in doc.layers:
        lp = ctx.layers.get(l.dxf.name)
        if lp is not None and l.is_frozen(): lp.visible = False
    Frontend(ctx, MatplotlibBackend(ax)).draw_layout(doc.modelspace(), finalize=True)
    ax.set_xlim(win[0], win[1]); ax.set_ylim(win[2], win[3])

for tag, a, b in [('A102', 'A102_WALL_DIFF_POC_V3.dxf', 'A102_STYLE_POC.dxf'),
                  ('A103', 'A103_CONSTRUCTION_POC_V7.dxf', 'A103_STYLE_POC.dxf')]:
    da = ezdxf.readfile(f'{CAD}/{a}')
    db = ezdxf.readfile(f'{CAD}/research/house_plan_designer_v01/dxf_style/{b}')
    for name, win in [('side_by_side', FULL)] + [(f'crop_{k}', v) for k, v in CROPS.items()]:
        fig, axs = plt.subplots(1, 2, figsize=(22, 11))
        draw(da, axs[0], win); axs[0].set_title(f'原版 {a}', fontsize=9)
        draw(db, axs[1], win); axs[1].set_title(f'STYLE POC {b}', fontsize=9)
        fig.savefig(f'{OUT}/{tag}_{name}.png', dpi=130, facecolor='white',
                    bbox_inches='tight')
        plt.close(fig)
    print(tag, 'comparisons done')
