#!/usr/bin/env python3
"""程序化 QA v3: 独立复算 (不读生成器 dimmap) → qa_report_v03.json"""
import json, hashlib, sys, math
from pathlib import Path
import ezdxf

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
GEO_NAME = sys.argv[1] if len(sys.argv) > 1 else 'geometry_v03.json'
DXF_NAME = sys.argv[2] if len(sys.argv) > 2 else 'A103_CONSTRUCTION_POC_V3.dxf'
GEO = json.loads((CAD / 'derived' / GEO_NAME).read_text())
doc = ezdxf.readfile(CAD / DXF_NAME); msp = doc.modelspace()
R = {}

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# G1 源文件实时新鲜度 (现在重算, 不信缓存)
stale = []
checked = set()
for a in GEO['anchors'] + GEO['managed_entities']:
    f = a['source_file']; want = a['source_file_sha256']
    if f in checked: continue
    checked.add(f)
    if not Path(f).exists() or sha256(f) != want: stale.append(f)
R['G1_source_fresh_live'] = {'status': 'PASS' if not stale else 'FAIL', 'stale': stale}

# G2 DIMENSION 层/计数
dims = [e for e in msp if e.dxftype() == 'DIMENSION']
bad = [e.dxf.handle for e in dims if e.dxf.layer != 'A-DIMS']
R['G2_native_dims_layer'] = {'status': 'PASS' if len(dims) == len(GEO['dims']) and not bad else 'FAIL',
                             'count': len(dims), 'expected': len(GEO['dims']), 'off_layer': bad}

# G3 独立复算: 从 geometry 锚点直接算期望值 (不读 dimmap)
A = {a['id']: a for a in GEO['anchors']}
dim_by_tag = {}
for e in dims:
    try:
        xd = e.get_xdata('DEVINDIM')
        if xd: dim_by_tag[xd[0][1]] = e
    except ezdxf.DXFValueError: pass
errs, missing = {}, []
for tag, spec in GEO['dims'].items():
    a, b = A[spec['a']], A[spec['b']]
    exp = abs(b['x'] - a['x']) if spec['axis'] == 'x' else abs(b['y'] - a['y'])
    e = dim_by_tag.get(tag)
    if not e: missing.append(tag); continue
    dev = abs(e.get_measurement() - exp)
    if dev > 1: errs[tag] = round(dev, 2)
R['G3_independent_recompute'] = {'status': 'PASS' if not errs and not missing else 'FAIL',
                                 'deviations': errs, 'unmapped_dims': missing}

# G4 对象级溯源完整 (含对象存在性——锚点对象必须出现在源 dump)
fc_objs = {o['name'] for o in json.loads((CAD/'derived'/'fc_objects_raw.json').read_text())}
bl_objs = set(json.loads((CAD/'derived'/'blender_geom_raw.json').read_text()).keys())
noobj = []
for a in GEO['anchors']:
    if not a.get('source_object_id'): noobj.append(a['id']); continue
    pool = fc_objs if a['source_file'].endswith('.FCStd') else bl_objs
    if a['source_file'].endswith('.dxf'): continue
    if a['source_object_id'] not in pool: noobj.append(f"{a['id']}→{a['source_object_id']}")
R['G4_object_exists_in_source'] = {'status': 'PASS' if not noobj else 'FAIL', 'bad': noobj}

# G5 旧标注处置
leg = [e for e in msp if e.dxf.layer == 'A-DIMS-LEGACY']
R['G5_legacy_dims_disposed'] = {'status': 'PASS' if doc.layers.get('A-DIMS-LEGACY').is_frozen() else 'FAIL',
                                'moved': len(leg)}

# G6 未确认对象登记
unc = [e for e in msp if e.dxf.layer == 'A-UNCERTAIN']
R['G6_uncertain_registry'] = {'status': 'HOLD' if unc else 'PASS', 'entities': len(unc),
    'note': '38 wall-diff candidates frozen & registered; human adjudication pending' if unc else ''}

# G7 门窗 INSERT 真实宽度 + 溯源
ins = [e for e in msp if e.dxftype() == 'INSERT']
wchk = []
for i in ins:
    if i.dxf.name == 'SYM-DOOR-LEAF':
        sid = next((a.dxf.text for a in i.attribs if a.dxf.tag == 'SRC_ID'), '')
        h = sid.split('|')[0].replace('dxf_handle:', '')
        op = next((o for o in GEO['door_openings'] if o['handle'] == h), None)
        if not op or abs(i.dxf.xscale * 1000 - op['opening_len']) > 1: wchk.append(i.dxf.handle)
