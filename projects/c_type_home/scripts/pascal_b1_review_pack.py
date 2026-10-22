#!/usr/bin/env python3
"""PASCAL B1 review pack: annotated PNGs for door clipping + limitation highlights + zone map.
Schematic (canonical mm -> px), PIL only. No scene mutation."""
import json, math
from PIL import Image, ImageDraw, ImageFont

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
M = json.load(open(f'{BASE}/design/b1_blockout/b1_model.json'))
G = json.load(open(f'{BASE}/design/pascal_b1/pascal_full_scene.json'))
OUT = f'{BASE}/design/pascal_b1'
N = G['nodes']
IDM = json.load(open(f'{BASE}/design/pascal_b1/pascal_full_id_map.json'))['map']
bypid = {e['pascal_id']: e for e in IDM}

try:
    FONT = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 26)
    FONT_S = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 18)
except Exception:
    FONT = FONT_S = ImageFont.load_default()

C_WALL = (60, 60, 70); C_CANON = (255, 200, 40); C_PASCAL = (220, 60, 60)
C_ZONE = (120, 160, 220); C_TXT = (30, 30, 30); C_LIM = (180, 40, 160)

def door_panel(canon_id, out_png):
    """Local schematic: wall band + canonical opening + pascal leaf + dims."""
    o = next(o for o in M['openings'] if o['id'] == canon_id)
    e = next(e for e in IDM if e.get('canonical_id') == canon_id
             and N[e['pascal_id']]['type'] == 'door')
    dn = N[e['pascal_id']]
    w = N[dn['wallId']]
    r = o['rect']
    horiz = (r[3]-r[1]) <= (r[2]-r[0])   # wall direction
    # wall global span
    if horiz:
        wspan = (min(w['start'][0], w['end'][0])*1000, max(w['start'][0], w['end'][0])*1000)
        wy = (w['start'][1])*1000
        wall_poly = [(wspan[0], wy-w['thickness']*500), (wspan[1], wy-w['thickness']*500),
                     (wspan[1], wy+w['thickness']*500), (wspan[0], wy+w['thickness']*500)]
        # pascal leaf global
        L = math.hypot(w['end'][0]-w['start'][0], w['end'][1]-w['start'][1])
        t = dn['position'][0]/L
        gx = (min(w['start'][0],w['end'][0]) + dn['position'][0])*1000
        pw = dn['width']*1000
        leaf = [(gx-pw/2, wy-350), (gx+pw/2, wy-350), (gx+pw/2, wy+350), (gx-pw/2, wy+350)]
    else:
        wspan = (min(w['start'][1], w['end'][1])*1000, max(w['start'][1], w['end'][1])*1000)
        wx = (w['start'][0])*1000
        wall_poly = [(wx-w['thickness']*500, wspan[0]), (wx+w['thickness']*500, wspan[0]),
                     (wx+w['thickness']*500, wspan[1]), (wx-w['thickness']*500, wspan[1])]
        gy = (min(w['start'][1],w['end'][1]) + dn['position'][0])*1000
        pw = dn['width']*1000
        leaf = [(wx-350, gy-pw/2), (wx+350, gy-pw/2), (wx+350, gy+pw/2), (wx-350, gy+pw/2)]
    canon = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
    allpts = wall_poly + leaf + canon
    xs = [p[0] for p in allpts]; ys = [p[1] for p in allpts]
    pad = 600
    x0, x1, y0, y1 = min(xs)-pad, max(xs)+pad, min(ys)-pad, max(ys)+pad
    sc = 800/max(x1-x0, y1-y0)
    W = int((x1-x0)*sc)+160; H = int((y1-y0)*sc)+240
    img = Image.new('RGB', (W, H), (250, 250, 248)); dr = ImageDraw.Draw(img)
    def P(p): return ((p[0]-x0)*sc+60, (p[1]-y0)*sc+90)
    dr.polygon([P(p) for p in wall_poly], fill=C_WALL)
    dr.polygon([P(p) for p in canon], outline=C_CANON, width=5)
    dr.polygon([P(p) for p in leaf], outline=C_PASCAL, width=5)
    sw = (r[2]-r[0]) if horiz else (r[3]-r[1])
    dr.text((60, 20), f'{canon_id}  canonical={sw:.0f}mm  pascal={pw:.0f}mm  '
                      f'diff={pw-sw:+.0f}mm', font=FONT, fill=C_TXT)
    dr.text((60, H-80), 'gray=host wall  yellow=canonical opening  red=pascal leaf',
            font=FONT_S, fill=C_TXT)
    img.save(out_png); print('wrote', out_png)

