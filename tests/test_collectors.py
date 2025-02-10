import shutil
import sys
import tempfile
import unittest
from pathlib import Path
import ast
import yaml

from deply.collectors import FileRegexCollector, ClassInheritsCollector
from deply.collectors.bool_collector import BoolCollector
from deply.collectors.class_name_regex_collector import ClassNameRegexCollector
from deply.collectors.decorator_usage_collector import DecoratorUsageCollector
from deply.collectors.directory_collector import DirectoryCollector
from deply.main import main

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
        (self.test_project_dir / 'excluded_folder_name').mkdir()
        (self.test_project_dir / 'utilities').mkdir()

        # Create files in controllers
        base_controller_py = self.test_project_dir / 'controllers' / 'base_controller.py'
        base_controller_py.write_text('class BaseController:\n    pass\n')

        user_controller_py = self.test_project_dir / 'controllers' / 'user_controller.py'
        user_controller_py.write_text('@login_required\nclass UserController(BaseController):\n    pass\n')

        # Create files in models
        base_model_py = self.test_project_dir / 'models' / 'base_model.py'
        base_model_py.write_text('class BaseModel:\n    pass\n')

        user_model_py = self.test_project_dir / 'models' / 'user_model.py'
        user_model_py.write_text('class UserModel(BaseModel):\n    pass\n')

        # Create files in services
        base_service_py = self.test_project_dir / 'services' / 'base_service.py'
        base_service_py.write_text('class BaseService:\n    pass\n')

        user_service_py = self.test_project_dir / 'services' / 'user_service.py'
        user_service_py.write_text('@service_decorator\nclass UserService(BaseService):\n    pass\n')

        deprecated_service_py = self.test_project_dir / 'excluded_folder_name' / 'deprecated_service.py'
        deprecated_service_py.write_text('@deprecated_service\nclass DeprecatedService(BaseService):\n    pass\n')

        # Create utility functions
        utils_py = self.test_project_dir / 'utilities' / 'utils.py'
        utils_py.write_text('@utility_decorator\ndef helper_function():\n    pass\n')

    def tearDown(self):
        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    def collect_elements_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
            tree = ast.parse(file_content, filename=str(file_path))
            elements = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    elements.append(node.name)
            return elements
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

    def run_collector(self, collector, paths, exclude_files):
        collected_elements = collector.collect(paths, exclude_files)
        return {element.name for element in collected_elements}

    def test_class_inherits_collector(self):
        collector_config = {
            'base_class': 'BaseModel',
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = ClassInheritsCollector(collector_config, paths, exclude_files)
        collected_class_names = self.run_collector(collector, paths, exclude_files)
        expected_classes = {'UserModel'}
        self.assertEqual(collected_class_names, expected_classes)

    def test_file_regex_collector(self):
        collector_config = {
            'regex': r'.*controller.py$',
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = FileRegexCollector(collector_config, paths, exclude_files)
        collected_class_names = self.run_collector(collector, paths, exclude_files)
        expected_classes = {'BaseController', 'UserController'}
        self.assertEqual(collected_class_names, expected_classes)

    def test_class_name_regex_collector(self):
        collector_config = {
            'class_name_regex': '^User.*',
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = ClassNameRegexCollector(collector_config, paths, exclude_files)
        collected_class_names = self.run_collector(collector, paths, exclude_files)
        expected_classes = {'UserController', 'UserModel', 'UserService'}
        self.assertEqual(collected_class_names, expected_classes)

    def test_directory_collector(self):
        collector_config = {
            'directories': ['services'],
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = DirectoryCollector(collector_config, paths, exclude_files)
        collected_class_names = self.run_collector(collector, paths, exclude_files)
        expected_classes = {'BaseService', 'UserService'}
        self.assertEqual(collected_class_names, expected_classes)

    def test_decorator_usage_collector(self):
        collector_config = {
            'decorator_name': 'login_required',
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = DecoratorUsageCollector(collector_config, paths, exclude_files)
        collected_class_names = self.run_collector(collector, paths, exclude_files)
        expected_classes = {'UserController'}
        self.assertEqual(collected_class_names, expected_classes)

        # Test with decorator_regex
        collector_config = {
            'decorator_regex': '^.*decorator$',
        }
        collector = DecoratorUsageCollector(collector_config, paths, exclude_files)
        collected_class_names = self.run_collector(collector, paths, exclude_files)
        expected_classes = {'UserService', 'helper_function'}
        self.assertEqual(collected_class_names, expected_classes)

    def test_class_name_regex_collector_no_matches(self):
        collector_config = {
            'class_name_regex': '^NonExistentClass.*',
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = ClassNameRegexCollector(collector_config, paths, exclude_files)
        collected_class_names = self.run_collector(collector, paths, exclude_files)
        self.assertEqual(len(collected_class_names), 0)

    def test_bool_collector(self):
        collector_config = {
            'type': 'bool',
            'must': [
                {'type': 'class_name_regex', 'class_name_regex': '.*Service$'}
            ],
            'must_not': [
                {'type': 'file_regex', 'regex': '.*/base_service.py'},
                {'type': 'file_regex', 'regex': '.*/excluded_folder_name/.*'},
                {'type': 'decorator_usage', 'decorator_name': 'deprecated_service'}
            ]
        }
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = BoolCollector(collector_config, paths, exclude_files)
        collected_class_names = self.run_collector(collector, paths, exclude_files)
        expected_classes = {'UserService'}
        self.assertEqual(collected_class_names, expected_classes)

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