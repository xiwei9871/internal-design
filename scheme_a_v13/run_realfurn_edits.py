from __future__ import annotations

import base64
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROMPTS = ROOT / "prompts"
OUT = ROOT / "renders_ai"

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


def edit(key: str, env: dict[str, str]) -> dict[str, object]:
    prompt = (PROMPTS / f"{key}.txt").read_text(encoding="utf-8").strip() + STRICT
    base = ROOT / f"realfurn_{key}.png"
    response = OUT / f".{key}.edit-response.json"
    output = OUT / f"{key}_ai.png"
    url = env["CODEX_API_URL"].rstrip("/") + "/images/edits"
    command = [
        "curl", "-sS", "--max-time", "240", "-o", str(response), "-w", "%{http_code}", url,
        "-H", f"Authorization: Bearer {env['CODEX_API_KEY']}",
        "-F", "model=gpt-image-2", "-F", f"prompt={prompt}", "-F", "size=1536x1024",
        "-F", "quality=high", "-F", "n=1", "-F", f"image=@{base};type=image/png",
    ]
    cp = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
    code = cp.stdout.strip()
    if code != "200":
        raise RuntimeError(f"{key}: HTTP {code}; {response.read_text(encoding='utf-8', errors='replace')[:300]}")
    data = json.loads(response.read_text(encoding="utf-8"))["data"][0]
    output.write_bytes(base64.b64decode(data["b64_json"]))
    return {"key": key, "output": str(output), "bytes": output.stat().st_size, "source": str(base)}


def main() -> None:
    env = env_from_dotenv()
    keys = ["living", "kitchen", "master", "child", "elder", "main_bath", "secondary_bath"]
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(edit, key, env): key for key in keys}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    (OUT / "manifest.json").write_text(json.dumps(sorted(results, key=lambda x: x["key"]), ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
