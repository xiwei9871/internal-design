#!/usr/bin/env python3
"""Task03A concept plan builder.
Coords = task01 mm system. Produces:
  concept/task03a_preferred_plan.dxf
  concept/option_smb_entry_W.dxf / option_smb_entry_S.dxf
  concept/split_level_study.dxf
  qc/*.png renders
All design data also dumped to concept/concept_data.json for QC/tests.
"""
import ezdxf, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M = json.load(open(ROOT / 'current_existing' / 'current_existing_v1.json'))

LAYERS = {'A-WALL-EXST-KEEP': 7, 'A-WALL-OWNER-NOOPEN': 1, 'A-WALL-EXST-REMOVE': 8,
          'A-WALL-NEW': 5, 'A-DOOR-EXST-KEEP': 3, 'A-DOOR-NEW': 4,
          'A-GLAZ-EXST-KEEP': 6, 'A-FURN-EXST-KEEP': 30, 'A-FURN-PROP': 2,
          'A-FIXT-PLUMB': 4, 'A-ACCESS-RAMP': 3, 'A-ACCESS-STAIR': 3,
          'A-LEVEL': 140, 'A-DIMS': 8, 'A-NOTE': 7, 'A-QC': 1}

def new_doc():
    d = ezdxf.new('R2010', setup=True)
    d.header['$INSUNITS'] = 4
    for n, c in LAYERS.items():
        if n not in d.layers: d.layers.add(n, color=c)
    return d

def rect(msp, lay, x1, y1, x2, y2):
    msp.add_lwpolyline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)],
                       dxfattribs={'layer': lay}, close=True)

def label(msp, txt, x, y, h=160, lay='A-NOTE', rot=0):
    msp.add_text(txt, height=h, dxfattribs={'layer': lay, 'rotation': rot}).set_placement((x, y))

def walls(msp):
    for w in M['walls']:
        cls = w['wall_class']
        if w['disposition'] == 'EXISTING':
            if 'NO_DEMOLITION' in cls or 'NO_OPEN' in cls:
                lay = 'A-WALL-OWNER-NOOPEN'
            elif 'REVIEW' in cls:
                lay = 'A-QC'
            else:
                lay = 'A-WALL-EXST-KEEP'
        else:
            lay = 'A-WALL-EXST-REMOVE'
        rect(msp, lay, *w['rect_mm'])

# ================================================================ CONCEPT DATA
CD = {}

# ---- split level: platform reduction
# stair (task01): x7200-7800, y6600-7800, 2 treads, climb +x.  rise ~400 TO_VERIFY
# retained upper landing/foyer: corridor x7800-13000 y6300-7800 already,
#   plus south arm x7800-9100 y4650-6300 (path to SMB door x8332 + bath-W door x9050)
# returned to lower level: x5900-7200 y4650-7800 strip (west of stair/landing)
CD['level'] = {
 'lower_zone_note': 'living+dining+kitchen+balconies at L1(+-0)',
 'upper_zone_note': 'bedroom wing + corridor + retained landing at L2 (delta TO_VERIFY)',
 'delta_status': 'LEVEL_DELTA_TO_VERIFY — owner <=350 vs CAD ~400; all slope/platform/living numbers PROVISIONAL',
 'stair_mm': [7200, 6600, 7800, 7800],
 'landing_kept_mm': [[7800, 4650, 9100, 6300], [7800, 6300, 13000, 7800]],
 'returned_to_L1_mm': [5900, 4650, 7200, 7800],
 'ramp': {'note': 'ASSISTED_WHEELCHAIR_FUTURE_PROVISION not code-compliant; PROVISIONAL pending level measure',
          'run_mm': 3000, 'width_mm': 1100,
          'slope': '1:7.5 @400mm / 1:8.6 @350mm — PROVISIONAL',
          'rect_mm': [4150, 5600, 7150, 6700],
          'topology': 'climbs +x along south edge of returned strip (kitchen side); '
                      'top lands on former-niche open passage x7150-7800 y4650-6600 -> upper landing'},
}

