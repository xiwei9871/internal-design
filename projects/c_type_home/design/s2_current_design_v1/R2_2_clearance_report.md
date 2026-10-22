# R2.2 Clearance Report

Status: `HUMAN_REVIEW`

All measurements come from the latest FCStd; no R2/R2.1 furniture coordinates are used.

| Metric | Available | Target | Shortfall | Status | Source |
|---|---:|---:|---:|---|---|
| 次卧小床1.2 side clearance | 215.4 | 600 | 384.6 | `CONFLICT` | latest FCStd bbox to historical room polygon |
| 次卧小床1.2 foot clearance | 1437.8 | 600 | 0 | `PASS` | latest FCStd bbox to historical room polygon |
| 次主卧床 side clearance | 233.4 | 600 | 366.6 | `CONFLICT` | latest FCStd bbox to historical room polygon |
| 次主卧床 foot clearance | 1412.8 | 600 | 0 | `PASS` | latest FCStd bbox to historical room polygon |
| 主卧床 side clearance | 173.6 | 600 | 426.4 | `CONFLICT` | latest FCStd bbox to historical room polygon |
| 主卧床 foot clearance | 1387.9 | 600 | 0 | `PASS` | latest FCStd bbox to historical room polygon |
| 客卫马桶 front clearance | 1044.0 | 800 | 0 | `PASS` | latest FCStd fixture bbox / candidate room polygon |
| 主卫马桶 front clearance | -71.1 | 800 | 871.1 | `CONFLICT` | latest FCStd fixture bbox / candidate room polygon |
| 次主卫马桶 front clearance | -120.8 | 800 | 920.8 | `CONFLICT` | latest FCStd fixture bbox / candidate room polygon |
| 餐椅 table gap | 121.1 | 150 | 28.900000000000006 | `CONFLICT` | latest FCStd table/chair bboxes |
| 餐椅003 table gap | 121.1 | 150 | 28.900000000000006 | `CONFLICT` | latest FCStd table/chair bboxes |
| 餐椅004 table gap | 198.5 | 150 | 0 | `PASS` | latest FCStd table/chair bboxes |
| 次主卫湿区 internal footprint | 1.44 | — | — | `TO_VERIFY` | latest named FCStd wet-zone guide |
| 主卫湿区 internal footprint | 1.57 | — | — | `TO_VERIFY` | latest named FCStd wet-zone guide |
| 客卫（湿区） internal footprint | 1.64 | — | — | `TO_VERIFY` | latest named FCStd wet-zone guide |

## Owner ensuite

Latest FCStd objects `次主卫湿区 / 次主卫台盆和柜体 / 次主卫马桶` are the source of truth. No fixture has been moved or rotated.

## Balcony/laundry

Latest FCStd `洗衣机+烘干机（叠放）` is preserved as stacked; SKU, service and environment remain TO_VERIFY.
