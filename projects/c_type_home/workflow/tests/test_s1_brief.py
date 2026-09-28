from pathlib import Path
import json
import unittest

ROOT=Path("/Users/xiwei/interior_design/projects/c_type_home")
class S1BriefTests(unittest.TestCase):
    def test_brief_exists_with_household_and_stage_boundaries(self):
        p=ROOT/"design/brief_v01.json"
        self.assertTrue(p.exists())
        d=json.loads(p.read_text())
        self.assertEqual(d["schema"],"residential-design-brief-v1")
        self.assertEqual(d["household"]["permanent"],["owner","mother"])
        self.assertEqual(d["stage_boundary"]["layout_coordinates"],"S2_ONLY")
        self.assertEqual(d["approval_status"],"DRAFT_HUMAN_REVIEW")

    def test_brief_separates_confirmed_and_to_verify(self):
        d=json.loads((ROOT/"design/brief_v01.json").read_text())
        self.assertIn("kitchen KEEP",d["confirmed"]["existing_keep"] )
        self.assertIn("LEVEL_DELTA_TO_VERIFY",d["to_verify"])
        self.assertIn("OPEN_NOT_ENCLOSED",d["confirmed"]["north_balcony"]["current_status"])
        self.assertNotIn("x",d["confirmed"].get("furniture_layout",{}))

if __name__=="__main__": unittest.main()
