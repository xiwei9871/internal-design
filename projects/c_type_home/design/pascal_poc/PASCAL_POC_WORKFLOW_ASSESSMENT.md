# PASCAL_POC_WORKFLOW_ASSESSMENT

## 验证结论(逐项)

1. **Devin 能否稳定操作 Pascal?** 能 — `devin mcp add pascal -- pascal mcp connect`,54 工具一次挂载成功,全程无断连。
2. **MCP 是否真正可用?** 是,MCP_NATIVE;scene 实时读写、save/undo/redo/export 全部经 MCP。
3. **2D→Pascal fidelity?** 家具中心 max 0.6mm,开口中心 ≤6mm(来自 t 参数化舍入),宽度精确。无自动重排。
4. **semantic scene 是否比 Blender B1 更好审?** 语义层显著更好:zone/door/window/item 是原生类型,describe_node 直接给 ancestry+参数,measure 即取;这些在 Blender 里是自造 custom props。人审交互(2D/3D 切换、选物改尺)编辑器原生支持。渲染质量则靠 Blender。
5. **Pascal→Blender 可靠?** 是 — pascal_blender-0.2.1 插件(手动 install zip + enable)。墙=参数化对象(pascal_params+start/end/thickness/height),门窗 boolean 洞口随移动更新,家具 GLB 实例,3 zone collections,`pascal_source.json` 全文存 Text datablock(零数据丢失,官方 CI 断言 deep-equal)。
6. **是否值得整体迁移?** 值得做下一层 PoC(全屋 semantic scene + B1 审查轨),但不宜一次替换:①catalog 资产尺寸与实测不符,需要 custom asset pipeline;②无 IFC/FreeCAD 直连,canonical→Pascal 转换脚本仍需自研(即本 PoC 的 mapping 层);③误层/飘窗等自研概念要靠 node metadata 带过去。
7. **预计减少的自研脚本?** room classification、window/door 语义、furniture-fit(check_collisions 内置,rotation-aware)、measure、undo、scene diff、editor 审查 UI、GLB/export —— 约等于 b1_extract 的语义层 + b1_build 的大部分。仍需保留:canonical→Pascal 转换、fidelity 对照、human-edit 同步规则。
8. **新风险?** ①catalog 尺寸名义化(碰撞检测基于名义 bbox,不是实测 footprint);②host wall 约束:门窗必须挂在墙上,异形开口(玻璃隔断、无墙洞口)要用"整墙段+满窗"近似;③单 agent client 限制(README:一个 MCP client 共享 scene state);④MCP 本地服务与编辑器 runtime 分离 —— 已实测 `pascal editor` 一键起 editor+MCP 双端口,人审入口 http://pascal.localhost:57071/editor/c-type-home-pascal-poc;⑤无 slab 时 verify_scene 报 issue(可接受但要在报告中解释)。

## 建议的后续链(待你批准,本次不执行)

```
PRE_BLENDER_MASTER_V2 → PASCAL_B1_SCENE_V1 → Human spatial review
→ pascal-blender → B2 Design Development
```

`PASCAL_POC = PASS`

确认项:MCP_NATIVE(Devin 直挂)、editor GUI 可启动、project 持久化、
furniture-fit candidate 通道工作正常、catalog 名义尺寸是唯一实质限制。
