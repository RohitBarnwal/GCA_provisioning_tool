import logging
import random
import string
from typing import Tuple, Optional

logger = logging.getLogger("gca_tracker")

class WorkspaceClient:
    def __init__(self, session):
        self._session = session

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
        if not self._session:
            return False, "Session not initialized"
            
        url = f"https://admin.googleapis.com/admin/directory/v1/users/{email}"
        try:
            response = self._session.get(url)
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
        if not self._session:
            return False, "Session not initialized"

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

        try:
            response = self._session.post(url, json=payload)
            if response.status_code == 200 or response.status_code == 201:
                return True, f"Successfully created user in Workspace Directory: {email}"
            else:
                return False, f"Failed to create user (HTTP {response.status_code}): {response.text}"
        except Exception as e:
            return False, f"Error calling Directory API: {e}"
