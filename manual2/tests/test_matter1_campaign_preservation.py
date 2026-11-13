"""The all-element campaign must preserve prior scientific data and placements."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'campaign_preservation', ROOT/'scripts/check_matter1_campaign_preservation.py')
preservation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preservation)


class CampaignPreservationTests(unittest.TestCase):
    def test_all_frozen_data_skills_and_chart_are_unchanged(self):
        report = preservation.verify(ROOT)
        self.assertEqual(report['status'], 'PASS_CAMPAIGN_PRESERVATION')
        self.assertEqual(report['checked_files'], 299)


if __name__ == '__main__':
    unittest.main()
