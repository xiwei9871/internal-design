#!/usr/bin/env python3
"""PRE_3D_FURNITURE_DIMENSION_GATE — furniture 3D dimension register.

XY footprint stays from MASTER_V2 canonical (b1_model.json, mm).
Heights come from the B1 default table (user instruction) — NO furniture may
fall back to room/level/wall height. Missing heights -> TO_VERIFY, never a
full-height box.

base_z: lower zones 0, upper zones +350 (split level delta_mm from
b1_model.stairs). Wall-mounted candidates get base_z='TO_VERIFY'.

Outputs (design/b1_blockout/):
  furniture_3d_dimension_register_v01.json
  FURNITURE_3D_DIMENSION_REGISTER_V01.csv
  FURNITURE_3D_DIMENSION_REGISTER_V01.md
  FURNITURE_HEIGHT_ANOMALY_REPORT.md
"""
import json, csv

ROOT = '/Users/xiwei/interior_design/projects/c_type_home'
OUT = f'{ROOT}/design/b1_blockout'
M = json.load(open(f'{ROOT}/design/b1_blockout/b1_model.json'))

UPPER_DELTA = M['stairs']['delta_mm']           # 350
LEVEL_OF = {s['id']: s.get('level') for s in M['spaces']}
ZONE_NAME = {s['id']: s.get('name') for s in M['spaces']}

