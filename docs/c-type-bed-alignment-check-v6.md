# 次主卧床板检查（2026-10-12）

业主截图疑似床板歪斜。检查已保存的console1310_v5模型，源SHA256 3d75cbabe06a0bbace8fb95fb395bcc7f645ed5d26d6fed2d1fb094f0881f63a保持，16个保护源保持。没有保存或修改模型，不涵盖直播Blender未保存修改。

对象旋转为0不能排除网格内部倾斜；最初点云PCA角度不能作为板面倾斜依据，最初空白相机图排除。重新生成三个正交灰模并打开审阅，三个主要水平面拟合倾角0.0022–0.0030度，选中面点高差0.5–0.9mm；未发现明显整体床板倾斜。顶视床框对齐、侧视承托板水平、床尾正视左右标高一致。布品不对称、后仰床头、斜向24mm广角导致视觉倾斜，图册2011-1.8参考已打开。结论retain_candidate；不为迎合透视截图旋转床。

证据design/bed_alignment_v6/diagnosis/{top,side,foot}.png与measurements.json；页面http://127.0.0.1:5188/bed_alignment_check_v6/review_gallery.html。二进制保持本地，0Image2。
