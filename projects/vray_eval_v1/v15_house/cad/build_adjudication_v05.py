#!/usr/bin/env python3
"""P1.3.2 台账: 物理墙段归并裁决 + D02 映射 + A102 只读差集勘察"""
import json, csv
from pathlib import Path
CAD = Path(__file__).resolve().parent
g = json.loads((CAD/'derived'/'geometry_v05.json').read_text())

# ---- 1) 物理墙段归并: 按 XY 相交/邻近聚类 ----
items = []
for a in g['anomalies']:
    for grp in (a.get('kept_both') or [a.get('dropped',[])+a.get('into',[])]):
        pass
for c in g['conflicts']:
    items.append({'kind':'conflict','objs':[c['a'],c['b']],'detail':f"{c['status_a']} vs {c['status_b']} iou={c['iou']}"})
for a in g['anomalies']:
    if a['rule']=='overlap_unresolved':
        items.append({'kind':'overlap_unresolved','objs':a['kept_both'][0]+a['kept_both'][1],
                      'detail':f"{a['status_i']} vs {a['status_j']} ov={a['overlap']}"})
    elif a['rule']=='subsumed':
        items.append({'kind':'subsumed_auto','objs':a['dropped']+a['into'],
                      'detail':f"{a['status_i']}=={a['status_j']} ov={a['overlap']}"})
for m in g['managed_entities']:
    if m.get('cut_height')=='FOOTPRINT_FALLBACK':
        items.append({'kind':'section_fallback','objs':m['objects'],'detail':'no section cut → full XY projection'})
    if m['design_status'] in ('UNVERIFIED','DESIGN_REVIEW_PENDING'):
        items.append({'kind':m['design_status'].lower(),'objs':m['objects'],'detail':m['design_status']})
obj2bb = {o:m['outline_bbox'] for m in g['managed_entities'] for o in m['objects']}
def center(o):
    b=obj2bb.get(o,[0,0,0,0]); return ((b[0]+b[2])/2,(b[1]+b[3])/2)
# 按对象集合空间接近归并 (2500mm 邻域)
clusters=[]
for it in items:
    placed=False
    for cl in clusters:
        if any(abs(center(a)[0]-center(b)[0])<2500 and abs(center(a)[1]-center(b)[1])<2500
               for a in it['objs'] for b in cl['objs']):
            cl['objs']+=it['objs']; cl['items'].append(it); placed=True; break
    if not placed: clusters.append({'objs':list(it['objs']),'items':[it]})
with open(CAD/'wall_adjudication_v05.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['case','objects','xy_range','kinds','auto_resolvable','needs_owner','needs_professional'])
    for i,cl in enumerate(clusters):
        xs=[obj2bb[o][k] for o in cl['objs'] if o in obj2bb for k in (0,2)]
        ys=[obj2bb[o][k] for o in cl['objs'] if o in obj2bb for k in (1,3)]
        rng=f"x{round(min(xs))}-{round(max(xs))} y{round(min(ys))}-{round(max(ys))}" if xs else ''
        kinds={it['kind'] for it in cl['items']}
        needs_owner = bool(kinds & {'conflict','overlap_unresolved','design_review_pending'})
        w.writerow([f'CASE-{i+1:02d}','|'.join(sorted(set(cl['objs']))),rng,'|'.join(kinds),
                    'subsumed_auto' in kinds or 'section_fallback' in kinds,
                    'YES' if needs_owner else '', 'structure' if 'unverified' in kinds else ''])
print('cases:',len(clusters))

# ---- 2) D02 映射表 ----
D02=[('D02-1 厨房西墙中段(开放式厨房)','W_INT_X5800','(5700,1800)-(5900,3800)','partial','A102 DEMO_PART verified'),
     ('D02-2 走廊西墙中段(楼梯敞开)','W_INT_X7900_U','(7800,5000)-(7900,7800)','partial','A102 DEMO_PART verified'),
     ('D02-3 生活阳台北墙东段','W_BALC_N','(3300,2400)-(5800,2560)','partial','A102 DEMO_PART verified'),
     ('D02-4 客厅北墙旧带','W_EXT_N_LV','(2700,12750)-(7900,12950)','full','A102 DEMO_FULL verified'),
     ('D02-5 阳光房北带','W_EXT_N_BAL','(7900,13400)-(13000,13600)','full','A102 DEMO_FULL verified')]
with open(CAD/'d02_mapping_v05.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['decision','object','demo_rect','scope','evidence','status'])
    stat={m['objects'][0]:m['design_status'] for m in g['managed_entities']}
    for d,obj,rect,scope,ev in D02:
        w.writerow([d,obj,rect,scope,ev,stat.get(obj,'NOT_FOUND')])
print('d02 mapped:',len(D02))

# ---- 3) A102 只读差集勘察 (数据, 非图纸) ----
rows=[]
for m in g['managed_entities']:
    st=m['design_status']
    for p in m['demolished_parts']:
        xs=[v[0] for v in p]; ys=[v[1] for v in p]
        rows.append(['EXISTING_DEMOLISHED','|'.join(m['objects']),m['source'],
                     f"{round(min(xs))},{round(min(ys))},{round(max(xs))},{round(max(ys))}",''])
    for p in m['parts']:
        xs=[v[0] for v in p['exterior']]; ys=[v[1] for v in p['exterior']]
        rows.append([st,'|'.join(m['objects']),m['source'],
                     f"{round(min(xs))},{round(min(ys))},{round(max(xs))},{round(max(ys))}",
                     m.get('cut_height') or ''])
with open(CAD/'a102_diff_survey.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['state','objects','source','xyxy','cut_height'])
    w.writerows(rows)
print('a102 survey rows:',len(rows))
