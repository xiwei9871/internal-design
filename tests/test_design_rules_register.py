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
