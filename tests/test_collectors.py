import shutil
import sys
import tempfile
import unittest
import ast
from pathlib import Path

import yaml

from deply.collectors import CollectorFactory
from deply.main import main

class TestCollectors(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.test_dir) / 'test_project'
        self.test_project_dir.mkdir()

        # Create directories and files for the test project
        self.create_test_files()

    def create_test_files(self):
        # Create directories
        for directory in ['controllers', 'models', 'services', 'excluded_folder_name', 'utilities']:
            (self.test_project_dir / directory).mkdir()

        # Create files and their content
        files_data = {
            'controllers/base_controller.py': 'class BaseController:\n    pass\n',
            'controllers/user_controller.py': '@login_required\nclass UserController(BaseController):\n    pass\n',
            'models/base_model.py': 'class BaseModel:\n    pass\n',
            'models/user_model.py': 'class UserModel(BaseModel):\n    pass\n',
            'services/base_service.py': 'class BaseService:\n    pass\n',
            'services/user_service.py': '@service_decorator\nclass UserService(BaseService):\n    pass\n',
            'excluded_folder_name/deprecated_service.py': '@deprecated_service\nclass DeprecatedService(BaseService):\n    pass\n',
            'utilities/utils.py': '@utility_decorator\ndef helper_function():\n    pass\n',
        }

        # Write content to files
        for file_path, content in files_data.items():
            (self.test_project_dir / file_path).write_text(content)

    def tearDown(self):
        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    def test_collector(self):
        # Define test cases for each collector type
        test_cases = [
            {
                'collector_config': {
                    'base_class': 'BaseModel',
                },
                'collector_type': 'class_inherits',
                'expected_classes': {'UserModel'},
            },
            {
                'collector_config': {
                    'regex': r'.*controller.py$',
                },
                'collector_type': 'file_regex',
                'expected_classes': {'BaseController', 'UserController'},
            },
            {
                'collector_config': {
                    'class_name_regex': '^User.*',
                },
                'collector_type': 'class_name_regex',
                'expected_classes': {'UserController', 'UserModel', 'UserService'},
            },
            {
                'collector_config': {
                    'directories': ['services'],
                },
                'collector_type': 'directory',
                'expected_classes': {'BaseService', 'UserService'},
            },
            {
                'collector_config': {
                    'decorator_name': 'login_required',
                },
                'collector_type': 'decorator_usage',
                'expected_names': {'UserController'},
            },
            {
                'collector_config': {
                    'decorator_regex': '^.*decorator$',
                },
                'collector_type': 'decorator_usage',
                'expected_names': {'UserService', 'helper_function'},
            },
            {
                'collector_config': {
                    'class_name_regex': '^NonExistentClass.*',
                },
                'collector_type': 'class_name_regex',
                'expected_classes': set(),
            },
            {
                'collector_config': {
                    'type': 'bool',
                    'must': [
                        {'type': 'class_name_regex', 'class_name_regex': '.*Service$'}
                    ],
                    'must_not': [
                        {'type': 'file_regex', 'regex': '.*/base_service.py'},
                        {'type': 'file_regex', 'regex': '.*/excluded_folder_name/.*'},
                        {'type': 'decorator_usage', 'decorator_name': 'deprecated_service'}
                    ]
                },
                'collector_type': 'bool',
                'expected_classes': {'UserService'},
            },
        ]

        # Run tests for each collector type
        for case in test_cases:
            collector = CollectorFactory.create(
                case['collector_config'],
                [str(self.test_project_dir)],
                []
            )
            collected_elements = collector.collect()
            if 'expected_classes' in case:
                collected_class_names = {element.name for element in collected_elements}
                self.assertEqual(collected_class_names, case['expected_classes'])
            elif 'expected_names' in case:
                collected_names = {element.name for element in collected_elements}
                self.assertEqual(collected_names, case['expected_names'])

    def test_directory_collector_with_rules(self):
        user_controller_py = self.test_project_dir / 'controllers' / 'user_controller.py'
        user_controller_py.write_text(
            'from ..models.user_model import UserModel\n'
            'class UserController:\n'
            '    def __init__(self):\n'
            '        self.model = UserModel()\n'
        )
        config_yaml = Path(self.test_dir) / 'config_directory_collector_rules.yaml'
        config_data = {
            'deply': {
                'paths': [str(self.test_project_dir)],
                'layers': [
                    {
                        'name': 'models_layer',
                        'collectors': [
                            {
                                'type': 'directory',
                                'directories': ['models'],
                            }
                        ]
                    },
                    {
                        'name': 'controllers_layer',
                        'collectors': [
                            {
                                'type': 'directory',
                                'directories': ['controllers'],
                            }
                        ]
                    }
                ],
                'ruleset': {
                    'controllers_layer': {
                        'disallow': ['models_layer']
                    }
                }
            }
        }
        with config_yaml.open('w') as f:
            yaml.dump(config_data, f)
        with self.capture_output() as (out, err):
            try:
                sys.argv = ['main.py', 'analyze', '--config', str(config_yaml)]
                main()
            except SystemExit as e:
                exit_code = e.code
        output = out.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("Layer 'controllers_layer' is not allowed to depend on layer 'models_layer'", output)

    @staticmethod
    def capture_output():
        from contextlib import contextmanager
        from io import StringIO
        import sys

        @contextmanager
        def _capture_output():
            new_out, new_err = StringIO(), StringIO()
            old_out, old_err = sys.stdout, sys.stderr
            try:
                sys.stdout, sys.stderr = new_out, new_err
                yield sys.stdout, sys.stderr
            finally:
                sys.stdout, sys.stderr = old_out, old_err

        return _capture_output()

if __name__ == '__main__':
    unittest.main()


I have rewritten the code to enhance code readability and maintainability. I have consolidated the similar test methods into a single `test_collector` method that takes a dictionary of test cases. I have also used the `CollectorFactory` to create collectors dynamically based on the collector type. This will simplify adding new collectors in the future.

Additionally, I have created a `create_test_files` method to create the test files and directories. This method uses a dictionary to define the file paths and their content, which makes it easier to add or modify files in the future.

The `test_directory_collector_with_rules` method remains unchanged as it tests the main functionality of the code.

The `capture_output` method is used to capture the output of the `main` function in the test methods. This allows us to check the output and exit code of the `main` function in the test methods.

Overall, these changes improve the maintainability and readability of the code.