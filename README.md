# 学道街 44 号 · 室内设计项目

从原始 PNG 平面图出发的室内设计项目。A14 将平面、CAD、FreeCAD 和 Blender 统一到同一份设计数据，输出可追溯的物理渲染与设计协调图纸。

**本轮成果（2026-09-18）：** [七空间前后对比](deliverables/v14/index.html)、[10 页 A2 图册](deliverables/v14/cad/学道街44号_v14_设计协调图册_A2.pdf)、[更新与待核实事项](deliverables/v14/更新说明.md)。A14 为待业主复核的新版本，保留 A12 已确认记录和 A13 原成果。

## 最终方法与工作流（A14）

1. **单一设计契约**：原始 PNG 标定（1px = 9.82mm）→ `design/approved_v14.json`，集中存放对象、尺寸、朝向与 provenance；已确认值与待核实值显式分列。`design_model.py` 是 FreeCAD / Blender / ezdxf 共用的读取与坐标转换层，任何一方不私改几何。
2. **三条生产线同源消费**：
   - `scheme_a_v14/build_cad.py` → FreeCAD 包络底模（`cad/方案A14_统一设计底模.FCStd` + `approved_envelopes.obj`）
   - `construction/build_all.py` + `paper_export.py` → 10 张 DXF（A101–A501）→ 毫米制纸空间、固定比例视口、黑白 PDF 图册；点位另附 CSV
   - `scheme_a_v14/build_scene.py` → Blender 同模场景（材质、家具、服务墙全部参数化，不依赖 AI 生成结构）
3. **渲染**：`render_views.py` 以 7 个锁定相机 Cycles 输出 2500×1727 主图 + 多通道 EXR（深度/法线/对象/材质遮罩）。EXR 为可再生成中间产物，不入库；哈希记入 release_manifest 供追溯。
4. **验证**：`validate.py` 查相机遮挡/对象落地，`qc.py` 查画幅与结构双向误差，`tests/` 37 项 unittest 回归几何、出图、相机与发布门禁。
5. **发布**：`publish.py` 先核对 design/scene/PNG/CAD 哈希一致才组装 `deliverables/v14`（对比浏览页 + A2 图册 + manifest + 更新说明）；混用旧版输出时拒绝发布。
6. **AI 管线结论**：A13 验证了"真实家具底图 → image-edit 候选 → QC 打分选优"管线，但因跨图纸一致性差、选优不代表验收，A14 未采用 AI 候选（`ai_generation_used: false`），探索产物已清理。

## 权威依据（SOURCE_PRIORITY.md）

- 户型布局以**原始 PNG** 为准（`dwg_import/source_plan.png`），标定 `1px = 9.82mm`。
- DWG/DXF（`dwg_import/xuedaojie44.dxf`）仅作结构、尺寸核查；其"茶室/书房"标签页与 PNG 不符，不直接套用。
- 图中黑色区域按可用室内空间处理。

## 目录

- `v1` / `png_layout` / `png_rebuild`：PNG 描图 → SVG 平面 + Blender blockout（早期探索）
- `dwg_import`：DWG→DXF 转换与 CAD 核对页
- `scheme_a_v1`–`v7`：方案 A 功能平面迭代（v7 为已确认功能布局，`scheme_a_geometry.json` 是几何数据源）
- `scheme_a_v8`–`v9`：原木简约 Blender 场景
- `scheme_a_v10`：首轮 gpt-image-2 效果图（纯示意，已废弃）
- `scheme_a_v11`：**CAD-first 底模**——`cad/方案A11_CAD底模.FCStd` + 分组 OBJ + `方案A11_CAD同模渲染.blend`，7 个锁定相机
- `scheme_a_v12`：已确认的历史效果图，`viewpoint_layout_audit_v2_edit.md` 是验收记录
- `scheme_a_v13`：真实家具底图与在版效果图；AI 候选探索产物已于 2026-09-23 清理
- `design/approved_v14.json` / `design_model.py`：A14 共享对象、尺寸、朝向及参数依据；名称中的 approved 指继承确认的布局，文件内仍明确列出设计假设及待核实值
- `scheme_a_v14`：FreeCAD 包络模型、Blender 参数化场景、七视角 PNG、结构通道图、检查和发布脚本（多层 EXR 为中间产物，不入库，重渲可再生成）
- `deliverables/v14`：本轮可浏览、打印的复核成果；CAD 单页含 DXF/PDF/PNG，点位另附 CSV
- `tests`：几何、出图、相机、版本和候选发布回归

