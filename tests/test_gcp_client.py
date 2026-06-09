import unittest
from unittest.mock import MagicMock, patch
from tracker_core.gcp_client import GCPClient

class TestGCPClient(unittest.TestCase):
    def setUp(self):
        self.client = GCPClient(
            project_id="test-project",
            billing_account_id="test-billing",
            order_id="test-order"
        )
        self.client._initialized = True
        self.client._session = MagicMock()

    @patch('google.auth.default')
    def test_initialize_success(self, mock_auth_default):
        mock_auth_default.return_value = (MagicMock(), "test-project")
        
        new_client = GCPClient()
        success, msg = new_client.initialize()
        self.assertTrue(success)
        self.assertTrue(new_client._initialized)

    def test_assign_license_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        self.client._session.post.return_value = mock_response

        success, msg = self.client.assign_license("user@example.com")
        self.assertTrue(success)
        self.assertTrue("Successfully assigned" in msg)
        self.client._session.post.assert_called_once_with(
            "https://cloudcommerceconsumerprocurement.googleapis.com/v1/billingAccounts/test-billing/orders/test-order/licensePool:assign",
            json={"usernames": ["user@example.com"]}
        )

    def test_assign_license_failure(self):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        self.client._session.post.return_value = mock_response

        success, msg = self.client.assign_license("user@example.com")
        self.assertFalse(success)
        self.assertTrue("Failed to assign license" in msg)

    def test_add_iam_role_success(self):
        # Mock get_iam_policy response
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "bindings": [
                {"role": "roles/viewer", "members": ["user:old@example.com"]}
            ]
        }
        
        # Mock set_iam_policy response
        mock_set_response = MagicMock()
        mock_set_response.status_code = 200
        
        self.client._session.post.side_effect = [mock_get_response, mock_set_response]

        success, msg = self.client.add_iam_role("user@example.com")
        self.assertTrue(success)
        
        # Ensure we made 2 posts: getIamPolicy and setIamPolicy
        self.assertEqual(self.client._session.post.call_count, 2)
        
        # Check setIamPolicy payload
        args, kwargs = self.client._session.post.call_args_list[1]
        self.assertEqual(args[0], "https://cloudresourcemanager.googleapis.com/v3/projects/test-project:setIamPolicy")
        bindings = kwargs["json"]["policy"]["bindings"]
        
        # Should have added roles/cloudaicompanion.user with user:user@example.com
        gca_binding = next(binding for binding in bindings if binding.get("role") == "roles/cloudaicompanion.user")
        self.assertIn("user:user@example.com", gca_binding["members"])

    def test_remove_iam_role_success(self):
        # Mock get_iam_policy response with existing role
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "bindings": [
                {"role": "roles/cloudaicompanion.user", "members": ["user:user@example.com"]}
            ]
        }
        
        # Mock set_iam_policy response
        mock_set_response = MagicMock()
        mock_set_response.status_code = 200
        
        self.client._session.post.side_effect = [mock_get_response, mock_set_response]

        success, msg = self.client.remove_iam_role("user@example.com")
        self.assertTrue(success)
        
        # Check setIamPolicy payload (user:user@example.com should be removed)
        args, kwargs = self.client._session.post.call_args_list[1]
        bindings = kwargs["json"]["policy"]["bindings"]
        gca_binding = next(b for b in bindings if b.get("role") == "roles/cloudaicompanion.user")
        self.assertNotIn("user:user@example.com", gca_binding["members"])

if __name__ == "__main__":
    unittest.main()
