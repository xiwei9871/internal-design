# PRE_B1_SOURCE_RESOLUTION

Date: 2026-09-29 · Branch: `feat/c-type-task03a-measured-concept` @ `f3ea1b0`
Scope: resolve WORKING vs WINDOW_RESTORED before Blender B1. **No modeling performed.**

## Verdict

```text
SOURCE_RESOLUTION = PASS  (CASE A)
B1 MASTER SOURCE = cad/freecad_import/世纪欣园FF_freecad_WINDOW_RESTORED.FCStd
B1 START = AUTHORIZED
```

## Physical design diff (full detail → `PRE_B1_SOURCE_DIFF.json`)

Method: per-object fingerprint over Name / Label / TypeId / Placement / BoundingBox / shape topology, excluding the 9 expected semantic-only `WINDOW_REF_*` objects.

| Metric | WORKING | WINDOW_RESTORED |
|---|---|---|
| total objects | 428 | 437 |
| physical objects | 416 | 415 |
| sha256 | `cac4df3f…dabe` | `9c2aa9ba…de3e` |

- Common objects compared: **415 / 415 identical**
- Only in WORKING: **`Bspline`** — `Part::Feature`, null shape (0 edges / 0 verts, `isNull=True`), Placement at origin. **Zero design content — a remnant, not furniture.**
- Only in RESTORED: none physical.
- Changed in common: none.

**Is the difference only mtime?** Yes in effect — WORKING's later mtime (23:34 vs 22:54) produced no physical design delta; its only delta is a null-shape leftover.

## Which file has the latest HUMAN furniture?

Both carry identical physical design. WINDOW_RESTORED additionally contains the verified 9 window semantics, so it is strictly the more complete single source. Latest human additions confirmed present in WINDOW_RESTORED: `3kg洗衣机` 450×450, `打印机` 400×400, `nas` 400×400, `洗衣机+烘干机（叠放）` 600×600, `冰柜` 1200×600.

## Required dimension check (in WINDOW_RESTORED)

| Item | Expected | Actual | Result |
|---|---|---|---|
| Mother bed 主卧床 | 1500×2100 | 2100×1500 | ✓ |
| Owner bed 次主卧床 | 1500×2100 | 2100×1500 | ✓ |
| Guest bed 次卧小床1.2 | 1200×1800 | 1800×1200 | ✓ |
| Guest wardrobe 次卧衣柜 | depth 500 | 500×2000 | ✓ |
| Dining table 餐桌 | ≈1600×800 | 1600×800 (Rectangle050, unlabeled) | ✓ |
| Study desk = 茶台 | HUMAN_CONFIRMED 2200×800 | 茶台 Rectangle026 800×2200 | ✓ owner correction 2026-09-29: 茶台 IS the study computer desk/workstation; no separate desk exists or is required |
| 3S sofa 三人位 | ≈2300×900 | 900×2300 | ✓ |
| 2S sofa 双人位 | ≈1900×850 | 1900×850 | ✓ |
| Chaise 贵妃椅 | ≈1700×900 | 1700×900 | ✓ |
| Coffee table 茶几 | ≈1000×550 | 550×1000 | ✓ |
| Side table 角几 | ≈500×500 | Ø500 | ✓ |
| Tea table 茶台 | = STUDY_DESK 2200×800 | 800×2200 | ✓ HUMAN_CONFIRMED |
| Dining chairs 餐椅 | ≈500×550 | Ø400 circles ×4 | ✓ reproduce as drawn; minor block sizing, revisit only if 3D review flags it |

Three bathroom fixture groups all present （主卫 / 次主卫 / 客卫： 马桶+台盆柜+湿区）, plus 客卫 3kg washer.

## Answers to required questions

- **Latest human furniture file:** identical in both; resolved to WINDOW_RESTORED.
- **WORKING has that RESTORED doesn't:** only null-shape `Bspline` (no design content).
- **Only mtime difference?** Yes.
- **B1 master source:** `世纪欣园FF_freecad_WINDOW_RESTORED.FCStd`.
- **9 window refs complete:** 9/9 resolve to physical geometry, 0 broken, 0 drift.
- **`test_s1_brief.py` restored:** yes — `git restore` executed, `test_s1_brief` + `test_pipeline_state` = **5/5 OK** via `.venv/bin/python3 -m unittest`.
- **Working tree:** expected-dirty only — untracked `cad/freecad_import/`, `design/s2_current_design_v1/`, `docs/superpowers/plans/…`; no accidental deletions remain.

## Flags for B1 — RESOLVED 2026-09-29 (owner)

1. ~~Study desk ≈1800×750 missing~~ → **RESOLVED**: `茶台` (Rectangle026, 2200×800) IS the study computer desk / dual-monitor workstation. `STUDY_DESK = HUMAN_CONFIRMED`, `SEPARATE_STUDY_DESK = NOT_REQUIRED`. Do not add a second desk, do not resize to 1800×800, not `90_TO_VERIFY`.
2. 茶台 2200×800 = final human dimension. Reproduce as drawn.
3. 餐椅 Ø400 ×4 — reproduce as drawn; non-blocking.

`PRE_B1_SOURCE_RESOLUTION = PASS` · `STUDY_DESK_SEMANTICS = RESOLVED` · `B1_BLOCKOUT = READY` · `formal_cad_allowed = false`


---

## ADDENDUM V2 — 2026-09-29 POST-FREEZE HUMAN EDITS (CASE B)

`世纪欣园FF_freecad_WORKING.FCStd` re-saved 2026-09-29 10:06 (new sha `2eddf2b7…`).
Fresh physical diff WORKING vs WINDOW_RESTORED:

**Changed objects (3, all explainable human edits):**
| Object | Label | Delta |
|---|---|---|
| Rectangle007 | 客卫（湿区） | moved +45.3x / −20.6y (wet-zone boundary re-placed by owner) |
| Rectangle017 | 次卧小床1.2 | moved −27.3x / −13.7y |
| Rectangle041 | 3kg洗衣机 | moved +12.4x / −32.9y |

**Removed (1):** `Rectangle018` 床背板+窄书桌占位 (199×2839 combined strip)
**Added (2, replacements):** `Rectangle051`(label Rectangle075, 200×1200 床背板) + `Rectangle052`(label Rectangle077, 350×1650 窄书桌)

All deltas correspond to owner's described corrections → **CASE B confirmed**.

**Action taken:** `世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd` created =
latest WORKING physical design (428 objs) + rebuilt 9 semantic-only
`WINDOW_REF_*` PropertyLink refs + `WINDOW_SEMANTIC_REFERENCES` group.
No Shape geometry copied; links resolve to master objects by Name.

Verification: 438 objs = 428 + 10 semantic; 0 physical fingerprint diffs;
85/85 link targets resolve to non-null Shape; save-close-reopen OK.

**B1 MASTER SOURCE = `世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd`**
