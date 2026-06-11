import unittest
from unittest.mock import MagicMock
from tracker_core.workspace_client import WorkspaceClient

class TestWorkspaceClient(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.client = WorkspaceClient(self.session)

    def test_parse_name_from_email_dot_separated(self):
        first, last = WorkspaceClient.parse_name_from_email("john.doe@example.com")
        self.assertEqual(first, "John")
        self.assertEqual(last, "Doe")

    def test_parse_name_from_email_multiple_parts(self):
        first, last = WorkspaceClient.parse_name_from_email("rohit.kumar.barnwal@example.com")
        self.assertEqual(first, "Rohit")
        self.assertEqual(last, "Kumar Barnwal")

    def test_parse_name_from_email_single_word(self):
        first, last = WorkspaceClient.parse_name_from_email("admin@example.com")
        self.assertEqual(first, "Admin")
        self.assertEqual(last, "Employee")

    def test_generate_random_password(self):
        pwd = WorkspaceClient.generate_random_password(16)
        self.assertEqual(len(pwd), 16)
        # Verify it has uppercase, lowercase, digit, and symbol
        self.assertTrue(any(c.islower() for c in pwd))
        self.assertTrue(any(c.isupper() for c in pwd))
        self.assertTrue(any(c.isdigit() for c in pwd))
        self.assertTrue(any(c in "!@#$%^&*" for c in pwd))

    def test_check_user_exists_true(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        self.session.get.return_value = mock_response

        exists, err = self.client.check_user_exists("user@example.com")
        self.assertTrue(exists)
        self.assertIsNone(err)
        self.session.get.assert_called_once_with("https://admin.googleapis.com/admin/directory/v1/users/user@example.com")

    def test_check_user_exists_false(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        self.session.get.return_value = mock_response

        exists, err = self.client.check_user_exists("user@example.com")
        self.assertFalse(exists)
        self.assertIsNone(err)

    def test_create_user_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 201
        self.session.post.return_value = mock_response

        success, msg = self.client.create_user("user@example.com", "John", "Doe", "TempPass123!")
        self.assertTrue(success)
        self.assertTrue("Successfully created" in msg)
        
        self.session.post.assert_called_once_with(
            "https://admin.googleapis.com/admin/directory/v1/users",
            json={
                "primaryEmail": "user@example.com",
                "name": {"givenName": "John", "familyName": "Doe"},
                "password": "TempPass123!",
                "changePasswordAtNextLogin": True
            }
        )

if __name__ == "__main__":
    unittest.main()