# ---- new walls (concept)
# Secondary master bath in former cloakroom x9050-11300 y4650-6300 (task01).
# RC1 truth: CLK walls demolished; Y4500-b cloakroom segment open/absent in
# measured DWG (only 600mm stub at x10800-11400) -> the zone is continuous
# with the secondary master. BOTH entries place doors in NEW partition walls.
SMB = {'x1': 9050, 'y1': 4650, 'x2': 11300, 'y2': 6300}
CD['smb'] = {
 'zone_mm': [SMB['x1'], SMB['y1'], SMB['x2'], SMB['y2']],
 'area_m2': round((SMB['x2']-SMB['x1'])*(SMB['y2']-SMB['y1'])/1e6, 2),
 'site_truth': 'RC1.5 owner correction: cloakroom N/W/E walls RETAINED (white-class); '
               'south side OPEN to bedroom (Y4500-b-CLKSEG absent, only 600mm stub x10800-11400 drawn — TO_VERIFY). '
               'Bath = existing shell + NEW south partition (wall or frosted glass) + interior wet/dry glass. No demolition.',
 'entry_S': {'door_rect': [9500, 4550, 10300, 4650], 'swing': 'into bath; door leaf in NEW south partition',
             'pros': 'zero existing-wall cutting; uses the open south edge; direct en-suite from bedroom',
             'cons': 'door axis faces bed zone (owner prefers not) — mitigate: place door at west end '
                     'x9050-9550 or use frosted-glass partition; residual stub x10800-11400 TO_VERIFY',
             'verdict': 'FEASIBLE — recommended (least intervention)'},
 'entry_W': {'door_rect': [9050, 5200, 9050, 5950], 'swing': 'into foyer',
             'foyer_mm': [7800, 4650, 9050, 6300],
             'pros': 'private suite vestibule; door does NOT face bed',
             'cons': 'requires NEW OPENING in existing CLK-W — white-class wall under owner-declared '
                     'no-opening rule; needs explicit owner exception + structural check',
             'verdict': 'CONSTRAINED — feasible only with owner rule exception'},
 'entry_N': {'door_rect': 'existing cloakroom door on CLK-N (D-CLK, leaf TO_VERIFY)',
             'pros': 'reuse existing opening; zero work',
             'cons': 'opens to shared corridor, not en-suite',
             'verdict': 'FALLBACK'},
 'comparison': 'S recommended (all-new partition, no existing wall touched). '
               'W only if owner grants exception to open CLK-W. N = zero-cost fallback.',
 'fixtures': {'shower': [10300, 4650, 11300, 5850],   # ~1000x1200 against east (master-bath wet) wall
              'vanity': [9050, 4650, 9850, 5250],
              'wc':     [9850, 4650, 10300, 5250]},
 'drain_note': 'east wall shared with MASTER_BATH wet zone — primary drain/vent candidate, TO_VERIFY',
}

# ---- furniture (task01 coords). [x1,y1,x2,y2]
F = []
def furn(id_, x1, y1, x2, y2, lay='A-FURN-PROP', note=''):
    F.append({'id': id_, 'rect': [x1, y1, x2, y2], 'layer': lay, 'note': note})

