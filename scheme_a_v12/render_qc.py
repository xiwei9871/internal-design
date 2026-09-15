"""效果图几何漂移 QC：对比 CAD 锁定素模与 image2 edit 图的边缘结构。

参考图用 workbench 平涂渲染（边缘=纯几何边界，无材质纹理），edit 图提取强边缘。
指标（edit 分辨率 1509×1042 下的 px）：
- recall: 素模几何边缘在 edit 图 TAU 内仍有边缘的比例（低=结构被改）
- chamfer: 素模边缘到 edit 边缘的平均距离
- 小连通域(<MINCC 像素)作为噪点剔除

用法: render_qc.py [key ...]   默认跑全部 7 视角，输出 qc_report.json + 叠加图
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, label, sobel

ROOT = Path(__file__).resolve().parent
EDIT = ROOT / "renders"
QC = ROOT / "qc"
KEYS = ["living", "kitchen", "master", "child", "elder", "main_bath", "secondary_bath"]
TAU = 8.0       # px：边缘匹配容差
PCT = 93        # 梯度前 7% 才算结构边缘
MINCC = 400     # 连通域最小像素数


def edges(img: np.ndarray) -> np.ndarray:
    g = img.astype(np.float32).mean(axis=2)
    mag = np.hypot(sobel(g, 0), sobel(g, 1))
    m = mag > np.percentile(mag, PCT)
    lbl, n = label(m)
    if n:
        sizes = np.bincount(lbl.ravel())
        m &= sizes[lbl] >= MINCC  # 剔小连通域噪点
    return m


def score(base_path: Path, edit_path: Path, key: str) -> dict:
    b = Image.open(base_path).convert("RGB")
    e = Image.open(edit_path).convert("RGB")
    if b.size != e.size:
        b = b.resize(e.size, Image.LANCZOS)
    bn, en = edges(np.asarray(b)), edges(np.asarray(e))

    dt_e = distance_transform_edt(~en)
    recall = float((dt_e[bn] <= TAU).mean())
    cham = float(dt_e[bn].mean())

    ov = np.full((*bn.shape, 3), 255, np.uint8)
    ov[bn & ~en] = [220, 40, 40]   # 红=素模边缘丢失
    ov[en & ~bn] = [60, 170, 60]   # 绿=edit 新增细节
    ov[bn & en] = [30, 30, 30]     # 黑=重合
    Image.fromarray(ov).save(QC / f"{key}_qc_overlay.png")
    return {"key": key, "recall": round(recall, 3), "chamfer_px": round(cham, 2),
            "base_edges": int(bn.sum()), "edit_edges": int(en.sum())}


def main() -> None:
    QC.mkdir(exist_ok=True)
    keys = sys.argv[1:] or KEYS
    rows = [score(QC / f"base_wb_{k}.png", EDIT / f"{k}_image2_edit.png", k) for k in keys]
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    (QC / "qc_report.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
