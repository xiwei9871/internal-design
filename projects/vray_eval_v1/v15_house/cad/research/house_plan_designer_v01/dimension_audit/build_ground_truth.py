#!/usr/bin/env python3
"""Gate 任务B: 15 条人工标准答案 + 测量端点证据。
绑定依据(人工判读): 同一尺寸行内, 相邻界线(长竖 LINE)刻度对划分链段;
每条标注文字位于其所属链段中点偏左约 200(半字宽), 且同链标签 x 单调递增。
外圈粗链 7 条 + 内圈细链 8 条 = 15 条。
"""
import ezdxf, json, math

BASE = '/Users/xiwei/interior_design/projects/c_type_home/cad/C型_原始户型数字化基准图.dxf'
OUT = '/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad/research/house_plan_designer_v01/dimension_audit/ground_truth_15.json'

doc = ezdxf.readfile(BASE)
msp = doc.modelspace()
lines = {e.dxf.handle: e for e in msp.query('LINE') if e.dxf.get('layer') == 'A-DIMS'}
texts = {e.dxf.handle: e for e in msp.query('TEXT') if e.dxf.get('layer') == 'A-DIMS'}

# 人工绑定表: text_handle -> (chain, 尺寸线 LINE handle)
GT = {
    '119': ('bottom_outer', '112'), '11A': ('bottom_outer', '113'),
    '11B': ('bottom_outer', '114'), '11C': ('bottom_outer', '115'),
    '11D': ('bottom_outer', '116'), '11E': ('bottom_outer', '117'),
    '11F': ('bottom_outer', '118'),
    '141': ('bottom_inner', '131'), '142': ('bottom_inner', '132'),
    '143': ('bottom_inner', '133'), '144': ('bottom_inner', '134'),
    '145': ('bottom_inner', '135'), '146': ('bottom_inner', '136'),
    '149': ('bottom_inner', '139'), '14C': ('bottom_inner', '13C'),
    # 顶行外圈 1 条(已含 15? 注意总数) — 见下统计
}
# 当前 15 条 = 7 outer + 8 inner, 全部在底部尺寸行
records = []
for th, (chain, lh) in GT.items():
    t, ln = texts[th], lines[lh]
    s, en = ln.dxf.start, ln.dxf.end
    L = math.dist((s.x, s.y), (en.x, en.y))
    x0, x1 = sorted([s.x, en.x])
    records.append({
        'text_handle': th, 'label': int(t.dxf.text.strip()),
        'text_at': [round(t.dxf.insert.x, 1), round(t.dxf.insert.y, 1)],
        'chain': chain, 'dimline_handle': lh,
        'measure_endpoints': [round(x0, 1), round(x1, 1)],
        'measured_seg_len_mm': round(L, 1),
        'residual_mm': round(int(t.dxf.text.strip()) - L, 1),
        'label_mid_offset': round((x0 + x1) / 2 - t.dxf.insert.x, 1),
    })
out = {
    'method': '人工逐条核验: 界线刻度对→链段→标注文字偏置规律(≈200左偏,同链单调)',
    'n_records': len(records), 'source': BASE.split('/')[-1],
    'records': records,
    'residual_summary': {
        'min': min(r['residual_mm'] for r in records),
        'max': max(r['residual_mm'] for r in records),
        'note': '标注为权威值, 绘制几何为近似值',
    },
}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
for r in records:
    print(f"{r['text_handle']:>4} {r['label']:>5} -> {r['dimline_handle']:>4} "
          f"len={r['measured_seg_len_mm']:>7} res={r['residual_mm']:>6} "
          f"mid_off={r['label_mid_offset']:>6} [{r['chain']}]")
