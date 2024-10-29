import os
import unittest
from unittest.mock import patch, mock_open

from architecture_checker.rules.no_cross_app_model_usage_rule import NoCrossAppModelUsageRule


class TestNoCrossAppModelUsageRule(unittest.TestCase):
    def setUp(self):
        # Set up a mock project root
        self.project_root = "/mock_project"

        # Define mock parameters for the rule
        self.params = {
            "target_files": ["*.py"],
            "exclude_apps": []
        }

    @patch("architecture_checker.get_django_apps")  # Mocking utility function
    @patch("architecture_checker.get_django_app_models")  # Mocking utility function
    @patch("builtins.open", new_callable=mock_open)  # Mocking file reading
    def test_rule_detection(self, mock_open, mock_get_models, mock_get_apps):
        # Mock app structure and model classes
        mock_get_apps.return_value = ["app1", "app2"]
        mock_get_models.return_value = {
            "app1": ["ModelA"],
            "app2": ["ModelB"]
        }

        # Mock file contents with an import violation
        file_content_with_violation = """
        from app2.models import ModelB  # This should trigger a violation
        """
        mock_open.side_effect = [
            mock_open(read_data=file_content_with_violation).return_value
        ]

        # Initialize the rule
        rule = NoCrossAppModelUsageRule(self.project_root, self.params)

        # Run the rule
        rule.run()

        # Check for expected violation
        self.assertEqual(len(rule.violations), 1)
        self.assertIn("app2", rule.violations[0]["app"])
        self.assertIn("ModelB", rule.violations[0]["message"])
        self.assertEqual(rule.violations[0]["file"], os.path.join(self.project_root, "app1", "views.py"))

    @patch("architecture_checker.get_django_apps")
    @patch("architecture_checker.get_django_app_models")
    @patch("builtins.open", new_callable=mock_open)
    def test_no_violation(self, mock_open, mock_get_models, mock_get_apps):
        # Mock app structure and model classes
        mock_get_apps.return_value = ["app1", "app2"]
        mock_get_models.return_value = {
            "app1": ["ModelA"],
            "app2": ["ModelB"]
        }

        # Mock file content without any model import violations
        file_content_no_violation = """
        from app1.models import ModelA  # This is allowed
        """
        mock_open.side_effect = [
            mock_open(read_data=file_content_no_violation).return_value
        ]

        # Initialize the rule
        rule = NoCrossAppModelUsageRule(self.project_root, self.params)

        # Run the rule
        rule.run()

        # Ensure no violations were found
        self.assertEqual(len(rule.violations), 0)


if __name__ == '__main__':
    unittest.main()