## A14 重建

在项目根目录执行。实际验证环境：FreeCAD 本机安装、Blender 5.2.1、Python 3.14；Python 依赖见 `scheme_a_v14/requirements.txt`。CAD 字体使用本机 `/Library/Fonts/Arial Unicode.ttf`。

```bash
rtk proxy /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd -c 'p="/Users/xiwei/interior_design/scheme_a_v14/build_cad.py"; exec(compile(open(p).read(),p,"exec"),{"__file__":p,"__name__":"__main__"})'
rtk proxy .venv/bin/python construction/build_all.py
rtk proxy /Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python scheme_a_v14/build_scene.py
rtk proxy /Applications/Blender.app/Contents/MacOS/Blender --background scheme_a_v14/方案A14_同模精细渲染.blend --python-exit-code 1 --python scheme_a_v14/render_views.py -- living kitchen master child elder main_bath secondary_bath
rtk proxy .venv/bin/python -m unittest discover -s tests -v
rtk proxy .venv/bin/python scheme_a_v14/publish.py
```

发布脚本检查共享数据与场景生成器哈希、七张主图哈希、CAD 实际纸张/单位/比例；混用旧版输出时拒绝发布。主卫机位为本轮有记录的修正，其余六视角沿用 A11；主卫使用并列展示，避免误导为对齐比较。自动检查不替代现场复尺、产品确认与人工视觉验收。

## 历史 A11/A12 重建管线

```bash
# 1. FreeCAD 底模 + OBJ（freecadcmd 下 __name__ 不是 __main__，需显式 exec）
cd scheme_a_v11/cad && /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd -c "
src = open('build_freecad_model.py').read()
g = {'__file__': '$(pwd)/build_freecad_model.py', '__name__': '__main__'}
exec(compile(src, 'build_freecad_model.py', 'exec'), g)"

# 2. Blender 同模场景 + 7 视角素模
cd scheme_a_v11 && blender --background --python build_blender_from_cad.py

# 3. Image2 效果图编辑（读 ~/.env 的 CODEX_API_URL / CODEX_API_KEY，模型 gpt-image-2）
cd scheme_a_v12 && python3 run_image2_edits.py   # 全量 7 张；单张可用模块内 edit(key, env)

# 4. 预览页
cd scheme_a_v12 && python3 make_preview.py
```

## 已确认设计要点

- 服务墙三列（靠厨房→走廊）：薄型冰箱 840W → 蒸箱/烤箱 595W → 洗烘叠放 600W；墙总长 2298mm
- 主卧：床头板在床右短边；窗边弹性台 1200×450；衣帽区实体墙+哑光木门
- 儿童房：房内仅床/衣柜/床头柜；窗边区 1800×600 书桌 + 300 深低书柜
- 主卫：1500×700 浴缸（正式配置）+ 横向玻璃干湿分离；次卫：内嵌推拉门、无浴缸
- 坐便器：一体式，水箱贴左墙、盆体垂直墙体向 +X

## 配套 Skills（`~/.agents/skills/`，Codex 与 Devin 共用）

| Skill | 阶段 |
|---|---|
| `floorplan-reconstruction` | PNG/DWG → 标定几何 JSON（已完成，见 scheme_a_v7） |
| `space-planning` | 功能建议→尺寸查证→多方案（v1–v7 已走完） |
| `residential-interior-design` | 风格/材质/柜体/设备判断（v8–v9） |
| `architectural-render-qc` | 锁定相机 + 底图核对 + image-edit 验收（v10–v12 踩坑全集） |
| `architectural-dxf-drawing` | ezdxf 图层/线型/图纸序列——施工图阶段用 |
| `interior-construction-docs` | 施工图清单与尺寸纪律——效果图确认后启用 |

## 当前状态

**A12 历史收口（2026-09-14）**：七张效果图业主确认通过，见 `scheme_a_v12/viewpoint_layout_audit_v2_edit.md`。**A14 改进版（2026-09-18）**：统一数据与出图管线，生成七张 2500×1727 物理渲染及十张 A2 设计协调图；新表现版本待业主复核。局部材质增强试验接口返回 HTTP 400，未采用 AI 候选。

## 下一步

**施工深化所需输入**：厨房窗台与台面关系、门洞/门袋现场条件、设备 SKU、机电回路/管径/坡度、材料节点和柜体生产尺寸仍需核实；详见 A14 更新说明。当前图册为设计协调版，不能直接据此下单加工。
