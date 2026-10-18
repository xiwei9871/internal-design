#!/usr/bin/env python3
"""Read-only DXF batch quality baseline. Usage:
    python cad_qa.py /path/to/cad.zip --out /path/to/cad_qa.json
    python cad_qa.py /path/to/folder --out /path/to/cad_qa.json
Requires: pip install ezdxf. Never modifies source drawings.
"""
import argparse
import collections
import io
import json
import pathlib
import re
import zipfile

import ezdxf


SHEETS_WITH_POSITIONAL_DIMENSIONS = {"A102", "A103", "A201", "A202", "A302", "A303"}
UNVERIFIED_LAYERS = ("A-UNCERTAIN",)
BASE_REFERENCE_LAYERS = ("A-SOURCE-REF",)


def gather(source):
    path = pathlib.Path(source)
    if path.is_dir():
        for p in sorted(path.rglob('*.dxf')):
            if '__MACOSX' not in p.parts:
                yield p.name, p.read_bytes()
    elif path.is_file() and path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as z:
            for p in sorted(z.namelist()):
                if p.lower().endswith('.dxf') and not p.startswith('__MACOSX/'):
                    yield pathlib.Path(p).name, z.read(p)
    elif path.is_file() and path.suffix.lower() == '.dxf':
        yield path.name, path.read_bytes()
    else:
        raise ValueError('Please supply a folder, zip file, or DXF file.')


def inspect(name, raw):
    # recover.read accepts a binary file-like object, returning structural repair diagnostics
    from ezdxf import recover
    doc, auditor = recover.read(io.BytesIO(raw))
    msp = doc.modelspace()
    entities = list(msp)
    by_type = collections.Counter(x.dxftype() for x in entities)
    by_layer = collections.Counter(x.dxf.layer for x in entities)
    code = re.match(r'^(A\d{3})', name)
    code = code.group(1) if code else 'UNKNOWN'
    layout = {x.name: len(x) for x in doc.layouts}
    risky_layers = []
    for layer_name in UNVERIFIED_LAYERS + BASE_REFERENCE_LAYERS:
        if layer_name in doc.layers and by_layer[layer_name]:
            layer = doc.layers.get(layer_name)
            risky_layers.append({"layer": layer_name, "entities": by_layer[layer_name], "visible": not layer.is_off() and not layer.is_frozen()})
    local_fonts = sorted({s.dxf.font for s in doc.styles if s.dxf.hasattr('font') and (
        s.dxf.font.startswith('/') or re.match(r'^[A-Za-z]:[\\/]', s.dxf.font)
    )})
    checks = []
    def add(key, severity, explanation):
        checks.append({"id": key, "severity": severity, "message": explanation})
    if auditor.has_errors:
        add('DXF_UNRECOVERABLE', 'BLOCK', f'{len(auditor.errors)} unfixable DXF audit errors')
    elif auditor.fixes:
        add('DXF_REPAIRED', 'WARN', f'{len(auditor.fixes)} fixes were required during loading; inspect details in CAD editor')
    if doc.header.get('$INSUNITS') != 4:
        add('UNITS_NOT_MM', 'BLOCK', 'DXF units are not declared as millimeters')
    if code in SHEETS_WITH_POSITIONAL_DIMENSIONS and by_type['DIMENSION'] == 0:
        add('NO_NATIVE_DIMENSION', 'BLOCK', 'No native DIMENSION objects; review drawn/text dimensions against geometry')
    if not any(count > 0 for lname, count in layout.items() if lname.lower() != 'model'):
        add('NO_PAPERSPACE_LAYOUT', 'WARN', 'No populated paper-space layout; verify printing scale and title block externally')
    for layer in risky_layers:
        if layer['layer'] in UNVERIFIED_LAYERS and layer['visible']:
            add('UNCERTAIN_VISIBLE', 'BLOCK', f"{layer['entities']} unverified reference elements are visible on {layer['layer']}")
        elif layer['layer'] in BASE_REFERENCE_LAYERS and layer['visible']:
            add('SOURCE_REFERENCE_VISIBLE', 'WARN', f"{layer['entities']} source-reference elements are visible")
    if local_fonts:
        add('LOCAL_FONT_PATH', 'WARN', 'Font style refers to OS-specific absolute path(s)')
    return {
        'sheet':code, 'filename':name, 'dxf_version':doc.dxfversion,
        'units_code':doc.header.get('$INSUNITS'),
        'modelspace_entity_count': len(entities),
        'entities':dict(by_type), 'layer_counts':dict(by_layer),
        'layouts':layout, 'audit_unrecoverable':len(auditor.errors),
        'audit_fixes':len(auditor.fixes), 'local_fonts':local_fonts,
        'risky_layers':risky_layers, 'checks':checks,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',help='cad.zip, directory, or file.dxf')
    ap.add_argument('--out',default='cad_qa.json')
    args=ap.parse_args()
    data=[]
    for name,content in gather(args.source):
        try:
            data.append(inspect(name,content))
        except Exception as exc:
            data.append({'filename':name, 'checks':[{'id':'READ_FAILED','severity':'BLOCK','message':str(exc)}]})
    versions=sorted({x.get('dxf_version') for x in data if x.get('dxf_version')})
    shared=[]
    if len(versions)>1:
        shared.append({'id':'INCONSISTENT_DXF_VERSION','severity':'WARN','message':f'Files use mixed versions: {versions}'})
    summary = dict(sheets=len(data),blocks=sum(c['severity']=='BLOCK' for x in data for c in x['checks']),
                   warnings=sum(c['severity']=='WARN' for x in data for c in x['checks']))
    result = {'scope':'Structural preflight only; not a proof of construction correctness', 'summary':summary,
              'shared_checks':shared, 'sheets':data}
    pathlib.Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'summary':summary,'version_warning': bool(shared),
      'sheets':{x['sheet']:[c['id'] for c in x['checks']] for x in data if x.get('sheet')}},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
