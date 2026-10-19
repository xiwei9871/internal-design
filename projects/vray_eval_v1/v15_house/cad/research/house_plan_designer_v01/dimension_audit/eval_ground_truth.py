#!/usr/bin/env python3
"""Gate 任务B: 适配器结果 vs 15条人工标准答案, 纯位置与值辅助分开统计。"""
import csv, json

D = '/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad/research/house_plan_designer_v01/dimension_audit'
gt = json.load(open(f'{D}/ground_truth_15.json'))['records']
mini = {r['th']: r for r in csv.DictReader(open(f'{D}/dimension_audit_mini.csv')) if r['src'] == 'baseline'}

rows, stat = [], {'pure_pos': 0, 'va': 0, 'unres': 0, 'correct': 0, 'misbound': 0}
for g in gt:
    r = mini.get(g['text_handle'], {})
    bound = r.get('cls', '') in ('CONSISTENT', 'DIGITIZATION_MISMATCH', 'CONSISTENT_VALUE_ASSISTED')
    hit = bound and r.get('seg') == g['dimline_handle']
    mode = 'value_assisted' if r.get('cls') == 'CONSISTENT_VALUE_ASSISTED' else \
           ('unresolved' if r.get('cls') == 'UNRESOLVED' else 'pure_positional')
    stat['pure_pos' if mode == 'pure_positional' else 'va' if mode == 'value_assisted' else 'unres'] += 1
    stat['correct'] += hit
    stat['misbound'] += bound and not hit
    rows.append({'text_handle': g['text_handle'], 'label': g['label'],
                 'gt_seg': g['dimline_handle'], 'adapter_seg': r.get('seg', ''),
                 'binding_mode': mode, 'hit': hit, 'adapter_cls': r.get('cls', ''),
                 'gt_residual': g['residual_mm'], 'adapter_residual': r.get('res', '')})

with open(f'{D}/ground_truth_eval.csv', 'w', newline='') as fo:
    w = csv.DictWriter(fo, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

print(f"GT={len(rows)} 正确绑定={stat['correct']} 误配={stat['misbound']} UNRESOLVED={stat['unres']}")
print(f"绑定方式分布: 纯位置={stat['pure_pos']} 值辅助={stat['va']} 未解={stat['unres']}")
print("注: 值辅助绑定用标注值消歧链归属, 不等于独立几何正确性证明")
