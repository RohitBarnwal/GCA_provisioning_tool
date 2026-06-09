import logging
import google.auth
from google.auth.transport.requests import AuthorizedSession
from google.auth.exceptions import DefaultCredentialsError
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger("gca_tracker")

class GCPClient:
    def __init__(self, project_id: Optional[str] = None, billing_account_id: Optional[str] = None, order_id: Optional[str] = None):
        self.project_id = project_id
        self.billing_account_id = billing_account_id
        self.order_id = order_id
        self._session = None
        self._initialized = False

    def initialize(self) -> Tuple[bool, str]:
        """Initializes Google credentials and authorized session."""
        try:
            credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            self._session = AuthorizedSession(credentials)
            self._initialized = True
            return True, "Credentials initialized successfully."
        except DefaultCredentialsError as e:
            return False, f"Google ADC authentication failed. Please run 'gcloud auth application-default login' first. Details: {e}"
        except Exception as e:
            return False, f"Unexpected authentication error: {e}"

    def assign_license(self, email: str) -> Tuple[bool, str]:
        """Assigns GCA license via Cloud Commerce Consumer Procurement API."""
        if not self._initialized:
            return False, "GCPClient not initialized"
        if not self.billing_account_id or not self.order_id:
            return True, "Skipped: Billing account ID or Order ID not provided."

        url = f"https://cloudcommerceconsumerprocurement.googleapis.com/v1/billingAccounts/{self.billing_account_id}/orders/{self.order_id}/licensePool:assign"
        payload = {"usernames": [email]}
        
        try:
            response = self._session.post(url, json=payload)
            if response.status_code == 200:
                return True, f"Successfully assigned procurement license to {email}"
            else:
                return False, f"Failed to assign license (HTTP {response.status_code}): {response.text}"
        except Exception as e:
            return False, f"Error calling Procurement API for {email}: {e}"

    def unassign_license(self, email: str) -> Tuple[bool, str]:
        """Unassigns GCA license via Cloud Commerce Consumer Procurement API."""
        if not self._initialized:
            return False, "GCPClient not initialized"
        if not self.billing_account_id or not self.order_id:
            return True, "Skipped: Billing account ID or Order ID not provided."

        url = f"https://cloudcommerceconsumerprocurement.googleapis.com/v1/billingAccounts/{self.billing_account_id}/orders/{self.order_id}/licensePool:unassign"
        payload = {"usernames": [email]}
        
        try:
            response = self._session.post(url, json=payload)
            if response.status_code == 200:
                return True, f"Successfully unassigned procurement license from {email}"
            else:
                return False, f"Failed to unassign license (HTTP {response.status_code}): {response.text}"
        except Exception as e:
            return False, f"Error calling Procurement API for {email}: {e}"

    def get_iam_policy(self) -> Tuple[Optional[dict], Optional[str]]:
        """Fetches the project IAM policy using v3 Resource Manager API."""
        if not self.project_id:
            return None, "No project ID provided"
        
        url = f"https://cloudresourcemanager.googleapis.com/v3/projects/{self.project_id}:getIamPolicy"
        try:
            response = self._session.post(url)
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"Failed to fetch IAM policy (HTTP {response.status_code}): {response.text}"
        except Exception as e:
            return None, f"Error fetching IAM policy: {e}"

    def set_iam_policy(self, policy: dict) -> Tuple[bool, str]:
        """Sets the project IAM policy using v3 Resource Manager API."""
        if not self.project_id:
            return False, "No project ID provided"

        url = f"https://cloudresourcemanager.googleapis.com/v3/projects/{self.project_id}:setIamPolicy"
        payload = {"policy": policy}
        try:
            response = self._session.post(url, json=payload)
            if response.status_code == 200:
                return True, "IAM policy updated successfully."
            else:
                return False, f"Failed to set IAM policy (HTTP {response.status_code}): {response.text}"
        except Exception as e:
            return False, f"Error setting IAM policy: {e}"

    def add_iam_role(self, email: str, role: str = "roles/cloudaicompanion.user") -> Tuple[bool, str]:
        """Adds the specified IAM role to the user on the project."""
        if not self._initialized:
            return False, "GCPClient not initialized"
        if not self.project_id:
            return True, "Skipped: Project ID not provided."

        policy, err = self.get_iam_policy()
        if err:
            return False, f"Could not add IAM role: {err}"

        # Modifying IAM policy
        bindings = policy.get("bindings", [])
        member = f"user:{email}"
        
        # Check if role binding already exists
        role_found = False
        for binding in bindings:
            if binding.get("role") == role:
                role_found = True
                if member not in binding.get("members", []):
                    binding.setdefault("members", []).append(member)
                else:
                    return True, f"User {email} already has IAM role {role}"
                break

        if not role_found:
            bindings.append({
                "role": role,
                "members": [member]
            })

        policy["bindings"] = bindings
        return self.set_iam_policy(policy)

    def remove_iam_role(self, email: str, role: str = "roles/cloudaicompanion.user") -> Tuple[bool, str]:
        """Removes the specified IAM role from the user on the project."""
        if not self._initialized:
            return False, "GCPClient not initialized"
        if not self.project_id:
            return True, "Skipped: Project ID not provided."

        policy, err = self.get_iam_policy()
        if err:
            return False, f"Could not remove IAM role: {err}"

        bindings = policy.get("bindings", [])
        member = f"user:{email}"
        
        role_found = False
        modified = False
        for binding in bindings:
            if binding.get("role") == role:
                role_found = True
                members = binding.get("members", [])
                if member in members:
                    members.remove(member)
                    modified = True
                break

        if not role_found or not modified:
            return True, f"User {email} does not have IAM role {role}"

        policy["bindings"] = bindings
        return self.set_iam_policy(policy)
