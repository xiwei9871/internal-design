#!/usr/bin/env python3
"""出图后处理: 生成器 DXF -> 可交付 DXF(R2010) + A1 1:50 PDF. 几何不改, 只改出图层.
- 文字样式统一 gbenor.shx + gbcbig.shx (QCAD/AutoCAD/中望/浩辰通用, 无本机绝对路径)
- 删除纸空间 VIEWPORT (QCAD 不显示), 图框/标题栏改放模型空间, 按 1:50 放大
- 输出 R2010 (AC1024), 兼容 AutoCAD 2010+
用法: publish_dxf.py SRC.dxf OUT_DIR --title 图名 --no 图号"""
import argparse, hashlib, datetime
from pathlib import Path
import ezdxf
from ezdxf import bbox

SCALE = 50
A1 = (841, 594)                    # GB/T 14689 A1 横式
MARGIN_BIND, MARGIN = 25, 10       # 装订边 a=25, 其余 c=10
TB = (180, 56)                     # 标题栏 宽x高 (纸面 mm)
FONT, BIGFONT = 'gbenor.shx', 'gbcbig.shx'
FRAME_LAYER = 'A-FRAME'


def sha10(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:10]


def unify_text_styles(doc):
    for s in doc.styles:
        s.dxf.font = FONT
        s.dxf.bigfont = BIGFONT


def drop_paperspace(doc):
    """移除纸空间内容, 返回其中的文字(迁移到模型空间标题栏)"""
    texts = []
    for lay in doc.layouts:
        if lay.name == 'Model': continue
        for e in list(lay):
            if e.dxftype() == 'TEXT': texts.append(e.dxf.text)
            lay.delete_entity(e)
    return texts


def plan_extents(msp, skip=()):
    ents = [e for e in msp if e.dxf.layer != FRAME_LAYER and e.dxf.layer not in skip and
            not msp.doc.layers.get(e.dxf.layer).is_frozen()]
    return bbox.extents(ents)


def add_frame(doc, title, sheet_no, src, notes):
    msp = doc.modelspace()
    if FRAME_LAYER not in doc.layers:
        doc.layers.new(FRAME_LAYER, dxfattribs={'color': 7})
    full = plan_extents(msp)
    if full.size.x > (A1[0] - MARGIN_BIND - MARGIN) * SCALE or \
       full.size.y > (A1[1] - 2 * MARGIN - TB[1]) * SCALE:
        raise SystemExit(f'BLOCK: 图面 {full.size.x:.0f}x{full.size.y:.0f} 超出 A1@1:{SCALE}')
    # 以平面(不含图注文字)居中; 若导致整图出框则退回全范围居中
    for ext in (plan_extents(msp, skip=('A-TEXT',)), full):
        x0 = ext.center.x - (MARGIN_BIND + (A1[0] - MARGIN_BIND - MARGIN) / 2) * SCALE
        y0 = ext.center.y - (MARGIN + TB[1] + (A1[1] - 2 * MARGIN - TB[1]) / 2) * SCALE
        if (full.extmin.x >= x0 + MARGIN_BIND * SCALE and full.extmax.x <= x0 + (A1[0] - MARGIN) * SCALE
                and full.extmin.y >= y0 + (MARGIN + TB[1]) * SCALE
                and full.extmax.y <= y0 + (A1[1] - MARGIN) * SCALE):
            break
    P = lambda u, v: (x0 + u * SCALE, y0 + v * SCALE)   # 纸面 mm -> 模型 mm
    att = {'layer': FRAME_LAYER}
    rect = lambda u0, v0, u1, v1, **kw: msp.add_lwpolyline(
        [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)], close=True,
        dxfattribs={**att, **kw})
    rect(0, 0, A1[0], A1[1])                                            # 图纸边界
    rect(MARGIN_BIND, MARGIN, A1[0] - MARGIN, A1[1] - MARGIN, const_width=0.7 * SCALE)  # 图框
    tu1, tv0 = A1[0] - MARGIN, MARGIN
    tu0, tv1 = tu1 - TB[0], tv0 + TB[1]
    rect(tu0, tv0, tu1, tv1, const_width=0.5 * SCALE)
    rows = [(f'{title}', 7), (f'图号 {sheet_no}    比例 1:{SCALE}    图幅 A1    单位 mm', 3.5),
            ('状态: 初步设计 PRELIMINARY_DESIGN - 非正式施工图, 尺寸须现场复核', 3.5),
            (f'源: {src.name}  sha256:{sha10(src)}', 2.5),
            (f'出图: publish_dxf.py  {datetime.date.today().isoformat()}', 2.5)]
    rows += [(n[:90], 2.5) for n in notes]
    v = tv1 - 4
    for text, h in rows:
        v -= h + 2.5
        if v < tv0 + 1: break
        msp.add_text(text, height=h * SCALE, dxfattribs={**att, 'style': 'Standard'}
                     ).set_placement(P(tu0 + 4, v))
    return (P(0, 0), P(*A1))


def export_pdf(doc, window, out_pdf):
    """按图框窗口精确输出 A1 PDF -> 1:50"""
    import matplotlib
    matplotlib.use('Agg')
    matplotlib.rcParams['font.family'] = ['Heiti TC', 'Arial Unicode MS']
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy
    fig = plt.figure(figsize=(A1[0] / 25.4, A1[1] / 25.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ctx = RenderContext(doc)
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE)   # 保留图层颜色语义(A102 依赖颜色图例)
    Frontend(ctx, MatplotlibBackend(ax), config=cfg).draw_layout(doc.modelspace(), finalize=False)
    (x0, y0), (x1, y1) = window
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
    fig.savefig(out_pdf, facecolor='white')
    plt.close(fig)


def publish(src, out_dir, title, sheet_no, pdf=True):
    src, out_dir = Path(src), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f'{src.stem}.issue.dxf'
    if out.resolve() == src.resolve():
        raise SystemExit('BLOCK: OUT == SRC')
    doc = ezdxf.readfile(src)
    n_before = len(doc.modelspace())
    unify_text_styles(doc)
    notes = drop_paperspace(doc)
    window = add_frame(doc, title, sheet_no, src, notes[1:])
    doc.dxfversion = 'AC1024'
    lay = doc.layouts.get('Layout1')
    lay.page_setup(size=A1, margins=(0, 0, 0, 0), units='mm')
    doc.saveas(out)
    chk = ezdxf.readfile(out)
    audit = chk.audit()
    report = {
        'src': src.name, 'src_sha10': sha10(src), 'out': out.name, 'out_sha10': sha10(out),
        'dxfversion': chk.dxfversion, 'audit_errors': len(audit.errors),
        'viewports_excl_overall': sum(1 for l in chk.layouts for e in l
                                      if e.dxftype() == 'VIEWPORT' and e.dxf.id != 1),
        'styles': sorted({(s.dxf.font, s.dxf.bigfont) for s in chk.styles}),
        'model_entities_src': n_before,
        'model_entities_out_excl_frame': sum(1 for e in chk.modelspace() if e.dxf.layer != FRAME_LAYER),
        'frame_window_mm': [list(map(round, window[0])), list(map(round, window[1]))],
    }
    if pdf:
        export_pdf(chk, window, out.with_suffix('.pdf'))
        report['pdf'] = out.with_suffix('.pdf').name
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('out_dir')
    ap.add_argument('--title', required=True); ap.add_argument('--no', required=True)
    ap.add_argument('--no-pdf', action='store_true')
    a = ap.parse_args()
    import json
    print(json.dumps(publish(a.src, a.out_dir, a.title, a.no, not a.no_pdf),
                     ensure_ascii=False, indent=1))
