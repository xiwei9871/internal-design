# 合同、验收与交付

## 最小持久合同

项目保存一个小render contract（沿用项目已有结构）：

```json
{
  "source": {"path": "/absolute/source.blend", "revision": "approved-revision", "sha256": "from-file"},
  "camera_register": "/absolute/camera-register.json",
  "reference_register": "/absolute/reference-register.json",
  "enabled_levels": ["A_faithful"],
  "target_jobs_manifest": "/absolute/jobs.json",
  "output_root": "/absolute/new-run",
  "input_budget_bytes": 25165824,
  "retry_limit_logical": 1,
  "stop_at": "HUMAN_REVIEW",
  "source_writeback": false
}
```

示例路径/版本/哈希须替换为真实值，未填写不能当执行合同。按实际决定view数量，不固定15房×5张；在有意复用或缺room时解释计数。

## 每图验收

下表用于Faithful/Designer的锁定主体。Creative按授权的新概念验收：设计是否有启发、构成/动线/尺度是否合理、图像是否可信；不因授权改变家具或布局标drift，但未授权假定的现场事实须标明。Creative始终INSPIRATION_ONLY，不替代模型真值。

| 轴 | 检查 | 不合格分类 |
|---|---|---|
| Camera | 原crop/FOV/verticals、可见锚点、遮挡一致；细节仍是细节 | REJECT_CAMERA_DRIFT |
| Architecture | 门窗、墙、柱、天花、标高、台阶/玻璃对应模型 | REJECT_ARCHITECTURE_DRIFT |
| Furniture/fixture | 数量、位置/包络、椅背/躺椅/软布、镜型、gas设备机制 | REJECT_FURNITURE_OR_FIXTURE_DRIFT |
| Continuity | 同room variant的柜缝、材质分配、支撑系统一致 | REVIEW_CONTINUITY |
| Photo | 接触阴影、纹理尺度、白/暗细节、光向、窗曝光/反射 | REVIEW_LOOKDEV |
| Style | 已指定ledger真的改变、无标签能指出差异 | STYLE_DISTINCTION_UNVERIFIED |

首次small sheet检查全图，疑点打开局部crop或原图。不可仅“看过一张hero”就称全房15张已验收。地图/数值锚点优先；边缘recall/chamfer用于排序与漂移定位，不能提供尺寸正确认证。贴图造成新边缘也不等于几何漂移。

先按模式判断：Designer允许新增软装，Creative允许概念重构。Faithful摄影风格不满意用表现层更改；结构/取景错先确认底模和相机，若底图正确则加强当前视角信号或裁掉hero构图，不用Creative掩盖。一次只纠正一个主因，保留before/after。超过自动重试限或规则矛盾则返回人工判断。

## 交付摘要

展示 gallery默认启用方向，其他旧方向可切换但注明历史。提供实际生成/有效decode/已打开/人工接受四种计数；native尺寸、request尺寸、source hashes、warnings、job retry使用、artifact路径。失败图仍可供审查但不标PASS。完成目标候选集合可写GENERATED_COMPLETE；只有用户确认才标HUMAN_ACCEPTED，不“晋升”为模型。

保存可编辑Presentation和可复现脚本（若任务需要），不把源几何改动混进渲染脚本。原图/大型二进制、目录照片、纹理、日志和cache只留磁盘，Git只审source/config/decision记录。
