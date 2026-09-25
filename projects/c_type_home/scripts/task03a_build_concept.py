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
          'A-WIND-EXST-KEEP': 4, 'A-WIND-TO-VERIFY': 6, 'A-GLAZ-PROP': 5,
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
 # RC2 E: honest net-area account — ramp footprint eats most of the returned area;
 # the real gain is regularising the living rectangle, not net floor area.
 'area_comparison': {
   'returned_platform_m2': round((7200-5900)*(7800-4650)/1e6, 2),          # 4.09
   'ramp_footprint_m2': round(3000*1100/1e6, 2),                           # 3.30
   'net_unobstructed_public_gain_m2': round((7200-5900)*(7800-4650)/1e6 - 3000*1100/1e6, 2),  # +0.79
   'living_largest_clear_rect': '4850x4850 (23.5m2) + returned annex — PROVISIONAL',
   'primary_circulation_mm': '>=1100 (ramp doubles as future step-free route)',
   'verdict': 'net floor gain modest (+0.79m2); value = rectangular living room + '
              'future assisted-wheelchair provision — PROVISIONAL until level delta measured'},
}

# ---- new walls (concept)
# Secondary master bath = retained cloakroom shell x9050-11300 y4650-6300
# (N/W/E walls EXISTING per owner image markup + DWG) + south annex pushed
# into the bedroom to reach owner target ~5.0m2 (RC2).
#   main  zone x9050-11300 y4650-6300  = 3.71 m2
#   connector x9050-10800 y4450-4650   = 0.35 m2 (demolished wall strip, open)
#   annex x9050-10700 y3900-4450       = 0.94 m2 (new south partition at y3800-3900)
#   total interior ~5.0 m2
# Annex east edge x10800 stops flush with the retained stub + SMB-WARD west face —
# full-width push rejected to keep the only viable wardrobe wall.
SMB = {'x1': 9050, 'y1': 4650, 'x2': 11300, 'y2': 6300}
ANNEX = [9050, 3900, 10700, 4450]          # interior of annexed bedroom strip
NEW_WALLS = [                              # rect + id
 ([8950, 3800, 9100, 3900], 'NW-SMB-S1'),   # south partition west of door
 ([9850, 3800, 10800, 3900], 'NW-SMB-S2'),  # south partition east of door
 ([8950, 3900, 9050, 4500], 'NW-SMB-W'),    # annex west wall -> meets CLK-W
 ([10700, 3900, 10800, 4450], 'NW-SMB-E'),  # annex east wall -> meets stub
]
NEW_DOORS = [([9100, 3800, 9850, 3900], 'D-SMB2-S')]  # S entry leaf 750, hinge east
CD['new_walls'] = [r for r, _ in NEW_WALLS]
CD['new_doors'] = [r for r, _ in NEW_DOORS]
CD['smb'] = {
 'zone_mm': [SMB['x1'], SMB['y1'], SMB['x2'], SMB['y2']],
 'annex_mm': ANNEX,
 'area_m2': 5.0,
 'area_breakdown': 'main 2250x1650=3.71 + connector 1750x200=0.35 + annex 1700x550=0.94 = ~5.0 m2',
 'site_truth': 'cloakroom N/W/E walls EXISTING (owner image markup + DWG drawn — consistent); '
               'south side OPEN to bedroom (Y4500-b-CLKSEG absent, only 600mm stub x10800-11400 — TO_VERIFY). '
               'Bath = shell + L-annex into bedroom + NEW south partition (wall or frosted glass). No demolition.',
 'entry_S': {'door_rect': [9100, 3800, 9850, 3900],
             'swing': 'hinge east @x9850, leaf 750, swings INTO bath annex; swing zone x9100-9850 y3900-4650 kept fixture-free',
             'pros': 'zero existing-wall cutting; 750 door at west end of new partition; meets ~5m2 owner target',
             'cons': 'annex bites 1700x550 of bedroom; door axis still roughly toward bed — mitigate with frosted glass partition; residual stub x10800-11400 TO_VERIFY',
             'verdict': 'FEASIBLE — recommended (least intervention, owner target ~5m2 met)'},
 'entry_W': {'door_rect': [8950, 4700, 9050, 5400],
             'swing': 'SLIDING door leaf (owner suggestion — saves swing space)',
             'foyer_mm': [7800, 4650, 9050, 6300],
             'pros': 'private suite vestibule; door does NOT face bed',
             'cons': 'requires NEW OPENING in retained CLK-W — white-class under owner-declared '
                     'no-opening rule; needs explicit owner exception + structural check',
             'verdict': 'CONSTRAINED — feasible only with owner rule exception (sliding leaf)'},
 'entry_N': {'door_rect': 'existing cloakroom door on CLK-N (D-CLK, leaf TO_VERIFY)',
             'pros': 'reuse existing opening; zero work',
             'cons': 'opens to shared corridor, not en-suite',
             'verdict': 'FALLBACK'},
 'comparison': 'S recommended (new partition only). W = sliding door, but requires owner exception '
               'to open retained white-class CLK-W. N = zero-cost fallback.',
 # RC2.1 throat closure: WC 650 / aisle 800 / shower 800 — main path 800mm continuous
 'fixtures': {'shower': [10500, 4650, 11300, 6300],   # 800x1650 east column (shared master-bath wet wall)
              'wc':     [9050, 5500, 9700, 6300],     # 650x800 NW corner
              'vanity': [9850, 3900, 10500, 4450]},   # 700x550 in annex east
 'shower_glass': {'panel': [10450, 5400, 10500, 6300],
                  'opening': '750mm clear entry on west face, y4650-5400'},
 'clearances': {'door_swing':   [9100, 3900, 9850, 4650],
                'wc_front':     [9050, 4700, 9700, 5500],
                'vanity_front': [9850, 4450, 10500, 4900],
                'shower_entry': [9700, 4650, 10500, 5400],
                'main_aisle':   [9700, 4650, 10500, 6300]},   # 800mm continuous
 'drain_note': 'east wall shared with MASTER_BATH wet zone — primary drain/vent candidate, TO_VERIFY',
}