# LIVING (x2900-7750 y7900-12750 + annex x5900-7200 y4650-7800 lowered)
# viewing axis W->E: screen on east wall; sofas face east/north, central zone kept open
furn('SOFA-3', 2900, 9500, 3800, 11700, note='3-seat on west wall, faces east screen')
furn('SOFA-2', 4600, 7900, 6300, 8800, note='2-seat south, faces north')
furn('LOUNGE-1', 3300, 12000, 4100, 12700, note='lounge chair NW')
furn('COFFEE-MOV', 5000, 9800, 5800, 10400, note='small movable round-corner table')
furn('PROJ-SCREEN', 7200, 9800, 7750, 12200, lay='A-NOTE', note='projection/laser-TV relation on east wall (no fixed cabinet)')
# DINING (x2900-5700 y2560-7900): table 1500x600 near kitchen side
furn('DIN-TABLE', 3700, 4800, 5200, 5400, note='1500x600 table, seats <=8 peak')
# KITCHEN: existing cabinets KEEP (from model keep_items K-CABINETS task01 x5500-8200 y0-4700)
furn('K-CAB', *M['keep_items'][0]['rect_mm'], lay='A-FURN-EXST-KEEP', note='2024 cabinets KEEP')
# MASTER BEDROOM x11600-15300 y0-4450: bed head south wall
furn('MB-BED', 12600, 300, 14400, 2400, note='1800x2100; route door->bed->bath clear')
furn('MB-WARD', 11600, 3850, 15300, 4450, lay='A-FURN-EXST-KEEP', note='existing wardrobe KEEP')
# SECONDARY MASTER x8030-11400 y0-4450: bed head south
furn('SMB-BED', 8800, 300, 10600, 2400, note='1800x2100')
furn('SMB-WARD', 10800, 3700, 11400, 4450, note='new wardrobe restoring lost cloakroom capacity')
# STUDY (R-BED-N x13100-16300 y6500-11350): desk on south wall facing north, east window = side light
furn('ST-DESK', 13800, 6500, 15500, 7300, note='1700x800 desk on south wall; east window side-lit')
furn('ST-DAYBED', 15000, 9500, 16000, 11300, note='daybed backup sleep')
furn('ST-BOOK', 15500, 8500, 16300, 10500, lay='A-FURN-EXST-KEEP', note='existing wardrobe->book/file/equip')
furn('ST-NAS', 13100, 6500, 13800, 7100, note='NAS/printer shelf, ventilated')
# GUEST BEDROOM (R-STUDY x9850-12900 y8000-10700): bunk along west wall, glass door north clear
furn('GB-BUNK', 9850, 8300, 9850+1500, 8300+2100, note='lower 1500 + optional upper 900-1000 bunk')
furn('GB-DESK', 12100, 8000, 12900, 8450, note='narrow desk 800x450 (entry side)')
furn('GB-GLASSDOOR-ZONE', 10500, 10400, 13000, 10700, lay='A-NOTE', note='KEEP CLEAR: double glass door to balcony')
furn('GB-BALC-STEP', 10500, 10700, 13000, 10900, lay='A-LEVEL', note='level transition at glass door: guest bed upper -> balcony lower, 2 risers TO_VERIFY')
# NORTH BALCONY x7900-13000 y10900-13400
furn('NB-WD', 7900, 13064, 8600, 13764, lay='A-FURN-EXST-KEEP', note='10kg W+D stacked, west end')
furn('NB-PLANTS', 7900, 13100, 13000, 13400, lay='A-NOTE', note='plant line along glazing')
furn('NB-TEA', 11000, 11800, 11800, 12400, note='light movable tea set')
# ENTRY (west wall x2700-2900, y~4500-5500 zone / door at y5440-6540)
furn('SHOE-CAB', 2900, 4600, 3400, 5600, lay='A-FURN-EXST-KEEP', note='existing low shoe cabinet')
furn('BENCH', 2900, 6800, 3400, 7200, note='shoe bench opposite door side')
# GUEST BATH x7900-9650 y8000-10700: front-dry(S)/rear-wet(N)
furn('GBATH-VANITY', 7900, 8000, 8600, 8600, lay='A-FIXT-PLUMB', note='dry zone vanity')
furn('GBATH-WC', 8700, 8000, 9400, 8600, lay='A-FIXT-PLUMB', note='smart toilet')
furn('GBATH-SHOWER', 7900, 9800, 9650, 10700, lay='A-FIXT-PLUMB', note='wet zone shower')
furn('GBATH-3KG', 9000, 9200, 9600, 9800, lay='A-FIXT-PLUMB', note='3kg washer, wet-service band, out of spray')
# MASTER BATH x13100-16300 y4650-6300: tub removed; west door enters dry zone;
# shower = north strip 2200x800 walk-in, WC SE, vanity NE, radiator south
furn('MBATH-SHOWER', 13100, 5500, 15300, 6300, lay='A-FIXT-PLUMB', note='walk-in shower 2200x800+, zero-threshold target, fold seat+grab bars')
furn('MBATH-WC', 15200, 4650, 16000, 5300, lay='A-FIXT-PLUMB', note='smart toilet SE')
furn('MBATH-VANITY', 15400, 5500, 16300, 6300, lay='A-FIXT-PLUMB', note='single vanity+storage NE')
furn('MBATH-RAD', 13600, 4650, 14200, 4900, lay='A-FIXT-PLUMB', note='radiator keep')
# SECONDARY MASTER BATH (Option W)
furn('SMB2-SHOWER', 10300, 4650, 11300, 5850, lay='A-FIXT-PLUMB', note='~1000x1200 shower, wet side vs master bath wall')
furn('SMB2-WC', 9550, 4650, 10300, 5250, lay='A-FIXT-PLUMB')
furn('SMB2-VANITY', 9050, 4650, 9550, 5250, lay='A-FIXT-PLUMB', note='single vanity')
# RAMP (kitchen-side of platform edge, in lowered strip)
furn('RAMP', *CD['level']['ramp']['rect_mm'], lay='A-ACCESS-RAMP',
     note='ramp 3000 run, slope 1:7.5-1:8.6 PROVISIONAL, ASSISTED WHEELCHAIR FUTURE PROVISION')
