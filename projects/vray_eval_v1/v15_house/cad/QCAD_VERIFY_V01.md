# QCAD_VERIFY_V01 — A102/A103 出图验证 (2026-10-23)

工具: QCAD Professional 3.33.1 (试用版, 界面人工查看) · LibreCAD 2.2.1.5
出图脚本: `publish_dxf.py` (只改出图层, 不改几何)
产物 (生成物, 不入库): `qcad_verify_v01/issue_v01/*.issue.{dxf,pdf}`

## 源文件 (未修改)

| 文件 | sha256 前10 |
|---|---|
| `A102_WALL_DIFF_POC_V3.dxf` | a3dc6631b5 |
| `A103_CONSTRUCTION_POC_V7.dxf` | 381eacb73e |

## 原图在 QCAD 中发现的问题

1. Layout1 视口在 QCAD 界面中为空 (最小测试文件同样为空) → 改为模型空间 1:50 出图。
2. `Standard` 样式 (`txt`) 的中文显示为 `??`; `HZTXT` 指向 `/System/Library/Fonts/STHeiti Medium.ttc`, 换机即失效。
3. Layout1 页面设置 420×297 (A3), 与 A1 图框和标题栏不符。
4. A103 为 R2018 (AC1032), A102 为 R2010。
5. 打开时的 handle collision 警告: ezdxf 新建空文件同样出现, QCAD 自动重分配, 非本图缺陷。

## 字体测试 (FONT_TEST.dxf, QCAD 界面人工确认)

| 写法 | QCAD | LibreCAD |
|---|---|---|
| `txt.shx` + `hztxt.shx` | 失败 `??` | 失败 |
| `gbenor.shx` + `gbcbig.shx` | 正常 | 失败 |
| `simhei.ttf` / `simsun.ttf` / `STHeiti Medium.ttc` | 正常 | 失败 |
| `noto-sans-sc.lff` / `Unicode.cxf` | 正常 | 失败 |

LibreCAD 对所有写法 (含自带 noto-sans-sc、wqy-microhei, ANSI_936 代码页, `\U+` 转义) 中文均显示 `◊`, 不作为验收工具。
选用 `gbenor.shx` + `gbcbig.shx`: QCAD 正常, 且为国内 AutoCAD/中望/浩辰标准国标字体。

## 出图版验证结果

| 项 | A103 | A102 |
|---|---|---|
| QCAD 中文无 `??` | PASS (人工) | PASS (人工) |
| 图框套住平面, 标题栏右下 | PASS (人工) | PASS (人工) |
| 图框外边实测 42050×29700 | PASS (人工) | PASS (人工) |
| DXF 版本 | R2010 AC1024 | R2010 AC1024 |
| ezdxf audit 错误 | 0 | 0 |
| 模型实体数 (源 / 出图不含 A-FRAME) | 594 / 594 | 251 / 251 |
| PDF MediaBox | 2383.9×1683.8pt = A1 | 同左 |

## 仍未验证 (保持 NOT_RUN)

- AutoCAD/天正原生打开、DIMENSION 编辑与打印 (待定装修方后)
- DWG 转换 (ODA File Converter 未安装)
- 原 `CAD_P15_FINAL_HANDOFF.md` 清单第 6 项 XDATA 抽查、第 7 项施工可读性
