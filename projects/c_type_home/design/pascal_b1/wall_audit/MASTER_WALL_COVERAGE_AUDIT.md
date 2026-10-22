# MASTER WALL COVERAGE AUDIT — 世纪欣园FF_PRE_BLENDER_MASTER_V2

Date: 2026-06-11 · Script: `scripts/master_wall_coverage_audit.py` (rerun-able, deterministic)

## Verdict

```
PASCAL_OPENING_HOST_ASSIGNMENT  = PASS   (unchanged, prior gate)
CANONICAL_WALL_COMPLETENESS     = NOT_PROVEN  →  PARTIAL (one proven gap, rest TO_VERIFY)
PASCAL_WALL_VISUAL_COMPLETENESS = FAIL   (mirrors canonical; cannot exceed it)
PASCAL_B1                       = HOLD
```

The user's hypothesis was right: `canonical→Pascal residual = 0mm` never proved wall
completeness. Independent extraction directly from the MASTER_V2 object dump finds
canonical covers **84.1%** of master wall centerline evidence, not 100%.

## Metrics

```
MASTER_WALL_SEGMENTS (evidence)      = 77     (24 thin-long closed geometry + 53 parallel line-pair bands)
CANONICAL_WALL_SEGMENTS              = 39     (35 walls + 4 parapets)
PASCAL_VISIBLE_WALL_SEGMENTS         = 40     (rendered wall nodes, arch-only export)

MASTER_TOTAL_CENTERLINE              = 160375 mm   (double-face lines included; inflated vs physical walls)
CANONICAL_COVERED                    = 134864 mm
CANONICAL_COVERAGE                   = 84.1 %
PASCAL_VISUAL_COVERAGE               = 84.1 %      (Pascal walls == canonical walls 1:1, residual 0.0mm)

MISSING (unexplained, >350mm from any canonical wall) = 2 segments, 2700 mm total
ALIGNMENT_VARIANT (same wall drawn at ±100–400mm offset) = 29 segments
LARGEST_UNEXPLAINED = 2300 mm
```

Method note: coverage is geometry-based. A master band counts as covered if ≥50%
intersects a canonical wall, or if it lies within 350 mm of one
(`ALIGNMENT_VARIANT` = the drawing's second face line / normalization offset —
documented, not silently dropped).

## Unexplained missing segments (source → trace)

| # | Source object(s) | Type | Canonical rect (mm) | Adjacency | Classification |
|---|------------------|------|--------------------|-----------|----------------|
| M1 | Line101/Line103 | Part::Line ×2 | [13500, 11700, 15800, 11800] | NE corner, outside `north_balcony` (poly ends x=13020); east of `W-EXT-NE` | EXTRACTOR_DROPPED — NE balcony/terrace parapet line never entered canonical |
| M2 | Line211/Line214 | Part::Line ×2 | [5500, 3900, 5900, 4000] | R-DINING (ends x=5700) \| R-KITCHEN (starts x=5900) boundary strip | EXTRACTOR_DROPPED — partial pier/stub wall at dining–kitchen junction |

## TO_VERIFY (flagged ALIGNMENT_VARIANT but physically suspicious)

| # | Source | Rect (mm) | Why it needs eyes |
|---|--------|-----------|-------------------|
| V1 | Rectangle020 | [9291, 4476, 10791, 4676] | 1500×200 closed wall band on the Y4500 line. Canonical FOYER wall stops at x=9050 and nothing exists 9050–12900 — probable real wall continuing the corridor boundary, absorbed as "variant" only by 241mm corner proximity |
| V2 | Line254/255 + Line255/256 | [7200..7500..7800, 6600, 7800] | Two parallel 300mm bands INSIDE stairs zone — split-level guard/platform edge walls, canonical models the zone but no wall geometry there |
| V3 | Line032/033/079 | [7750, 7775, 8000, 12050] | 4275mm vertical band, ~250mm west of canonical `W-INT-X7900-U-TV` — possibly a drawn second wall (service shaft / double wall), not just a face line |
| V4 | Line259 | [7473, 5397, 7522, 7738] | 2341mm isolated thin rect at leisure/stair boundary — single-line wall evidence, no canonical counterpart |
| V5 | Line050/235/236/237 + Line050/210 | [5500, 3847, 5948, 4700] | ~250mm-square pier + stub at R-DINING\|R-KITCHEN junction — master drew physical jamb walls canonical dropped |

## Why the Pascal screenshot "looks like it's missing walls"

1. **Real gaps**: M1 (NE railing), V1 (corridor wall continuation), V5
   (dining/kitchen piers) are drawn in MASTER_V2 and absent in both canonical and
   Pascal — visible in `MASTER_VS_CANONICAL_WALL_OVERLAY.png` as red.
2. **Band merging**: master draws double face lines; canonical normalizes to one
   150–250mm band, so 3D walls read thinner/sparser than the CAD suggests.
3. **Open boundaries by design**: e.g. R-DINING↔R-KITCHEN (except V5 stubs),
   G-DIN-LIV glazed screen — zone edges with no drawn wall are real openings, not
   extraction loss.

## Artifacts (this folder)

- `MASTER_WALL_ONLY.png` — all master wall evidence, black
- `PASCAL_WALL_ONLY.png` — rendered Pascal wall rects only
- `CANONICAL_WALL_ONLY.png` — canonical walls only
- `MASTER_VS_CANONICAL_WALL_OVERLAY.png` — grey=full FC linework, blue=canonical, red=master evidence not in canonical
- `MASTER_VS_PASCAL_WALL_OVERLAY.png` — grey=FC linework, green=Pascal walls, red=missing
- `wall_coverage_audit.json` — every missing segment with source object provenance

## Next action (needs human ruling, no auto-add)

- Confirm V1/V2/V3/V5 against the FCStd drawing — if real, they enter canonical
  via extractor fix, not converter patching.
- M1/M2 are confirmed drawn-but-unextracted; add to canonical or mark
  `intentionally excluded` with reason.
