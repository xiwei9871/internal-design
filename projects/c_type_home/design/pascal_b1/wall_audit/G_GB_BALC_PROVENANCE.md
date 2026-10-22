# G-GB-BALC PROVENANCE — 正确提取链对照样本

中间客房 → 北阳台推拉门。整条链每一环都可追溯：

```
MASTER physical objects          (S-S.WALL linework, canonical mm)
  Line081  x9900–10400 @y10900   门位西端墙线
  Line088  x10400 @y10900–11100  西垛
  Line089  x12400 @y10900–11100  东垛
  Line090  x12400–12900 @y10900  门位东端墙线
  Line094  x10400–12400 @y10900  门洞跨线
        │  App::PropertyLinkListHidden
        ▼
WINDOW_REF_G_GB_BALC             (MASTER_V2 内语义引用, union bbox resolved 5/5)
        ▼
FINAL_WINDOW_REGISTER_95ab90e    G-GB-BALC: GLASS_DOOR, span 2000,
                                 opening_rect [10400,10700,12400,10900],
                                 host W-INT-Y10800, CONFIRMED
        ▼
canonical_arch_v2 → Pascal       door_v2_0057 (glass_door, w=2.0m, MAPPED)
                                 + W-INT-Y10800#G-GB-BALC.0/.1 侧 PARAPET
                                 (x7900–10400 / x12400–13000 @y10700–10900)
```

为什么它对：开口有**显式语义引用 + register 里显式 opening_rect/host**，不依赖"从线稿猜墙"。两侧墙垛也是 register 显式登记的 PARAPET。

对照：墙体没有等价语义引用 —— S-S.WALL 的 209 条 Line/Polyline 必须经解释器配对成墙，解释器的输出（register）与 master 线稿之间存在未验证的偏移和漏配。
