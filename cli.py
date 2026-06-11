import os
import typer
from datetime import date, datetime
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from tracker_core.excel_manager import ExcelManager
from tracker_core.evaluator import LicenseEvaluator
from tracker_core.gcp_client import GCPClient
from tracker_core.workspace_client import WorkspaceClient

app = typer.Typer(help="GCA License Tracker CLI")
console = Console()

@app.command()
def run(
    file: str = typer.Option("gca_tracker.xlsx", "--file", "-f", help="Path to gca_tracker.xlsx"),
    project_id: Optional[str] = typer.Option(None, "--project", "-p", help="GCP Project ID to manage IAM bindings"),
    billing_account_id: Optional[str] = typer.Option(None, "--billing-account", "-b", help="GCP Billing Account ID for Procurement API"),
    order_id: Optional[str] = typer.Option(None, "--order", "-o", help="GCP Order ID for Procurement API"),
    execute: bool = typer.Option(False, "--execute", "-x", help="Actually execute GCP changes and update Excel (default is dry-run)"),
    eval_date_str: Optional[str] = typer.Option(None, "--date", "-d", help="Override evaluation date (YYYY-MM-DD), default is today"),
    workspace: bool = typer.Option(False, "--workspace", "-w", help="Enable Google Workspace directory check and auto-creation of missing users"),
):
    """
    Evaluates and processes GCA user licenses and IAM role bindings.
    By default, runs in DRY-RUN mode to show actions without modifying anything.
    """
    
    # 1. Determine Evaluation Date
    eval_date = date.today()
    if eval_date_str:
        try:
            eval_date = datetime.strptime(eval_date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            console.print(f"[bold red]Error:[/] Invalid date format '{eval_date_str}'. Must be YYYY-MM-DD.", err=True)
            raise typer.Exit(code=1)

    # 2. Check and load Excel
    if not os.path.exists(file):
        # Fallback to template if gca_tracker.xlsx doesn't exist to make UX easy
        if file == "gca_tracker.xlsx" and os.path.exists("gca_tracker_template.xlsx"):
            console.print("[yellow]gca_tracker.xlsx not found. Copying from gca_tracker_template.xlsx...[/]")
            import shutil
            shutil.copy("gca_tracker_template.xlsx", "gca_tracker.xlsx")
        else:
            console.print(f"[bold red]Error:[/] File not found: '{file}'", err=True)
            raise typer.Exit(code=1)

    excel_manager = ExcelManager(file)
    try:
        records = excel_manager.read_records()
    except Exception as e:
        console.print(f"[bold red]Error loading Excel:[/] {e}", err=True)
        raise typer.Exit(code=1)

    # 3. Evaluate records
    evaluator = LicenseEvaluator()
    to_provision, to_revoke, skipped = evaluator.evaluate(records, eval_date)

    # 4. Print Status Dashboard / Dry Run Report
    console.print(Panel(
        f"[bold blue]GCA License Tracker[/]\n"
        f"File: [yellow]{file}[/]\n"
        f"Evaluation Date: [green]{eval_date}[/]\n"
        f"Mode: [bold]{'EXECUTE' if execute else 'DRY-RUN (Safe Mode)'}[/]\n"
        f"Configuration: Project={project_id or 'None'}, BillingAccount={billing_account_id or 'None'}, Order={order_id or 'None'}, WorkspaceOnboarding={'Enabled' if workspace else 'Disabled'}",
        title="Session Info"
    ))

    # Display skipped rows if any
    if skipped:
        skipped_table = Table(title="Skipped Rows (Validation Failures)", header_style="bold magenta")
        skipped_table.add_column("Row #")
        skipped_table.add_column("Details")
        skipped_table.add_column("Reason", style="red")
        for item in skipped:
            # item["record"] contains the raw dictionary
            skipped_table.add_row(
                str(item["row_index"]),
                str(item["record"]),
                item["reason"]
            )
        console.print(skipped_table)
        console.print()

    # Display Actions Table
    actions_table = Table(title="Pending License Actions", header_style="bold cyan")
    actions_table.add_column("Action", style="bold")
    actions_table.add_column("Email", style="green")
    actions_table.add_column("Team")
    actions_table.add_column("Date Trigger", style="yellow")
    actions_table.add_column("Reason")

    for item in to_provision:
        rec = item["record"]
        actions_table.add_row(
            "PROVISION",
            item["email"],
            rec.get("Team Name", "N/A"),
            f"Start: {item['start_date']}",
            rec.get("Reason", "")
        )

    for item in to_revoke:
        rec = item["record"]
        actions_table.add_row(
            "REVOKE",
            item["email"],
            rec.get("Team Name", "N/A"),
            f"End: {item['end_date']}",
            rec.get("Reason", "")
        )

    if not to_provision and not to_revoke:
        console.print("[bold green]No actions needed today![/]")
        if not execute:
            return
    else:
        console.print(actions_table)
        console.print()

    # 5. Execute Mode
    if not execute:
        console.print("[bold yellow]This was a DRY-RUN. No changes were made to GCP, Workspace, or your Excel file.[/]")
        console.print("To execute these actions, run with the [green]--execute[/] (or [green]-x[/]) flag.")
        return

    # Check that at least one config element is present
    if not project_id and not (billing_account_id and order_id):
        console.print("[bold red]Error:[/] You must provide either --project (for IAM) or --billing-account and --order (for Procurement) in execute mode.", err=True)
        raise typer.Exit(code=1)

    # Initialize GCP Client
    gcp_client = GCPClient(project_id, billing_account_id, order_id)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task("Authenticating with Google Cloud...", total=None)
        success, msg = gcp_client.initialize()
        if not success:
            progress.stop()
            console.print(f"[bold red]Authentication Error:[/] {msg}", err=True)
            raise typer.Exit(code=1)

    # Track successes
    successful_provisions = 0
    successful_revocations = 0
    failed_actions = 0

    # Initialize Workspace Client if enabled
    workspace_client = None
    if workspace:
        workspace_client = WorkspaceClient(gcp_client._session)

    # Process Provisions
    if to_provision:
        console.print("[bold green]Executing Provisioning Actions...[/]")
        for item in to_provision:
            email = item["email"]
            row_idx = item["row_index"]
            console.print(f"  • Processing [cyan]{email}[/]...")
            
            # Step 0: Google Workspace directory onboarding
            if workspace_client:
                console.print(f"    Checking Workspace directory for {email}...")
                exists, ws_err = workspace_client.check_user_exists(email)
                if ws_err:
                    console.print(f"    [red]✗ Workspace Query Error:[/] {ws_err}")
                    failed_actions += 1
                    continue
                
                if not exists:
                    console.print(f"    User {email} not found in directory. Attempting creation...")
                    first, last = WorkspaceClient.parse_name_from_email(email)
                    temp_password = WorkspaceClient.generate_random_password()
                    
                    ws_ok, ws_msg = workspace_client.create_user(email, first, last, temp_password)
                    if not ws_ok:
                        console.print(f"    [red]✗ Workspace Creation Error:[/] {ws_msg}")
                        failed_actions += 1
                        continue
                    
                    # Log credentials to local, private text file (ignored by Git)
                    creds_file = f"workspace_creations_{date.today().strftime('%Y%m%d')}.txt"
                    try:
                        with open(creds_file, "a", encoding="utf-8") as f:
                            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"Email:     {email}\n")
                            f.write(f"Name:      {first} {last}\n")
                            f.write(f"Temporary Password: {temp_password}\n")
                            f.write("-" * 50 + "\n")
                        console.print(f"    [green]✓ Created Directory Account for {email}![/]")
                        console.print(f"      Temporary credentials logged to [yellow]{creds_file}[/]")
                    except Exception as e:
                        console.print(f"    [yellow]⚠ Warning:[/] Created user, but failed to write local backup file: {e}")
                        console.print(f"      Credentials to distribute: Email={email}, Pass={temp_password}")
                else:
                    console.print(f"    [green]✓ User already exists in directory.[/]")

            # Step A: IAM bindings
            iam_ok, iam_msg = gcp_client.add_iam_role(email, "roles/cloudaicompanion.user")
            if not iam_ok:
                console.print(f"    [red]✗ GCA User IAM Error:[/] {iam_msg}")
                failed_actions += 1
                continue

            iam_ok2, iam_msg2 = gcp_client.add_iam_role(email, "roles/serviceusage.serviceUsageConsumer")
            if not iam_ok2:
                console.print(f"    [red]✗ Service Usage IAM Error:[/] {iam_msg2}")
                # Rollback GCA user role on failure
                gcp_client.remove_iam_role(email, "roles/cloudaicompanion.user")
                failed_actions += 1
                continue
                
            # Step B: Procurement licensing
            lic_ok, lic_msg = gcp_client.assign_license(email)
            if not lic_ok:
                console.print(f"    [red]✗ License Error:[/] {lic_msg}")
                # Rollback both IAM roles on failure
                gcp_client.remove_iam_role(email, "roles/serviceusage.serviceUsageConsumer")
                gcp_client.remove_iam_role(email, "roles/cloudaicompanion.user")
                failed_actions += 1
                continue

            # Success! Update status in record
            records[row_idx]["Status"] = "Provisioned"
            console.print(f"    [green]✓ Successfully provisioned GCA access for {email}[/]")
            successful_provisions += 1

    # Process Revocations
    if to_revoke:
        console.print("[bold red]Executing Revocation Actions...[/]")
        for item in to_revoke:
            email = item["email"]
            row_idx = item["row_index"]
            console.print(f"  • Processing [cyan]{email}[/]...")
            
            # Step A: Remove IAM bindings
            iam_ok, iam_msg = gcp_client.remove_iam_role(email, "roles/cloudaicompanion.user")
            if not iam_ok:
                console.print(f"    [red]✗ GCA User IAM Error:[/] {iam_msg}")
                failed_actions += 1
                continue

            iam_ok2, iam_msg2 = gcp_client.remove_iam_role(email, "roles/serviceusage.serviceUsageConsumer")
            if not iam_ok2:
                console.print(f"    [red]✗ Service Usage IAM Error:[/] {iam_msg2}")
                failed_actions += 1
                continue

            # Step B: Unassign Procurement License
            lic_ok, lic_msg = gcp_client.unassign_license(email)
            if not lic_ok:
                console.print(f"    [red]✗ License Error:[/] {lic_msg}")
                failed_actions += 1
                continue

            # Success! Update status in record
            records[row_idx]["Status"] = "Revoked"
            console.print(f"    [green]✓ Successfully revoked GCA access for {email}[/]")
            successful_revocations += 1

    # 6. Save changes back to Excel
    if successful_provisions > 0 or successful_revocations > 0:
        try:
            backup_path = excel_manager.write_records(records)
            console.print()
            console.print(f"[bold green]✓ Excel file successfully updated![/]")
            console.print(f"  Backup created at: [yellow]{backup_path}[/]")
        except Exception as e:
            console.print(f"[bold red]Failed to write updates to Excel:[/] {e}", err=True)
            raise typer.Exit(code=1)

    # Final summary panel
    console.print()
    console.print(Panel(
        f"Provisions Successful: [green]{successful_provisions}[/]\n"
        f"Revocations Successful: [green]{successful_revocations}[/]\n"
        f"Actions Failed: [red]{failed_actions}[/]",
        title="Execution Summary",
        subtitle="Done"
    ))

if __name__ == "__main__":
    app()