door_panel('D-SM', f'{OUT}/PASCAL_REVIEW_D_SM.png')
door_panel('D-MB', f'{OUT}/PASCAL_REVIEW_D_MB.png')

# ---------- limitation highlight map ----------
xs_all, ys_all = [], []
polys = []
for w in M['walls'] + M['parapets']:
    r = w['rect']
    polys.append(((r[0], r[1], r[2], r[3]), C_WALL))
zones = [(s['poly'], s['id'], s.get('name','')) for s in M['spaces']]
LIMS = {  # canonical id -> highlight label
    'D-SM': 'L-02 clip -236mm', 'D-MB': 'L-02 clip -66mm',
    'W-LBALC-S': 'L-04 glass on parapet',
    'G-DIN-LIV': 'L-05 synthetic host', 'W-LIV-N': 'L-05 bay front',
}
marks = []
for o in M['openings']:
    if o['id'] in LIMS: marks.append((o['rect'], LIMS[o['id']], o['id']))
for w in M['windows']:
    if w['id'] in LIMS: marks.append((w['rect'], LIMS[w['id']], w['id']))
    if w.get('bay') and 'front' in w['bay']:
        fr = w['bay']['front']; marks.append((fr, 'bay front', w['id']+'-FR'))

allr = [p[0] for p in polys]
xs_all = [r[0] for r in allr]+[r[2] for r in allr]
ys_all = [r[1] for r in allr]+[r[3] for r in allr]
x0,x1,y0,y1 = min(xs_all)-1500, max(xs_all)+1500, min(ys_all)-1500, max(ys_all)+1500
sc = 1600/max(x1-x0, y1-y0); W=int((x1-x0)*sc); H=int((y1-y0)*sc)
img = Image.new('RGB',(W,H),(252,252,250)); dr=ImageDraw.Draw(img)
def P2(x,y): return ((x-x0)*sc,(y-y0)*sc)
for s in M['spaces']:
    dr.polygon([P2(x,y) for x,y in s['poly']], outline=C_ZONE, width=2)
for r,c in polys:
    dr.rectangle([P2(r[0],r[1]),P2(r[2],r[3])], fill=c)
for r,lab,cid in marks:
    cx,cy=(r[0]+r[2])/2,(r[1]+r[3])/2
    dr.rectangle([P2(r[0],r[1]),P2(r[2],r[3])], outline=C_LIM, width=6)
    dr.ellipse([P2(cx-150,cy-150),P2(cx+150,cy+150)],outline=C_LIM,width=5)
    dr.text(P2(cx+200,cy-200),f'{cid}: {lab}',font=FONT_S,fill=C_LIM)
img.save(f'{OUT}/PASCAL_REVIEW_LIMITATIONS.png'); print('wrote limitations map')

# ---------- zone map ----------
img = Image.new('RGB',(W,H),(252,252,250)); dr=ImageDraw.Draw(img)
for s in M['spaces']:
    poly=[P2(x,y) for x,y in s['poly']]
    dr.polygon(poly, outline=(80,120,200), width=3)
    cx=sum(p[0] for p in s['poly'])/len(s['poly']); cy=sum(p[1] for p in s['poly'])/len(s['poly'])
    dr.text(P2(cx,cy), f"{s.get('name','')}\n{s['id']}", font=FONT_S, fill=(30,60,140))
for r,c in polys:
    dr.rectangle([P2(r[0],r[1]),P2(r[2],r[3])], fill=c)
img.save(f'{OUT}/PASCAL_REVIEW_ZONE_MAP.png'); print('wrote zone map')
