# B1 SPATIAL ISSUES V003 — 世纪欣园

> FORMALIZATION_REVIEW = CLOSED — 全部冲突项已由用户裁决,无待办位移

## HUMAN_ACCEPTED_AS_DRAWN(用户批准忽略,不再处理)

| 对象 | 原冲突 | 用户裁决 |
|---|---|---|
| 主卫马桶 | 压主卫墙带 ~74mm | ACCEPTED_AS_DRAWN |
| 次主卫马桶 | 压次主卫墙带 ~74mm | ACCEPTED_AS_DRAWN |
| 主卧电视柜 | 压 R-MASTER 门洞带 ~277mm | ACCEPTED_AS_DRAWN |
| 双人位 | 压客厅墙带 ~83mm | ACCEPTED_AS_DRAWN |

## 已知保留状态(人工确认)

- `Rectangle` 847×3163(客厅西侧,压三人位足迹)— 源文件残留工作线,V003 排除建模。**是否从 FCStd 本体删除待你确认**
- 3kg 洗衣机:用户最新人工位保留(湿区内,已平移 +12/−33),壁挂候选按 +750 高 blockout
- 床背板+窄书桌占位已由用户拆分为 床背板 200×1200 + 窄书桌 350×1650(原位保留)
- 贵妃椅越客厅名义房间线 ~104mm —— 名义多边形非实体墙,不动

## 临时值台账

`blockout_temp_dimensions_v01.json` 38 项(层高/门高/错层高/洁具高度等)全部 BLOCKOUT_TEMP_VALUE。
