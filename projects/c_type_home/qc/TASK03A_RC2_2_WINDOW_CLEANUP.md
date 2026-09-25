# TASK03A RC2.2 — Window Register & Drawing Expression Cleanup

Base: `feat/c-type-task03a-measured-concept` @ `246ff12` (RC2.1).
Scope: window/opening reconstruction + CAD presentation cleanup only.
**No furniture, bathroom, guest-path, stair/ramp or room-program coordinates changed** (G25 verified against frozen baseline `qc/layout_baseline_246ff12.json` + `qc/walls_baseline_246ff12.json`).

## 1. Window register summary

`current_existing/window_register.json` + `.csv` — **11 records**.

| window_id | room/zone | type | span_mm | verification | evidence basis |
|---|---|---|---|---|---|
| W-KIT-S | kitchen | STANDARD_WINDOW | 1000 | CONFIRMED | dev-plan thin-line + DWG 4-line glazing in band |
| W-KIT-SW | kitchen/life-balcony | STANDARD_WINDOW | 380 | TO_VERIFY | south-wall gap x5000–5380; could be window or balcony door |
| W-SMB-S | secondary master bed | BAY_WINDOW | 2400 | CONFIRMED | DWG bay box x8400–11000 proj. 700 |
| W-MB-S | master bed | BAY_WINDOW | 2700 | CONFIRMED | DWG bay box x12000–14900 proj. 700 |
| W-LIV-N | living | BAY_WINDOW | 3100 | CONFIRMED | face gap x3800–6900 + glazed front y13800–13900 |
| W-STUDY-NE | study | BAY_WINDOW | 2100 | CONFIRMED | face y11100 gap x13600–15700, bay to y11800 |
| W-GBATH-N | guest bath | STANDARD_WINDOW | 800 | TO_VERIFY | DWG triple-line in band; dev-plan ambiguous (bath→open balcony) |
| G-GB-BALC | guest bedroom | GLASS_DOOR | 2000 | CONFIRMED | DWG triple-line x10400–12400; interior door, EXISTING_KEEP |
| D-BALC-W | north balcony west | GLASS_DOOR | 600 | MEASURED | door insert rot270; leaf type TO_VERIFY |
| G-DIN-LIV | kitchen/dining↔living | GLASS_DOOR | 2700 | CONFIRMED | owner blue-line 3-track sliding, EXISTING_KEEP |
| N-BALC-ENCL | north balcony edge | PROPOSED_BALCONY_ENCLOSURE | 5100 | PROPOSED | parapet only today — OPEN_NOT_ENCLOSED |

Counts: **11 total** · DWG-precisely-located 8 · TO_VERIFY 2 (W-KIT-SW, W-GBATH-N) · MEASURED 1 · bay windows 4 · glass doors 3 · proposed enclosure 1.

**East wall: NO window** — solid in both dev plan and measured DWG (inner face continuous y4500–10900). Study is lit by the NE bay window; earlier note claiming "east window side-lit" was wrong and is corrected.

## 2. North balcony time-state (preserved)

- current exterior enclosure: `OPEN_NOT_ENCLOSED` (DWG draws parapet outline only)
- future enclosure: `PROPOSED` — drawn as dashed green glazing line on `A-GLAZ-PROP`, never as existing window
- `G-GB-BALC` interior double glass door: `EXISTING_KEEP` — separate record from exterior enclosure

## 3. Broken geometry — root causes

**Bottom-left phantom L (grey thick lines, x1300–5800 y450–2400)**
Root cause: real measured geometry — the **life-balcony parapet walls** `W-BALC-W`/`W-BALC-S` (DWG line x1300–5500 y500 confirms). They *looked* like stale orphans because the balcony's north separation wall was demolished (opened to dining), leaving the parapet visually floating with no room label.
Fix: kept (they are real railing/parapet), labeled `LIFE BALCONY parapet`, exempted in orphan gate as `railing_parapet` type.

**Top floating red segments (living room north)**
Root cause: `W-BAY-F` was modeled at y13400–13600 but the measured bay glazed front is at y13800–13900 — the rect sat mid-air inside the bay projection. `W-BAY-JW/JE` jambs also ended 400mm short.
Fix: W-BAY-F removed from wall set (it is the **glazed front** of window `W-LIV-N`, not a wall); jambs extended to measured y13800; wall `W-EXT-N-LV` split `wall | opening x3800–6900 | wall`.

**Right floating red segments (study NE corner)**
Root cause: `W-EXT-NE` was drawn as a solid band y11350–11550 across what is actually a **bay window** — measured study north face is y10900–11100 with opening x13600–15700 and bay projecting to y11800 (jambs x13500–13600 / x15700–15800, glazed front y11700–11800).
Fix: W-EXT-NE → west wall segment [13000,10900,13600,11100]; W-EXT-NE2 → east segment [15700,10900,16400,11100]; opening + bay registered as `W-STUDY-NE`.

**South wall continuous through windows**
Root cause: `W-EXT-S` was one solid rect; DWG shows kitchen window (4-line symbol x6100–7100) plus two 700-deep bay boxes (SMB x8400–11000, master x12000–14900).
Fix: split into 4 wall segments + 3 openings; bay jambs/fronts drawn as glazing components.

Also corrected: `G-GB-BALC` glazed span refined x10500–13000 → **x10400–12400** (DWG triple-line); west wall `W-EXT-W` now split at the measured entry-door gap y5440–6540; `D-BALC-W` opening aligned to wall band (north face ends x7800 measured).

## 4. Wall-through-window conflicts

G22 check over all registered spans: **0 conflicts** after segmentation (previously W-EXT-S, W-EXT-N-LV, W-INT-Y10800, W-EXT-W all crossed openings).

## 5. Drawing outputs

Owner-facing: `task03a_s3_furniture_presentation.png/.pdf` — walls, windows (blue glazing lines + bay outlines), doors with leaf/arc, furniture with friendly labels, room names, key dims, minimal legend. No QC boxes / swing envelopes / object IDs.
Diagnostic: `task03a_s3_furniture_qc.png/.pdf` — adds swing envelopes, clear zones, guest path, window IDs + status tags, full 13-class legend.
Plus: `window_register_overlay.png`, `wall_window_conflict_check.png`, `window_cleanup_before_after.png` (4 areas × before/after).

Old `task03a_s3_furniture.png/.pdf` removed — superseded by the pair above.

## 6. Approved spatial layout — unchanged

G25 compares every design coordinate against the frozen RC2.1 baseline: furniture rects, plumbing fixtures, SMB bath (zone/annex/fixtures/clearances/shower glass/doors), guest path, door swings, new walls/doors, level/stair/ramp/area account — **all identical**. Only window/opening geometry, wall segmentation at openings, and rendering metadata changed.

## 7. Gate results (G1–G25 + G10b = 26)

All **26/26 PASS** — see `qc/task03a_gates.json`.
New gates: G21 register coverage (missing=0) · G22 wall-through-window (0) · G23 balcony time-state · G24 orphan graphics (0) · G25 layout freeze (changed=none).

## 8. Remaining TO_VERIFY (unchanged, non-blocking)

- `W-KIT-SW` 380mm south opening — window or balcony door, field check
- `W-GBATH-N` bath→balcony window — DWG drawn, dev-plan ambiguous
- `D-BALC-W` leaf type (solid vs glazed)
- level delta ≤350 vs ~400; SMB-bath drainage; 600mm cloakroom stub
