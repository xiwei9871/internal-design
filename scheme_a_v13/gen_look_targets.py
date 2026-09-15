"""生成漫游关键帧表 walk_keys.json：沿路径每 ~0.4m 采一帧。

每个采样：cam=路径位置；look=路径上前视点（视线不穿墙，门洞豁免；
被挡则逐级缩短前视距离）。末段前视收敛到窗边梳妆台。
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT.parent / "scheme_a_v7" / "scheme_a_geometry.json").read_text(encoding="utf-8"))

PATH = [(1120, 715), (980, 735), (1040, 820), (1040, 1000), (960, 1060),
        (870, 1120), (855, 1250), (880, 1130), (980, 1030), (1085, 940),
        (1085, 800), (970, 735), (860, 735), (770, 735), (710, 745),
        (700, 860), (640, 870), (540, 870), (515, 1050), (545, 1180),
        (600, 1205)]
END_LOOK = (520, 1337)  # 收尾注视主卧南窗（不要落在梳妆台 footprint 里）
STEP_PX = 40           # 采样间距 ~0.39m
# 前视候选：先正常前视，回头弯处加试更远点（让镜头平滑扫过弯心），再逐级缩短兜底
LOOKAHEADS = [320, 420, 520, 240, 160, 90]
SPEED_MMS, FPS = 950.0, 24  # mm/s → 帧号

walls = [Polygon(w["polygon"]) for w in DATA["walls"]]
doorboxes = [box(min(p[0] for p in [dr["hinge"], dr["leaf"], dr["closed"]]) - 18,
                 min(p[1] for p in [dr["hinge"], dr["leaf"], dr["closed"]]) - 18,
                 max(p[0] for p in [dr["hinge"], dr["leaf"], dr["closed"]]) + 18,
                 max(p[1] for p in [dr["hinge"], dr["leaf"], dr["closed"]]) + 18)
             for dr in DATA["doors"]]
doors_u = unary_union(doorboxes)
line = LineString(PATH)
total = line.length


def los_wall(cam, tgt):
    seg = LineString([cam, tgt])
    for w in walls:
        hit = seg.intersection(w)
        if not hit.is_empty and not hit.covered_by(doors_u):
            return True
    return False


MIN_EUCLID = 150  # 注视点与相机的最小直线距离 ~1.5m；回头弯处弧长前视会落回相机脚下

def tangent(s_):
    a = line.interpolate(max(s_ - 15, 0))
    b = line.interpolate(min(s_ + 15, total))
    return math.atan2(b.y - a.y, b.x - a.x)


def ang_diff(a1, a2):
    d = a1 - a2
    while d > math.pi:
        d -= 2 * math.pi
    while d < -math.pi:
        d += 2 * math.pi
    return d


MAX_TURN = math.radians(58)  # 每个键位(≈10帧)最大转头角——限速防甩镜头，同时保证过门洞转向不滞后到怼墙
LOOK_DIST = 300              # 注视点距相机 ~3m

samples = []
s = 0.0
while s <= total:
    cam = line.interpolate(s)
    samples.append((s, cam))
    s += STEP_PX

# 第一遍：每键的期望朝向
desired = []
for s, cam in samples:
    if s > total - 260:
        desired.append(math.atan2(END_LOOK[1] - cam.y, END_LOOK[0] - cam.x))
        continue
    curve = abs(ang_diff(tangent(s + 30), tangent(s - 30))) > 0.4  # ~23°：在弯内
    cands = [110, 150] if curve else LOOKAHEADS   # 弯内只跟切线，视线随弯转
    min_d = 80 if curve else MIN_EUCLID
    ang = None
    for la in cands:
        t = line.interpolate(min(s + la, total))
        if math.hypot(t.x - cam.x, t.y - cam.y) < min_d:
            continue
        if not los_wall((cam.x, cam.y), (t.x, t.y)):
            ang = math.atan2(t.y - cam.y, t.x - cam.x)
            break
    desired.append(tangent(s) if ang is None else ang)

# 第二遍：朝向限速——相邻键之间转头角度 clamp，视线连续扫过弯角
headings = [desired[0]]
for a in desired[1:]:
    step = max(-MAX_TURN, min(MAX_TURN, ang_diff(a, headings[-1])))
    headings.append(headings[-1] + step)

# 第三遍：沿限速后的朝向取注视点，视线不穿墙则放 3m，挡则缩短（保留 90px 下限）
keys = []
for (s, cam), h in zip(samples, headings):
    dx, dy = math.cos(h), math.sin(h)
    dist = LOOK_DIST
    for w in walls:
        hit = LineString([(cam.x, cam.y), (cam.x + dx * LOOK_DIST, cam.y + dy * LOOK_DIST)]).intersection(w)
        if hit.is_empty or hit.covered_by(doors_u):
            continue  # 门洞豁口不挡视线
        d_hit = cam.distance(hit)
        if 0 < d_hit < dist:
            dist = max(90, d_hit - 15)
    look = (round(cam.x + dx * dist, 1), round(cam.y + dy * dist, 1))
    frame = 1 + round(s * 9.82 / SPEED_MMS * FPS)
    keys.append({"frame": frame, "cam": [round(cam.x, 1), round(cam.y, 1)], "look": [look[0], look[1]]})
if keys[-1]["cam"] != list(PATH[-1]):
    keys.append({"frame": 1 + round(total * 9.82 / SPEED_MMS * FPS),
                 "cam": list(PATH[-1]), "look": list(END_LOOK)})

dst = ROOT / "walk_keys.json"
dst.write_text(json.dumps(keys), encoding="utf-8")
print(f"{len(keys)} keys, last frame {keys[-1]['frame']}, {keys[-1]['frame'] / FPS:.1f}s")
print(dst)
