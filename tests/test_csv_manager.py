import unittest
import os
import tempfile
from tracker_core.csv_manager import CSVManager, REQUIRED_COLUMNS

class TestCSVManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.test_dir.name, "test_tracker.csv")
        
        # Create a valid test csv
        with open(self.csv_path, "w", encoding="utf-8") as f:
            f.write("Email,Team Name,Start Date,End Date,Status,Reason\n")
            f.write("test@example.com,Engineering,2026-06-01,2026-06-30,Pending,Some reason\n")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_read_records_success(self):
        manager = CSVManager(self.csv_path)
        records = manager.read_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["Email"], "test@example.com")
        self.assertEqual(records[0]["Team Name"], "Engineering")
        self.assertEqual(records[0]["Status"], "Pending")

    def test_read_records_missing_file(self):
        manager = CSVManager(os.path.join(self.test_dir.name, "non_existent.csv"))
        with self.assertRaises(FileNotFoundError):
            manager.read_records()

    def test_read_records_invalid_headers(self):
        bad_csv = os.path.join(self.test_dir.name, "bad_tracker.csv")
        with open(bad_csv, "w", encoding="utf-8") as f:
            f.write("Email,Start Date,Status\n") # Missing other columns
            
        manager = CSVManager(bad_csv)
        with self.assertRaises(ValueError):
            manager.read_records()

    def test_write_records_and_backup(self):
        manager = CSVManager(self.csv_path)
        records = [
            {"Email": "test@example.com", "Team Name": "Engineering", "Start Date": "2026-06-01", "End Date": "2026-06-30", "Status": "Provisioned", "Reason": "Updated status"}
        ]
        backup_path = manager.write_records(records)
        
        # Verify backup was created
        self.assertTrue(os.path.exists(backup_path))
        self.assertTrue("backups" in backup_path)
        
        # Verify file was written
        updated_records = manager.read_records()
        self.assertEqual(len(updated_records), 1)
        self.assertEqual(updated_records[0]["Status"], "Provisioned")
        self.assertEqual(updated_records[0]["Reason"], "Updated status")

if __name__ == "__main__":
    unittest.main()
