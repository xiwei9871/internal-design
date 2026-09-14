from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).parent
V10_SCRIPT = ROOT.parent / "scheme_a_v10" / "build_viewpoint_sheet.py"
V7 = ROOT.parent / "scheme_a_v7"


def main() -> None:
    spec = importlib.util.spec_from_file_location("viewpoint_sheet", V10_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {V10_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Keep the map arrows synchronized with the A11 Blender anchors.  The
    # revised L/K cameras are placed outside the furniture/service-wall
    # envelopes so the intended objects are actually inside the fixed view.
    for view in module.VIEWS:
        if view["id"] == "L":
            view["camera"], view["target"] = (1080, 760), (930, 1130)
        elif view["id"] == "K":
            view["camera"], view["target"] = (735, 650), (620, 250)
    geometry = json.loads((V7 / "scheme_a_geometry.json").read_text(encoding="utf-8"))
    svg = module.build_svg(
        geometry,
        title="A11 CAD 同模相机定位（V2）",
        status_line="校核状态：A11 已从同一套 FreeCAD/OBJ 几何底模渲染。",
        status_detail="虚线箭头与下方相机表已绑定；材质、SKU 和现场复尺仍在设计阶段。",
    )
    path = ROOT / "A11_CAD同模视角定位图.svg"
    path.write_text(svg, encoding="utf-8")
    (ROOT / "a11-viewpoint-map.svg").write_text(svg, encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
