import unittest
from pathlib import Path

class ModelOutputsTests(unittest.TestCase):
    def test_main_bath_camera_clears_open_door(self):
        import json
        from design_model import load_design
        from scheme_a_v14.validate import camera_door_issues
        anchors=json.loads(Path('scheme_a_v14/scene_manifest.json').read_text())['camera_anchors']
        blocked={**anchors['main_bath'],'camera_px':[395,835]}
        self.assertTrue(camera_door_issues({'main_bath':blocked},load_design()))
        self.assertEqual(camera_door_issues(anchors,load_design()),[])

    @unittest.skipUnless(Path('scheme_a_v14/geometry_audit.json').exists(),'model not built')
    def test_generated_assemblies_and_cameras_match_contract(self):
        from scheme_a_v14.validate import validate
        result=validate()
        self.assertEqual(result['issues'],[])
        self.assertEqual(result['camera_count'],7)
