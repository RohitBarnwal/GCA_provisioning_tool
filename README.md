# GCA License Tracker (Python MVP)

The **Gemini Code Assist (GCA) License Tracker** is a low-tech, locally executed IT automation tool designed to help customer admins track, provision, and deprovision GCA licenses accurately. 

Using a local Excel spreadsheet (`gca_tracker.xlsx`), this tool parses user-requested Start/End dates and coordinates automatically with Google Cloud APIs (Commerce Procurement and IAM) to grant/revoke access. It supports both an **Interactive Desktop GUI** (powered by `CustomTkinter`) and an **Enhanced CLI** (powered by `Typer` and `Rich`), both operating with full default `Dry-Run` security.

Additionally, this tool includes built-in **programmatic Google Workspace onboarding support**. It can automatically check if a pending user has an email directory account in Google Workspace and, if missing, securely generate their user account, parse their names from their email, auto-create a strong random temporary password, and write their credentials to a secure, private local report.

---

## 📁 Repository Structure
```text
.
├── tracker_core/
│   ├── excel_manager.py   # Parses, updates, and creates backups of the Excel spreadsheet
│   ├── evaluator.py       # Filters records into To Provision/Revoke based on dates
│   ├── gcp_client.py      # Authenticates and interacts with GCP APIs (REST)
│   └── workspace_client.py# Checks and creates accounts in Google Workspace Directory
├── tests/
│   ├── test_excel_manager.py # Unit tests for Excel logic
│   ├── test_evaluator.py  # Unit tests for business logic
│   ├── test_gcp_client.py # Unit tests with mocked GCP calls
│   └── test_workspace_client.py # Unit tests for Workspace directory calls
├── cli.py                 # Elegant Terminal Interface
├── gui.py                 # Polished Standalone Desktop Application
├── gca_tracker_template.xlsx # Default sample template for tracking
├── requirements.txt       # Project python dependencies
└── README.md              # Project documentation (this file)
```

---

## 🛠️ Prerequisites

1. **Google Cloud SDK (`gcloud`):**
   Install the `gcloud` CLI and log in with your administrative credentials:
   ```bash
   gcloud auth login
   ```

2. **Application Default Credentials (ADC):**
   The Python script authenticates via local credentials. Generate local ADC credentials.

   *   **Standard Mode (GCP Licensing + IAM only):**
       ```bash
       gcloud auth application-default login
       ```
   *   **Workspace Integration Mode (GCP + Workspace Directory Creation):**
       You must include Workspace-specific Admin API scopes when logging in. This authorizes the script to create users under your personal Super-Admin or User-Admin identity:
       ```bash
       gcloud auth application-default login --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/admin.directory.user"
       ```
   
   *Note: Ensure your authenticated account has permissions to manage project IAM policies (e.g. `Project IAM Admin`), Billing account license pools (e.g. `Billing Account Admin`), and, if Workspace mode is used, User directory administrative permissions.*

3. **Python 3.9+**

---

## 🚀 Getting Started

### 1. Set Up Virtual Environment
Create and activate a virtual environment, then install the dependencies:
```bash
# Create venv
python3 -m venv venv

# Activate venv (macOS/Linux)
source venv/bin/activate

# Activate venv (Windows)
.\venv\Scripts\activate

# Install requirements (includes openpyxl, typer, rich, customtkinter)
pip install -r requirements.txt
```

### 2. Prepare Your Excel File
Copy `gca_tracker_template.xlsx` to `gca_tracker.xlsx` and populate it with your team's GCA assignments:
```bash
cp gca_tracker_template.xlsx gca_tracker.xlsx
```

#### Spreadsheet Columns:
*   **Email:** User's GCP identity email.
*   **Team Name:** Admin context (e.g., "Engineering", "Design").
*   **Start Date:** Date when access starts (`YYYY-MM-DD`).
*   **End Date:** Date when access should be revoked (`YYYY-MM-DD`).
*   **Status:** Must be `Pending`, `Provisioned`, or `Revoked`.
*   **Reason:** Audit trail info.

---

## 🖥️ Running the Desktop GUI

To open the modern standalone desktop dashboard, run:
```bash
python gui.py
```

### GUI Features:
*   **File Picker:** Click "Browse..." to select your tracker Excel (`.xlsx`) file.
*   **Settings Form:** Fill in your `GCP Project ID`, `Billing Account ID`, and `Procurement Order ID` (optional parameters, skip what you don't need).
*   **Auto-Onboard Checkbox:** Check **Auto-Onboard Missing Users to Google Workspace Directory** to automatically query Workspace and safely generate accounts and passwords for users who do not exist.
*   **Dry Run:** Click **Dry Run (Analyze Plan)** to inspect which rows will be acted on today in a safe mode.
*   **Execute Sync:** Click **Execute GCA Sync** (requires confirmation) to securely apply the changes. It automatically updates statuses in the active worksheet and creates a timestamped backup inside a `backups/` directory, **preserving any custom styles, formatting, or other sheets in the workbook!**
*   **Private Credentials Report:** If a user is created in Workspace, a local file `workspace_creations_YYYYMMDD.txt` is written with their generated temporary password (this file is fully ignored by Git).

---

## 💻 Running the CLI

If you prefer to operate directly from your shell, use the CLI.

### 🔍 Dry-Run Mode (Default)
Safe preview mode. Parses the Excel file and displays pending actions in a color-coded Rich table without modifying anything:
```bash
# Evaluate today's actions on default 'gca_tracker.xlsx'
python cli.py

# Evaluate a specific date (great for future planning!)
python cli.py --date 2026-06-08

# Specify a custom Excel file
python cli.py --file path/to/my_tracker.xlsx
```

### ⚡ Execute Mode
Executes the API calls and writes the results back to the Excel spreadsheet. **Requires an explicit `--execute` or `-x` flag.**
```bash
# Sync GCA User and Service Usage IAM roles on project
python cli.py --project my-gca-project-id --execute

# Sync both IAM and Procurement Licencing Entitlements
python cli.py -p my-gca-project-id -b 012345-6789AB-CDEF01 -o oph-987654321 -x

# Sync IAM, Procurement, AND Auto-Create Missing Users in Google Workspace Directory
python cli.py -p my-gca-project-id -b 012345-6789AB-CDEF01 -o oph-987654321 --workspace -x
```

---

## 🧪 Running Unit Tests

To run the complete test suite (18 tests verifying parsing, logical evaluations, Workspace API calls, and mock GCP interactions):
```bash
python -m unittest discover -s tests
```
