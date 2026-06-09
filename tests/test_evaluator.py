import unittest
from datetime import date
from tracker_core.evaluator import LicenseEvaluator

class TestLicenseEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator = LicenseEvaluator()
        self.eval_date = date(2026, 6, 8)

    def test_evaluate_to_provision(self):
        records = [
            {"Email": "user1@example.com", "Team Name": "Team A", "Start Date": "2026-06-05", "End Date": "2026-07-05", "Status": "Pending", "Reason": ""}, # should provision
            {"Email": "user2@example.com", "Team Name": "Team A", "Start Date": "2026-06-08", "End Date": "2026-07-08", "Status": "Pending", "Reason": ""}, # should provision (today)
            {"Email": "user3@example.com", "Team Name": "Team B", "Start Date": "2026-06-10", "End Date": "2026-07-10", "Status": "Pending", "Reason": ""}, # should NOT provision (future)
        ]
        
        to_provision, to_revoke, skipped = self.evaluator.evaluate(records, self.eval_date)
        
        self.assertEqual(len(to_provision), 2)
        self.assertEqual(len(to_revoke), 0)
        self.assertEqual(len(skipped), 0)
        
        self.assertEqual(to_provision[0]["email"], "user1@example.com")
        self.assertEqual(to_provision[1]["email"], "user2@example.com")

    def test_evaluate_to_revoke(self):
        records = [
            {"Email": "user1@example.com", "Team Name": "Team A", "Start Date": "2026-05-01", "End Date": "2026-06-01", "Status": "Provisioned", "Reason": ""}, # should revoke
            {"Email": "user2@example.com", "Team Name": "Team A", "Start Date": "2026-05-08", "End Date": "2026-06-08", "Status": "Provisioned", "Reason": ""}, # should revoke (today)
            {"Email": "user3@example.com", "Team Name": "Team B", "Start Date": "2026-05-10", "End Date": "2026-06-10", "Status": "Provisioned", "Reason": ""}, # should NOT revoke (future)
        ]
        
        to_provision, to_revoke, skipped = self.evaluator.evaluate(records, self.eval_date)
        
        self.assertEqual(len(to_provision), 0)
        self.assertEqual(len(to_revoke), 2)
        self.assertEqual(len(skipped), 0)
        
        self.assertEqual(to_revoke[0]["email"], "user1@example.com")
        self.assertEqual(to_revoke[1]["email"], "user2@example.com")

    def test_evaluate_skipped_and_errors(self):
        records = [
            {"Email": "", "Team Name": "Team A", "Start Date": "2026-06-01", "End Date": "2026-06-30", "Status": "Pending", "Reason": ""}, # skipped (missing email)
            {"Email": "user2@example.com", "Team Name": "Team A", "Start Date": "bad-date", "End Date": "2026-06-30", "Status": "Pending", "Reason": ""}, # skipped (bad date format)
        ]
        
        to_provision, to_revoke, skipped = self.evaluator.evaluate(records, self.eval_date)
        
        self.assertEqual(len(to_provision), 0)
        self.assertEqual(len(to_revoke), 0)
        self.assertEqual(len(skipped), 2)
        
        self.assertEqual(skipped[0]["reason"], "Missing email")
        self.assertTrue("Invalid date format" in skipped[1]["reason"])

if __name__ == "__main__":
    unittest.main()
