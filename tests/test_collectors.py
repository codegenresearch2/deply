# tests/test_collectors.py
import sys
import unittest
import tempfile
import shutil
import os
from pathlib import Path

import yaml

from deply.collectors import FileRegexCollector, ClassInheritsCollector
from deply.collectors.class_name_regex_collector import ClassNameRegexCollector
from deply.collectors.directory_collector import DirectoryCollector
from deply.main import main
from deply.models.code_element import CodeElement


class TestCollectors(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.test_dir) / 'test_project'
        self.test_project_dir.mkdir()

        # Create directories
        (self.test_project_dir / 'controllers').mkdir()
        (self.test_project_dir / 'models').mkdir()
        (self.test_project_dir / 'services').mkdir()

        # Create files in controllers
        base_controller_py = self.test_project_dir / 'controllers' / 'base_controller.py'
        base_controller_py.write_text('class BaseController:\n    pass\n')

        user_controller_py = self.test_project_dir / 'controllers' / 'user_controller.py'
        user_controller_py.write_text('class UserController(BaseController):\n    pass\n')

        # Create files in models
        base_model_py = self.test_project_dir / 'models' / 'base_model.py'
        base_model_py.write_text('class BaseModel:\n    pass\n')

        user_model_py = self.test_project_dir / 'models' / 'user_model.py'
        user_model_py.write_text('class UserModel(BaseModel):\n    pass\n')

        # Create files in services
        base_service_py = self.test_project_dir / 'services' / 'base_service.py'
        base_service_py.write_text('class BaseService:\n    pass\n')

        user_service_py = self.test_project_dir / 'services' / 'user_service.py'
        user_service_py.write_text('class UserService(BaseService):\n    pass\n')

    def tearDown(self):
        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    def test_class_inherits_collector(self):
        # Instantiate the ClassInheritsCollector
        collector_config = {
            'base_class': 'BaseModel',
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = ClassInheritsCollector(collector_config, paths, exclude_files)
        collected_elements = collector.collect()

        # Extract the names of the collected classes
        collected_class_names = {element.name for element in collected_elements}

        expected_classes = {'UserModel'}
        self.assertEqual(collected_class_names, expected_classes)

    def test_file_regex_collector(self):
        # Instantiate the FileRegexCollector
        collector_config = {
            'regex': r'.*controller.py$',
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = FileRegexCollector(collector_config, paths, exclude_files)
        collected_elements = collector.collect()

        # Extract the names of the collected functions
        collected_function_names = {element.name for element in collected_elements}

        expected_functions = {'BaseController', 'UserController'}
        self.assertEqual(collected_function_names, expected_functions)

    def test_class_name_regex_collector(self):
        # Instantiate the ClassNameRegexCollector directly
        collector_config = {
            'class_name_regex': '^User.*',
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = ClassNameRegexCollector(collector_config, paths, exclude_files)
        collected_elements = collector.collect()

        # Extract the names of the collected classes
        collected_class_names = {element.name for element in collected_elements}

        expected_classes = {'UserController', 'UserModel', 'UserService'}
        self.assertEqual(collected_class_names, expected_classes)

    def test_directory_collector(self):
        # Instantiate the DirectoryCollector directly
        collector_config = {
            'directories': ['services'],
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = DirectoryCollector(collector_config, paths, exclude_files)
        collected_elements = collector.collect()

        collected_class_names = {element.name for element in collected_elements}

        expected_classes = {'BaseService', 'UserService'}
        self.assertEqual(collected_class_names, expected_classes)

    def test_class_name_regex_collector_no_matches(self):
        # Instantiate the ClassNameRegexCollector with a pattern that matches nothing
        collector_config = {
            'class_name_regex': '^NonExistentClass.*',
            'exclude_files_regex': ''
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = ClassNameRegexCollector(collector_config, paths, exclude_files)
        collected_elements = collector.collect()

        # The collected_elements should be empty
        self.assertEqual(len(collected_elements), 0)

    def test_directory_collector_with_rules(self):
        # This test remains the same as it involves the main program logic and rules
        # Modify user_controller.py to import UserModel
        user_controller_py = self.test_project_dir / 'controllers' / 'user_controller.py'
        user_controller_py.write_text(
            'from ..models.user_model import UserModel\n'
            'class UserController:\n'
            '    def __init__(self):\n'
            '        self.model = UserModel()\n'
        )

        # Write config.yaml for DirectoryCollector with rules
        config_yaml = Path(self.test_dir) / 'config_directory_collector_rules.yaml'
        config_data = {
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
        with config_yaml.open('w') as f:
            yaml.dump(config_data, f)

        # Capture the output
        with self.capture_output() as (out, err):
            try:
                # Run main with the test config
                sys.argv = ['main.py', '--config', str(config_yaml)]
                main()
            except SystemExit as e:
                exit_code = e.code

        output = out.getvalue()

        # Check that the exit code is 1 (violations found)
        self.assertEqual(exit_code, 1)

        # Verify that the violation message is as expected
        self.assertIn("Layer 'controllers_layer' is not allowed to depend on layer 'models_layer'", output)

    # Helper context manager for capturing output
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