# STAIR
furn('STAIR', *CD['level']['stair_mm'], lay='A-ACCESS-STAIR', note='2 risers, delta LEVEL_TO_VERIFY (<=350 owner / ~400 CAD)')
CD['furniture'] = F

# ================================================================ emit main DXF
doc = new_doc(); msp = doc.modelspace()
walls(msp)
# openings
for o in M['openings']:
    lay = {'sliding_glass_3track': 'A-GLAZ-EXST-KEEP', 'glazing_door_double': 'A-GLAZ-EXST-KEEP',
           'open_passage': 'A-NOTE'}.get(o['kind'], 'A-DOOR-EXST-KEEP')
    rect(msp, lay, *o['rect_mm'])
# new bath enclosure: cloakroom shell N/W/E kept (drawn by walls());
# NEW south partition along open edge y4550-4650 with door x9500-10300;
# interior wet/dry glass partition optional (marked A-NOTE)
x1, y1, x2, y2 = SMB['x1'], SMB['y1'], SMB['x2'], SMB['y2']
rect(msp, 'A-WALL-NEW', x1, 4550, 9500, 4650)            # new south wall west part
rect(msp, 'A-WALL-NEW', 10300, 4550, x2, 4650)           # new south wall east part
rect(msp, 'A-DOOR-NEW', 9500, 4550, 10300, 4650)         # S door leaf zone
label(msp, 'SEC-MASTER-BATH S-door in NEW partition', x1 - 200, 4350, 130)
# residual stub marker
rect(msp, 'A-QC', 10800, 4450, 11400, 4550)
label(msp, 'stub TO_VERIFY', 10800, 4300, 120)
# landing edge: new level boundary line along x7800 + stair
rect(msp, 'A-LEVEL', 7800, 4650, 7900, 7800)
label(msp, 'L2 upper (delta LEVEL_TO_VERIFY)', 7950, 7600, 140)
label(msp, 'L1 +-0 returned to living', 5950, 7000, 140)
# ramp (E-W along kitchen side, climbs +x onto open passage -> landing)
rr = CD['level']['ramp']['rect_mm']
rect(msp, 'A-ACCESS-RAMP', *rr)
for i in range(11):
    x = rr[0] + (rr[2] - rr[0]) * i / 10
    msp.add_line((x, rr[1]), (x, rr[3]), dxfattribs={'layer': 'A-ACCESS-RAMP'})
label(msp, 'RAMP 3000 run, slope 1:7.5-8.6 PROVISIONAL assisted-use', rr[0], rr[3] + 120, 130)
# stair
rect(msp, 'A-ACCESS-STAIR', *CD['level']['stair_mm'])
sx = CD['level']['stair_mm']
for i in range(3):
    x = sx[0] + (sx[2] - sx[0]) * i / 2
    msp.add_line((x, sx[1]), (x, sx[3]), dxfattribs={'layer': 'A-ACCESS-STAIR'})
