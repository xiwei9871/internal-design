# B1 FORMALIZATION DELTA — V002

Rule: RAW source (FCStd) unchanged. Formal model may apply **minimal XY translations** so furniture clears hard architecture (existing walls, door openings, window/glass-door openings). Dimensions, orientation, room assignment, topology unchanged. Each item logged.

| Object | Zone | Source rect (mm) | Formal rect (mm) | Shift (mm) | Reason |
|---|---|---|---|---|---|
| 主卧衣柜 | R-MASTER | [13176,3878,15276,4478] | shifted −31 y | −31 | clears south wall band |
| 次卧小床1.2 (guest bed) | R-STUDY | [10851,8006,12651,9206] | shifted +197 y | +197 | south edge sat inside D-GBATH/D-GBED door band (y7800–8200) |
| 床背板+窄书桌占位 | R-STUDY | — | −132 y | −132 | clears same south door band |
| 主卧电视柜 | R-MASTER | — | −277 y | −277 | crossed wall band between master/hall |
| 鞋柜 | R-DINING | — | +18 y | +18 | entry/wall line cleanup |
| 双人位 (2S sofa) | R-LIVING | — | −83 y | −83 | clears living south wall band |
| 客卫（湿区） | R-BATH-P | — | (−26, −163) | diag | clears bath wall/door band |
| 主卫湿区 | R-BATH-M | — | −47 y | −47 | bath wall band |
| 主卫马桶 | R-BATH-M | — | −74 y | −74 | bath wall band |
| 主卫洗手盆和柜体 | R-BATH-M | — | −49 y | −49 | bath wall band |
| 次主卫湿区 | R-CLOAK | — | (−77, −53) | diag | owner-ensuite wall band |
| 次主卫马桶 | R-CLOAK | — | −74 y | −74 | owner-ensuite wall band |
| 3kg洗衣机 | R-BATH-P | — | −107 y | −107 | clears bath north wall (was poking ~103 mm into wall) |
| 次卧衣柜 (guest wardrobe) | R-STUDY | [9918,8884,10418,10884] | shifted −187 y | −187 | clears `G-GB-BALC` glass-door band + north wall; **depth 500 mm unchanged** |

Machine-readable: `b1_model.json → formalization_delta[]` (source_rect / formal_rect / shift_mm / resolution).

**Not corrected (by rule):** 贵妃椅 crossing the *nominal* living/hall space polygon by ~104 mm — no wall there, polygon edge is not hard geometry. Left as drawn.

## Excluded object (documented, not modeled)

`Rectangle` — unlabeled FCStd object, 847×3163, canon c≈(3762,10067), living-west. It is a **real physical object in WINDOW_RESTORED.FCStd** (not an extraction artifact), but unlabeled and overlapping the labeled 三人位 sofa footprint — consistent with a stale working outline. Excluded from V002 geometry per cleanup directive; the FCStd source itself is untouched. If it turns out to be a real design element (e.g. rug boundary), flag it and I'll reinstate.
