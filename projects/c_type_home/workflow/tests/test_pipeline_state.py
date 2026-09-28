from pathlib import Path
import json
import sys
import unittest
from copy import deepcopy

WORKFLOW = Path("/Users/xiwei/interior_design/projects/c_type_home/workflow")
sys.path.insert(0, str(WORKFLOW))

class PipelineStateTests(unittest.TestCase):
    def load_inputs(self):
        state=json.loads((WORKFLOW/"project_state.json").read_text())
        import yaml
        gates=yaml.safe_load((WORKFLOW/"gates_v2.yaml").read_text())
        return state,gates

    def test_current_state_blocks_formal_cad(self):
        from validate_pipeline_state import evaluate_state
        state,gates=self.load_inputs()
        result=evaluate_state(state,gates)
        self.assertFalse(result["formal_cad_allowed"])
        self.assertEqual(state["formal_design_cad"],"HOLD")
        self.assertEqual(state["construction_docs"],"HOLD")

    def test_exact_five_design_gates_are_required(self):
        from validate_pipeline_state import evaluate_state
        state,gates=self.load_inputs()
        required=gates["formal_cad_allowed"]["all_of"]
        self.assertEqual(set(required),{
            "S2_HUMAN_APPROVAL","S3_3D_BLOCKOUT","S4_SPATIAL_REVIEW",
            "S4_HUMAN_APPROVAL","S5_DESIGN_CONTRACT_FREEZE"
        })
        ready=deepcopy(state)
        for gate in required: ready["gate_evidence"][gate]="PASS"
        self.assertTrue(evaluate_state(ready,gates)["formal_cad_allowed"])
        for gate in required:
            partial=deepcopy(ready)
            partial["gate_evidence"][gate]="HOLD"
            self.assertFalse(evaluate_state(partial,gates)["formal_cad_allowed"],gate)

    def test_experiment_labels_remain_non_approved(self):
        state,_=self.load_inputs()
        self.assertEqual(state["experiments"]["D0.1"],"INFRASTRUCTURE PROTOTYPE PASS / SKILL BENCHMARK INVALID")
        self.assertEqual(state["experiments"]["D0.2"],"BENCHMARK EXECUTION VALID / DESIGN QUALITY NOT ACCEPTED")
        self.assertEqual(state["experiments"]["F1R"],"RESEARCH ONLY / NOT APPROVED DESIGN")

if __name__=="__main__":
    unittest.main()

