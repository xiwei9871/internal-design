# 传输预算、128 MB 与可续跑队列

## 分层诊断

| 证据位置 | 意味着什么 | 对应行动 |
|---|---|---|
| Codex `task_complete`/聊天请求报body too large；CLI无该错误 | 对话的工具输出/图片/上下文可能累计超限 | 紧凑续接、停止往旧聊天加原图、迁移既有heartbeat；不重发旧历史 |
| 单job CLI/API edit 413或明确payload错误 | 本次multipart/base64输入不合规 | 查输入图真实字节/数量、mask与prompt；制作新派生reference而不改原图 |
| 浏览器慢/内存高，但API编辑成功 | 网页展示下载问题 | thumbnail+lazy load+点击原图；不是修改模型或API限额 |

报错中的128 MB是该请求路径的实际限制，不把它当所有API统一上限。不猜“图片太大”就重装Image2。只查该job与相关日志的短错误、请求ID、状态和输入meta；不要为找错误输出几MB一行的全局state或聊天JSONL。必要的聊天日志统计在本地脚本逐行计算，输出汇总。

## 字节和上下文控制

- 不输出base64/data URL；不用Python/JS把全图读成字符串再`text()`。图像只从有限的派生JPEG用image工具交给模型。
- 预估字节=文件总bytes × 4/3 + prompt UTF-8 + header余量。24 MiB是默认保守编辑预算，可按具体provider调整并在contract记录。大reference先裁相关部位、缩尺寸；不降输出质量、不毁原reference、不静默压几何。
- 评审JPEG单sheet默认长边1600、quality82；不强制读取整房15张原图。相机/家具细部使用局部crop。小JPEG是传输用，不是新的权威。
- token窗口与HTTP字节是不同约束；摘要可减少文字上下文，但无法保证已带入图片被移除；降低视觉detail也未必降低传输字节。
- 超限后以小handoff记录source hash、branch、jobs/flags/status、进程与retry ledger路径、下一步和授权。不要复制旧完整history，自动化不能持续唤醒不可用旧thread。创建新chat需要用户明确要求；已在轻chat则直接继续。

## 任务恢复

每job保存 `job_id, room_id, view_id, level, input_paths, roles, input_hashes, prompt_path/hash, output_path, source_revision, camera_revision, status, attempts, retry_count, error_class, native_size, visual_status`。成功文件存在先验证decode后cache，meta缺失重建为`CACHE_PENDING_QA`；不能因缺meta重跑。失败meta记录剩余retry，不用删除它来让队列再次尝试。

policy是最新用户授权范围，不是旧脚本默认值。单一coordinator，用OS-lock而不是仅PID；僵尸非运行，PID还可能复用。重启只调度未完成且获准任务。串行起步，队列并发调高必须有provider与资源证据；不要混Blender队列和重复AI进程。长期任务写原子进度，小JSON与gallery更新分离。

401/403停止授权请求，不retry；400/413/422停止请求验证；429遵循返回退避并暂停批量，不能靠重启绕过限流；5xx/timeout最多一次logicalretry。记录CLI内部transport attempt与外层retry的乘积风险，不允许嵌套的2×2×2重试。重试以新log保留原失败，覆盖失败meta需保留attempt ledger。设置单次timeout、整队列time/cost预算及停止条件。

记录中 `GENERATED`、`OPENED`、`PROPAGATION_CANDIDATE`、`HUMAN_ACCEPTED` 互不等价。正常无变化的监控保持安静；任务到人工gate停生成。
