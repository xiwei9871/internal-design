# 专用效果图技能验证 — 2026-10-09

技能：`.codex/skills/archviz-interior-workflow`，正常自动发现；显式调用 `$archviz-interior-workflow`。本次未生成新AI图、未启动Blender、未重新唤醒渲染队列。

## 自动与实际命令验证

- skill-creator `quick_validate.py`：PASS。验证器所需PyYAML放临时目录，仅用于检查，没有修改Image2或项目Python依赖。
- 工具4个行为测试：PASS。编码开销导致超预算拒绝；快照检出改变/缺失；联系表保留输入且拒绝覆盖；preflight不序列化像素或输出prompt内容。
- 既有Faithful流程6个测试：PASS。
- 实际preflight读取当前厨房图+几何图，原图2,667,830 bytes，估算3,625,992 bytes，在24MiB本地预算内。仅stat，未读取像素。
- 临时隔离目录实际运行snapshot、verify、sheet均exit0；1920×1080测试输入生成1200×365 JPEG 14,283 bytes，输入不变。
- 7个Markdown文件内部reference链接全存在；没有未完成scaffold标记。`git diff --check`通过。

## 桌面情景审查（没有真实API调用，不是独立代理盲测）

| 请求情景 | 技能中的对应决策 |
|---|---|
| 只规划客厅，不出图 | scope不授权生成；读取合同、机位/reference和风险，输出计划 |
| 已认可Faithful，续全屋 | 读取enabled policy、cache、每级hero gate与锁；保留成功图、只做缺图 |
| 旧chat128MB，CLI没有413 | 诊断聊天与编辑请求分层；轻续接小manifest，不重发历史，不安装Image2 |
| 三风格差不多，要求调整 | 一view局部ledger，各自参考；未生成新图前只能称prompt规则未验证 |
| 实物灶外观错误，用户SKU未知 | 查询真实官方多角度机制；不采用参考尺寸或T形烟道改动冻结柜体 |
| 已批准28mm镜头，建议统一35mm | approved register优先，保持确认机位；实际preview查裁切而非机械套值 |
| 小房间只要3张 | 用途最小集合，不强制5张或15空间 |
| 细节图变主视角 | REJECT_CAMERA_DRIFT；局部appearance参考或减少完整hero，保留原图 |
| 503之后运行cache恢复 | 一次logicalretry留失败证据，锁控单实例；失败meta不因重启重发 |

限制：此版本是基于真实项目证据的工作流固化，并通过工具与情景检查。未来Designer/Creative显著差异仍需实际小样和人审；技能不能保证AI严格保留几何，也无法改变供应商HTTP限额或修复已超限的旧聊天。新增可靠证据后按窄范围更新。
