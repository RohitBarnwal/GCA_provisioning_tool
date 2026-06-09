from datetime import datetime, date
from typing import List, Dict, Tuple, Any

class LicenseEvaluator:
    @staticmethod
    def parse_date(date_str: str) -> date:
        """Parses YYYY-MM-DD date string into a datetime.date object."""
        if not date_str:
            raise ValueError("Date string is empty")
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()

    def evaluate(self, records: List[Dict[str, str]], evaluation_date: date = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Evaluates records and splits them into:
        - to_provision (Start Date <= target_date AND Status == 'Pending')
        - to_revoke (End Date <= target_date AND Status == 'Provisioned')
        - skipped (parsing error or other validation issues)
        """
        if evaluation_date is None:
            evaluation_date = date.today()

        to_provision = []
        to_revoke = []
        skipped = []

        for index, record in enumerate(records):
            email = record.get("Email", "").strip()
            status = record.get("Status", "").strip()
            start_date_str = record.get("Start Date", "").strip()
            end_date_str = record.get("End Date", "").strip()

            if not email:
                skipped.append({
                    "record": record,
                    "row_index": index + 2, # 1-based index plus header
                    "reason": "Missing email"
                })
                continue

            try:
                start_date = self.parse_date(start_date_str) if start_date_str else None
                end_date = self.parse_date(end_date_str) if end_date_str else None
            except ValueError as e:
                skipped.append({
                    "record": record,
                    "row_index": index + 2,
                    "reason": f"Invalid date format (must be YYYY-MM-DD): {e}"
                })
                continue

            # Evaluate provisioning
            if status.lower() == "pending":
                if start_date and start_date <= evaluation_date:
                    to_provision.append({
                        "record": record,
                        "row_index": index, # raw 0-based list index for update reference
                        "email": email,
                        "start_date": start_date
                    })
            # Evaluate revocation
            elif status.lower() == "provisioned":
                if end_date and end_date <= evaluation_date:
                    to_revoke.append({
                        "record": record,
                        "row_index": index,
                        "email": email,
                        "end_date": end_date
                    })

        return to_provision, to_revoke, skipped
