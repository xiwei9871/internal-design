# P1.2 验证报告 — 几何×标注×版本 同步闭环

日期: 2026-10-18 | POC: A103_CONSTRUCTION_POC_V3

## 架构升级
```
FCStd (freecadcmd)          V15_WORK.blend (blender -b 实时dump)
   ↓ verts/bbox                  ↓ mesh tris → shapely union
extract_anchors_v03.py → geometry_v03.json
   27锚点(对象+子元素+sha) + 158管理实体(轮廓+状态) + 9门洞 + 衍生数据hash登记
   ↓
make_a103_poc_v3.py — 每次生成前对真实文件重算SHA (不信缓存)
   墙线按源轮廓重建 + XDATA(DEVINSRC)对象绑定 + DIMENSION(XDATA tag) + INSERT
   ↓
qa_a103_v3.py — 独立从 geometry 复算 (不读生成器dimmap)
```

## 四类回归测试 (derived/p12_tests/, 生产文件零接触)

| 测试 | 结果 | 证据 |
|---|---|---|
| **T-A FC几何+尺寸同步** | **PASS** | 副本 `W_BALC_S.Placement.x+100` → 墙线实体 xmin 1300→1400 **且** `south_total` 14300→14200。不是只改数字 |
| **T-B Blender对象传播** | **PASS** | 副本 `R3_COMPLETE_PARTITION_WALLS` mesh顶点+0.1m → 隔墙实体 9059→9159。发现该对象未链接场景集合(location无效),改用真实mesh变换 |
| **T-C 提取后源变更** | **PASS** | 提取后篡改FC副本 → 生成器 live-rehash → `BLOCK: source CHANGED` rc=1 |
| **T-D 缺锚点** | **PASS** | 移除 S-SPAN-E → `BLOCK: dim south_total missing anchor` rc=1 |

## 审阅问题逐条

| P1.1 问题 | P1.2 落实 |
|---|---|
| preflight 信缓存 FRESH | 每次生成重算全部 source_file sha256 → BLOCK 证据 T-C |
| 墙线不随对象更新 | 158 个管理实体按源轮廓重建+XDATA绑定; G9 验证实体bbox==outline_bbox ≤2mm |
| Blender 中间JSON失关联 | 改为 `blender -b` 实时 dump (489对象); model_walls3/stair_footprints 不再使用; 衍生数据登记 parent_sha256 |
| G8 固定 PASS | 真实比对锚点/管理实体 revision 集合 |
| G4 只查字段存在 | 新增对象存在性核查 (锚点对象必须在对应 dump 中) |
| bbox 语义 | 新增 `bath2_net_w` (2191 = 隔墙内面→走廊墙面, 与 envelope 2341 区分); 台阶锚点标 FIELD_VERIFY |
| 门洞语义 | openings 带 orient/design_status/swing(UNKNOWN_UNVERIFIED 诚实标注) |
| 测试污染生产 | stale 测试只改临时副本; 全部测试在 derived/p12_tests/ |

## QA Gate 现状 (qa_report_v03.json, 程序化)
G1-G5,G7-G10 **PASS**; G6 A-UNCERTAIN 38实体 **HOLD**(已登记待裁决); G11 编辑器 **PARTIAL**(FreeCAD可导入,无QCAD/LibreCAD交互验证=NOT_RUN); G12 纸面 **PARTIAL**(Layout1 A1框+矢量PDF已出,打印未验)。

## 发现并修复的真实缺陷
- FreeCAD `o.Shape.Edges` 遍历会内核崩溃 → 改用 Vertexes+concave_hull 重建轮廓
- Blender `o.matrix_world` 不含 location (对象未链场景) → dump 改用 evaluated matrix_world; 测试改 mesh 顶点
- 重叠墙对象互相认领同一底图实体 → 一实体一对象, XDATA 多名并列

## 仍 HOLD (不受技术 Gate 影响)
结构安全核实 / 北阳台封窗构造合规 / 台阶450mm现场复尺 / 38个A-UNCERTAIN裁决 / CAD编辑器交互验证
