# A1 — 输入能力审查（C 型资料）

| 文件 | SHA256(12) | 实体构成 | 尺寸表达 | cadvec 适配性 |
|---|---|---|---|---|
| `cad/measured_working.dxf` | `3711c47c1172` | LINE 223, TEXT 40, DIMENSION 18, LWPOLYLINE 15, CIRCLE 18, HATCH 6, MTEXT 6, ARC 3, INSERT 13 | **18 个原生 DIMENSION（ordinate 型，S-COLUMN 层，无文字覆写）** | ✅ 可读，dimsx 约束路径生效 |
| `source/世纪欣园FF.dwg` | `f01a9bb5de96` | DWG 二进制（AC1018），ezdxf 不可读 | — | ❌ 需转换（measured_working 即其转换产物） |
| `cad/C型_原始户型数字化基准图.dxf` | `7285527be00a` | TEXT 114, LWPOLYLINE 84, LINE 82 | **39 个数字 TEXT + 82 条 A-DIMS LINE，但无 45° 起止符号、无原生 DIMENSION** | ⚠️ 几何可读（17 墙/7 洞口），尺寸约束不可启动 → `INSUFFICIENT_DIM_EVIDENCE` |
| `source/source_plan_original.jpg` | `0125ad6c1695` | 位图 1279×1986 | 印刷标注（位图） | ❌ cadvec 不支持位图（走 analyze.py 路线，本轮未测） |
| `C型_原始户型数字化基准模型.FCStd` | — | FreeCAD 参数化模型 | 无标注实体 | ❌ 非 DXF，不适用 |

## 关键结论

1. **基准图的 39 条尺寸标注对 cadvec 不可机读**：A-DIMS 层尺寸线只有尺寸线+尺寸界线，
   缺国标 45° 起止符号，cadvec 的 tick 检测返回 0 → 尺寸约束完全不启动。这 39 个数字在审计中
   记为 `UNRESOLVED`（人工仍可读，工具无法绑定到几何段）。
2. **measured_working.dxf 的 18 个 DIMENSION 为 ordinate 型**，`get_measurement()` 返回的是
   轴坐标值；其中近水平/竖直者（8+5 条）被 cadvec 正确纳入最小二乘方程且全部自洽，
   其余斜向/短程的无法验证（defpoint 间距≠标注值），记 `UNRESOLVED`。
3. **循环证明风险提示**：`C型_原始户型数字化基准图.dxf`、`measured_working.dxf`、
   `geometry_v05.json` 都源自同一 DWG/同一批测绘整理。cadvec 对它们的一致性检查
   **只能证明"同一数字化结果自洽"，不能证明与原图/现场一致**。开发商原图
   `source_plan_original.jpg`（位图）才是独立来源，需 analyze.py 路线或人工核对。
4. `measured_working.dxf` 无 LFS 问题，可直接 ezdxf 解析。
