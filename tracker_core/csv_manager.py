import csv
import os
import shutil
from datetime import datetime
from typing import List, Dict

REQUIRED_COLUMNS = ["Email", "Team Name", "Start Date", "End Date", "Status", "Reason"]

class CSVManager:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def read_records(self) -> List[Dict[str, str]]:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Tracker CSV file not found at: {self.file_path}")
        
        records = []
        with open(self.file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate columns
            headers = reader.fieldnames if reader.fieldnames else []
            # Strip whitespace from headers
            headers = [h.strip() for h in headers if h]
            missing = [col for col in REQUIRED_COLUMNS if col not in headers]
            if missing:
                raise ValueError(f"CSV is missing required columns: {missing}. Found: {headers}")
            
            for row in reader:
                # Clean up keys and values
                clean_row = {k.strip(): v.strip() for k, v in row.items() if k}
                records.append(clean_row)
        return records

    def create_backup(self) -> str:
        if not os.path.exists(self.file_path):
            return ""
        
        dir_name = os.path.dirname(os.path.abspath(self.file_path))
        backup_dir = os.path.join(dir_name, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        base_name = os.path.basename(self.file_path)
        name, ext = os.path.splitext(base_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{name}_backup_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        shutil.copy2(self.file_path, backup_path)
        return backup_path

    def write_records(self, records: List[Dict[str, str]]) -> str:
        # Create a backup first
        backup_path = self.create_backup()
        
        with open(self.file_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            for record in records:
                # Filter to only write the required columns
                row = {col: record.get(col, "") for col in REQUIRED_COLUMNS}
                writer.writerow(row)
                
        return backup_path
