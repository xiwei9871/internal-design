"""Deterministic 1:1 CAD model -> locked paper viewport -> A2 PDF/PNG."""
from pathlib import Path
import csv
import json

from cad_common import DATA, add_text, make_paper_layout


def export_sheet(doc, png_path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, ColorPolicy, BackgroundPolicy
    from design_model import design_hash

    png_path = Path(png_path)
    stem = png_path.stem.removesuffix('_preview')
    sheet, title, notes = getattr(doc, '_sheet_metadata', (stem[:4], stem, []))
    common = ['尺寸依据：A7 PNG × 9.82mm/px，非现场测量。',
              '门表参考跨距≠结构洞口；门套及设备SKU待确认。',
              '干区吊顶2600 / 湿区2400 / 墙2700，现场复核。']
    scale = 25 if sheet == 'A402' else 20 if sheet == 'A403' else 50
    sidebar = sheet not in ('A401', 'A402', 'A403', 'A501')
    schedule = getattr(doc, '_point_schedule', [])
    paper = make_paper_layout(doc, sheet, title, scale, common + notes if not schedule else [], sidebar)
    if sheet == 'A101':
        add_text(paper, '家具索引 / 图块按锁定包络绘制', 2.8, (414,303))
        for i,f in enumerate(DATA['furniture'],1):
            name=f['name'].split('（')[0]
            add_text(paper,f'F{i:02d}  {name}',2.35,(414,296-(i-1)*5.65))
    elif schedule:
        add_text(paper,'设计新增点位 / 全部待现场及产品复核',2.6,(414,367))
        add_text(paper,'详见同名CSV：编号、用途、X/Y定位坐标(mm)',2.35,(414,361))
        y=353
        for code,label,x,y_mm in schedule:
            # Two lines per point only when necessary, preserving full schedule in CSV.
            add_text(paper,f'{code}  {label}',2.15,(414,y))
            add_text(paper,f'X {x:.0f} / Y {y_mm:.0f}',1.9,(423,y-2.9))
            y-=6.4 if len(schedule)>30 else 11.5
        add_text(paper,'定位原点：源图(200,1337)；X向东、Y向北。',2.35,(414,75))
        add_text(paper,'未包含回路/管径/坡度计算，须机电深化。',2.35,(414,68))
        with png_path.with_name(stem+'_points.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(['编号','设计用途/高度（均待确认）','X_mm','Y_mm'])
            writer.writerows((code,label,round(x),round(y)) for code,label,x,y in schedule)
    elif not sidebar:
        # Compact top margin keeps schedule/elevation model space entirely clear.
        add_text(paper,' / '.join(notes)[:155],2.2,(18,385))

    audit=doc.audit()
    if audit.errors or audit.fixes:
        raise ValueError(f'{sheet}: DXF audit errors={audit.errors}, fixes={audit.fixes}')
    dxf_path=png_path.with_name(stem+'.dxf')
    doc.saveas(dxf_path)
    config=Configuration(color_policy=ColorPolicy.COLOR,background_policy=BackgroundPolicy.WHITE,
                         min_lineweight=0.08)
    fig=plt.figure(figsize=(594/25.4,420/25.4))
    ax=fig.add_axes([0,0,1,1]);ax.set_axis_off()
    ctx=RenderContext(doc)
    ctx.set_current_layout(paper)
    frontend=Frontend(ctx,MatplotlibBackend(ax),config=config)
    def monochrome_with_masks(entity,properties):
        properties.color='#ffffff' if entity.dxf.layer=='A-MASK' else '#000000'
    frontend.push_property_override_function(monochrome_with_masks)
    frontend.draw_layout(paper,finalize=True)
    # MatplotlibBackend.finalize() resizes figures to its default inches.
    # Restore the physical paper after drawing; otherwise printed scales are wrong.
    fig.set_size_inches(594/25.4,420/25.4,forward=True)
    ax.set_xlim(0,594);ax.set_ylim(0,420);ax.set_aspect('equal', adjustable='box')
    fig.savefig(png_path,dpi=110,facecolor='white')
    fig.savefig(png_path.with_name(stem+'.pdf'),facecolor='white')
    plt.close(fig)
    png_path.with_name(stem+'_audit.json').write_text(json.dumps({
        'sheet':sheet,'paper_mm':[594,420],'viewport_scale':scale,'model_unit':'mm',
        'audit_errors':0,'audit_fixes':0,'design_sha256':design_hash(),
        'review_status':'Design coordination; site/SKU/MEP verification pending',
    },ensure_ascii=False,indent=2),encoding='utf-8')
    return dxf_path
