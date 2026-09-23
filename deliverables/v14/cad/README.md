# v14 设计协调图册

10张A2横向图纸，真实纸空间视口，模型单位mm、1:1。PDF按100%打印。
A101/A102/A201/A301/A302/A303/A401/A501：1:50；A402节点示意：1:25；A403服务墙：1:20。
合订PDF与单页PDF均为594×420mm；PNG仅为预览。图内尺寸来自A7标定和v14共享设计，非现场测量。

已修复立面/节点矩形y+h、吊顶标高、缺失线型、次卫暗藏推拉门、儿童矮柜及服务墙参数不一致。
A101采用家具块、室内设备符号、定位尺寸链和编号索引。电气/给排水为编号点位，图侧及CSV列出定位坐标；原点对应源图(200,1337)，X向东、Y向北。

本套为设计协调版：柜板/五金/开孔、门套及结构洞口、暗藏门口袋、设备SKU/散热/检修、施工节点及机电回路/管径/坡度仍待现场与厂家确认。无新增拆改范围，未提供可直接下单或施工的最终深化承诺。
窗边学习区低书柜H1100，衣柜H2300，服务墙H2400，干区吊顶2600/湿区2400/墙高2700均沿用共享设计中的假设状态。
各页audit.json及manifest.json记录共享源SHA256；已读回DXF验证audit errors=0、fixes=0，无未定义线型。

重建：`rtk proxy .venv/bin/python construction/build_all.py`
验证：`rtk proxy .venv/bin/python -m unittest discover -s tests -p 'test_cad*.py'`
依赖：ezdxf、matplotlib、shapely、Pillow、pymupdf；字体/Library/Fonts/Arial Unicode.ttf。
旧construction内的DXF/PNG及A13未覆盖。
