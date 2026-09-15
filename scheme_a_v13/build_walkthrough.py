"""A13 漫游动画：入户→过道→餐区→客厅→主卧→窗边区 一镜到底白模预演。

相机沿已验证净空的路径匀速行进（~0.95m/s，约21s/510帧@24fps），
注视空物体前视平滑转向。先出 Workbench 低分辨率预览验证路径与构图，
再出 EEVEE 白模成片，作为视频模型的镜头/空间参考。

用法:
  blender --background <A11.blend> --python build_walkthrough.py -- [workbench|eevee]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT.parent / "scheme_a_v7" / "scheme_a_geometry.json").read_text(encoding="utf-8"))
SCALE_MM = float(DATA["metres_per_pixel"]) * 1000.0
ORIGIN_X, ORIGIN_Y = 200.0, 1337.0
FRAMES = ROOT / "walkthrough_frames"
FRAMES.mkdir(parents=True, exist_ok=True)

# 路径（源像素，已通过净空验证，净距100mm）与每点注视目标
PATH = [(1120, 715), (980, 735), (1040, 820), (1040, 1000), (960, 1060),
        (870, 1120), (855, 1250), (880, 1130), (980, 1030), (1085, 940),
        (1085, 800), (970, 735), (860, 735), (770, 735), (710, 745),
        (700, 860), (640, 870), (540, 870), (515, 1050), (545, 1180),
        (600, 1205)]
END_LOOK = (560, 1300)  # 收尾注视：窗边梳妆台/南窗

CAM_H, LOOK_H = 1550, 1350  # mm；视线接近水平，避免俯视地面
LOOKAHEAD_PX = 320  # 沿路径前视 ~3.1m，转向平滑
SPEED_MS, FPS = 0.95, 24
LENS = 24


def world(px, py, z_mm):
    return ((px - ORIGIN_X) * SCALE_MM / 1000.0,
            (ORIGIN_Y - py) * SCALE_MM / 1000.0, z_mm / 1000.0)


def look_points():
    """每个路径点的注视目标 = 路径上前视 ~3m 的位置；末段收敛到窗边梳妆台。"""
    cum = [0.0]
    for i in range(1, len(PATH)):
        cum.append(cum[-1] + math.dist(PATH[i - 1], PATH[i]))
    total = cum[-1]
    pts = []
    for i in range(len(PATH)):
        ahead = cum[i] + LOOKAHEAD_PX
        if i >= len(PATH) - 3 or ahead >= total:
            pts.append(END_LOOK)
            continue
        j = next(k for k in range(len(cum) - 1) if cum[k] <= ahead <= cum[k + 1])
        t = (ahead - cum[j]) / max(cum[j + 1] - cum[j], 1e-6)
        pts.append((PATH[j][0] + (PATH[j + 1][0] - PATH[j][0]) * t,
                    PATH[j][1] + (PATH[j + 1][1] - PATH[j][1]) * t))
    return pts


def main():
    mode = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "workbench"
    scene = bpy.context.scene

    # --- 相机 + 注视空物体 ---
    bpy.ops.object.camera_add(location=world(*PATH[0], CAM_H))
    cam = bpy.context.object
    cam.name = "Camera_Walk"
    cam.data.lens = LENS
    cam.data.sensor_width = 36
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=world(*PATH[0], LOOK_H))
    target = bpy.context.object
    target.name = "Walk_Target"
    # TRACK_TO + UP_Y：锁定世界竖直方向，DAMPED_TRACK 在注视方向翻转时会带翻相机
    con = cam.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"

    # --- 稠密关键帧：由 walk_keys.json 驱动（每~0.4m一帧，匀速+前视） ---
    # 必须 LINEAR：Bezier 自动手柄会在转角处把相机/目标甩出已审计的净空走廊
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    keys = json.loads((ROOT / "walk_keys.json").read_text())
    for k in keys:
        cam.location = world(*k["cam"], CAM_H)
        cam.keyframe_insert("location", frame=k["frame"])
        target.location = world(*k["look"], LOOK_H)
        target.keyframe_insert("location", frame=k["frame"])
    last = keys[-1]["frame"]

    scene.frame_start = 1
    scene.frame_end = last
    scene.render.fps = FPS
    scene.camera = cam

    # --- 渲染设置 ---
    if mode == "workbench":
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.resolution_x, scene.render.resolution_y = 640, 360
        outdir = FRAMES / "workbench"
    else:
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = 960, 540
        outdir = FRAMES / "eevee"
    outdir.mkdir(exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(outdir / "f_")
    scene.render.resolution_percentage = 100

    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "方案A13_漫游.blend"))
    if mode == "stills":  # 抽查关键帧构图
        for f in (1, 80, 160, 240, 330, 420, 500, last):
            scene.frame_set(f)
            scene.render.filepath = str(outdir / f"still_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
    print(json.dumps({"frames": last, "fps": FPS, "seconds": round(last / FPS, 1),
                      "out": str(outdir)}, ensure_ascii=False))


main()
