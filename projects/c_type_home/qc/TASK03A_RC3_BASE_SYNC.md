# TASK03A RC3 — Canonical Base Sync + Full Regeneration

Base: `feat/c-type-task03a-measured-concept` @ `95ab90e`
Scope: base-truth freeze + kitchen cabinet projection + canonical geometry.
No furniture / bath / ramp / registry changes.

## 1. Canonical base

`current_existing/canonical_plan_v1.json` — single geometry source:
walls, openings (14 doors), windows (9), balconies, split_level,
keep_items, kitchen_cabinets (9), owner_corrections.
Each section carries a sha256 recorded in `hashes`.

## 2. Kitchen cabinet register

`current_existing/kitchen_cabinet_register.json` + `.csv`
Source: `source/世纪欣园3-1-901_cabinet_plan.pdf` （深化图 2024-08-31).

Layout confirmed by dimension lock: east run 3915 = interior 4450 − 535
(sink-leg depth) — U-shape against E/N/S walls, west side open to dining
(west wall demolished).

| ID | Kind | Rect (task01 mm) | Status |
|---|---|---|---|
| K-RUN-E | base run 3915×600 | [7200,535,7800,4450] | CONFIRMED |
| K-COOK | 灶具 900 slot | [7200,2705,7800,3605] | CONFIRMED |
| K-DISHW | 洗碗机 600 slot | [7200,2105,7800,2705] | CONFIRMED |
| K-BASKET | 拉篮 ~800 | [7200,3605,7800,4400] | TO_VERIFY (exact y) |
| K-FRIDGE-TALL | 冰箱高柜 1840×700 | [5900,3750,7740,4450] | CONFIRMED |
| K-FRIDGE | fridge slot 905×710 | inside tall cab | TO_VERIFY (internal split) |
| K-RUN-S | sink leg 1210×600 | [6100,0,7310,600] | CONFIRMED (x-origin ±210) |
| K-SINK | 水槽柜 990 | [6100,0,7090,600] | CONFIRMED |
| K-WALL-E | 吊柜 380 deep | [7420,535,7800,4450] | TO_VERIFY (module splits) |

`K-CABINETS` placeholder block removed from keep_items; `K-CAB` in
concept furniture is now only a zone outline (G3 still uses it as the
no-intrusion zone).

## 3. Drawing sync

All sheets + DXFs regenerate from the same model/canonical data:
- `kitchen_cabinet_alignment_overlay.png` — cabinets x walls x window x doors
- cabinet footprints now render in S1/S2/S3 presentation/QC + both DXFs
- parapets get their own colour/layer (`A-PARP-EXST`, tan) — no longer red

## 4. New gates

- **G28** canonical base hash consistency — walls/openings/windows/cabinets/
  keeps/balconies/level sections all hash-match the canonical file
- **G29** kitchen cabinets clear of walls/windows/door openings — 0 conflicts
- Total: **30/30 PASS**

## 5. Not done (per spec)

Furniture NOT re-laid out this round — K-CAB zone + real cabinet geometry
is now the hard constraint for the upcoming furniture pass.

---

# RC3.1 — Wall Correction + Cabinet Collision Closure + Output Hash Sidecars

Owner review of RC3 @ 5164f25 found three issues; all closed here.

## 1. W-INT-Y4500-bc split (owner-confirmed corridor opening)

Was: continuous wall [11400,4450,16500,4650].
Now:
- `W-INT-Y4500-bc-OPEN`  [11400,4450,12900,4650]  DEMOLISHED_OWNER_CONFIRMED — corridor, no current wall
- `W-INT-Y4500-bc-MBATH` [12900,4450,16500,4650]  EXISTING — retained master-bath wall

Propagates to canonical_plan_v1.json, all S1-S6 sheets, overlays and DXFs
(all regenerated from the same canonical base).

## 2. Kitchen cabinet collision resolved (0.378m2 -> 0)

Root cause re-read from cabinet PDF p0: the "3915" east-wall dimension is a
wall-to-wall chain that includes the 700mm-deep NE corner, which belongs to the
refrigerator tall cabinet (it holds the corner, sockets + side cabs per PDF).
The physical east base run is 3215mm ending at the tall-cab face y=3750.

Final footprints:
- K-RUN-E        [7200,535,7800,3750]   physical 3215mm (PDF chain 3915 incl. corner)
- K-FRIDGE-TALL  [5900,3750,7740,4450]  owns NE corner; abuts run at y=3750
- K-RUN-S        [6100,0,7310,600]      sink leg under W-KIT-S
- modules        K-COOK 900 / K-DISHW 600 / K-BASKET / K-SINK 990 / K-FRIDGE 905x710
                 nested via `parent` inside their runs
- K-WALL-E       [7420,535,7800,3750]   380-deep wall cabs, `wall_cabinet_above` K-RUN-E

Relationship semantics added: `parent` (module nesting), `relation.type`
(abuts / corner_owner / wall_cabinet_above), `corner_join` (declared zone).
SE corner K-RUN-E x K-RUN-S overlap 110x65mm declared as `corner_join` zone
[7200,535,7310,600] — a real shared corner base cabinet, exempted by G30.

## 3. Confidence split

Every cabinet record now carries `dimension_status` + `placement_status`
instead of a single CONFIRMED flag. E.g. K-RUN-S: length 1210 CONFIRMED,
placement TO_VERIFY (x-origin ±210). Module positions inside runs are
placement TO_VERIFY where the PDF dim chain does not pin them.

## 4. Gates

- G28 strengthened: checks canonical section hashes AND every output sidecar
  (qc/render_manifest.json, current_existing_v1.base.json,
  concept/concept_dxf_base.json) — all report canonical_sha = identical value.
- G30 new: floor-standing cabinets (runs + tall cab) pairwise overlap must be
  zero except declared corner_join zones.
  Result: collisions=none; exempted=[K-RUN-E x K-RUN-S corner_join 110x65mm].

31/31 ALL PASS. Furniture coordinates unchanged (G27 freeze: changed=none).