# guest bedroom continuous path entry -> balcony glass door (RC2.1):
# door leaf re-hung OUTWARD or surface sliding on existing opening -> interior
# freed for portrait bunk on west wall; east lane >=800 continuous to glass zone
CD['guest_path'] = [
 [10900, 8000, 12200, 8300],   # entry strip below bunk/desk line
 [11400, 8300, 12200, 8450],   # pinch between bunk east face and desk
 [11400, 8450, 12900, 10400],  # open east lane
 [10500, 10400, 13000, 10700], # balcony glass-door zone
]

# door swing envelopes (conservative squares, leaf = opening width)
CD['door_swings'] = [
 {'door': 'D-SMB2-S', 'rect': [9100, 3900, 9850, 4650], 'note': 'new S partition door, swings into bath'},
 {'door': 'D-GBED',   'rect': [10900, 7000, 11700, 7800], 'note': 'RC2.1: leaf re-hung OUTWARD into corridor or surface sliding — interior freed; exterior swing noted, TO_VERIFY'},
 {'door': 'D-STUDY',  'rect': [13100, 6564, 13900, 7364], 'note': 'study door swings east into room'},
 {'door': 'D-MB',     'rect': [13100, 4564, 13900, 5364], 'note': 'master bath door swings east into bath'},
 {'door': 'D-SM',     'rect': [8000, 3564, 8700, 4364],   'note': 'secondary master door swings into bedroom'},
]

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
# STUDY (R-BED-N x13100-16300 y6500-11350): RC2 — fix daybed/bookcase overlap and
# door-swing collisions (D-STUDY swing envelope x13100-13900 y6564-7364 stays clear)
furn('ST-DESK', 14000, 6500, 15700, 7300, note='1700x800 desk on south wall, east of door swing; NE bay window lights room')
furn('ST-DAYBED', 13100, 8300, 13900, 10300, note='800x2000 daybed on west wall, north of door swing')
furn('ST-BOOK', 15500, 8500, 16300, 10500, lay='A-FURN-EXST-KEEP', note='existing wardrobe->book/file/equip')
furn('ST-NAS', 13100, 7450, 13800, 8050, note='NAS/printer shelf, ventilated, north of door swing')
# GUEST BEDROOM (x9900-12900 y8000-10700): RC2.1 — entry door re-hung outward /
# surface sliding on EXISTING opening (no new white-wall cut) -> interior swing
# zone freed; portrait bunk back on west wall; continuous >=800 east lane
# entry -> bedside -> balcony glass door (fixes the 300mm throat)
furn('GB-BUNK', 9900, 8300, 11400, 10400, note='1500x2100 portrait on west wall; ladder at south end')
furn('GB-DESK', 12200, 8000, 12900, 8450, note='narrow desk 700x450 SE corner, east of 800mm lane')
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
# MASTER BATH x13100-16300 y4650-6300: RC2 — replace 2200x800 strip with
# 1600x900+ corner shower (ageing-friendly: fold seat + grab bars + handheld).
# West door (D-MB) swing envelope x13100-13900 y4564-5364 kept clear.
furn('MBATH-SHOWER', 14700, 5400, 16300, 6300, lay='A-FIXT-PLUMB', note='corner shower 1600x900 NE; zero-threshold target, fold seat+grab bars+handheld')
furn('MBATH-WC', 15500, 4650, 16300, 5350, lay='A-FIXT-PLUMB', note='smart toilet SE, front clearance faces west')
furn('MBATH-VANITY', 13100, 5500, 13700, 6300, lay='A-FIXT-PLUMB', note='single vanity NW, north of door swing')
furn('MBATH-RAD', 13900, 4650, 14500, 4900, lay='A-FIXT-PLUMB', note='radiator keep on south wall, clear of door swing')
# SECONDARY MASTER BATH — RC2.1: shell + south annex (~5.0m2); S door 750 in new
# partition (hinge east, swings into annex); main aisle 800 continuous:
# WC 650 west / aisle x9700-10500 / shower 800 east column w/ 750 glass entry
furn('SMB2-SHOWER', 10500, 4650, 11300, 6300, lay='A-FIXT-PLUMB', note='800x1650 east column (shared master-bath wet wall); glass panel y5400-6300, 750 entry at south')
furn('SMB2-WC', 9050, 5500, 9700, 6300, lay='A-FIXT-PLUMB', note='smart toilet NW 650x800, 800mm front clearance')
furn('SMB2-VANITY', 9850, 3900, 10500, 4450, lay='A-FIXT-PLUMB', note='700x550 vanity in annex east, clear of door swing')
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
# windows / glazing (RC2.2 register)
for win in M.get('windows', []):
    vs = win['verification_status']
    lay = {'CONFIRMED': 'A-WIND-EXST-KEEP', 'MEASURED': 'A-WIND-EXST-KEEP',
           'TO_VERIFY': 'A-WIND-TO-VERIFY', 'PROPOSED': 'A-GLAZ-PROP'}[vs]
    r = win['opening_rect_mm']
    if win['window_type'] == 'PROPOSED_BALCONY_ENCLOSURE':
        if (r[2]-r[0]) >= (r[3]-r[1]):
            msp.add_line((r[0], (r[1]+r[3])/2), (r[2], (r[1]+r[3])/2), dxfattribs={'layer': lay})
        else:
            msp.add_line(((r[0]+r[2])/2, r[1]), ((r[0]+r[2])/2, r[3]), dxfattribs={'layer': lay})
        continue
    if (r[2]-r[0]) >= (r[3]-r[1]):
        for i in (0.25, 0.5, 0.75):
            y = r[1] + (r[3]-r[1])*i
            msp.add_line((r[0], y), (r[2], y), dxfattribs={'layer': lay})
    else:
        for i in (0.25, 0.5, 0.75):
            x = r[0] + (r[2]-r[0])*i
            msp.add_line((x, r[1]), (x, r[3]), dxfattribs={'layer': lay})
    bay = win.get('bay')
    if bay:
        for j in bay['jambs']:
            rect(msp, lay, *j)
        rect(msp, lay, *bay['front'])
