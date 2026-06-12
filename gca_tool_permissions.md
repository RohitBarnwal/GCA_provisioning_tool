# GCA Provisioning Tool - Required Permissions Guide

To run this utility tool successfully, specific permissions must be configured across three layers: **Google Workspace App Whitelisting**, **GCP Project IAM**, and **GCP Billing**. This document lists the exact roles, permissions, and client IDs we configured.

---

### 1. Google Workspace App Whitelisting (The "App Blocked" Fix)
To allow your personal admin account to authenticate Directory API scopes via `gcloud` without getting blocked, you must explicitly trust the **Google Cloud SDK** Client ID in your Workspace console.

*   **Console Path:** Google Workspace Admin Console (`admin.google.com`) ➡️ **Security** ➡️ **Access and data control** ➡️ **API controls** ➡️ **Manage Third-Party App Access** ➡️ **Configure new app** ➡️ **OAuth App Name or Client ID**.
*   **OAuth Client ID to search & whitelist:**
    ```text
    764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com
    ```
*   **Configured Access Level:** Set to **`Trusted`**.

---

### 2. GCP Project IAM Developer Roles
When a user is provisioned, the utility script automatically assigns **both** of the following standard GCP IAM roles to their email identity at the project level. 

These roles are required for GCA to function in their local IDE (VS Code, IntelliJ, etc.):

1.  **Gemini for Google Cloud User (`roles/cloudaicompanion.user`)**
    *   *Why:* Grants permissions to call Gemini companion code-generation, chat, and auto-complete methods.
2.  **Service Usage Consumer (`roles/serviceusage.serviceUsageConsumer`)**
    *   *Why:* Grants permissions to consume project-level billing quota when calling the Gemini companion API endpoint. If this is missing, the IDE client will return quota/billing errors.

---

### 3. GCP Billing Account Licensing Permission
To allow your personal admin account (running the script) to allocate GCA license seats from your billing subscription order pool, you must have the specific licensing role assigned **at the Billing Account level** (not the Project level).

*   **Console Path:** Google Cloud Console ➡️ Search **Billing** ➡️ Select Billing Account (`01017E-F2F698-0611A0`) ➡️ **Show Info Panel** (permissions tab) ➡️ **Add Principal**.
*   **Required Predefined Role:** **`Consumer Procurement License Pool Editor`**
*   **Key Permission Granted:**
    ```text
    consumerprocurement.licensePools.assign
    ```
    *(Allows the caller to add user email addresses to the paid license order pool).*
