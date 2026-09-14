from __future__ import annotations

import base64
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROMPTS = ROOT / "prompts"
OUT = ROOT / "renders"
OUT.mkdir(parents=True, exist_ok=True)


def load_env_file(path: Path) -> dict[str, str]:
    env = dict(os.environ)
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return env


def generate(key: str, env: dict[str, str]) -> dict[str, object]:
    prompt = (PROMPTS / f"{key}.txt").read_text(encoding="utf-8").strip()
    # Generation is the compatible fallback for this endpoint: it accepts
    # gpt-image-2, while its multipart edits endpoint rejects image uploads.
    prompt += "\nGenerate a single final image; use the confirmed plan and dimensions as hard design constraints."
    response_path = OUT / f".{key}.response.json"
    output_path = OUT / f"{key}_image2.png"
    url = env["CODEX_API_URL"].rstrip("/") + "/images/generations"
    command = [
        "curl", "-sS", "--max-time", "240", "-o", str(response_path), "-w", "%{http_code}",
        url, "-H", f"Authorization: Bearer {env['CODEX_API_KEY']}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"model": "gpt-image-2", "prompt": prompt, "size": "1536x1024", "quality": "high", "n": 1}, ensure_ascii=False),
    ]
    completed = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
    code = completed.stdout.strip()
    if code != "200":
        detail = response_path.read_text(encoding="utf-8", errors="replace")[:300]
        raise RuntimeError(f"{key}: HTTP {code}; {detail}")
    payload = json.loads(response_path.read_text(encoding="utf-8"))
    item = payload["data"][0]
    data = base64.b64decode(item["b64_json"])
    output_path.write_bytes(data)
    return {"key": key, "output": str(output_path), "bytes": len(data), "size": "1536x1024", "model": "gpt-image-2"}


def main() -> None:
    env = load_env_file(Path.home() / ".env")
    if not env.get("CODEX_API_URL") or not env.get("CODEX_API_KEY"):
        raise SystemExit("CODEX_API_URL/CODEX_API_KEY not available from ~/.env or environment")
    keys = ["living", "kitchen", "master", "child", "elder", "main_bath", "secondary_bath"]
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(generate, key, env): key for key in keys}
        for future in as_completed(futures):
            results.append(future.result())
            print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    (ROOT / "image2_manifest.json").write_text(json.dumps({"schema": "scheme-a12-image2-v1", "source": "A11 Blender camera views + confirmed A7 layout", "results": sorted(results, key=lambda x: x["key"])}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
