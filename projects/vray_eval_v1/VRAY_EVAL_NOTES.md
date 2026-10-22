# V-Ray for Blender 评估记录 (2026-10-15)

## 环境
- V-Ray for Blender 7.40.02 (V-Ray 7.40.05 engine, arm64) + Blender 5.2.1 LTS, Apple M4, CPU 渲染
- 许可: Chaos 云许可, ULA 已登录; 安装于 `~/Library/Application Support/Chaos/V-Ray for Blender 5.2`

## 硬性结论
1. **`blender --background` 拿不到云许可** — headless 服务器带 `-headlessMode`，只会去 `localhost:30304` 找本地许可服务器 → 报 61 refused。脚本化渲染必须用 **GUI 方式** (`Blender file.blend --python x.py`)。
2. 脚本里渲染前必须等 `ZMQ.isRunning()`，否则第一帧 `Empty renderer object` 出空图。
3. `progressive_maxTime` 单位是**分钟**。
4. 枚举参数必须传字符串 (`'1'`, `'3'`)。

## 场景转换坑（Cycles 场景 → V-Ray）
| Cycles 写法 | V-Ray 结果 | 修法 |
|---|---|---|
| World: Light Path 混两个 Background（相机射线暗背景+亮天空 GI） | 只转换第一个 → 相机背景错/过曝 | 换单一天空节点 |
| `adaptation_only=2`（只映射不做 gamma） + AgX | 双重色调映射 → 灰白一片 | `adaptation_only='0'` 交给 V-Ray 完整色彩映射 |
| 无物理相机 | 曝光失控 | `use_physical=True` + `CameraPhysical.exposure='2'` + `exposure_value=12` |
| Brick Texture 木地板 | 无对应节点 → 摊平成纯色 | 换真实 PBR 贴图 (TexImage+Generated → UVWGenProjection 自动转换) |
| ShaderNodeTexImage/Generated 坐标 | 正常转换 ✓ | — |
| 面光源 W 值 | 正常转换 ✓ | — |
| 降噪通道 | `VRayNodeRenderChannelDenoiser` 需接入 `VRayNodeRenderChannels` 的专用 `Denoiser` 输入 + `VRayNodeWorldOutput`；且会报 "No render element plugin for type 144" | 暂用 progressive 采样代替 |

## 对比结论（living 视角, 2500×1727）
- `living_vray_full4.png` (V-Ray, ~5min) vs `scheme_a_v14/renders/living.png` (Cycles, 128sp)
- V-Ray：真实木纹地板、物理曝光干净、软阴影/GI 平滑、TV 屏反射正确
- Cycles 基线：整体色调更暖、程序化地板更规整；两者构图/曝光相当
- 判定：此场景（简单材质）下 **V-Ray ≈ Cycles**，谈不上明显更好；V-Ray 真正优势在未用到的功能（VFB 后期、LightMix、降噪、散布、复杂材质）
- 提速空间：M4 只能 CPU（V-Ray GPU 走 CUDA）；如果想追原设计师效果图质感，差距主要在**材质资产**不在渲染器

## 可复用脚本
`vray_render_a14.py` — GUI 方式 + ZMQ 就绪等待 + 物理相机 EV + 完整色彩映射 + progressive 限时
