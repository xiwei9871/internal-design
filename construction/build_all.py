"""Build ten v14 sheets, validate exact paper size, and bind the PDF set."""
import importlib
import json
from pathlib import Path
import sys

import ezdxf
import pymupdf
from cad_common import OUT
from design_model import design_hash

BUILDERS = [
    'build_a101_plan','build_a102_structure','build_a201_floor','build_a301_ceiling',
    'build_a302_electrical','build_a303_plumbing','build_a401_elevations',
    'build_a402_details','build_a403_service_wall','build_a501_schedules',
]


def verify_package():
    report={'design_sha256':design_hash(),'sheets':[]}
    paths=sorted(OUT.glob('A*.dxf'))
    if len(paths)!=10:
        raise ValueError(f'Expected 10 sheets, found {len(paths)}')
    for path in paths:
        doc=ezdxf.readfile(path)
        if doc.units!=4:
            raise ValueError(f'{path.name}: model units must be millimetres (INSUNITS=4)')
        undefined=sorted({e.dxf.linetype for e in doc.entitydb.values()
                          if e.is_alive and e.dxf.hasattr('linetype')
                          and e.dxf.linetype.upper() not in ('BYLAYER','BYBLOCK')
                          and e.dxf.linetype not in doc.linetypes})
        audit=doc.audit()
        pdf=pymupdf.open(path.with_suffix('.pdf'))
        page=pdf[0]
        size=[round(page.rect.width*25.4/72,2),round(page.rect.height*25.4/72,2)]
        metadata=json.loads(path.with_name(path.stem+'_audit.json').read_text())
        if audit.errors or audit.fixes or undefined or size!=[594.,420.]:
            raise ValueError(f'Invalid sheet {path.name}: {size}, undefined {undefined}, audit {audit.errors}/{audit.fixes}')
        if metadata['design_sha256']!=report['design_sha256']:
            raise ValueError(f'Stale shared-design hash: {path.name}; rebuild all sheets')
        paper=doc.layouts.get(path.name[:4])
        if (abs(paper.dxf.paper_width-594)>.001 or abs(paper.dxf.paper_height-420)>.001):
            raise ValueError(f'{path.name}: DXF paper size must be A2 594x420mm')
        if paper.dxf.plot_paper_units!=1:
            raise ValueError(f'{path.name}: paper units must be millimetres')
        viewports=[v for v in paper.query('VIEWPORT') if v.dxf.status>=2]
        if len(viewports)!=1:
            raise ValueError(f'{path.name}: expected one locked viewport')
        vp=viewports[0]
        if not vp.dxf.flags & 16384:
            raise ValueError(f'{path.name}: unlocked viewport')
        actual=vp.dxf.view_height/vp.dxf.height
        if abs(actual-metadata['viewport_scale'])>.00001:
            raise ValueError(f'Wrong viewport scale: {path.name}')
        report['sheets'].append({**metadata,'file':path.name,'paper_mm':size,
                                 'undefined_linetypes':undefined})
    return report


def main():
    for module in BUILDERS:
        importlib.import_module(module).main()
    report=verify_package()
    combined=pymupdf.open()
    for sheet in report['sheets']:
        pdf=pymupdf.open(OUT/Path(sheet['file']).with_suffix('.pdf'))
        combined.insert_pdf(pdf)
    combined.save(OUT/'学道街44号_v14_设计协调图册_A2.pdf')
    report['combined_pdf_pages']=len(combined)
    (OUT/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    from PIL import Image,ImageDraw
    canvas=Image.new('RGB',(1800,1800),'white')
    for i,path in enumerate(sorted(OUT.glob('A*_preview.png'))):
        im=Image.open(path);im.thumbnail((600,425))
        canvas.paste(im,((i%3)*600,(i//3)*450+20))
        ImageDraw.Draw(canvas).text(((i%3)*600+10,(i//3)*450+4),path.stem[:4],fill='black')
    canvas.save(OUT/'contact_sheet.png')
    (OUT/'README.md').write_text('''# v14 设计协调图册

10张A2横向图纸，真实纸空间视口，模型单位mm、1:1。PDF按100%打印。
A101/A102/A201/A301/A302/A303/A401/A501：1:50；A402节点示意：1:25；A403服务墙：1:20。
合订PDF与单页PDF均为594×420mm；PNG仅为预览。图内尺寸来自A7标定和v14共享设计，非现场测量。

已修复立面/节点矩形y+h、吊顶标高、缺失线型、次卫暗藏推拉门、儿童矮柜及服务墙参数不一致。
A101采用家具块、室内设备符号、定位尺寸链和编号索引。电气/给排水为编号点位，图侧及CSV列出定位坐标；原点对应源图(200,1337)，X向东、Y向北。

本套为设计协调版：柜板/五金/开孔、门套及结构洞口、暗藏门口袋、设备SKU/散热/检修、施工节点及机电回路/管径/坡度仍待现场与厂家确认。无新增拆改范围，未提供可直接下单或施工的最终深化承诺。
窗边学习区低书柜H1100，衣柜H2300，服务墙H2400，干区吊顶2600/湿区2400/墙高2700均沿用共享设计中的假设状态。
各页audit.json及manifest.json记录共享源SHA256；已读回DXF验证audit errors=0、fixes=0，无未定义线型。

重建：`rtk proxy .venv/bin/python construction/build_all.py`
验证：`rtk proxy .venv/bin/python -m unittest discover -s tests -p 'test_cad*.py'`
依赖：ezdxf、matplotlib、shapely、Pillow、pymupdf；字体/Library/Fonts/Arial Unicode.ttf。
旧construction内的DXF/PNG及A13未覆盖。
''',encoding='utf-8')
    print(f'Validated {len(report["sheets"])} A2 sheets; combined PDF {len(combined)} pages; hash {report["design_sha256"]}')


if __name__=='__main__':
    main()