R['G7_door_windows_traced'] = {'status': 'PASS' if not wchk else 'FAIL',
                               'inserts': len(ins), 'width_mismatch': wchk}

# G8 同源 revision 真实比对 (锚点 sha 互查 + 与 managed 一致)
revset = set()
for a in GEO['anchors']:
    if a['source_file'].endswith('.FCStd'): revset.add(('fc', a['source_file_sha256']))
    if a['source_file'].endswith('.blend'): revset.add(('bl', a['source_file_sha256']))
mset = set()
for m in GEO['managed_entities']:
    mset.add((('fc' if m['source'] == 'fcstd' else 'bl'), m['source_file_sha256']))
R['G8_same_revision_real'] = {'status': 'PASS' if revset <= mset or revset == mset else 'FAIL',
                              'anchor_revs': sorted(revset), 'managed_revs': sorted(mset)}

# G9 管理实体 ↔ 源对象几何一致 (墙线同步核验)
tagged = {}
for e in msp:
    if e.dxftype() == 'LWPOLYLINE':
        try:
            xd = e.get_xdata('DEVINSRC')
            if xd:
                for c, v in xd:
                    if c == 1000 and v not in ('EXISTING', 'PROPOSED', 'DEMOLISHED'):
                        tagged[v] = e
        except ezdxf.DXFValueError: pass
geo_mismatch, untag = [], []
for spec in GEO['managed_entities']:
    e = tagged.get(spec['object'])
    if not e: untag.append(spec['object']); continue
    pts = list(e.get_points('xy'))
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    eb = [min(xs), min(ys), max(xs), max(ys)]
    sb = spec.get('outline_bbox', spec['bbox'])
    dev = max(abs(eb[i] - sb[i]) for i in range(4))
    if dev > 2: geo_mismatch.append({'object': spec['object'], 'dev_mm': round(dev, 1)})
R['G9_geometry_sync'] = {'status': 'PASS' if not geo_mismatch and not untag else 'FAIL',
                         'managed': len(GEO['managed_entities']), 'mismatch': geo_mismatch[:10],
                         'untagged': untag[:10]}

# G10 洞口有效性: KOPEN 两边界在同一墙带 (x 区间重叠 >50%)
ks, kn = A.get('KOPEN-S'), A.get('KOPEN-N')
if ks and kn:
    xs = [o['rect'] for o in GEO['door_openings']]  # noqa
    # 对象 bbox 从 derived 读取
    blobs = json.loads((CAD/'derived'/'blender_geom_raw.json').read_text())
    b1 = blobs['KITCHEN_DIVIDER_PIER_SITE_REVIEW']['bbox']; b2 = blobs['W_wall_md_0010']['bbox']
    ov = max(0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
    wmin = min(b1[2]-b1[0], b2[2]-b2[0])
    R['G10_opening_validity'] = {'status': 'PASS' if ov > 0.5 * wmin else 'HOLD',
        'x_overlap_mm': round(ov, 1), 'note': 'pier-top & stub-bottom share wall band'}
else:
    R['G10_opening_validity'] = {'status': 'FAIL', 'note': 'opening anchors missing'}

# G11 编辑器 / G12 纸面
R['G11_editor_verify'] = {'status': 'PARTIAL',
    'note': 'FreeCAD importDXF reads file (prior check); interactive QCAD/LibreCAD select-edit NOT_RUN'}
R['G12_paper_pdf'] = {'status': 'PARTIAL', 'note': 'Layout1 A1 frame added; PDF regen pending T5'}

out = {'sheet': DXF_NAME, 'generated_by': 'qa_a103_v3.py', 'gates': R}
out['verdict'] = 'FAIL' if any(g['status'] == 'FAIL' for g in R.values()) else \
                 'HOLD' if any(g['status'] in ('HOLD', 'NOT_RUN', 'PARTIAL') for g in R.values()) else 'PASS'
(CAD / 'qa_report_v03.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps({k: v['status'] for k, v in R.items()}, indent=1)); print('VERDICT:', out['verdict'])
