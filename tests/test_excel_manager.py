import unittest
import os
import tempfile
from tracker_core.excel_manager import ExcelManager, REQUIRED_COLUMNS

class TestExcelManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.xlsx_path = os.path.join(self.test_dir.name, "test_tracker.xlsx")
        
        # Create a valid test xlsx
        manager = ExcelManager(self.xlsx_path)
        records = [
            {"Email": "test@example.com", "Team Name": "Engineering", "Start Date": "2026-06-01", "End Date": "2026-06-30", "Status": "Pending", "Reason": "Some reason"}
        ]
        manager.write_records(records)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_read_records_success(self):
        manager = ExcelManager(self.xlsx_path)
        records = manager.read_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["Email"], "test@example.com")
        self.assertEqual(records[0]["Team Name"], "Engineering")
        self.assertEqual(records[0]["Status"], "Pending")

    def test_read_records_missing_file(self):
        manager = ExcelManager(os.path.join(self.test_dir.name, "non_existent.xlsx"))
        with self.assertRaises(FileNotFoundError):
            manager.read_records()

    def test_write_records_and_backup(self):
        manager = ExcelManager(self.xlsx_path)
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
