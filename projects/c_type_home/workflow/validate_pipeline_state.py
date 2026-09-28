from __future__ import annotations
import json
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parent
def evaluate_state(state:dict,gates:dict)->dict:
    required=list(gates["formal_cad_allowed"]["all_of"])
    evidence=state.get("gate_evidence",{})
    missing=[g for g in required if evidence.get(g)!="PASS"]
    allowed=not missing
    return {"formal_cad_allowed":allowed,"missing_prerequisites":missing,"required_prerequisites":required,"declared_formal_design_cad":state.get("formal_design_cad"),"declared_construction_docs":state.get("construction_docs")}
def load():
    state=json.loads((ROOT/"project_state.json").read_text())
    gates=yaml.safe_load((ROOT/"gates_v2.yaml").read_text())
    return state,gates
if __name__=="__main__":
    state,gates=load(); print(json.dumps(evaluate_state(state,gates),ensure_ascii=False,indent=2))

