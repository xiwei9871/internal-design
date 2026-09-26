import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects/c_type_home"
RULE_DIR = PROJECT / "knowledge/design_rules"
PREC_DIR = PROJECT / "knowledge/precedents"
QUERY = PROJECT / "scripts/query_design_knowledge.py"


class A1A2KnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules_doc = json.loads((RULE_DIR / "design_rulebook_v01.json").read_text())
        cls.rules = cls.rules_doc["rules"]
        cls.principles = json.loads((RULE_DIR / "project_design_principles.json").read_text())["principles"]
        cls.a1qa = json.loads((RULE_DIR / "rulebook_qa.json").read_text())
        cls.precedents = json.loads((PREC_DIR / "precedent_index_v01.json").read_text())["precedents"]
        cls.patterns = json.loads((PREC_DIR / "pattern_library_v01.json").read_text())["patterns"]
        cls.a2qa = json.loads((PREC_DIR / "precedent_qa.json").read_text())
        cls.audit = json.loads((PROJECT / "qc/a1_a2_f1_design_audit.json").read_text())

    def test_a1_count_schema_and_gates(self):
        self.assertEqual(len(self.rules), 100)
        self.assertEqual(self.a1qa["status"], "PASS")
        required = {"rule_id", "category", "topic", "rule_type", "priority", "statement", "source_id", "source_url", "source_type", "jurisdiction", "gateable", "project_override", "notes"}
        self.assertTrue(all(required <= set(rule) for rule in self.rules))
        self.assertTrue(all(rule["source_url"].startswith("https://") for rule in self.rules))
        self.assertGreaterEqual(len(self.principles), 10)
        self.assertTrue(any("TO_VERIFY" in p["status"] for p in self.principles))

    def test_a2_count_and_pattern_evidence(self):
        self.assertEqual(len(self.precedents), 60)
        self.assertEqual(len(self.patterns), 20)
        self.assertEqual(self.a2qa["status"], "PASS")
        self.assertTrue(all(p["url"].startswith("https://") for p in self.precedents))
        self.assertTrue(all(isinstance(p["floor_plan_available"], bool) for p in self.precedents))
        self.assertTrue(all(len(set(p["precedent_ids"])) >= 2 for p in self.patterns))

    def run_query(self, *args):
        cmd = [sys.executable, str(QUERY), *args, "--json"]
        return json.loads(subprocess.check_output(cmd, cwd=ROOT, text=True))

    def test_living_query_and_traceability(self):
        result = self.run_query("--room", "living", "--tags", "child-friendly", "aging-in-place", "projector", "balcony", "--top", "8")
        self.assertTrue(result["rules"])
        self.assertTrue(result["patterns"])
        self.assertTrue(result["precedents"])
        self.assertTrue(all(x.get("trace") for section in ("rules", "patterns", "precedents") for x in result[section]))

    def test_bedroom_aging_query(self):
        result = self.run_query("--room", "bedroom", "--tags", "elderly", "ensuite", "wheelchair", "--top", "10")
        self.assertTrue(result["rules"])
        self.assertTrue(any("aging" in " ".join(x.get("tags", [])) or x.get("rule_id", "").startswith("AGE") for x in result["rules"]))

    def test_repeated_queries_are_identical(self):
        args = ("--room", "living", "--tags", "child-friendly", "projector", "balcony", "--top", "8")
        self.assertEqual(self.run_query(*args), self.run_query(*args))

    def test_audit_has_required_sections_and_citations(self):
        sections = self.audit["sections"]
        expected = {"rules_already_satisfied", "potential_rule_conflicts", "project_specific_conflicts", "relevant_precedents", "applicable_patterns", "unresolved_spatial_issues", "next_design_directions"}
        self.assertEqual(set(sections), expected)
        rule_ids = {r["rule_id"] for r in self.rules}
        pattern_ids = {p["pattern_id"] for p in self.patterns}
        precedent_ids = {p["precedent_id"] for p in self.precedents}
        principle_ids = {p["principle_id"] for p in self.principles}
        for issue in sections["unresolved_spatial_issues"]:
            self.assertTrue(set(issue["citations"]).intersection(rule_ids | pattern_ids | principle_ids))
        self.assertGreaterEqual(len(sections["next_design_directions"]), 2)
        for p in sections["relevant_precedents"]:
            self.assertIn(p["precedent_id"], precedent_ids)


if __name__ == "__main__":
    unittest.main()
