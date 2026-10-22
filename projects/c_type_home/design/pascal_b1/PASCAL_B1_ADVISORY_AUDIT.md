# PASCAL_B1 — ADVISORY AUDIT (verify_scene v3, 47 issues)

Rule: `ACKNOWLEDGED_HUMAN_OVERRIDE` is NOT a blanket silencer. Only items the
user explicitly adjudicated count as A. Everything else is listed honestly.

| class | count |
|---|---|
| A EXPLICIT_HUMAN_OVERRIDE | 11 |
| B AUTO_DRAFTING_TOLERANCE | 0 |
| C REPRESENTATION_LIMITATION | 26 |
| D NOMINAL_ZONE_ONLY | 0 |
| **E UNREVIEWED_WARNING** | **10** |

---

## A. EXPLICIT_HUMAN_OVERRIDE (11)

Items the user explicitly adjudicated (the 4 accepts / 3 wet-zone region
corrections / 5 manual corrections kept). Positions as drawn — NO_MOVE.

Door keep-out (6):
- `D-GBATH` × 次卧小床1.2 — bed kept at human position
- `D-GBED` × 次卧小床1.2 — same
- `G-GB-BALC` × 次卧衣柜 — wardrobe kept at human position (depth 500)
- `D-CONN-MB-SMB` × 主卧电视柜 — explicitly accepted as drawn
- `D-ENS-OWNER` × 次主卫湿区 — wet-zone region boundary (adjudicated)
- `D-ENS-OWNER` × 次主卫马桶 — explicitly accepted as drawn

Item pairs (5):
- overlap 客卫（湿区） × 3kg洗衣机 — washer inside wet region; wall-mount
  candidate, adjudicated position
- <8cm 次卧小床1.2 × 床背板 — both manual-correction-kept
- <8cm 次卧小床1.2 × 窄书桌 — same
- <8cm 床背板 × 窄书桌 — same
- <8cm 次主卫湿区 × 次主卫台盆和柜体 — wet-zone adjudicated adjacency

## C. REPRESENTATION_LIMITATION (26)

Advisories that exist only because of how Pascal represents things — not real
space problems:

- `slabs/floors missing`, `ceilings missing` — scene has no slab/ceiling
  nodes (L-06)
- `D-CONN-MB-SMB` × 次主卧床头占位 — `占位` objects are analysis-region
  annotation rectangles, not physical furniture
- <8cm 次主卧床头占位 × 次主卧床 — same placeholder
- <8cm 主卧床 × 主卧床头柜占位 — same placeholder
- `G-DIN-LIV` × 餐椅 / 餐椅003 / 鞋柜 — dining/living partition is an open
  glazed band represented as a `door` node; chairs near a partition are not
  "blocking a door" (L-05)
- 18 × `K-*` kitchen pairs — canonical cabinet runs legitimately contain the
  appliance blocks drawn on top of them; nested rects as drawn (not spatial
  conflicts)

## E. UNREVIEWED_WARNING (10) — needs your call

**Door keep-out (5):**

| door | blocking item | note |
|---|---|---|
| D-CONN-MB-SMB (主卧↔次主卧连通门) | 次主卧衣柜 | wardrobe near connecting door |
| G-GB-BALC (次卧↔阳台玻璃门) | 次卧凳子 | stool near glass door |
| G-GB-BALC | 洗衣机+烘干机（叠放） | stack near glass door |
| ENT-1 (入户门) | 鞋柜 | shoe cabinet near entry |
| D-BATHM (主卫门) | 主卫洗手盆和柜体 | basin/vanity near bath door |

**Item proximity/overlap (5):**

| pair | type |
|---|---|
| 书柜 × 矮书柜 | <8 cm — study/BED-N cluster |
| 书柜 × 打印机 | <8 cm |
| 矮书柜 × 打印机 | overlap (printer on shelf?) |
| 矮书柜 × nas | overlap (NAS on shelf?) |
| 次卧凳子 × 窄书桌 | <8 cm |

These were never explicitly adjudicated. Options per item: accept as drawn
(upgrades to A), or flag for real design change in a later revision.

---

**Audit result**: UNREVIEWED_WARNING = **10** → gate stays `DRAFT_HUMAN_REVIEW`.
