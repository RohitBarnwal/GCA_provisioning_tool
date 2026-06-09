# GCA License Tracker (Python MVP)

The **Gemini Code Assist (GCA) License Tracker** is a low-tech, locally executed IT automation tool designed to help customer admins track, provision, and deprovision GCA licenses accurately. 

Using a local CSV file (`gca_tracker.csv`), this tool parses user-requested Start/End dates and coordinates automatically with Google Cloud APIs (Commerce Procurement and IAM) to grant/revoke access. It supports both an **Interactive Desktop GUI** (powered by `CustomTkinter`) and an **Enhanced CLI** (powered by `Typer` and `Rich`), both operating with full default `Dry-Run` security.

---

## 📁 Repository Structure
```text
.
├── tracker_core/
│   ├── csv_manager.py     # Parses, updates, and creates backups of the CSV
│   ├── evaluator.py       # Filters records into To Provision/Revoke based on dates
│   └── gcp_client.py      # Authenticates and interacts with GCP APIs (REST)
├── tests/
│   ├── test_csv_manager.py# Unit tests for CSV logic
│   ├── test_evaluator.py  # Unit tests for business logic
│   └── test_gcp_client.py # Unit tests with mocked GCP calls
├── cli.py                 # Elegant Terminal Interface
├── gui.py                 # Polished Standalone Desktop Application
├── gca_tracker_template.csv # Default sample template for tracking
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
   The Python script authenticates via local credentials. To enable this, generate local ADC credentials:
   ```bash
   gcloud auth application-default login
   ```
   *Note: Ensure your authenticated account has permissions to manage project IAM policies (e.g. `Project IAM Admin`) and Billing account license pools (e.g. `Billing Account Admin` or `Procurement Editor`).*

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

# Install requirements
pip install -r requirements.txt
```

### 2. Prepare Your CSV File
Copy `gca_tracker_template.csv` to `gca_tracker.csv` and populate it with your team's GCA assignments:
```bash
cp gca_tracker_template.csv gca_tracker.csv
```

#### CSV Schema:
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
*   **File Picker:** Click "Browse..." to select your tracker CSV file.
*   **Settings Form:** Fill in your `GCP Project ID`, `Billing Account ID`, and `Procurement Order ID` (optional parameters, skip what you don't need).
*   **Dry Run:** Click **Dry Run (Analyze Plan)** to inspect which rows will be acted on today in a safe mode.
*   **Execute Sync:** Click **Execute GCA Sync** (requires confirmation) to securely apply the changes on Google Cloud. It automatically updates statuses in the CSV and creates a timestamped backup inside a `backups/` directory!

---

## 💻 Running the CLI

If you prefer to operate directly from your shell, use the CLI.

### 🔍 Dry-Run Mode (Default)
Safe preview mode. Parses the CSV and displays pending actions in a color-coded Rich table without modifying anything:
```bash
# Evaluate today's actions on default 'gca_tracker.csv'
python cli.py

# Evaluate a specific date (great for future planning!)
python cli.py --date 2026-06-08

# Specify a custom CSV file
python cli.py --file path/to/my_tracker.csv
```

### ⚡ Execute Mode
Executes the API calls and writes the results back to the CSV. **Requires an explicit `--execute` or `-x` flag.**
```bash
# Sync IAM Role bindings for GCA (adds/removes 'roles/cloudaicompanion.user')
python cli.py --project my-gca-project-id --execute

# Sync both IAM and Procurement Licencing Entitlements
python cli.py -p my-gca-project-id -b 012345-6789AB-CDEF01 -o oph-987654321 -x
```

---

## 🧪 Running Unit Tests

To run the complete test suite (12 tests verifying parsing, logical evaluations, and mock GCP interactions):
```bash
python -m unittest discover -s tests
```
