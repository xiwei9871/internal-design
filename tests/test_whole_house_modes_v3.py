import importlib.util
import tempfile
import unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"projects/c_type_home/scripts/whole_house_modes_v3.py"
spec=importlib.util.spec_from_file_location("modes",SCRIPT)
modes=importlib.util.module_from_spec(spec)
if SCRIPT.exists():spec.loader.exec_module(modes)
class ModesQueueTests(unittest.TestCase):
 def test_followup_requires_same_level_gate(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);hero=root/"dining/B_designer/VIEW_01.png";hero.parent.mkdir(parents=True);hero.write_bytes(b"image")
   self.assertFalse(modes.gate_ready(root,"dining","B_designer"))
   modes.atomic_json(root/"dining/HERO_QA_B_designer.json",{"status":"PASS_FOR_PROPAGATION"})
   self.assertTrue(modes.gate_ready(root,"dining","B_designer"))
   self.assertFalse(modes.gate_ready(root,"dining","C_creative"))
 def test_cached_or_failed_never_reschedules(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"view.png";self.assertTrue(modes.unattempted(p))
   p.with_suffix(".json").write_text("{}")
   self.assertFalse(modes.unattempted(p))
   p.write_bytes(b"success");self.assertFalse(modes.unattempted(p))
 def test_selected_repair_preserves_original_slot(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/"kitchen/B_designer/VIEW_01.png";p.parent.mkdir(parents=True);p.write_bytes(b"original")
   new=p.with_name("VIEW_01_repair1.png");new.write_bytes(b"fixed")
   modes.atomic_json(p.with_suffix(".json"),{"selected_derivative":str(new)})
   self.assertEqual(modes.selected_image(root,"kitchen","B_designer","VIEW_01"),new)
   self.assertEqual(p.read_bytes(),b"original")
 def test_modes_have_different_contracts(self):
  b=modes.prompt_contract("dining","VIEW_01","B_designer",False)
  c=modes.prompt_contract("dining","VIEW_01","C_creative",False)
  self.assertIn("STYLING",b);self.assertIn("main furniture",b)
  self.assertIn("INSPIRATION",c);self.assertIn("pale",c);self.assertIn("redesign",c)
  self.assertNotIn("same furniture count",c)
 def test_followup_uses_current_crop(self):
  t=modes.prompt_contract("hallway","VIEW_03","B_designer",True)
  self.assertIn("do not copy the hero crop",t);self.assertIn("THIS view",t)
if __name__=="__main__":unittest.main()
