# FULL-HOUSE FURNITURE CALIBRATION V1 — HUMAN_REVIEW

前置：LIVING_ASSET_CALIBRATION=PASS / FURNITURE_ORIENTATION_INFERENCE=PASS / ARCH=LOCKED
场景：**http://pascal.localhost:57071/editor/pascal-master-direct-furnished-v2**
（v1 场景未动；本场景 = 96 arch + 11 厨房 PDF blockout + 51 校准 item 节点，共 158 节点）

## DESIGN_REVIEW 预设（viewer 侧，不改 geometry）

Display 菜单实测存在并可复现：`Shadows=Off` + `Render=Solid` + `Edges=Soft`
（scene JSON 不含 viewer 字段——属客户端状态，截图均用此预设；如需可写进 README）

## 结果总览

| 分类 | 数量 | 明细 |
|---|---|---|
| PASS | 29 | 客厅 6 件 + 床×3 + 衣柜×3 + 电视柜×2 + 书柜×2(模块化重复) + 餐台/书桌、餐桌椅×5、阳台柜×2、马桶×3、3kg 洗衣机 |
| SIZE_DISTORTION | 2 | MEDIA_CABINET(tv-stand 拉 1.56×)、LOW_BOOKCASE(shelf 深度 0.32→0.45 拉 1.4×) |
| PRIMITIVE_FALLBACK | 16 | 见下 |
| 厨房 K-* | 11 | 复用 v1 的 PDF blockout，保持尺寸真实（§9 要求） |

## PRIMITIVE_FALLBACK 原因（不为好看而塞错模型）

- HEADBOARD ×3：床头板是独立薄板件，catalog 无
- SHOWER_ZONE ×3：湿区 footprint(1.64×0.81 等）与 shower-square 0.8×0.8 比例悬殊
- FREEZER:catalog freezer 0.43m 宽太小（目标卧式冰柜 1.2m)
- STACKED_WASHER_DRYER：叠放柜 1.7m 高，单筒洗衣机拉 1.98× 会明显失真
- BENCH / STOOL×2 / STUDY_ARMCHAIR(LOW conf)/ SHOE_CABINET / PRINTER / NAS / NARROW_DESK（仅 0.35m 深，desk asset 会压扁柜腿）

## Facing 冲突 → OVERRIDE（已 flag，待复核）

| 件 | 登记 facing | 判定 |
|---|---|---|
| R030 客卫台盆 | 90°N（与长轴平行，物理不可能） | 改朝东（向房中心）,yaw=90 |
| R035 主卫台盆 | 0°E（同上） | 改朝南（向房中心）,yaw=0 |
| R032 生活阳台柜 | 180°W（同上） | 改朝北（贴南墙开向北）,yaw=180 |

其余 facing 均与 footprint 一致，直接采用登记值。

## QA（自动核对）

每件：target center = rect 中心解析计算；rendered footprint = 旋转+缩放后的 GLB bbox 投影，plan 图上 6/6 客厅件与其余全部重合（center drift = 0 mm 构造保证；anchor 用 GLB 实测 min/bbox-center 归一化到 FOOTPRINT_CENTER_ON_FLOOR)。orientation：所有 facing 由 `cad_facing_to_pascal_yaw` 统一换算 + register 内 correction=0（全 catalog 惯例 front=+Z)。

## 待人工确认

1. tv-stand 开口面（+Z 假设）在 R004/R022/R023 三处
2. bookshelf 开口面（+Z 假设）
3. sink-cabinet 开口面（+Z，由抽屉拉手佐证）+ 3 处 OVERRIDE 朝向
4. MEDIA_CABINET 1.56× 长向拉伸是否接受（或双拼/换 closet)
5. 贵妃椅 yaw=90 躺轴朝向（上轮遗留，MEDIUM)
6. Circle007 主人椅仍 PRIMITIVE + LOW，朝向未定
7. 3KG_WASHER base_z=TO_VERIFY；当前放在地面（primitive 级近似）

## 产物

- `FURNITURE_ASSET_CALIBRATION_V02.json`(51 条记录：native dims/pivot/front/correction/yaw/anchor/scale/分类/notes)
- `WHOLE_HOUSE_3D_CLEAN.png`(DESIGN_REVIEW:shadows off + solid + soft edges)
- `WHOLE_HOUSE_2D.png`(Pascal 2D 实拍）/`WHOLE_HOUSE_2D_PLAN.png`（解析校验图）
- `ZONE_*.png` ×7:LIVING_DINING / STUDY / GUEST_BEDROOM / OWNER_BEDROOM / MOTHER_BEDROOM / THREE_BATHROOMS / NORTH_BALCONY
- 脚本：`scripts/pascal_fullhouse_calibration_v1.py`（全部角度经 register 驱动，无散落魔法值）
