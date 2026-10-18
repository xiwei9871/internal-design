# P1_SPEC — A103 原生工程出图规范 V1.1

## 1. 权威来源分级
| 层级 | 来源 | 用途 |
|---|---|---|
| S1 | `C型_原始户型数字化基准模型.FCStd` (FreeCAD Part::Feature, 语义命名 W_*/WIN_*/COL_*) | 既有墙体/窗/柱锚点 |
| S2 | `C型_原始户型数字化基准图.dxf` (实体 handle) | 门洞、墙线交接、基准标注 |
| S3 | `V15_WORK.blend` (对象名 W_wall_md_*/WAVE_STEP_*/WAVE_HANDRAIL_*) | 新建墙、台阶、设计对象 |
| 禁 | 渲染图/像素分割/手抄坐标 | 不得作为工程锚点 |

## 2. 锚点字段 (geometry_v02.json)
每锚点: id, x, y, source_file, source_file_sha256, source_revision, source_object_id, subelement_reference, geometry_role, design_status, verification_status, evidence。
- subelement_reference: `Shape.Vertexes[i]` / `Edge[i]` / `dxf_handle:XX` / `bbox.corner(NW)`
- verification_status: VERIFIED_OBJECT | MANUAL_MAPPING_PENDING | FIELD_VERIFY
- 无法对象级关联的锚点必须 MANUAL_MAPPING_PENDING，不得计 PASS

## 3. 图层规范
- `A-DIMS` — 原生 DIMENSION（新，开启）
- `A-DIMS-LEGACY` — 旧 LINE+TEXT 标注（冻结保留审计）
- `A-UNCERTAIN` — 未确认对象登记层；其上对象必须在 object_mapping 登记处置状态
- 门窗符号 → `A-DOOR`/`A-WINDOW` 层 INSERT，属性 SRC_ID=源对象

## 4. 尺寸规范
- dimstyle `STD-ARCH`（AC1032, HZTXT 链, dimtxt=180 模型mm→1:50≈3.6mm 纸面）
- 所有 DIMENSION 值=锚点几何实测，禁止 dim.text 覆写
- 同锚点复算误差 ≤1mm

## 5. 完整性门禁（生成前执行）
- manifest 全部源文件重算 SHA256；失配 → BLOCK
- 标注引用的锚点缺失 source_object_id → BLOCK
- geometry/标注/QA 必须使用同一次提取的 source_revision
- A-UNCERTAIN 上有可见（未冻结/未登记）实体 → BLOCK

## 6. 测试定义
- `stale_source_test.py`：篡改源文件 → 生成必须 BLOCK
- `change_propagation_test.py`：FreeCAD 测试副本中移动对象 100mm → 重提锚点 → 重生成 → 对应 DIMENSION 变化 = 端到端 PASS
- `qa_a103_poc.py`：程序化生成 qa_report_v02.json（PASS/FAIL/NOT_RUN/HOLD，禁止手工宣告）

## 7. 交付物
P1_SPEC.md / geometry_v02.json / A103_CONSTRUCTION_POC_V2.dxf (+pdf) / object_mapping_v02.csv / qa_report_v02.json / stale_source_test.py / change_propagation_test.py / P1_1_VALIDATION_REPORT.md
