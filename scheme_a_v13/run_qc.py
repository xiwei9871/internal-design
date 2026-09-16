import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scheme_a_v12"))
import render_qc
import json
ROOT = Path(__file__).resolve().parent
render_qc.QC = ROOT / "qc"
render_qc.QC.mkdir(exist_ok=True)
rows = []
for k in ["living","kitchen","master","child","elder","main_bath","secondary_bath"]:
    rows.append(render_qc.score(ROOT / f"realfurn_wb_{k}.png", ROOT / "renders_ai" / f"{k}_ai.png", k))
for r in rows: print(json.dumps(r, ensure_ascii=False))
(render_qc.QC / "qc_report.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))
