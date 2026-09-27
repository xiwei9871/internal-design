from pathlib import Path
import sys
import unittest
import ezdxf

EXP = Path("/Users/xiwei/interior_design/projects/c_type_home/experiments/design_skill_benchmark_v01")
sys.path.insert(0, str(EXP / "scripts"))

class BenchmarkTests(unittest.TestCase):
    def test_required_a04_blocks_are_explicit(self):
        from run_benchmark import REQUIRED_BLOCKS
        self.assertTrue({
            "SOFA_3S_2200x900_PLAN",
            "SOFA_2S_1800x850_PLAN",
            "LOUNGE_CHAIR_900x900_PLAN",
            "DINING_TABLE_1500x600_PLAN",
            "DINING_CHAIR_450x500_PLAN",
        } <= set(REQUIRED_BLOCKS))

    def test_clean_base_removes_only_old_public_movable_inserts(self):
        from run_benchmark import remove_public_movable_from_doc, OLD_PUBLIC_INSERT_NAMES
        src = EXP.parents[1] / "cad" / "design_v02_f1_l1.dxf"
        doc = ezdxf.readfile(str(src))
        before_walls = [(e.dxf.handle, e.dxftype(), e.dxf.layer) for e in doc.modelspace()
                        if e.dxf.layer in {"S-S.WALL","A-WALL-EXST-CORR","F-DOOR","A-GLAZ-EXST"}]
        removed = remove_public_movable_from_doc(doc)
        after_walls = [(e.dxf.handle, e.dxftype(), e.dxf.layer) for e in doc.modelspace()
                       if e.dxf.layer in {"S-S.WALL","A-WALL-EXST-CORR","F-DOOR","A-GLAZ-EXST"}]
        self.assertGreaterEqual(set(removed), set(OLD_PUBLIC_INSERT_NAMES))
        self.assertEqual(before_walls, after_walls)
        self.assertFalse(any(e.dxftype()=="INSERT" and e.dxf.layer=="A-FURN-PROP" and e.dxf.name in OLD_PUBLIC_INSERT_NAMES
                             for e in doc.modelspace()))

    def test_arm_specs_are_method_specific_and_share_iteration_limit(self):
        from run_benchmark import ARM_SPECS, ITERATIONS
        self.assertEqual(set(ARM_SPECS), {"CTRL","ARCH","STUDIO","REROOM"})
        self.assertTrue(all(spec["iteration_limit"] == ITERATIONS for spec in ARM_SPECS.values()))
        self.assertEqual(len({spec["device"] for spec in ARM_SPECS.values()}), 4)

    def test_verifier_confirms_blind_package(self):
        from verify_benchmark import verify
        report = verify()
        self.assertTrue(report["all_pass"])
        self.assertEqual(report["gate_count"], 9)

if __name__ == "__main__":
    unittest.main()

