"""每视角多候选 AI 修图 + QC 自动选优。

强项视角(living/kitchen/secondary_bath)跑 2 候选，弱项跑 3。
选优规则：recall>=0.55 里取 chamfer 最小；全不达标取 recall 最高。
输出 renders_ai/{key}_best.png + qc/candidates_report.json
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROMPTS = ROOT / "prompts"
OUT = ROOT / "renders_ai"
CAND = OUT / "cand"
QC = ROOT / "qc"

sys.path.insert(0, str(ROOT.parent / "scheme_a_v12"))
import render_qc  # noqa: E402
render_qc.QC = QC

N_CAND = {"living": 2, "kitchen": 2, "secondary_bath": 2,
          "master": 3, "child": 3, "elder": 3, "main_bath": 3}

STRICT = ("\nEdit only materials, lighting, surface detail, and soft furnishings. "
          "Preserve the input geometry exactly: do not add, remove, move, resize, or rotate any wall, door, "
          "window, cabinet, fixture, bed, table, sofa, chair, lamp, or plant. Do not invent objects absent "
          "from the reference. Keep the camera position, crop, perspective, room proportions, and every "
          "furniture footprint identical to the input image.")


def env_from_dotenv() -> dict[str, str]:
    env = dict(os.environ)
    p = Path.home() / ".env"
    for raw in p.read_text(encoding="utf-8").splitlines():
        if "=" in raw and not raw.lstrip().startswith("#"):
            k, v = raw.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def edit(key: str, i: int, env: dict[str, str]) -> Path:
    prompt = (PROMPTS / f"{key}.txt").read_text(encoding="utf-8").strip() + STRICT
    base = ROOT / f"realfurn_{key}.png"
    response = CAND / f".{key}_{i}.resp.json"
    output = CAND / f"{key}_{i}.png"
    url = env["CODEX_API_URL"].rstrip("/") + "/images/edits"
    cp = subprocess.run([
        "curl", "-sS", "--max-time", "300", "-o", str(response), "-w", "%{http_code}", url,
        "-H", f"Authorization: Bearer {env['CODEX_API_KEY']}",
        "-F", "model=gpt-image-2", "-F", f"prompt={prompt}", "-F", "size=1536x1024",
        "-F", "quality=high", "-F", "n=1", "-F", f"image=@{base};type=image/png",
    ], env=env, capture_output=True, text=True, check=False)
    if cp.stdout.strip() != "200":
        raise RuntimeError(f"{key}_{i}: HTTP {cp.stdout.strip()} {response.read_text(errors='replace')[:200]}")
    output.write_bytes(base64.b64decode(json.loads(response.read_text())["data"][0]["b64_json"]))
    return output


def pick(scores: list[dict]) -> dict:
    ok = [s for s in scores if s["recall"] >= 0.55]
    return min(ok, key=lambda s: s["chamfer_px"]) if ok else max(scores, key=lambda s: s["recall"])


def main() -> None:
    CAND.mkdir(parents=True, exist_ok=True)
    QC.mkdir(exist_ok=True)
    env = env_from_dotenv()
    jobs = [(k, i) for k, n in N_CAND.items() for i in range(n)]
    print(f"{len(jobs)} candidates")
    done = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = {pool.submit(edit, k, i, env): (k, i) for k, i in jobs}
        for f in as_completed(futs):
            k, i = futs[f]
            try:
                p = f.result()
                done.setdefault(k, []).append(p)
                print(f"{k}_{i} ok", flush=True)
            except Exception as e:
                print(f"{k}_{i} FAIL {e}", flush=True)

    report = {}
    for key, paths in done.items():
        scores = []
        for p in sorted(paths):
            s = render_qc.score(ROOT / f"realfurn_wb_{key}.png", p, f"{key}_{p.stem.rsplit('_', 1)[-1]}")
            s["file"] = p.name
            scores.append(s)
        best = pick(scores)
        shutil.copy(CAND / best["file"], OUT / f"{key}_best.png")
        report[key] = {"best": best, "all": scores}
        print(f"{key}: best={best['file']} recall={best['recall']} chamfer={best['chamfer_px']}", flush=True)
    (QC / "candidates_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