# label -> (semantic_type, height_mm, dimension_source, confidence, notes)
RULES = {
    '电视柜（或者悬浮电视墙）': ('MEDIA_CABINET', 480, 'STANDARD_BLOCKOUT', 'high',
                             'B1_REPRESENTATION=FLOOR_STANDING; FINAL_MEDIA_SOLUTION=TO_VERIFY; '
                             'FLOATING_MOUNT_Z=TO_VERIFY; DO NOT use room height'),
    '主卧电视柜': ('TV_CABINET', 480, 'STANDARD_BLOCKOUT', 'high', 'was stretched to ~level height — fixed'),
    '次主卧电视柜': ('TV_CABINET', 480, 'STANDARD_BLOCKOUT', 'high', 'was stretched to ~level height — fixed'),
    '三人位': ('SOFA_3S', 850, 'HUMAN_CONFIRMED', 'high', 'seat_height=430; compound: seat+back+arms envelope ok for B1'),
    '双人位': ('SOFA_2S', 850, 'HUMAN_CONFIRMED', 'high', 'seat_height=430'),
    '贵妃椅': ('CHAISE', 800, 'HUMAN_CONFIRMED', 'high', 'seat_height=430'),
    '茶几': ('COFFEE_TABLE', 400, 'HUMAN_CONFIRMED', 'high', ''),
    '角几': ('SIDE_TABLE', 500, 'HUMAN_CONFIRMED', 'high', 'Ø500 nominal'),
    '餐桌': ('DINING_TABLE', 750, 'HUMAN_CONFIRMED', 'high', '1600×800'),
    '餐椅': ('DINING_CHAIR', 850, 'HUMAN_CONFIRMED', 'high', 'seat_height=450'),
    '餐椅003': ('DINING_CHAIR', 850, 'HUMAN_CONFIRMED', 'high', 'seat_height=450'),
    '餐椅004': ('DINING_CHAIR', 850, 'HUMAN_CONFIRMED', 'high', 'seat_height=450'),
    '茶台': ('STUDY_WORKSTATION', 750, 'HUMAN_CONFIRMED', 'high', '2200×800 workstation/tea table — footprint human confirmed'),
    '窄书桌': ('NARROW_DESK', 750, 'HUMAN_CONFIRMED', 'high', '350×1650'),
    '主人椅': ('STUDY_ARMCHAIR', 850, 'STANDARD_BLOCKOUT', 'medium', 'OWNER_CHAIR; seat_height=430; do not classify as DINING_CHAIR'),
    '条凳': ('BENCH', 450, 'STANDARD_BLOCKOUT', 'medium', 'seat-height bench'),
    '凳子': ('STOOL', 450, 'STANDARD_BLOCKOUT', 'medium', ''),
    '次卧凳子': ('STOOL', 450, 'STANDARD_BLOCKOUT', 'medium', ''),
    '次主卧床': ('BED_BASE', 550, 'HUMAN_CONFIRMED', 'high', 'mattress/base envelope only; separate HEADBOARD block'),
    '主卧床': ('BED_BASE', 550, 'HUMAN_CONFIRMED', 'high', 'mattress/base envelope only; separate HEADBOARD block'),
    '次卧小床1.2': ('BED_BASE', 550, 'HUMAN_CONFIRMED', 'high', 'mattress/base envelope only; separate HEADBOARD block'),
    '次主卧床头占位': ('HEADBOARD', 1050, 'STANDARD_BLOCKOUT', 'medium', 'separate block behind bed'),
    '主卧床头柜占位': ('HEADBOARD', 1050, 'SOURCE_LABEL_SEMANTIC_CORRECTION', 'high',
                     'source_label kept for traceability; geometry is a backboard panel — never reclassify as nightstand'),
    '床背板': ('HEADBOARD', 1050, 'STANDARD_BLOCKOUT', 'medium', 'separate block behind study bed'),
    '主卧衣柜': ('WARDROBE', 2200, 'STANDARD_BLOCKOUT', 'high', ''),
    '次主卧衣柜': ('WARDROBE', 2200, 'STANDARD_BLOCKOUT', 'high', ''),
    '次卧衣柜': ('GUEST_WARDROBE', 2200, 'STANDARD_BLOCKOUT', 'high', 'depth 500 = HUMAN_CONFIRMED'),
    '书柜': ('TALL_BOOKCASE', 2000, 'HUMAN_CONFIRMED', 'high', ''),
    '矮书柜': ('LOW_BOOKCASE', 900, 'HUMAN_CONFIRMED', 'high', ''),
    '鞋柜': ('SHOE_CABINET', 1000, 'HUMAN_CONFIRMED', 'medium', ''),
    '客卫洗手盆柜体': ('VANITY', 850, 'HUMAN_CONFIRMED', 'high', 'countertop height'),
    '主卫洗手盆和柜体': ('VANITY', 850, 'HUMAN_CONFIRMED', 'high', 'countertop height'),
    '次主卫台盆和柜体': ('VANITY', 850, 'HUMAN_CONFIRMED', 'high', 'countertop height'),
    '客卫马桶': ('WC', 780, 'HUMAN_CONFIRMED', 'high', 'overall blockout height'),
    '主卫马桶': ('WC', 780, 'HUMAN_CONFIRMED', 'high', 'overall blockout height'),
    '次主卫马桶': ('WC', 780, 'HUMAN_CONFIRMED', 'high', 'overall blockout height'),
    '客卫（湿区）': ('SHOWER_ZONE', 2000, 'HUMAN_CONFIRMED', 'medium', 'not solid furniture — glass screen blockout only'),
    '主卫湿区': ('SHOWER_ZONE', 2000, 'HUMAN_CONFIRMED', 'medium', 'not solid furniture — glass screen blockout only'),
    '次主卫湿区': ('SHOWER_ZONE', 2000, 'HUMAN_CONFIRMED', 'medium', 'not solid furniture — glass screen blockout only'),
    '洗衣机+烘干机（叠放）': ('STACKED_WASHER_DRYER', 1700, 'HUMAN_CONFIRMED', 'high', 'two units stacked 850+850'),
    '3kg洗衣机': ('3KG_WASHER', 550, 'SKU_TO_VERIFY', 'low', 'wall-mounted candidate; physical body ~500–600; mount/base_z TO_VERIFY'),
    '冰柜': ('FREEZER', 850, 'SKU_TO_VERIFY', 'low', 'temporary B1 value; SKU TO_VERIFY'),
    '打印机': ('PRINTER', 300, 'STANDARD_BLOCKOUT', 'medium', 'generic blockout'),
    'nas': ('NAS', 400, 'STANDARD_BLOCKOUT', 'medium', 'generic blockout'),
    '现有橱柜': ('CABINET', 850, 'STANDARD_BLOCKOUT', 'medium', 'life-balcony counter'),
    '橱柜': ('CABINET', 850, 'STANDARD_BLOCKOUT', 'medium', 'life-balcony counter'),
}
WALL_MOUNTED = {'3KG_WASHER': True}

