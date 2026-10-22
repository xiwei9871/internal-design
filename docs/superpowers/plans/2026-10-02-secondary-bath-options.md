# 次主卫 A/B 隔断方案 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 从冻结基础版生成两个可对比的次主卫分支：A 南侧推拉门，B 南侧向内平开门。

**Architecture:** 不修改 `HOUSE_BASE_GEOMETRY_V1.blend`。脚本每次从基础版打开，复制到各自分支，在 R-CLOAK 既有包络内增加可逆的白色隔断、门框和门型；黑色墙体、厨房、全屋家具和洁具位置保持不变。两个分支共用同一房间/洁具基线，只改变南侧隔断与门型，输出相同相机和检查指标。

**Tech Stack:** Blender 5.2.1 LTS, Python/bpy, Workbench PNG, JSON manifests.

---

### Task 1: 记录输入与共同几何基线

**Files:**
- Create: `projects/c_type_home/design/secondary_bath_options/build_options.py`
- Create: `projects/c_type_home/design/secondary_bath_options/OPTION_INPUT_REGISTER.json`

- [ ] 读取 `HOUSE_BASE_MANIFEST.json`，核对基础版 SHA256 与 B0、厨房冻结清单。
- [ ] 固定共同房间矩形 `R-CLOAK=[9050,4650,11300,6300]` mm、上下标高 `z=.45/3.25` m；固定洁具包络：台盆 `[9419.5,4750.1,10419.5,5250.1]`、WC `[9693.4,5770.7,10193.4,6370.7]`、湿区 `[10473.8,4749.9,11297,6297]`。
- [ ] 记录不可拆黑墙清单和白色可调整段；断言两个选项只创建 `SECONDARY_BATH_OPTION_*` 集合，不隐藏或修改基础对象。

### Task 2: 生成方案 A（南侧推拉门）

**Files:**
- Modify: `projects/c_type_home/design/secondary_bath_options/build_options.py`
- Create: `projects/c_type_home/design/secondary_bath_options/OPTION_A_SLIDING.blend`
- Create: `projects/c_type_home/design/secondary_bath_options/OPTION_A_MANIFEST.json`

- [ ] 在南侧 y=4.45–4.65 m 建立可调整隔断，保留约850 mm门洞和门套上墙；不覆盖黑墙。
- [ ] 建立单扇表面推拉门，门扇在南侧停车，带上轨、止口、门套和墙端收口；门扇不扫过台盆、WC、湿区。
- [ ] 将入口、室内、俯视三个相机写入 manifest，记录方案假设“停车墙长度/走廊净宽需现场复尺”。

### Task 3: 生成方案 B（南侧内开平开门）

**Files:**
- Modify: `projects/c_type_home/design/secondary_bath_options/build_options.py`
- Create: `projects/c_type_home/design/secondary_bath_options/OPTION_B_INWARD_SWING.blend`
- Create: `projects/c_type_home/design/secondary_bath_options/OPTION_B_MANIFEST.json`

- [ ] 使用与 A 相同的南侧隔断和850 mm门洞。
- [ ] 创建向内开启的单扇门，铰链放在避开台盆/WC/湿区入口的一侧，显示门套、门上墙、侧墙和90°开启位置。
- [ ] 计算门扇扫掠包络与洁具净空相交；若相交，manifest 标记 `CLEARANCE_CONFLICT`，不静默移动洁具。

### Task 4: Fresh-open 校验与对比证据

**Files:**
- Create: `projects/c_type_home/design/secondary_bath_options/OPTION_QA.json`
- Create: `projects/c_type_home/design/secondary_bath_options/OPTION_COMPARISON.md`
- Create: `projects/c_type_home/design/secondary_bath_options/renders/` (filesystem-only images)

- [ ] 在干净 Blender 进程分别重开 A/B，核对基础对象快照、黑墙状态、共同洁具 bounds 和门洞尺寸。
- [ ] 对 A 检查推拉门停车区与走廊；对 B 检查门扇扫掠、洁具前净空和开启方向。
- [ ] 每个方案生成入口正面、室内、俯视三张图；图像仅落盘，manifest 记录 SHA256、分辨率和引擎。
- [ ] 用同一评价表比较：小空间可用面积、门扇冲突、私密性、施工复杂度、走廊占用、未来维修；推荐 A，但保留用户选择权。

### Task 5: 保留基础版并交付选择点

**Files:**
- Modify: `projects/c_type_home/design/secondary_bath_options/OPTION_SPEC.md`
- Create: `projects/c_type_home/design/secondary_bath_options/DELIVERY_MANIFEST.json`

- [ ] 断言基础版 SHA256 未变；A/B 仅从基础版派生。
- [ ] 写清门套/墙体/洁具均为审阅几何，设备 SKU、排水、门套厚度和墙体施工方式仍需现场复尺。
- [ ] 在交付说明中保留“尚未选择 A 或 B，不回写基础版”的状态。
