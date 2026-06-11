import os
import logging
import random
import string
from typing import Tuple, Optional

logger = logging.getLogger("gca_tracker")

class WorkspaceClient:
    def __init__(self, session, key_path: Optional[str] = None, admin_email: Optional[str] = None, project_id: Optional[str] = None):
        self._session = session
        self.key_path = key_path or "workspace_key.json"
        self.admin_email = admin_email
        self.project_id = project_id
        self._workspace_session = None
        self._initialized = False

    def initialize(self) -> Tuple[bool, str]:
        """Initializes Google Workspace directory session, supporting service account fallback."""
        from google.auth.transport.requests import AuthorizedSession
        
        # Check if local service account key file is present and we have an admin email to impersonate
        if os.path.exists(self.key_path) and self.admin_email:
            try:
                from google.oauth2 import service_account
                creds = service_account.Credentials.from_service_account_file(
                    self.key_path,
                    scopes=["https://www.googleapis.com/auth/admin.directory.user"],
                    subject=self.admin_email
                )
                self._workspace_session = AuthorizedSession(creds)
                self._initialized = True
                return True, f"Authenticated Workspace using Service Account Key: '{self.key_path}' impersonating {self.admin_email}"
            except Exception as e:
                return False, f"Failed to initialize Workspace Service Account authentication: {e}"
        
        # Fallback to the personal gcloud session
        if self._session:
            self._workspace_session = self._session
            self._initialized = True
            return True, "Workspace initialized using personal gcloud credentials session fallback."
            
        return False, "Workspace not initialized. Please ensure either personal login is configured or a valid 'workspace_key.json' and Workspace Admin email is provided."

    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """
        Generates a secure temporary password with digits, letters, and punctuation.
        """
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        # Ensure at least one lowercase, one uppercase, one digit, and one special character
        password = [
            random.choice(string.ascii_lowercase),
            random.choice(string.ascii_uppercase),
            random.choice(string.digits),
            random.choice("!@#$%^&*")
        ]
        # Fill the rest
        password += [random.choice(characters) for _ in range(length - 4)]
        random.shuffle(password)
        return "".join(password)

    def check_user_exists(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Checks if a user exists in Google Workspace.
        Returns:
            Tuple[exists, error_message]
        """
        if not self._initialized:
            success, msg = self.initialize()
            if not success:
                return False, msg
            
        url = f"https://admin.googleapis.com/admin/directory/v1/users/{email}"
        
        # Inject the quota project header to avoid API errors when using personal credentials
        headers = {}
        if self.project_id:
            headers["X-Goog-User-Project"] = self.project_id
            
        try:
            response = self._workspace_session.get(url, headers=headers)
            if response.status_code == 200:
                return True, None
            elif response.status_code == 404:
                return False, None
            else:
                return False, f"Failed to check user in directory (HTTP {response.status_code}): {response.text}"
        except Exception as e:
            return False, f"Error calling Admin SDK Directory API: {e}"

    def create_user(self, email: str, first_name: str, last_name: str, password: str) -> Tuple[bool, str]:
        """
        Creates a new user inside the Google Workspace directory.
        Returns:
            Tuple[success, message_or_error]
        """
        if not self._initialized:
            success, msg = self.initialize()
            if not success:
                return False, msg

        url = "https://admin.googleapis.com/admin/directory/v1/users"
        payload = {
            "primaryEmail": email,
            "name": {
                "givenName": first_name,
                "familyName": last_name
            },
            "password": password,
            "changePasswordAtNextLogin": True
        }

        # Inject the quota project header to avoid API errors when using personal credentials
        headers = {}
        if self.project_id:
            headers["X-Goog-User-Project"] = self.project_id

        try:
            response = self._workspace_session.post(url, json=payload, headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                return True, f"Successfully created user in Workspace Directory: {email}"
            else:
                return False, f"Failed to create user (HTTP {response.status_code}): {response.text}"
        except Exception as e:
            return False, f"Error calling Directory API: {e}"
