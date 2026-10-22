# DEVIN_PASCAL_CAPABILITY — 世纪欣园 PoC

> 2026-09-29 | 结果:**A. MCP_NATIVE**

## 环境

- node v24.14.1 / npm 11.11.0 ✓(要求 ≥22.13)
- `npm i -g @pascal-app/cli` → pascal 1.0.3 ✓
- `devin mcp add pascal -- pascal mcp connect` → `.devin/mcp_config.local.json`

## 判定:A. MCP_NATIVE

`pascal mcp connect` 是标准 stdio MCP server,Devin 通过 `devin mcp add` 直接挂载,
`mcp_list_tools` 返回 **54 个工具**(get_scene/create_wall/add_door/add_window/
place_item/set_zone/measure/verify_scene/check_collisions/apply_patch/undo/redo/
export_json/export_glb/save_scene/create_project…)。
无需改 Pascal 源码、无需 CLI/JSON 绕行。

## 并行说明(供 Codex 对照)

官方也支持 `pascal mcp setup codex`,但本 PoC 全程走 Devin 原生 MCP,未使用 Codex 插件。

## 补充验证(2026-09-29 第二轮)

- `pascal editor --no-open` → **PASS**:editor 运行于 http://pascal.localhost:57071,MCP port 57075
- 项目持久化 ✓:`~/.pascal/data/pascal.db`,`pascal projects` 列出 `c-type-home-pascal-poc`(36 nodes)
- 编辑器 URL:`http://pascal.localhost:57071/editor/c-type-home-pascal-poc`
- skills 安装:`npx skills add pascalorg/editor --skill pascal-3d --skill furniture-fit` → `.agents/skills/` ✓