label(msp, '2 RISERS (delta TO_VERIFY)', sx[0], sx[3] + 120, 130)
# furniture + labels
for f in F:
    rect(msp, f['layer'], *f['rect'])
    cx = (f['rect'][0] + f['rect'][2]) / 2; cy = (f['rect'][1] + f['rect'][3]) / 2
    label(msp, f['id'], cx - 300, cy, 130)
# room labels
ROOMS = [('FLEX FAMILY ROOM 客厅', 4200, 10600), ('DINING 餐厅', 3700, 6600),
         ('KITCHEN 厨房', 6200, 2500), ('LIFE BALC 生活阳台', 2600, 1500),
         ('MASTER BED 主卧', 12500, 2800), ('SEC MASTER BED 次主卧', 9000, 2800),
         ('SEC MASTER BATH 次主卫', 9200, 5600), ('MASTER BATH 主卫', 14200, 5500),
         ('STUDY 书房', 14000, 10000), ('GUEST BED 客卧', 10600, 9300),
         ('GUEST BATH 客卫', 8200, 9600), ('N BALCONY 北阳台', 9800, 12200),
         ('LANDING/FOYER 平台', 8000, 6800)]
for t, x, y in ROOMS:
    label(msp, t, x, y, 200)
doc.saveas(str(ROOT / 'concept' / 'task03a_preferred_plan.dxf'))

# ================================================================ option compare DXF
for opt in ('S', 'W'):
    d = new_doc(); m = d.modelspace(); walls(m)
    if opt == 'S':
        # RC1.5: cloakroom shell kept; south edge open -> NEW partition w/ door
        rect(m, 'A-WALL-NEW', x1, 4550, 9500, 4650)
        rect(m, 'A-WALL-NEW', 10300, 4550, x2, 4650)
        rect(m, 'A-DOOR-NEW', 9500, 4550, 10300, 4650)
        rect(m, 'A-QC', 10800, 4450, 11400, 4550)                     # residual stub TO_VERIFY
        label(m, 'OPTION S: NEW south partition + door, zero demolition (RECOMMENDED)', 7000, 4300, 180)
        label(m, 'residual stub x10800-11400 TO_VERIFY', 10400, 4200, 130)
    else:
        # W needs a NEW OPENING cut in existing CLK-W (white-class) — owner exception
        rect(m, 'A-QC', 8950, 5200, 9050, 5950)                       # proposed cut zone
        label(m, 'OPTION W: opening cut in EXISTING CLK-W (white-class) — needs owner exception', 7000, 4300, 170)
        label(m, 'CLK-W retained wall — cut zone marked', 7000, 4600, 150)
    for f in F:
        if 'SMB2' in f['id'] or 'SMB-' in f['id']:
            rect(m, f['layer'], *f['rect'])
            label(m, f['id'], f['rect'][0], f['rect'][1] - 150, 120)
    d.saveas(str(ROOT / 'concept' / f'option_smb_entry_{opt}.dxf'))

# ================================================================ split level study DXF
d = new_doc(); m = d.modelspace(); walls(m)
rect(m, 'A-ACCESS-STAIR', *CD['level']['stair_mm'])
rect(m, 'A-ACCESS-RAMP', *CD['level']['ramp']['rect_mm'])
for r in CD['level']['landing_kept_mm']: rect(m, 'A-LEVEL', *r)
rect(m, 'A-LEVEL', *CD['level']['returned_to_L1_mm'])
label(m, 'KEPT UPPER LANDING + FOYER', 8000, 6600, 180)
label(m, 'RETURNED TO L1 (lowered to living level)', 5950, 7300, 160)
label(m, 'STAIR 2 risers (delta LEVEL_TO_VERIFY)', 6300, 7900, 160)
label(m, 'RAMP study 3000x1100 slope 1:7.5-1:8.6 PROVISIONAL', 5900, 4800, 160)
d.saveas(str(ROOT / 'concept' / 'split_level_study.dxf'))

json.dump(CD, open(ROOT / 'concept' / 'concept_data.json', 'w'), ensure_ascii=False, indent=1)
print('concept dxf + options + study written; furniture:', len(F))
