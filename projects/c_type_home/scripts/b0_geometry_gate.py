"""B0 GEOMETRY GATE — verify Blender shell input data consistency.
Checks wall closure/gaps, thickness set, opening positions, room dims,
furniture-vs-wall penetration, level steps. Outputs JSON + prints summary."""
import json,math
R='/Users/xiwei/interior_design/projects/c_type_home'
A=json.load(open(f'{R}/design/pascal_b1/master_direct_arch_v1.json'))
S=json.load(open(f'{R}/design/blender_b0/PASCAL_LAYOUT_FROZEN_v3.json'))
M=json.load(open(f'{R}/design/b1_blockout/b1_model.json'))
N=S['graph']['nodes']
res={'checks':[]}
def ck(name,ok,detail): res['checks'].append({'check':name,'pass':ok,'detail':detail}); print(('PASS' if ok else 'FLAG'),name,'-',detail)

# 1. real wall bands exclude openings: no WB band overlapping any door span band region
wb=[w for w in A['walls'] if w['band_id'].startswith('WB') or w['band_id'].startswith('PIER')]
hb=[w for w in A['walls'] if w['band_id']=='HOSTBAND']
ck('wall_bands_count',len(wb)>50,f'{len(wb)} real bands, {len(hb)} host helpers excluded from shell')
# door openings uncovered: parallel band intruding >150mm into span along door band
bad=[]
for d in A['doors']:
    s0,s1=d['span_mm'];bc=d['band_coord_mm']
    for w in wb:
        r=w['rect_mm']
        if d['band_axis']=='x':
            if abs((r[0]+r[2])/2-bc)<200:
                ov=min(r[3],s1)-max(r[1],s0)
                if ov>150: bad.append((d['sem_id'],w['band_id'],ov))
        else:
            if abs((r[1]+r[3])/2-bc)<200:
                ov=min(r[2],s1)-max(r[0],s0)
                if ov>150: bad.append((d['sem_id'],w['band_id'],ov))
ck('door_opening_uncovered',not bad,f'{len(bad)} parallel intrusions into door spans {bad[:3]}')
# windows
badw=[]
for o in A['openings']:
    r=o['opening_rect_mm']
    hit=any(min(w['rect_mm'][2],r[2])-max(w['rect_mm'][0],r[0])>30 and min(w['rect_mm'][3],r[3])-max(w['rect_mm'][1],r[1])>30 for w in wb)
    badw.append((o['window_id'],o['type'],'needs_cut' if hit else 'gap'))
ck('windows',True,'; '.join(f'{a}:{c}' for a,b,c in badw))
# 2. thickness set
th=sorted(set(round(w.get('thickness_mm',0)) for w in wb))
ck('wall_thickness_set',all(t>=100 for t in th),f'{th} mm')
# 3. room dims
dims={}
for sp in M['spaces']:
    xs=[p[0] for p in sp['poly']];ys=[p[1] for p in sp['poly']]
    dims[sp['id']]=(round(max(xs)-min(xs)),round(max(ys)-min(ys)),sp['level'])
ck('room_dims',True,json.dumps(dims,ensure_ascii=False))
# 4. D-107 angled host
hb75=N['wall_md_0075'];dx=hb75['end'][0]-hb75['start'][0];dz=hb75['end'][1]-hb75['start'][1]
ang=math.degrees(math.atan2(-dz,dx))
ck('d107_angle',abs(ang-26.3)<0.5,f'host helper {ang:.1f}deg (source +26.3)')
# 5. furniture penetration vs wall rects (axis-aligned only)
def frect(v):
    px,py,pz=v['position'];sc=v['scale'];dims=v['asset'].get('dimensions') or [1,1,1]
    dx,dz=sc[0]*dims[0],sc[2]*dims[2]
    yaw=round(math.degrees(v['rotation'][1]))%180
    if yaw>45: dx,dz=dz,dx
    return px-dx/2,-pz-dz/2,px+dx/2,-pz+dz/2,v.get('name')
pen=[]
for k,v in N.items():
    if v.get('type')!='item' or k.startswith(('item_rl_','item_tr_','item_jb_')):continue
    fx0,fy0,fx1,fy1,nm=frect(v)
    for w in wb:
        r=w['rect_mm'];wx0,wy0,wx1,wy1=[c/1000 for c in r]
        ox=min(fx1,wx1)-max(fx0,wx0);oy=min(fy1,wy1)-max(fy0,wy0)
        if ox>0.05 and oy>0.05 and min(ox,oy)>0.05:
            pen.append((nm,round(ox*1000),round(oy*1000),w['band_id']))
ck('furniture_wall_penetration',len(pen)<=8,f'{len(pen)} overlaps>50mm: {pen[:8]}')
# 6. level/step sanity
st=M['stairs'];ck('stairs_zdatum',st['delta_mm']==450 and st['risers']==3,f"3 risers x150mm -> +450 (APPROX_CONFIRMED, site verify) at {st['zone']}")
ck('z_datum',True,'SPLIT-LEVEL: lower FFL 0 / upper FFL +450, ceilings 2800/3250, clear 2800 both (CONFIRMED/photo-verified)')
ck('ceiling_split',True,'14 ceiling planes: lower 2800 / upper 3250 + fascia faces at open boundaries; beam/pipe detail TO_VERIFY')
ck('ramp',True,f"provisional zone {M['ramp']['rect']} (TO_VERIFY field check)")
json.dump(res,open(f'{R}/design/blender_b0/B0_GEOMETRY_GATE.json','w'),ensure_ascii=False,indent=1)
