# PRD: GCA License Tracker (Python MVP)

## 👍 Approvals
| ROLE | TEAMMATE | REVIEWED | STATUS |
| :---- | :---- | :---- | :---- |
| Product | User | Pending | Pending |

## 📝 Abstract
The Gemini Code Assist (GCA) License Tracker (Python MVP) is a low-tech IT automation tool built using a local Python script and an XLSX (Excel) tracking file. Its purpose is to provide customer admins with a simple, locally-executed mechanism to track, provision, and deprovision GCA licenses. This solution avoids cloud infrastructure overhead like Apps Script while still preventing manual tracking errors and wasted spend.

## 🎯 Business Objectives
- Automate the provisioning and deprovisioning lifecycle of GCA licenses using a locally managed tracking sheet.
- Eliminate wasted license costs by ensuring accurate and timely deprovisioning when a user's requested duration ends.
- Provide a clear, auditable trail of actions through both dry-run reporting and direct execution modes.

## 📊 KPI
| GOAL | METRIC | QUESTION |
| :---- | :---- | :---- |
| Operational Efficiency | Admin hours saved per week | How much time is saved by using the script vs manually checking the Google Cloud Console? |
| Cost Savings | % of licenses reclaimed on time | Are we achieving 100% on-time deprovisioning to prevent wasted spend? |

## 🏆 Success Criteria
- Script correctly parses the local XLSX file to identify pending provisions and pending revocations based on Start Date and End Date.
- Script supports a `--dry-run` mode that safely outputs a report of actions to be taken without modifying GCP.
- Script supports an `--execute` mode that correctly calls the GCP Consumer Procurement API and Cloud Resource Manager API with 0 manual errors.

## 🚶‍♀️ User Journeys
### 📖 Scenarios
1. An admin updates the local `gca_tracker.xlsx` file with a new user's email, requested start date, and end date. The admin runs the script in dry-run mode to verify the pending actions. Satisfied, the admin runs the script in execute mode. The script assigns the GCA IAM role and Procurement license, then updates the XLSX file row status to "Provisioned".

### 🕹️ User Flow
1. Admin manually updates `gca_tracker.xlsx` with user details and requested dates.
2. Admin opens their terminal and runs `python tracker.py --dry-run`.
3. Admin reviews the output report.
4. Admin runs `python tracker.py --execute`.
5. Python script authenticates via local gcloud credentials.
6. Script triggers GCP API calls for users needing provisioning (Start Date <= Today and Status == 'Pending').
7. Script triggers GCP API calls for users needing revocation (End Date <= Today and Status == 'Provisioned').
8. Script updates the XLSX file with the new statuses.

## 🧰 Functional Requirements
- **Intake/Dashboard:** Local `gca_tracker.xlsx` file with columns: Email, Team Name, Start Date, End Date, Status, Reason.
- **Dry-Run Mode:** Generate a console report of which emails will be provisioned or revoked based on the current date, without making GCP changes.
- **Execution Mode:** Call Cloud Commerce Consumer Procurement API and Cloud Resource Manager API to perform the actual provisioning/deprovisioning.
- **Status Updating:** The script must write back to the XLSX file to update the "Status" column (e.g., Pending -> Provisioned, Provisioned -> Revoked) after successful execution.

## 📐 Model Requirements
N/A - This is an IT automation tool.

## 🧮 Data Requirements
N/A - This is an IT automation tool.

## 💬 Prompt Requirements
N/A - This is an IT automation tool.

## 🧪 Eval Spec for Testing and Measurement
- Unit tests for the XLSX parsing and writing logic.
- Unit tests for GCP API client wrappers (using mocked API responses).
- Manual E2E test using a test GCP project and `--execute` mode.

## ⚠️ Eval Gates for Risks & Mitigations
| RISK (FAILURE MODE) | SEVERITY | MITIGATION |
| :---- | :---- | :---- |
| Accidental execution | High | Require explicit `--execute` flag; default to dry-run mode. |
| XLSX file lock/corruption | Medium | Script should create a backup copy of the XLSX before writing changes. |

## 💰 AI Costs & Latency
N/A

## 🔗 Assumptions & Dependencies
- Customer's Gemini Code Assist subscription is configured for "Manual Assignment".
- Admin has Google Cloud SDK (`gcloud`) installed, authenticated, and has appropriate IAM permissions (Project IAM Admin, Billing Account Admin/Procurement Editor).
- Python 3.9+ and required libraries (e.g., `pandas`, `openpyxl`, `google-cloud-*`) are installed locally.

## 🔒 Compliance/Privacy/Legal
- The XLSX file containing user data remains on the admin's local machine, reducing data exposure risks.

## 📣 GTM/Rollout Plan
**Packaging and Distribution:**
- Package as a GitHub repository containing `tracker.py`, `requirements.txt`, a sample `gca_tracker_template.xlsx`, and a `README.md`.
- `README.md` will provide instructions to install Python dependencies, authenticate via `gcloud auth application-default login`, and use the CLI flags.