# new bath enclosure: cloakroom shell N/W/E kept (drawn by walls());
# NEW walls = south partition (door gap) + annex east/west walls into bedroom;
# interior wet/dry glass partition optional (marked A-NOTE)
x1, y1, x2, y2 = SMB['x1'], SMB['y1'], SMB['x2'], SMB['y2']
for r, wid in NEW_WALLS:
    rect(msp, 'A-WALL-NEW', *r)
for r, did in NEW_DOORS:
    rect(msp, 'A-DOOR-NEW', *r)
label(msp, 'SEC-MASTER-BATH ~5.0m2: shell + annex;\nS-door in NEW partition (hinge E, swings in)', 9050, 3550, 130)
# residual stub marker
rect(msp, 'A-QC', 10800, 4450, 11400, 4550)
label(msp, 'stub TO_VERIFY', 10900, 4350, 120)
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
        # RC2: shell kept + L-annex into bedroom; door in NEW partition at y3800-3900
        for r, _ in NEW_WALLS:
            rect(m, 'A-WALL-NEW', *r)
        for r, _ in NEW_DOORS:
            rect(m, 'A-DOOR-NEW', *r)
        rect(m, 'A-QC', 10800, 4450, 11400, 4550)                     # residual stub TO_VERIFY
        rect(m, 'A-QC', *CD['smb']['clearances']['door_swing'])       # swing zone kept clear
        label(m, 'OPTION S: NEW south partition + annex (~5.0m2), zero demolition (RECOMMENDED)', 6800, 3300, 180)
        label(m, 'door swing zone — fixture-free', 8000, 3600, 130)
        label(m, 'residual stub x10800-11400 TO_VERIFY', 10400, 4300, 130)
    else:
        # W needs a NEW OPENING cut in existing CLK-W (white-class) — owner exception; sliding leaf
        rect(m, 'A-QC', 8950, 4700, 9050, 5400)                       # proposed cut zone
        label(m, 'OPTION W: SLIDING door in RETAINED CLK-W (white-class) — needs owner exception', 6800, 3300, 170)
        label(m, 'CLK-W retained wall — cut zone marked', 7000, 3550, 150)
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
ac = CD['level']['area_comparison']
label(m, f"AREA ACCOUNT: returned {ac['returned_platform_m2']}m2 vs ramp {ac['ramp_footprint_m2']}m2 "
         f"-> net +{ac['net_unobstructed_public_gain_m2']}m2; value = rectangular living + assisted-use route",
      5900, 4400, 150)
d.saveas(str(ROOT / 'concept' / 'split_level_study.dxf'))

json.dump(CD, open(ROOT / 'concept' / 'concept_data.json', 'w'), ensure_ascii=False, indent=1)
print('concept dxf + options + study written; furniture:', len(F))
