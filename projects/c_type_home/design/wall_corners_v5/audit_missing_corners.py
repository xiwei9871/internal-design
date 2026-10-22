"""Find true missing L/T corner quadrants, not merely non-manifold seams."""
import json,importlib.util,itertools
from pathlib import Path
from collections import defaultdict
import shapely
from shapely.geometry import Polygon,MultiPoint,box
from shapely.ops import unary_union

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
spec=importlib.util.spec_from_file_location('wall_backend',ROOT/'design/wall_junctions_v4/solid_wall_backend.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
d=json.loads((OUT/'V4_JUNCTION_REFERENCE.json').read_text());bands=[]
for r in d['wall_bands']:
    lo,hi=r['bounds'];rect=[round(lo[0]*1000)/1000,round(lo[1]*1000)/1000,round(hi[0]*1000)/1000,round(hi[1]*1000)/1000]
    dx,dy=rect[2]-rect[0],rect[3]-rect[1]
    hull=MultiPoint([v[:2] for v in r['vertices']]).convex_hull
    if dx*dy<1e-6 or abs(hull.area/(dx*dy)-1)>.003:continue
    axis='H' if dx>=2*dy and dx>=.4 and dy<=.45 else 'V' if dy>=2*dx and dy>=.4 and dx<=.45 else None
    if axis:bands.append(dict(name=r['name'],rect=rect,z0=round(lo[2],5),z1=round(hi[2],5),axis=axis))
candidates={}
for h,v in itertools.product([x for x in bands if x['axis']=='H'],[x for x in bands if x['axis']=='V']):
    hr,vr=h['rect'],v['rect']
    # The transverse wall ends at the longitudinal wall's SIDE, not its axis.
    # Extending each to its intended outer corner fills the missing quadrant.
    side_touch=min(abs(hr[2]-vr[0]),abs(hr[0]-vr[2]))<=.001
    y_gap=max(vr[1]-hr[3],hr[1]-vr[3],0)
    if not side_touch or y_gap>.001:continue
    z0=max(h['z0'],v['z0']);z1=min(h['z1'],v['z1'])
    if z1-z0<.025:continue
    if h['z1']-h['z0']>=2 and v['z1']-v['z0']>=2:z0=min(h['z0'],v['z0'])
    rect=(vr[0],hr[1],vr[2],hr[3]);key=(*rect,z0,z1)
    if key not in candidates:candidates[key]=dict(rect=list(rect),z0=z0,z1=z1,sources=[])
    candidates[key]['sources'].append([h['name'],v['name']])
skin=d['skin'];zs=[v[2] for v in skin['vertices']];skin['minz']=min(zs);skin['maxz']=max(zs)
levels=sorted(set(round(z,5) for z in zs));sections={}
def section(z):
    if z not in sections:sections[z]=mod.cross_section(skin,z)
    return sections[z]
patches=[];rejected=[]
for c in candidates.values():
    rect=box(*c['rect']);cuts_z=sorted(set([c['z0'],c['z1']]+[z for z in levels if c['z0']<z<c['z1']]))
    active=[];volume=0;probes=[];volumes=[];fractions=[]
    for z0,z1 in zip(cuts_z,cuts_z[1:]):
        z=(z0+z1)/2;allowed=rect
        for cut in d['cuts']:
            if cut['lo'][2]<=z<=cut['hi'][2]:allowed=allowed.difference(box(cut['lo'][0],cut['lo'][1],cut['hi'][0],cut['hi'][1]))
        for cut in d['intentional_open_regions']:
            if cut['lo'][2]<=z<=cut['hi'][2]:allowed=allowed.difference(box(cut['lo'][0],cut['lo'][1],cut['hi'][0],cut['hi'][1]))
        missing=allowed.difference(section(z))
        if missing.area>.000001 and missing.area/rect.area>=.10:
            active.append((z0,z1));volume+=missing.area*(z1-z0);volumes.append((z0,z1,missing.area*(z1-z0)));fractions.append(missing.area/rect.area)
            p=missing.representative_point();probes.append([p.x,p.y,z])
    if not active:
        rejected.append(dict(**c,reason='ALREADY_FILLED_OR_PROTECTED_OPENING'));continue
    if max(fractions)<.10:
        rejected.append(dict(**c,reason='CONTINUOUS_ANGLED_RETURN_NOT_A_MISSING_QUADRANT',max_missing_fraction=max(fractions)));continue
    # Generate bounded volumes only in the actual height bands with a gap.
    merged=[]
    for z0,z1 in active:
        if merged and abs(merged[-1][1]-z0)<1e-5:merged[-1][1]=z1
        else:merged.append([z0,z1])
    for z0,z1 in merged:
        patches.append({**c,'z0':z0,'z1':z1,'missing_volume_m3':sum(v for a,b,v in volumes if a>=z0-1e-5 and b<=z1+1e-5),
                            'probes':[p for p in probes if z0<=p[2]<=z1]})
groups=defaultdict(list)
for p in patches:groups[tuple(p['rect'])].append(p)
dedup=[]
for n,rect in enumerate(sorted(groups),1):
    ranges=[]
    for p in sorted(groups[rect],key=lambda p:p['z0']):
        if ranges and p['z0']<=ranges[-1][1]+1e-5:ranges[-1][1]=max(ranges[-1][1],p['z1'])
        else:ranges.append([p['z0'],p['z1']])
    sources=list({tuple(s) for p in groups[rect] for s in p['sources']})
    for i,(z0,z1) in enumerate(ranges,1):
        probes=list({tuple(pt) for p in groups[rect] for pt in p['probes'] if z0<=pt[2]<=z1})
        dedup.append(dict(id=f'J{n:02d}_{i}',rect=list(rect),z0=z0,z1=z1,sources=sources,probes=[list(pt) for pt in probes]))
patches=dedup
report=dict(status='MISSING_MACRO_CORNERS_IDENTIFIED',source=d['source'],source_sha256=d['source_sha256'],
            axis_wall_bands=len(bands),junction_candidates=len(candidates),missing_corner_sites=len(groups),
            patch_volumes=len(patches),patches=patches,already_complete_candidates=rejected,
            intentional_open_regions=d['intentional_open_regions'],opening_cuts=d['cuts'])
(OUT/'CORNER_REPAIR_REGISTER.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['patches','already_complete_candidates','opening_cuts']},ensure_ascii=False,indent=2))
print(json.dumps([dict(id=p['id'],rect_mm=[round(v*1000,2) for v in p['rect']],z_mm=[p['z0']*1000,p['z1']*1000]) for p in patches],ensure_ascii=False,indent=2))
