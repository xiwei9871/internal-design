#!/usr/bin/env python3
"""用 ezdxf 渲染管线直读 DXF 模型空间 → PNG + PDF。用法: render_dxf_native.py FILE.dxf"""
import sys
from pathlib import Path
import ezdxf
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family']='Heiti TC'
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt
from ezdxf.addons.drawing.properties import LayerProperties

def render(src):
    src = Path(src)
    doc = ezdxf.readfile(src)
    fig = plt.figure(figsize=(17,17))
    ax = fig.add_axes([0,0,1,1]); ax.set_axis_off()
    ctx = RenderContext(doc)
    for name in doc.layers:
        lp = ctx.layers.get(name.dxf.name)
        if lp is not None and doc.layers.get(name.dxf.name).is_frozen():
            lp.visible = False
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True)
    fig.savefig(src.with_suffix('.native.png'), dpi=150, facecolor='white')
    fig.savefig(src.with_suffix('.native.pdf'), facecolor='white')
    print('rendered', src.with_suffix('.native.png').name)

if __name__=='__main__':
    for f in sys.argv[1:]: render(f)
