# GCA License Tracker - Implementation Plan

## Background & Motivation
Managing Gemini Code Assist (GCA) licenses manually introduces the risk of wasted spend due to forgotten deprovisioning, and manual errors when granting IAM roles or assigning procurement entitlements. The goal is to build an IT automation tool that allows admins to track GCA requests in a simple CSV file and execute provisioning/revocation actions accurately via local GCP credentials.

## Scope & Impact
**In Scope:**
- A core Python engine to process a local `gca_tracker.csv`.
- Evaluation logic to determine required actions based on Start Date, End Date, and Current Status.
- GCP Integration (IAM Role Binding on a specified project/org, and Consumer Procurement API for license assignments using `google-auth` REST calls).
- Two user interfaces sharing the core engine:
  - An Enhanced CLI (using `Typer` and `Rich`).
  - A Desktop GUI (using `CustomTkinter`).
- Safe execution mechanisms: Default Dry-Run reporting before actual API execution.

**Out of Scope:**
- Cloud-hosted automation (e.g., Cloud Functions, Cron Jobs). This remains a locally executed tool.
- Excel (`.xlsx`) support. We are utilizing CSV for simplicity.

## Proposed Solution
The project will be structured into modular components:

1.  **`tracker_core/` (Core Logic)**
    -   `csv_manager.py`: Parses the CSV, validates columns (`Email`, `Start Date`, `End Date`, `Status`), and writes status updates back to the file. Backs up the CSV before modification.
    -   `evaluator.py`: Compares dates to today's date.
        -   *To Provision:* `Start Date <= Today` AND `Status == Pending`.
        -   *To Revoke:* `End Date <= Today` AND `Status == Provisioned`.
    -   `gcp_client.py`: Uses `google-auth` to fetch credentials and makes REST API calls to the Cloud Commerce Consumer Procurement API to assign/unassign licenses. It will also handle the `roles/cloudaicompanion.user` IAM role binding.

2.  **`cli.py` (Enhanced CLI Interface)**
    -   Uses `Typer` to accept arguments like `--dry-run`, `--execute`, and `--file`.
    -   Uses `Rich` to print visual tables of pending actions to the terminal.

3.  **`gui.py` (Desktop GUI Interface)**
    -   Built with `CustomTkinter` for a modern look.
    -   Provides a file selector, a tabular summary of the CSV, and large action buttons for "Dry Run" and "Execute".
    -   Routes output (like Rich tables) to a log text box within the GUI.

## Alternatives Considered
-   **Excel Parsing (`openpyxl` / `pandas`):** Initially proposed in the PRD. Dropped in favor of CSV based on user preference to reduce dependency and parsing complexity.
-   **Streamlit Web App:** Considered for the GUI layer. CustomTkinter was selected by the user to provide a true standalone desktop experience without spawning a local web server.

## Phased Implementation Plan
-   **Phase 1: Project Setup & Core Logic**
    -   Initialize virtual environment and `requirements.txt` (`google-auth`, `google-cloud-resourcemanager`, `requests`, `typer`, `rich`, `customtkinter`).
    -   Implement the CSV reading/writing and date evaluation engine.
-   **Phase 2: CLI Implementation & Dry-Run**
    -   Build `cli.py`.
    -   Implement the Dry-Run workflow that outputs Rich tables of what *would* happen.
-   **Phase 3: GCP API Integrations**
    -   Implement Commerce Consumer Procurement logic (license pooling).
    -   Connect these to the Execute workflow.
-   **Phase 4: CustomTkinter GUI Implementation**
    -   Build `gui.py` wrapping the core engine.
    -   Link GUI buttons to Dry-Run and Execute logic, displaying results visually.
-   **Phase 5: Testing & Refinement**
    -   Add unit tests for the evaluator and CSV parsing.
    -   Perform end-to-end testing with mock CSVs.

## Verification
-   **Dry-Run Verification:** Ensure the CLI and GUI accurately identify which rows need action without making any API calls.
-   **Execution Verification:** In a test GCP environment, verify that executing the script updates IAM policies and entitlements correctly, and that the CSV file is successfully updated with "Provisioned" and "Revoked" statuses.

## Migration & Rollback
-   **CSV Backup:** Before the `core.py` makes any changes to the statuses, it will create a timestamped backup of the `.csv` file (e.g., `gca_tracker_backup_20260608.csv`) to prevent data loss in case of a crash during the write process.
-   **Idempotency:** The date evaluator ensures that if the script is interrupted and re-run, it will only attempt to provision/revoke users who are still in `Pending` or `Provisioned` states, preventing duplicate actions.