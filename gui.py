import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctkinter
from datetime import date, datetime
import re

from tracker_core.excel_manager import ExcelManager
from tracker_core.evaluator import LicenseEvaluator
from tracker_core.gcp_client import GCPClient
from tracker_core.workspace_client import WorkspaceClient

# Set theme and appearance options
ctkinter_theme = "blue" # blue, green, dark-blue
ctk_appearance = "System" # System, Dark, Light

ctk_set_theme = ctkinter.set_default_color_theme(ctkinter_theme)
ctk_set_appearance = ctkinter.set_appearance_mode(ctk_appearance)

class GCATrackerApp(ctkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gemini Code Assist License Tracker")
        self.geometry("900x750")
        self.minsize(800, 650)

        # Main grid configuration (2 columns, multiple rows)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Log/Output area takes available space

        # --- HEADER PANEL ---
        self.header_frame = ctkinter.CTkFrame(self, height=60, corner_radius=0, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 5))
        
        title_font = ctkinter.CTkFont(size=24, weight="bold")
        self.title_label = ctkinter.CTkLabel(
            self.header_frame, 
            text="GCA License Tracker Dashboard", 
            font=title_font
        )
        self.title_label.pack(side="left", pady=10)

        # --- CONFIGURATION PANEL (Grid layout inside frame) ---
        self.config_frame = ctkinter.CTkFrame(self)
        self.config_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.config_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Row 1: Excel File Path
        self.file_label = ctkinter.CTkLabel(self.config_frame, text="Tracker Excel File:")
        self.file_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.file_entry = ctkinter.CTkEntry(self.config_frame)
        self.file_entry.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # Pre-fill default if available
        if os.path.exists("gca_tracker.xlsx"):
            self.file_entry.insert(0, os.path.abspath("gca_tracker.xlsx"))
        elif os.path.exists("gca_tracker_template.xlsx"):
            self.file_entry.insert(0, os.path.abspath("gca_tracker_template.xlsx"))

        self.browse_btn = ctkinter.CTkButton(self.config_frame, text="Browse...", command=self.browse_file)
        self.browse_btn.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        # Row 2: GCP Credentials
        self.project_label = ctkinter.CTkLabel(self.config_frame, text="GCP Project ID:")
        self.project_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.project_entry = ctkinter.CTkEntry(self.config_frame, placeholder_text="my-gca-project-id")
        self.project_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.date_label = ctkinter.CTkLabel(self.config_frame, text="Evaluation Date:")
        self.date_label.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        self.date_entry = ctkinter.CTkEntry(self.config_frame)
        self.date_entry.grid(row=1, column=3, padx=10, pady=5, sticky="ew")
        self.date_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        # Row 3: Billing & Order
        self.billing_label = ctkinter.CTkLabel(self.config_frame, text="Billing Account ID:")
        self.billing_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.billing_entry = ctkinter.CTkEntry(self.config_frame, placeholder_text="012345-6789AB-CDEF01")
        self.billing_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        self.order_label = ctkinter.CTkLabel(self.config_frame, text="Procurement Order ID:")
        self.order_label.grid(row=2, column=2, padx=10, pady=5, sticky="w")
        self.order_entry = ctkinter.CTkEntry(self.config_frame, placeholder_text="oph-987654321")
        self.order_entry.grid(row=2, column=3, padx=10, pady=5, sticky="ew")

        # Row 4: Google Workspace Checkbox
        self.workspace_var = tk.BooleanVar(value=False)
        self.workspace_checkbox = ctkinter.CTkCheckBox(
            self.config_frame, 
            text="Auto-Onboard Missing Users to Google Workspace Directory", 
            variable=self.workspace_var
        )
        self.workspace_checkbox.grid(row=3, column=0, columnspan=4, padx=10, pady=(5, 10), sticky="w")


        # --- OUTPUT/LOG AREA ---
        self.output_frame = ctkinter.CTkFrame(self)
        self.output_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_rowconfigure(1, weight=1)

        font_sub = ctkinter.CTkFont(size=14, weight="bold")
        self.output_header = ctkinter.CTkLabel(self.output_frame, text="Activity Logs & Actions Plan", font=font_sub)
        self.output_header.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        font_mono = ctkinter.CTkFont(family="Courier", size=12)
        self.log_textbox = ctkinter.CTkTextbox(self.output_frame, font=font_mono)
        self.log_textbox.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")


        # --- CONTROL ACTIONS PANEL ---
        self.control_frame = ctkinter.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))
        self.control_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.clear_btn = ctkinter.CTkButton(self.control_frame, text="Clear Logs", fg_color="gray", hover_color="#555555", command=self.clear_logs)
        self.clear_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        font_bold = ctkinter.CTkFont(weight="bold")
        self.dry_run_btn = ctkinter.CTkButton(self.control_frame, text="🔍 Dry Run (Analyze Plan)", font=font_bold, command=self.run_dry_run)
        self.dry_run_btn.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.execute_btn = ctkinter.CTkButton(self.control_frame, text="⚡ Execute GCA Sync", fg_color="#C82333", hover_color="#A71D2A", font=font_bold, command=self.run_execute)
        self.execute_btn.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

        # Initial log message
        self.log("Welcome to GCA License Tracker GUI.\n"
                 "Ensure you have authenticated with GCP and Workspace using:\n"
                 "  'gcloud auth application-default login --scopes=\"https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/admin.directory.user\"'\n\n"
                 "Select your tracker Excel file, enter your project details, and click 'Dry Run' to preview pending actions.")

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Tracker Excel File",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
        )
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
            self.log(f"\n[INFO] Loaded tracker file: {filename}")

    def log(self, text: str):
        self.log_textbox.insert(tk.END, text + "\n")
        self.log_textbox.see(tk.END)

    def clear_logs(self):
        self.log_textbox.delete("1.0", tk.END)

    def get_config(self):
        file_path = self.file_entry.get().strip()
        project_id = self.project_entry.get().strip() or None
        billing_id = self.billing_entry.get().strip() or None
        order_id = self.order_entry.get().strip() or None
        workspace = self.workspace_var.get()
        
        date_str = self.date_entry.get().strip()
        try:
            eval_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Invalid Date", f"Date format must be YYYY-MM-DD. Found: '{date_str}'")
            return None

        if not file_path:
            messagebox.showerror("Error", "Please select a Tracker Excel file.")
            return None

        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"Excel file not found: {file_path}")
            return None

        return {
            "file_path": file_path,
            "project_id": project_id,
            "billing_id": billing_id,
            "order_id": order_id,
            "eval_date": eval_date,
            "workspace": workspace
        }

    def run_dry_run(self):
        config = self.get_config()
        if not config:
            return

        self.log("\n" + "="*80)
        self.log(f"--- STARTING DRY RUN EVALUATION ({config['eval_date']}) ---")
        self.log(f"File: {config['file_path']}")
        self.log(f"Workspace Directory Check/Auto-Creation: {'Enabled' if config['workspace'] else 'Disabled'}")
        
        excel_manager = ExcelManager(config["file_path"])
        try:
            records = excel_manager.read_records()
        except Exception as e:
            self.log(f"[ERROR] Failed to parse Excel: {e}")
            return

        evaluator = LicenseEvaluator()
        to_provision, to_revoke, skipped = evaluator.evaluate(records, config["eval_date"])

        if skipped:
            self.log(f"\n⚠️  [SKIPPED ROWS]: {len(skipped)}")
            for item in skipped:
                self.log(f"   Row {item['row_index']}: {item['reason']}")

        self.log(f"\n📊 [EVALUATION PLAN]:")
        self.log(f"   To Provision: {len(to_provision)} records")
        self.log(f"   To Revoke:    {len(to_revoke)} records")

        if to_provision:
            self.log("\n👉 [PROVISIONS PENDING]:")
            for item in to_provision:
                self.log(f"   • {item['email']} (Team: {item['record'].get('Team Name', 'N/A')}, Start: {item['start_date']})")

        if to_revoke:
            self.log("\n👉 [REVOCATIONS PENDING]:")
            for item in to_revoke:
                self.log(f"   • {item['email']} (Team: {item['record'].get('Team Name', 'N/A')}, End: {item['end_date']})")

        if not to_provision and not to_revoke:
            self.log("\n✅ [STATUS]: Everything is up to date! No pending actions.")
        else:
            self.log("\n💡 Ready to execute. Fill in GCP configurations above and click 'Execute GCA Sync' to run.")
        self.log("="*80)

    def run_execute(self):
        config = self.get_config()
        if not config:
            return

        # Double check with user to prevent accidental execute
        if not messagebox.askyesno("Confirm Sync", "Are you sure you want to execute GCA license changes on Google Cloud?"):
            return

        # Ensure we have some config
        if not config["project_id"] and not (config["billing_id"] and config["order_id"]):
            messagebox.showerror("Error", "In Execute mode, you must provide either a GCP Project ID (for IAM) or Billing Account ID and Procurement Order ID (for licensing).")
            return

        self.log("\n" + "#"*80)
        self.log(f"--- STARTING GCP EXECUTION SYNC ({config['eval_date']}) ---")
        
        excel_manager = ExcelManager(config["file_path"])
        try:
            records = excel_manager.read_records()
        except Exception as e:
            self.log(f"[ERROR] Failed to parse Excel: {e}")
            return

        evaluator = LicenseEvaluator()
        to_provision, to_revoke, skipped = evaluator.evaluate(records, config["eval_date"])

        if not to_provision and not to_revoke:
            self.log("✅ No actions pending. Nothing to execute.")
            self.log("#"*80)
            return

        # Initialize GCP client
        self.log("🔐 Authenticating with Google Cloud...")
        gcp_client = GCPClient(config["project_id"], config["billing_id"], config["order_id"])
        success, msg = gcp_client.initialize()
        if not success:
            self.log(f"❌ [AUTH ERROR]: {msg}")
            self.log("#"*80)
            return
        
        self.log(f"   {msg}")

        # Initialize Workspace client if requested
        workspace_client = None
        if config["workspace"]:
            self.log("📂 Connecting to Google Workspace Admin Directory...")
            workspace_client = WorkspaceClient(gcp_client._session, project_id=config["project_id"])

        successful_provisions = 0
        successful_revocations = 0
        failed_actions = 0

        # Run Provisions
        if to_provision:
            self.log("\n🚀 Executing Provisions...")
            for item in to_provision:
                email = item["email"]
                row_idx = item["row_index"]
                self.log(f"   • Processing {email}...")

                # Workspace onboarding step
                if workspace_client:
                    self.log(f"     Checking directory account status...")
                    exists, ws_err = workspace_client.check_user_exists(email)
                    if ws_err:
                        self.log(f"     ✗ [Workspace Error]: {ws_err}")
                        failed_actions += 1
                        continue
                    
                    if not exists:
                        self.log(f"     User not found. Auto-onboarding to Workspace...")
                        
                        # Retrieve names directly from Excel record
                        first = item["record"].get("First Name", "").strip()
                        last = item["record"].get("Last Name", "").strip()
                        
                        if not first or not last:
                            self.log(f"     ✗ [Onboarding Error]: Cannot create account for {email} because 'First Name' or 'Last Name' is missing in the Excel sheet.")
                            failed_actions += 1
                            continue
                            
                        temp_password = WorkspaceClient.generate_random_password()
                        
                        ws_ok, ws_msg = workspace_client.create_user(email, first, last, temp_password)
                        if not ws_ok:
                            self.log(f"     ✗ [Workspace Creation Error]: {ws_msg}")
                            failed_actions += 1
                            continue
                        
                        creds_file = f"workspace_creations_{date.today().strftime('%Y%m%d')}.txt"
                        try:
                            with open(creds_file, "a", encoding="utf-8") as f:
                                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                f.write(f"Email:     {email}\n")
                                f.write(f"Name:      {first} {last}\n")
                                f.write(f"Temporary Password: {temp_password}\n")
                                f.write("-" * 50 + "\n")
                            self.log(f"     ✓ Successfully created directory account for {email}")
                            self.log(f"       Temporary credentials logged to local file: {creds_file}")
                        except Exception as e:
                            self.log(f"     ⚠ [Warning]: User created but failed to log to local file: {e}")
                            self.log(f"       Credentials to distribute: Email={email}, Pass={temp_password}")
                    else:
                        self.log(f"     ✓ Directory account already exists.")

                # IAM Bindings
                iam_ok, iam_msg = gcp_client.add_iam_role(email, "roles/cloudaicompanion.user")
                if not iam_ok:
                    self.log(f"     ✗ [GCA User IAM Error]: {iam_msg}")
                    failed_actions += 1
                    continue

                iam_ok2, iam_msg2 = gcp_client.add_iam_role(email, "roles/serviceusage.serviceUsageConsumer")
                if not iam_ok2:
                    self.log(f"     ✗ [Service Usage IAM Error]: {iam_msg2}")
                    gcp_client.remove_iam_role(email, "roles/cloudaicompanion.user")
                    failed_actions += 1
                    continue

                # Procurement Assignment
                lic_ok, lic_msg = gcp_client.assign_license(email)
                if not lic_ok:
                    self.log(f"     ✗ [Licensing Error]: {lic_msg}")
                    gcp_client.remove_iam_role(email, "roles/serviceusage.serviceUsageConsumer")
                    gcp_client.remove_iam_role(email, "roles/cloudaicompanion.user")
                    failed_actions += 1
                    continue

                records[row_idx]["Status"] = "Provisioned"
                self.log(f"     ✓ Successfully provisioned access for {email}")
                successful_provisions += 1

        # Run Revocations
        if to_revoke:
            self.log("\n🚀 Executing Revocations...")
            for item in to_revoke:
                email = item["email"]
                row_idx = item["row_index"]
                self.log(f"   • Processing {email}...")

                # Remove IAM Bindings
                iam_ok, iam_msg = gcp_client.remove_iam_role(email, "roles/cloudaicompanion.user")
                if not iam_ok:
                    self.log(f"     ✗ [GCA User IAM Error]: {iam_msg}")
                    failed_actions += 1
                    continue

                iam_ok2, iam_msg2 = gcp_client.remove_iam_role(email, "roles/serviceusage.serviceUsageConsumer")
                if not iam_ok2:
                    self.log(f"     ✗ [Service Usage IAM Error]: {iam_msg2}")
                    failed_actions += 1
                    continue

                # Unassign Procurement
                lic_ok, lic_msg = gcp_client.unassign_license(email)
                if not lic_ok:
                    self.log(f"     ✗ [Licensing Error]: {lic_msg}")
                    failed_actions += 1
                    continue

                records[row_idx]["Status"] = "Revoked"
                self.log(f"     ✓ Successfully revoked access for {email}")
                successful_revocations += 1

        # Write updates back to Excel
        if successful_provisions > 0 or successful_revocations > 0:
            try:
                backup_path = excel_manager.write_records(records)
                self.log(f"\n💾 [EXCEL UPDATED]: File successfully saved!")
                self.log(f"   Backup created: {backup_path}")
            except Exception as e:
                self.log(f"\n❌ [CRITICAL]: Failed to update Excel file: {e}")
                messagebox.showerror("Excel Save Error", f"Failed to save Excel changes: {e}")

        self.log("\n🏆 --- SYNC SUMMARY ---")
        self.log(f"   Provisions Successful: {successful_provisions}")
        self.log(f"   Revocations Successful: {successful_revocations}")
        self.log(f"   Failed Actions:         {failed_actions}")
        self.log("#"*80)

        messagebox.showinfo(
            "Sync Complete", 
            f"Successfully processed:\n"
            f"• Provisions: {successful_provisions}\n"
            f"• Revocations: {successful_revocations}\n"
            f"• Failed: {failed_actions}"
        )

if __name__ == "__main__":
    app = GCATrackerApp()
    app.mainloop()
