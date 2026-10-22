#!/usr/bin/env python3
"""ARCH EXTRACTION AUDIT — coverage: MASTER_V2 linework vs Pascal stored walls.
Read-only. Rasterize master edges (canonical mm), check each sample point
against Pascal wall rects. Uncovered -> candidate missing wall linework."""
import json, urllib.request
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
DX, DY = -1298172.0, 296458.0
OUT = f'{BASE}/design/pascal_b1'
TOL = 80.0  # mm

inv = json.load(open(f'{BASE}/design/pascal_b1/wall_audit/MASTER_ARCH_OBJECT_INVENTORY.json'))['objects']

def seg_pts(pts):
    out = []
    for i in range(len(pts)-1):
        x0,y0 = pts[i][0]+DX, pts[i][1]+DY
        x1,y1 = pts[i+1][0]+DX, pts[i+1][1]+DY
        n = max(2, int((((x1-x0)**2+(y1-y0)**2)**.5)/40))
        for k in range(n):
            t=k/(n-1); out.append((x0+(x1-x0)*t, y0+(y1-y0)*t))
    return out

# collect master linework, all edges per object
master = {}   # name -> dict(layer, pts, edges)
for n, v in inv.items():
    if not v.get('edges'): continue
    layer = v['dwg_layers'][0] if v['dwg_layers'] else ('NO_LAYER')
    pts = []
    for e in v['edges']:
        pts += seg_pts(e['pts'])
    if pts: master[n] = {'layer': layer, 'label': v['label'], 'type': v['type'], 'pts': pts}

# pascal walls
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
G = json.loads(op.open('http://pascal.localhost:57071/api/scenes/pascal-arch-truth-v1', timeout=15).read())['graph']
def wrect(n):
    (x0,z0),(x1,z1)=n['start'],n['end']; t=n['thickness']*1000
    X0,X1=sorted([x0*1000,x1*1000]); Y0,Y1=sorted([-z0*1000,-z1*1000])
    if Y1-Y0<1: Y0-=t/2; Y1+=t/2
    else: X0-=t/2; X1+=t/2
    return [X0,Y0,X1,Y1]
pw=[wrect(n) for n in G['nodes'].values() if n['type']=='wall']

def covered(x,y):
    for r in pw:
        if r[0]-TOL<=x<=r[2]+TOL and r[1]-TOL<=y<=r[3]+TOL: return True
    return False

report={}
for n,m in master.items():
    cov=[covered(x,y) for x,y in m['pts']]
    frac=sum(cov)/len(cov)
    report[n]={'layer':m['layer'],'label':m['label'],'type':m['type'],
               'pts':len(m['pts']),'covered_frac':round(frac,2)}
    m['cov']=cov

missing={n:r for n,r in report.items() if r['covered_frac']<0.5 and r['pts']>=4}
print('master objects w/ linework:',len(master))
print('uncovered(<50%):',len(missing))
from collections import Counter
print('by layer:',Counter(r['layer'] for r in missing.values()))
for n,r in sorted(missing.items()):
    print(' MISS',n,r['layer'],r['label'],r['type'],'cov',r['covered_frac'],'pts',r['pts'],
          'xy~',round(sum(p[0] for p in master[n]['pts'])/len(master[n]['pts'])),
          round(sum(p[1] for p in master[n]['pts'])/len(master[n]['pts'])))
json.dump(report, open(f'{OUT}/wall_audit/EXTRACTOR_COVERAGE.json','w'), indent=1, ensure_ascii=False)

# overlay: master linework colored by coverage, pascal rects faint
fig,ax=plt.subplots(figsize=(13,13))
for r in pw:
    ax.add_patch(Rectangle((r[0],r[1]),r[2]-r[0],r[3]-r[1],color='#9ccc65',alpha=.35,zorder=1))
for n,m in master.items():
    if m['layer'] in ('F-FURN','F-SAN FIT'): continue
    xs=[p[0] for p in m['pts']]; ys=[p[1] for p in m['pts']]
    f=report[n]['covered_frac']
    col='#111111' if f>=0.5 else '#d32f2f'
    ax.scatter(xs[::3],ys[::3],s=1,c=col,zorder=2)
ax.set_xlim(300,17000); ax.set_ylim(14700,-1500); ax.set_aspect('equal')
ax.set_title('MASTER linework: black=covered by Pascal wall, RED=MISSING; green=Pascal walls')
plt.savefig(f'{OUT}/MASTER_DIRECT_VS_PASCAL_OVERLAY.png',dpi=140,bbox_inches='tight'); plt.close()

# raw arch top: master linework only, no furniture/sanitary
fig,ax=plt.subplots(figsize=(13,13))
for n,m in master.items():
    if m['layer'] in ('F-FURN','F-SAN FIT'): continue
    xs=[p[0] for p in m['pts']]; ys=[p[1] for p in m['pts']]
    col={'S-S.WALL':'#111111','F-DOOR':'#1565c0','S-楼梯':'#6d4c41'}.get(m['layer'],'#999999')
    ax.scatter(xs[::3],ys[::3],s=1,c=col)
ax.set_xlim(300,17000); ax.set_ylim(14700,-1500); ax.set_aspect('equal')
ax.set_title('MASTER_V2_RAW_ARCH_TOP: black=S-S.WALL, blue=F-DOOR, brown=stairs, grey=unlayered')
plt.savefig(f'{OUT}/MASTER_V2_RAW_ARCH_TOP.png',dpi=140,bbox_inches='tight'); plt.close()
print('images done')
