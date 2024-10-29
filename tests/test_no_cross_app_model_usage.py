import unittest
from unittest.mock import patch, mock_open

from architecture_checker.rules.no_cross_app_model_usage_rule import NoCrossAppModelUsageRule


def mocked_open(file, mode='r', *args, **kwargs):
    if file == '/mock_project/app1/views.py':
        file_content_with_violation = """
from app2.models import ModelB  # This should trigger a violation
"""
        mock_file = mock_open(read_data=file_content_with_violation).return_value
        return mock_file
    elif file == '/mock_project/app1/another_view.py':
        file_content_no_violation = """
from app1.models import ModelA  # This is allowed
"""
        mock_file = mock_open(read_data=file_content_no_violation).return_value
        return mock_file
    else:
        raise FileNotFoundError(f"No such file or directory: '{file}'")


class TestNoCrossAppModelUsageRule(unittest.TestCase):
    def setUp(self):
        self.project_root = "/mock_project"
        self.params = {
            "target_files": ["*.py"],
            "exclude_apps": []
        }

    @patch("architecture_checker.rules.no_cross_app_model_usage_rule.open", new_callable=mock_open)
    @patch("architecture_checker.rules.no_cross_app_model_usage_rule.os.walk")
    @patch("architecture_checker.rules.no_cross_app_model_usage_rule.os.path.isdir")
    @patch("architecture_checker.rules.no_cross_app_model_usage_rule.os.listdir")
    @patch("architecture_checker.rules.no_cross_app_model_usage_rule.get_django_app_models")
    @patch("architecture_checker.rules.no_cross_app_model_usage_rule.get_django_apps")
    def test_violation(self, mock_get_django_apps, mock_get_django_app_models, mock_os_listdir, mock_os_isdir,
                       mock_os_walk, mock_open_file):
        # Set up mocks
        mock_get_django_apps.return_value = ["app1", "app2"]
        mock_get_django_app_models.return_value = {
            "app1": ["ModelA"],
            "app2": ["ModelB"]
        }
        mock_os_listdir.return_value = ["app1", "app2"]
        mock_os_isdir.return_value = True
        mock_os_walk.return_value = [
            ("/mock_project/app1", ("subdir",), ("views.py",)),
        ]
        file_content_with_violation = """
from app2.models import ModelB  # This should trigger a violation
"""
        mock_open_file.return_value.read.return_value = file_content_with_violation

        # Run the rule
        rule = NoCrossAppModelUsageRule(self.project_root, self.params)
        rule.run()

        # Assertions
        self.assertEqual(len(rule.violations), 1)
        self.assertIn("app2", rule.violations[0]["app"])
        self.assertIn("ModelB", rule.violations[0]["message"])
        self.assertIn("app1/views.py", rule.violations[0]["file"])

    @patch("architecture_checker.rules.no_cross_app_model_usage_rule.open", new_callable=mock_open)
    @patch("architecture_checker.rules.no_cross_app_model_usage_rule.os.listdir")
    @patch("architecture_checker.rules.no_cross_app_model_usage_rule.os.walk")
    @patch("architecture_checker.utils.get_django_apps")
    @patch("architecture_checker.utils.get_django_app_models")
    def test_no_violation(self, mock_get_django_app_models, mock_get_django_apps, mock_os_walk, mock_os_listdir,
                          mock_open_file):
        mock_os_listdir.return_value = ["app1", "app2"]
        mock_get_django_apps.return_value = ["app1", "app2"]
        mock_get_django_app_models.return_value = {
            "app1": ["ModelA"],
            "app2": ["ModelB"]
        }
        mock_os_walk.return_value = [
            ("/mock_project/app1", ("subdir",), ("another_view.py",)),
        ]
        mock_open_file.side_effect = mocked_open

        rule = NoCrossAppModelUsageRule(self.project_root, self.params)
        rule.run()

        self.assertEqual(len(rule.violations), 0)


if __name__ == '__main__':
    unittest.main()