KITCHEN = {
    'K-RUN-E': ('BASE_CABINET', 900, 0, 'STANDARD_BLOCKOUT', 'east run; contains K-COOK/K-DISHW/K-BASKET'),
    'K-COOK': ('BASE_CABINET_MODULE', 900, 0, 'STANDARD_BLOCKOUT', 'nested in K-RUN-E — hob module'),
    'K-DISHW': ('BASE_CABINET_MODULE', 900, 0, 'STANDARD_BLOCKOUT', 'nested in K-RUN-E — dishwasher'),
    'K-BASKET': ('BASE_CABINET_MODULE', 900, 0, 'STANDARD_BLOCKOUT', 'nested in K-RUN-E — pull basket'),
    'K-RUN-S': ('BASE_CABINET', 900, 0, 'STANDARD_BLOCKOUT', 'south run; contains K-SINK'),
    'K-SINK': ('BASE_CABINET_MODULE', 900, 0, 'STANDARD_BLOCKOUT', 'nested in K-RUN-S — sink module'),
    'K-FRIDGE-TALL': ('TALL_CABINET', 2000, 0, 'STANDARD_BLOCKOUT', 'tall unit housing fridge cavity'),
    'K-FRIDGE': ('TALL_CABINET_MODULE', 2000, 0, 'ARCHITECTURAL_TO_VERIFY', 'nested cavity inside K-FRIDGE-TALL; exact appliance recess TO_VERIFY'),
    'K-WALL-E': ('WALL_CABINET', 700, 1400, 'STANDARD_BLOCKOUT', 'wall-hung cabinet; bottom z=1400, top=2100'),
}

rows = []
for f in M['furniture']:
    lab = f['label']
    w = f['rect'][2] - f['rect'][0]
    d = f['rect'][3] - f['rect'][1]
    zone = f.get('zone')
    level = LEVEL_OF.get(zone, 'lower')
    if lab not in RULES:
        sem, h, src, conf, note = lab.upper(), 'TO_VERIFY', 'SKU_TO_VERIFY', 'low', 'no rule matched'
    else:
        sem, h, src, conf, note = RULES[lab]
    base = 'TO_VERIFY' if WALL_MOUNTED.get(sem) else (UPPER_DELTA if level == 'upper' else 0)
    rows.append(dict(source_name=f.get('obj', ''), label=lab, semantic_type=sem,
                     room=f'{zone}/{ZONE_NAME.get(zone,"")}' if zone else '',
                     length=round(w), depth=round(d), height=h, base_z=base,
                     dimension_source=src, confidence=conf,
                     level=level, notes=note))
for kc in M.get('kitchen_cabinets', []):
    kid = kc['id']; r = kc['rect']
    sem, h, bz, src, note = KITCHEN.get(kid, ('CABINET', 'TO_VERIFY', 0, 'SKU_TO_VERIFY', ''))
    rows.append(dict(source_name=kid, label=kid, semantic_type=sem, room='R-KITCHEN/厨房',
                     length=round(r[2]-r[0]), depth=round(r[3]-r[1]), height=h,
                     base_z=bz, dimension_source=src, confidence='medium',
                     level='lower', notes=note))

json.dump({'register': 'FURNITURE_3D_DIMENSION_REGISTER_V01',
           'units': 'mm', 'upper_delta': UPPER_DELTA,
           'rule': 'no furniture may use floor/room/wall height as fallback',
           'items': rows}, open(f'{OUT}/furniture_3d_dimension_register_v01.json', 'w'),
          ensure_ascii=False, indent=1)

cols = ['source_name', 'label', 'semantic_type', 'room', 'length', 'depth',
        'height', 'base_z', 'dimension_source', 'confidence', 'notes']
