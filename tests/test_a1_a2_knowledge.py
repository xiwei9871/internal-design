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
        cls.verification = json.loads((PREC_DIR / "verification_registry_v01.json").read_text())
        cls.audit = json.loads((PROJECT / "qc/a1_a2_f1_design_audit.json").read_text())

    def test_a1_count_schema_and_gates(self):
        self.assertEqual(len(self.rules), 120)
        self.assertEqual(self.a1qa["status"], "PASS")
        required = {"rule_id", "category", "topic", "rule_type", "priority", "statement", "source_id", "source_url", "source_type", "jurisdiction", "gateable", "automatic_gate", "classification", "source_strength", "project_override", "notes"}
        self.assertTrue(all(required <= set(rule) for rule in self.rules))
        self.assertTrue(all(rule["source_url"].startswith("https://") for rule in self.rules))
        self.assertTrue(all("archdaily.com/tag" not in rule["source_url"] for rule in self.rules))
        self.assertTrue(all(rule["source_strength"] in {"STRONG", "MEDIUM", "WEAK"} for rule in self.rules))
        numeric_weak = [r for r in self.rules if any(r.get(k) is not None for k in ("recommended_min_mm", "preferred_mm", "maximum_mm", "recommended_dimensions_mm")) and r["source_strength"] != "STRONG"]
        self.assertTrue(all(r["classification"] == "DESIGN_HEURISTIC" and r["automatic_gate"] is False for r in numeric_weak))
        self.assertEqual(sum(r["category"] == "spatial_composition" for r in self.rules), 20)
        owner = next(p for p in self.principles if p["principle_id"] == "P-OWNER-COUPLE")
        self.assertIn("owner and his mother", owner["statement"])
        self.assertIn("periodic residents", owner["statement"])
        self.assertGreaterEqual(len(self.principles), 10)
        self.assertTrue(any("TO_VERIFY" in p["status"] for p in self.principles))

    def test_a2_count_and_pattern_evidence(self):
        self.assertEqual(len(self.precedents), 60)
        self.assertEqual(len(self.patterns), 20)
        self.assertEqual(self.a2qa["status"], "PASS")
        self.assertTrue(all(p["url"].startswith("https://") for p in self.precedents))
        self.assertTrue(all(isinstance(p["floor_plan_available"], bool) for p in self.precedents))
        self.assertTrue(all((p["evidence_type"] == "PROJECT_DERIVED" and p["project_basis"] and p["evidence"]) or len(set(p["precedent_ids"])) >= 2 for p in self.patterns))
        self.assertTrue(all((p["evidence_type"] == "PROJECT_DERIVED" or len(p["evidence"]) == len(p["precedent_ids"])) and all(e["evidence"] and e["confidence"] for e in p["evidence"] ) for p in self.patterns))
        self.assertTrue(all(p["evidence_type"] == "PROJECT_DERIVED" or p["evidence_confidence"] != "HIGH" or all(e.get("verification_status") == "VERIFIED_PRECEDENT" for e in p["evidence"]) for p in self.patterns))
        self.assertEqual(sum(p["curation_level"] == "VERIFIED_PRECEDENT" for p in self.precedents), 10)
        self.assertEqual(sum(p["curation_level"] == "CURATED_METADATA" for p in self.precedents), 8)
        self.assertEqual(sum(p["curation_level"] == "METADATA_ONLY" for p in self.precedents), 42)
        self.assertTrue(all("relevance_score" in p and "evidence_confidence" in p for p in self.precedents))
        self.assertTrue(all(p["relevance_components"].get("area_similarity") is None or p["area_m2"] is not None for p in self.precedents))
        self.assertLessEqual(max(p["relevance_components"]["household_similarity"] for p in self.precedents), 0.65)
        self.assertTrue(all(p["relevance_components"]["household_similarity"] == 0.0 for p in self.precedents if p["household_program_status"] == "not_stated_in_captured_metadata"))
        curated = [p for p in self.precedents if p["curation_level"] in {"CURATED_METADATA", "VERIFIED_PRECEDENT"}]
        self.assertTrue(all(p["actual_spatial_strategy"] and 2 <= len(p["design_lessons"]) <= 5 and p["curation_review"]["override_used"] for p in curated))
        self.assertGreaterEqual(len({p["design_lessons"][0] for p in curated}), 15)
        verified = [p for p in self.precedents if p["curation_level"] == "VERIFIED_PRECEDENT"]
        self.assertEqual(len(verified), 10)
        self.assertTrue(all(p["verification_confidence"] == 1.0 and p["floor_plan_url"] and len(p["verified_spatial_observations"]) >= 2 for p in verified))
        self.assertTrue(all(p["evidence_confidence"] == 1.0 for p in verified))
        self.assertTrue(all(p["evidence_confidence"] < 1.0 for p in self.precedents if p["curation_level"] != "VERIFIED_PRECEDENT"))
        self.assertEqual(self.verification["verified_count"], 10)
        self.assertEqual(len(self.verification["verified"]), 10)
        self.assertEqual(next(p for p in self.precedents if p["url"].endswith("renovation-of-joan-blanques-apartment-allaround-lab"))["precedent_id"], "PREC-002")

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
        expected = {"rules_already_satisfied", "potential_rule_conflicts", "project_specific_conflicts", "spatial_composition_assessment", "relevant_precedents", "applicable_patterns", "unresolved_spatial_issues", "next_design_directions"}
        self.assertEqual(set(sections), expected)
        rule_ids = {r["rule_id"] for r in self.rules}
        pattern_ids = {p["pattern_id"] for p in self.patterns}
        precedent_ids = {p["precedent_id"] for p in self.precedents}
        principle_ids = {p["principle_id"] for p in self.principles}
        for issue in sections["unresolved_spatial_issues"]:
            self.assertTrue(set(issue["citations"]).intersection(rule_ids | pattern_ids | principle_ids))
        self.assertGreaterEqual(len(sections["spatial_composition_assessment"]), 9)
        for item in sections["spatial_composition_assessment"]:
            self.assertTrue(set(item["citations"]).intersection(rule_ids | pattern_ids | principle_ids))
        self.assertGreaterEqual(len(sections["next_design_directions"]), 2)
        for p in sections["relevant_precedents"]:
            self.assertIn(p["precedent_id"], precedent_ids)


if __name__ == "__main__":
    unittest.main()
