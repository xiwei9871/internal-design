# 学道街 44 号 · 室内设计项目

从原始 PNG 平面图出发的 AI 辅助装修设计：平面功能优化 → CAD 底模 → Blender 同模渲染 → gpt-image-2 效果图，确认后输出施工图。

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
- `scheme_a_v12`：当前最新效果图——以 A11 素模为底的 image-edit，`viewpoint_layout_audit_v2_edit.md` 是验收记录

## 重建管线

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

**效果图阶段已收口（2026-09-14）**：A12 七张效果图业主确认通过，见 `scheme_a_v12/viewpoint_layout_audit_v2_edit.md` 收口节。

## 下一步

**施工图阶段**：从 FCStd 底模经 ezdxf 出 DXF。图纸清单与门禁见 `interior-construction-docs` skill，图层/图框约定见 `architectural-dxf-drawing` skill。开工前需与业主确认：拆改范围、电气点位、天花/风口、柜体展开深度等新增信息（底模不含机电点位）。
