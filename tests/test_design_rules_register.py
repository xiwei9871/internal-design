import csv
import json
import unittest
from pathlib import Path

D = Path(__file__).resolve().parents[1] / 'docs/design_rules_poc_v01'
FIELDS = {'rule_id', 'topic', 'document', 'edition', 'clause', 'source_url', 'effective_date',
          'applicable_scope', 'requirement_type', 'comparison_method', 'evidence_status', 'reviewer_status'}


class RegisterTests(unittest.TestCase):
    def setUp(self):
        self.rules = json.loads((D / 'RULE_REGISTER.json').read_text())['rules']
        self.std = {r['code']: r for r in csv.DictReader(open(D / 'STANDARD_REGISTER.csv', encoding='utf-8'))}

    def test_rules_have_required_fields(self):
        for r in self.rules:
            self.assertFalse(FIELDS - set(r), r['rule_id'])

    def test_rule_ids_unique(self):
        ids = [r['rule_id'] for r in self.rules]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_rule_cites_a_registered_current_standard(self):
        for r in self.rules:
            s = self.std.get(r['document'])
            self.assertIsNotNone(s, r['rule_id'])
            self.assertEqual(s['status_2026_11'], 'CURRENT')
            self.assertEqual(r['source_url'], s['announcement_url'])
            self.assertTrue(r['source_url'].startswith('https://www.mohurd.gov.cn/'))

    def test_superseded_standards_not_cited(self):
        for r in self.rules:
            self.assertNotIn(r['document'], ('GB 50368-2005', 'GB 50034-2013', 'GB 50763-2012'))

    def test_no_rule_claims_professional_review(self):
        for r in self.rules:
            self.assertNotEqual(r['reviewer_status'], 'VERIFIED')


if __name__ == '__main__':
    unittest.main()


class ClauseRepealTests(unittest.TestCase):
    """Clause-level repeal: a standard can stay current while specific clauses are repealed."""
    def setUp(self):
        self.rules = json.loads((D / 'RULE_REGISTER.json').read_text())['rules']
        self.repealed = {(r['code'], c) for r in json.loads((D / 'REPEALED_CLAUSES.json').read_text())['repealed']
                         for c in r['clauses']}

    def test_jgj367_mandatory_clauses_listed_as_repealed(self):
        self.assertIn(('JGJ 367-2015', '3.0.4'), self.repealed)
        self.assertIn(('JGJ 367-2015', '3.0.7'), self.repealed)

    def test_no_rule_cites_a_repealed_clause(self):
        for r in self.rules:
            for c in r['clause'].replace(' ', '').split(','):
                self.assertNotIn((r['document'], c.split('-')[0]), self.repealed, r['rule_id'])

    def test_safety_intent_of_repealed_367_3_0_7_is_carried_by_current_code(self):
        carriers = [r for r in self.rules if 'JGJ 367-2015 第 3.0.7' in r.get('replaces', '')]
        self.assertTrue(carriers)
        self.assertTrue(all(r['document'] == 'GB 55038-2025' for r in carriers))

    def test_jgj367_not_described_as_having_current_mandatory_clauses(self):
        std = {r['code']: r for r in csv.DictReader(open(D / 'STANDARD_REGISTER.csv', encoding='utf-8'))}
        self.assertIn('NO_CURRENT_MANDATORY', std['JGJ 367-2015']['type'])
        report = (D / 'RESEARCH_REPORT.md').read_text()
        self.assertNotIn('强制性条文仅 3.0.4、3.0.7）', report)
