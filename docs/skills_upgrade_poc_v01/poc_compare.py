#!/usr/bin/env python3
"""SKILLS_UPGRADE_POC_V01: old (render-pixel segmentation) vs new (real geometry) for A202 / A201.

Reference truth = design zones read from the model's own floor/ceiling meshes
(PRESENTATION_* floor zones, CEILING_LOWER/UPPER). Both methods are scored against it.
Usage: poc_compare.py EXTRACT_JSON OUT_DIR
  EXTRACT_JSON: output of extract_plan_geometry.py (extract mode) on the new model.
Old-method inputs are the tracked V15 artifacts (topmap.png, seg_meta.json, plan_geom.json,
A202/A201 DXFs) under projects/vray_eval_v1/v15_house/cad/.
"""
import hashlib, json, sys
from pathlib import Path

import ezdxf
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from skimage import measure

ROOT = Path(__file__).resolve().parents[2]
V15 = ROOT / 'projects/vray_eval_v1/v15_house/cad'
ext_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)
EXT = json.loads(ext_path.read_text())


def sha16(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def U(tris): return unary_union([Polygon(t[:3]) for t in tris if Polygon(t[:3]).area > 1])


def parts(g):
    return [] if g.is_empty else ([g] if g.geom_type == 'Polygon' else
                                  [p for p in g.geoms if p.geom_type == 'Polygon'])


# ---------- reference zones from model geometry ----------
# walls: A103 V7 (as-built base + approved changes); floor surfaces: model floor meshes.
A103 = ezdxf.readfile(V15 / 'A103_CONSTRUCTION_POC_V7.dxf').modelspace()
WALLS = unary_union([Polygon(list(e.get_points('xy'))) for e in A103.query('LWPOLYLINE')
                     if e.dxf.layer in ('A-WALL', 'A-DESIGN', 'A-REVIEW', 'A-CONFLICT', 'A-WINDOW')
                     and len(list(e.get_points('xy'))) >= 3]).buffer(0)
DOORS = [box(*Polygon(list(e.get_points('xy'))).bounds) for e in A103.query('LWPOLYLINE')
         if e.dxf.layer == 'A-DOOR']
F = EXT['floor']
floor_all = unary_union([U(F['FLOOR_LOWER']['tris']),
                         U(F['R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD']['tris'])] +
                        [U(v['tris']) for v in EXT['stair'].values()]).difference(WALLS)
REF = {}
for k, v in F.items():
    if not k.startswith('PRESENTATION_'): continue
    REF[k.split('_', 2)[2]] = {'geom': U(v['tris']).buffer(0).difference(WALLS),
                               'mat': 'TILE' if 'TILE' in v['mats'][0] else 'WOOD'}
named = unary_union([z['geom'] for z in REF.values()])
REF['living_dining_stair_rest'] = {'geom': floor_all.difference(named), 'mat': 'WOOD'}
ref_tile = unary_union([z['geom'] for z in REF.values() if z['mat'] == 'TILE'])
ref_wood = unary_union([z['geom'] for z in REF.values() if z['mat'] == 'WOOD'])
ref_all = unary_union([ref_tile, ref_wood])
# enclosed interior from walls+door openings: used to detect zones the model floors miss
_solid = unary_union([WALLS] + DOORS)
INTERIOR = _solid.buffer(3000).buffer(-3000).difference(_solid)


# ---------- OLD: replicate make_a202_v6 segmentation (steps 1-4) ----------
def old_segmentation():
    G = json.loads((V15 / 'plan_geom.json').read_text())
    meta = json.loads((V15 / 'seg_meta.json').read_text())
    img = np.asarray(Image.open(V15 / 'topmap.png').convert('RGB')).astype(int)
    R, Gc, B = img[..., 0], img[..., 1], img[..., 2]
    wood_px = (R > 120) & (R > Gc + 40) & (R > B + 40)
    tile_px = (Gc > 120) & (Gc > R + 40) & (Gc > B + 40)
    wall_px = (B > 120) & (B > R + 40) & (B > Gc + 40)
    SPAN, CX, CY, W, H = meta['span'], meta['cx'] * 1000, meta['cy'] * 1000, meta['W'], meta['H']
    MM = SPAN * 1000 / W
    px2mm = lambda x, y: ((x - W / 2) * MM + CX, (H / 2 - y) * MM + CY)
    mm2px = lambda xm, ym: ((xm - CX) / MM + W / 2, H / 2 - (ym - CY) / MM)
    ps = [box(*it['bbox'][:4]) for it in G['items']['wall'] + G['items']['window']
          if it['bbox'][2] - it['bbox'][0] > 30 and it['bbox'][3] - it['bbox'][1] > 30]
    shell = unary_union(ps)
    buff = unary_union([p.buffer(500) for p in parts(shell)])
    envelope = unary_union([Polygon(p.exterior) for p in parts(buff)]).buffer(-500)
    im = Image.new('1', (W, H), 0); dr = ImageDraw.Draw(im)
    for p in parts(envelope):
        dr.polygon([mm2px(x, y) for x, y in p.exterior.coords], fill=1, outline=1)
        for r in p.interiors: dr.polygon([mm2px(x, y) for x, y in r.coords], fill=0, outline=0)
    env_px = np.asarray(im, dtype=bool)
    wall_px = ndimage.binary_dilation(wall_px, iterations=1)
    interior = ndimage.binary_closing(ndimage.binary_opening(env_px & ~wall_px, iterations=1), iterations=2)
    known = (wood_px | tile_px) & interior
    other = interior & ~known
    _, idx = ndimage.distance_transform_edt(other, return_indices=True)
    lab = np.where(wood_px, 'W', 'X'); lab = np.where(tile_px, 'T', lab)
    mat = np.full(lab.shape, 'O', dtype='<U1')
    mat[interior] = lab[interior]; mat[other] = lab[idx[0][other], idx[1][other]]
    for x0, y0, x1, y1 in [(5900, 0, 7900, 4600), (7900, 10900, 12950, 13450)]:   # hard-coded intent
        px0, py0 = mm2px(x0, y1); px1, py1 = mm2px(x1, y0)
        m = np.zeros(mat.shape, dtype=bool); m[int(py0):int(py1), int(px0):int(px1)] = True
        mat[interior & m] = 'T'
    res = {}
    for key, ch in (('WOOD', 'W'), ('TILE', 'T')):
        msk = interior & (mat == ch)
        l, n = ndimage.label(msk); sz = np.bincount(l.ravel())
        msk[np.isin(l, np.where((sz > 0) & (sz < 300))[0])] = False
        polys = []
        for c in measure.find_contours(msk.astype(float), 0.5):
            if len(c) < 6: continue
            p = Polygon([px2mm(x, y) for y, x in c])
            if p.is_valid and p.area / 1e6 > 0.3: polys.append(p.simplify(150, preserve_topology=True))
        res[key] = unary_union([p.buffer(0) for p in polys])
    return res, {'mm_per_px': round(MM, 2), 'hardcoded_intent_boxes': 2,
                 'inputs': {n: sha16(V15 / n) for n in ('topmap.png', 'seg_meta.json', 'plan_geom.json')}}


# ---------- NEW: zones straight from geometry ----------
def new_geometry():
    return {'WOOD': ref_wood, 'TILE': ref_tile}


def score(zones, label):
    rows = {}
    for mat, ref in (('WOOD', ref_wood), ('TILE', ref_tile)):
        g = zones[mat]
        inter = g.intersection(ref).area
        rows[mat] = {'area_m2': round(g.area / 1e6, 2), 'ref_m2': round(ref.area / 1e6, 2),
                     'iou': round(inter / max(g.union(ref).area, 1), 4),
                     'missed_m2': round(ref.difference(g).area / 1e6, 2),
                     'spill_outside_ref_m2': round(g.difference(ref).area / 1e6, 2),
                     'vertices': sum(len(p.exterior.coords) for p in parts(g)),
                     'hausdorff_mm': round(g.hausdorff_distance(ref)) if not g.is_empty else None}
    cross = zones['WOOD'].intersection(ref_tile).area + zones['TILE'].intersection(ref_wood).area
    rows['wrong_material_m2'] = round(cross / 1e6, 2)
    per_room = {}
    for k, z in REF.items():
        g = zones[z['mat']]
        per_room[k] = round(g.intersection(z['geom']).area / max(z['geom'].area, 1), 3)
    rows['per_room_coverage'] = per_room
    allz = unary_union([zones['WOOD'], zones['TILE']])
    rows['geometry_only'] = {   # material-agnostic: isolates method error from model material changes
        'iou': round(allz.intersection(ref_all).area / max(allz.union(ref_all).area, 1), 4),
        'missed_m2': round(ref_all.difference(allz).area / 1e6, 2),
        'spill_m2': round(allz.difference(ref_all).area / 1e6, 2),
        'hausdorff_mm': round(allz.hausdorff_distance(ref_all))}
    rows['rooms_below_95pct'] = sorted(k for k, v in per_room.items() if v < 0.95)
    return rows


old, old_meta = old_segmentation()
old2, _ = old_segmentation()
new = new_geometry()
rep = {'reference': {'source': ext_path.name, 'extract_sha16': sha16(ext_path),
                     'blend': EXT.get('blend'), 'zones': len(REF)},
       'A202_old_pixel_segmentation': {**score(old, 'old'), 'meta': old_meta,
           'repeat_identical': old['WOOD'].equals(old2['WOOD']) and old['TILE'].equals(old2['TILE'])},
       'A202_new_real_geometry': score(new, 'new')}

# ---------- A201: old DXF ceiling zones vs model ceilings ----------
lo = U(EXT['ceiling']['CEILING_LOWER']['tris']); hi = U(EXT['ceiling']['CEILING_UPPER']['tris'])
d = ezdxf.readfile(V15 / 'A201_天花布置图.dxf'); m = d.modelspace()
old_ceil = [Polygon(list(e.get_points('xy'))) for e in m.query('LWPOLYLINE') if e.dxf.layer == 'A-CEIL']
old_txt = [t.dxf.text for t in m.query('TEXT')]
elev = sorted({t for t in old_txt if t.startswith('H=')})
step_x = sorted({round(c[0]) for s in parts(lo.intersection(hi.buffer(10)).buffer(0)) for c in s.exterior.coords})
shared = lo.boundary.intersection(hi.boundary.buffer(5))
rep['A201_old_dxf'] = {'ceiling_polys': len(old_ceil),
                       'elevation_labels': elev,
                       'distinguishes_2800_vs_3250': any('2800' in e or '2650' in e for e in elev)
                       and any('3250' in e or '3100' in e for e in elev),
                       'has_step_line_layer': 'A-CEIL-STEP' in d.layers,
                       'covered_low_m2': round(unary_union(old_ceil).intersection(lo).area / 1e6, 2),
                       'covered_high_m2': round(unary_union(old_ceil).intersection(hi).area / 1e6, 2)}
rep['A201_new_real_geometry'] = {'low_zone_m2': round(lo.area / 1e6, 2), 'low_soffit_z': 2800,
                                 'high_zone_m2': round(hi.area / 1e6, 2), 'high_soffit_z': 3250,
                                 'shared_boundary_len_mm': round(shared.length),
                                 'finished_ceiling_after_150_drop': {'low': 2650, 'high': 3100}}
sys.path.insert(0, str(ROOT / '.codex/skills/interior-renovation-cad-docs/scripts'))
import zone_qa
zq = zone_qa.run({'zones': [{'id': k, 'polygon': list(p.exterior.coords),
                              'holes': [list(h.coords) for h in p.interiors]}
                             for k, z in REF.items() for i, p in enumerate(parts(z['geom']))
                             if p.area > 1e4],
                  'interior': [list(p.exterior.coords) for p in parts(INTERIOR) if p.area > 0.5e6]},
                 overlap_tol_m2=0.01, gap_tol_m2=0.3)
rep['A202_new_zone_qa'] = {k: zq[k] for k in ('overlaps', 'gaps', 'invalid', 'result', 'total_m2')}
(out_dir / 'poc_metrics.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep, ensure_ascii=False, indent=1))