with open(f'{OUT}/FURNITURE_3D_DIMENSION_REGISTER_V01.csv', 'w', newline='') as fp:
    w = csv.DictWriter(fp, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({c: r[c] for c in cols})

md = ['# FURNITURE_3D_DIMENSION_REGISTER_V01',
      '',
      'Gate: `PRE_3D_FURNITURE_DIMENSION_GATE`. Units mm. XY from MASTER_V2 '
      '(unchanged). Heights from the B1 default table — **no furniture may use '
      'floor/room/wall height as fallback**; missing -> TO_VERIFY.',
      '',
      f'Split level: `upper` zones sit +{UPPER_DELTA} (stairs.delta_mm). '
      'Wall-mounted candidates: `base_z = TO_VERIFY`.', '',
      'Category rules: real `NIGHTSTAND` (if one ever appears) = ~500 generic '
      'height — NEVER 2200; `STUDY_ARMCHAIR`/`OWNER_CHAIR` is not `DINING_CHAIR` '
      '(seat≈430, overall 850); `MEDIA_CABINET` B1 = floor-standing h480, '
      'floating treatment TO_VERIFY in B2.', '',
      '| label | type | L×D×H | base_z | source | notes |',
      '|---|---|---|---|---|---|']
for r in rows:
    md.append(f"| {r['label']} | {r['semantic_type']} | {r['length']}×{r['depth']}×{r['height']} "
              f"| {r['base_z']} | {r['dimension_source']} | {r['notes']} |")
open(f'{OUT}/FURNITURE_3D_DIMENSION_REGISTER_V01.md', 'w').write('\n'.join(md) + '\n')

# ---------- anomaly audit ----------
LOW_TYPES = {'TV_CABINET', 'MEDIA_CABINET', 'SOFA_3S', 'SOFA_2S', 'CHAISE',
             'COFFEE_TABLE', 'SIDE_TABLE', 'DINING_TABLE', 'DINING_CHAIR',
             'STUDY_ARMCHAIR', 'BENCH', 'STOOL', 'STUDY_WORKSTATION',
             'NARROW_DESK', 'VANITY', 'WC', 'BED_BASE', 'CABINET',
             'BASE_CABINET', 'BASE_CABINET_MODULE', 'SHOE_CABINET',
             'NIGHTSTAND', 'PRINTER', 'NAS', 'HEADBOARD', 'MAIN_WASHER',
             '3KG_WASHER', 'FREEZER'}
TALL_OK = {'WARDROBE', 'GUEST_WARDROBE', 'TALL_BOOKCASE', 'STACKED_WASHER_DRYER',
           'TALL_CABINET', 'TALL_CABINET_MODULE', 'SHOWER_ZONE'}
lines = ['# FURNITURE_HEIGHT_ANOMALY_REPORT', '',
         'Rule: height >= 1500 is FAIL for furniture-like categories; allowed '
         'only for wardrobe / tall bookcase / tall cabinet / stacked laundry / '
         'shower-glass zone.', '']
bad = []
for r in rows:
    h = r['height']
    if h == 'TO_VERIFY':
        bad.append(('TO_VERIFY', r, 'height unresolved'))
    elif isinstance(h, (int, float)) and h >= 1500 and r['semantic_type'] in LOW_TYPES:
        bad.append(('FAIL', r, f'height {h} >= 1500'))
    elif isinstance(h, (int, float)) and h >= 1500 and r['semantic_type'] not in TALL_OK:
        bad.append(('REVIEW', r, f'height {h} >= 1500 unlisted category'))
    if r['base_z'] == 'TO_VERIFY':
        bad.append(('TO_VERIFY', r, 'mount/base_z unresolved'))
    if isinstance(r['base_z'], (int, float)) and isinstance(h, (int, float)) \
            and r['base_z'] + h > 2600:
        bad.append(('REVIEW', r, f'base_z+height {r["base_z"] + h} approaches level height'))
if not bad:
    lines.append('No anomalies. All furniture heights within category limits.')
else:
    lines += ['| verdict | label | type | L×D×H | base_z | issue |', '|---|---|---|---|---|---|']
    for v, r, why in bad:
        lines.append(f"| {v} | {r['label']} | {r['semantic_type']} | "
                     f"{r['length']}×{r['depth']}×{r['height']} | {r['base_z']} | {why} |")
lines += ['', f'FAIL={sum(1 for v,_,_ in bad if v=="FAIL")}  '
          f'REVIEW={sum(1 for v,_,_ in bad if v=="REVIEW")}  '
          f'TO_VERIFY={sum(1 for v,_,_ in bad if v=="TO_VERIFY")}']
open(f'{OUT}/FURNITURE_HEIGHT_ANOMALY_REPORT.md', 'w').write('\n'.join(lines) + '\n')

print(f'rows {len(rows)} | anomalies {len(bad)} | '
      f'FAIL {sum(1 for v,_,_ in bad if v=="FAIL")}')
for v, r, why in bad:
    print(' ', v, r['label'], r['semantic_type'], why)
