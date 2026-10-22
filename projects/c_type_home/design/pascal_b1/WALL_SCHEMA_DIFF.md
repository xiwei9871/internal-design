# PASCAL 3D REGRESSION — WALL SCHEMA DIFF & ROOT CAUSE

Date: 2026-09-30
Task: 旧 Pascal scene 3D 正常 / 新 `pascal-master-direct-arch-v1` 2D 正确但 3D "错" —
找出 schema / hierarchy / height / transform 层面发生了什么变化。

## VERDICT

**不是数据回归，是观察误读。** master-direct 场景的墙数据、层级、坐标、高度全部正确；
Pascal 3D **编辑模式对所有场景的墙一律渲染为半透明 stud 面板**（可编辑预览样式），
从未存在"实心墙编辑视图"。旧场景"3D 正常"的观感来自 56 个家具 item（白色不透明
blockout 盒）遮挡了半透明墙；新场景 item=0，裸半透明墙被误判为"3D 坏"。
**Preview 模式下 master-direct 的墙渲染完全正常**（浅色实体墙板 + 蓝色玻璃窗 + 飘窗）。

Binary test: `OLD_SCENE_CURRENT_RUNTIME = PASS`（pascal-ab-clone-good 原样克隆当前 runtime 渲染正常）

## SCENES COMPARED

| scene | version | nodeCount | items | 3D-edit look | Preview look |
|---|---|---|---|---|---|
| pascal-b1-blocks-v1 (KNOWN GOOD) | 8 | 156 | 56 | 白墙(实为items)+玻璃墙 | — |
| pascal-b1-full-v1 | 4 | 141 | 56 | 同上 | — |
| pascal-b1-full-v2 | 5 | 158 | 56 | 同上 | — |
| pascal-wall-debug-v1 | 3 | 43 | 0 | 全玻璃墙 | — |
| pascal-master-direct-arch-v1 (CURRENT) | 2 | 96 | 0 | 全玻璃墙 | **正常实体墙** |

关键相关性曾被误读为 "projectId / items 触发实心渲染"：
实为 **items 的视觉遮挡**。item 越少 → 半透明墙越显眼。

## WALL SCHEMA DIFF (40 good walls vs 72 bad walls)

FIELD_PRESENT_IN_GOOD_ONLY: **none** — 键集完全一致：
`object, id, type, parentId, visible, metadata, children, thickness, height, start, end, frontSide, backSide`

FIELD_VALUE_PATTERN_CHANGED:
- metadata：good=`{canonical_ids, merged_from}`；bad=`{canonical_id, source, wall_class, height_status}`
  → A/B 实验证明**无渲染影响**（good 墙+bad metadata 仍正常；bad 墙+good metadata 不变）
- thickness 分布：good `{0.2:25,0.1:8,0.25:2,0.15:2,...}`；bad `{0.2:48,0.1:11,0.4:3,...}` → 混合厚度两边都有，无关
- height：good `{2.5:36,1.05:4}`；bad `{2.5:63,1.05:8,2.4:1}` → 正常

FIELD_UNIT_CHANGED: none（两边均米制，`start/end=[x,z]`）
FIELD_DEFAULT_CHANGED: none

## HIERARCHY

完全一致：`site → building(position[0,0,0],rotation[0]) → level → {wall,zone,item,slab}`；
`door/window` 在两边都是 wall 的 children（parentId=wall）。无孤儿、无双 elevation、无错位 level。

## 排除过的假设（全部有 A/B 场景证据）

| 假设 | 实验 | 结果 |
|---|---|---|
| runtime/编辑器版本回归 | clone-good 原样重渲染 | 正常 → 排除 |
| 缺 materials 键 | bad+`materials:{}` | 仍玻璃 → 排除 |
| 缺 item | bad+1 item / +56 items | 仍玻璃 → 排除 |
| 缺 zone | bad+19 zones | 仍玻璃 → 排除 |
| 缺 slab | bad+slabs / full-v1 slab=0 仍正常 | 排除 |
| 门/窗节点 schema 毒化 | bad 去门窗 + items | 仍玻璃 → 排除 |
| wall metadata 差异 | good墙+badmeta / bad墙+goodmeta | 无影响 → 排除 |
| 房间闭合环检测 | clone-good 开缺口 / 删 7 墙 | 仍正常 → 排除 |
| 墙端点未对齐 | 端点距分布对比 | 两边几乎一致 → 排除 |
| 平行重叠墙冲突 | 重叠对计数 | good 1 对 / bad 1 对 → 排除 |
| 单墙永远玻璃（验证基线） | one-good-wall / one-bad-wall / 闭合四环 / 环+内 slab/zone/item | 全玻璃 → **证明编辑模式墙样式是全局的** |

决定性反证：`ab9-none` = 40 根 **good 墙** 去掉全部 items → **同样全玻璃**。
"实心"从来只是 items 的白色不透明 blockout。

## 附带发现（非阻塞）

- Preview 点击后 console 出现 ~77 条 `[viewer] Skipping BVH for incompatible mesh geometry`
  warning（raycast 加速构建失败，不影响显示，待查是否与 glazed screen/hostband 薄墙相关）。
- 1 条 404：`material/wood/woodplank_48_basecolor_512.ktx2` 材质贴图缺失（与墙无关）。

## 最小修复建议

**无需修数据。** 3D 观感差异用以下任一方式解决：
1. 评审时用 **Preview**（工具栏）看材质实体墙；
2. 后续把 DESIGN GUIDE 的家具 items 灌入 master-direct 场景后，观感与旧场景一致；
3. 若要求编辑模式也显示实心墙 → 需查 Pascal "Display settings" 中是否有墙材质开关（产品行为，非数据问题）。

Walls data: PASS。2D gate 已全绿，Preview 3D 结构正确 → **可以进入 ARCH_XY 人工复核**。

## 实验场景存档

`/tmp/pascal-regression/ab*.json` + `ab*-*.png`（A/B 场景 id 前缀 `pascal-ab*`，可随时删）。
原始导出：`pascal-b1-*.json`（KNOWN_GOOD raw）、`pascal-master-direct-arch-v1.json`（CURRENT raw）。
