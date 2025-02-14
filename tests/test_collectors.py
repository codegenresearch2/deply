import argparse
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager
from io import StringIO
from pathlib import Path

import yaml

from deply.collectors import FileRegexCollector, ClassInheritsCollector, BoolCollector, ClassNameRegexCollector, DecoratorUsageCollector, DirectoryCollector
from deply.main import main

class TestCollectors(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.test_dir) / 'test_project'
        self.test_project_dir.mkdir()
        (self.test_project_dir / 'controllers').mkdir()
        (self.test_project_dir / 'models').mkdir()
        (self.test_project_dir / 'services').mkdir()
        (self.test_project_dir / 'excluded_folder_name').mkdir()
        (self.test_project_dir / 'utilities').mkdir()
        base_controller_py = self.test_project_dir / 'controllers' / 'base_controller.py'
        base_controller_py.write_text('class BaseController:\n    pass\n')
        user_controller_py = self.test_project_dir / 'controllers' / 'user_controller.py'
        user_controller_py.write_text('@login_required\nclass UserController(BaseController):\n    pass\n')
        base_model_py = self.test_project_dir / 'models' / 'base_model.py'
        base_model_py.write_text('class BaseModel:\n    pass\n')
        user_model_py = self.test_project_dir / 'models' / 'user_model.py'
        user_model_py.write_text('class UserModel(BaseModel):\n    pass\n')
        base_service_py = self.test_project_dir / 'services' / 'base_service.py'
        base_service_py.write_text('class BaseService:\n    pass\n')
        user_service_py = self.test_project_dir / 'services' / 'user_service.py'
        user_service_py.write_text('@service_decorator\nclass UserService(BaseService):\n    pass\n')
        deprecated_service_py = self.test_project_dir / 'excluded_folder_name' / 'deprecated_service.py'
        deprecated_service_py.write_text('@deprecated_service\nclass DeprecatedService(BaseService):\n    pass\n')
        utils_py = self.test_project_dir / 'utilities' / 'utils.py'
        utils_py.write_text('@utility_decorator\ndef helper_function():\n    pass\n')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_collector(self, collector_config, expected_classes):
        paths = [str(self.test_project_dir)]
        exclude_files = []
        collector = CollectorFactory.create(collector_config, paths, exclude_files)
        collected_elements = collector.collect()
        collected_class_names = {element.name for element in collected_elements}
        self.assertEqual(collected_class_names, expected_classes)

    def test_collectors(self):
        collectors_test_cases = [
            ({'type': 'class_inherits', 'base_class': 'BaseModel'}, {'UserModel'}),
            ({'type': 'file_regex', 'regex': r'.*controller.py$'}, {'BaseController', 'UserController'}),
            ({'type': 'class_name_regex', 'class_name_regex': '^User.*'}, {'UserController', 'UserModel', 'UserService'}),
            ({'type': 'directory', 'directories': ['services']}, {'BaseService', 'UserService'}),
            ({'type': 'decorator_usage', 'decorator_name': 'login_required'}, {'UserController'}),
            ({'type': 'decorator_usage', 'decorator_regex': '^.*decorator$'}, {'UserService', 'helper_function'}),
            ({'type': 'class_name_regex', 'class_name_regex': '^NonExistentClass.*'}, set()),
            ({'type': 'bool', 'must': [{'type': 'class_name_regex', 'class_name_regex': '.*Service$'}],
              'must_not': [{'type': 'file_regex', 'regex': '.*/base_service.py'},
                           {'type': 'file_regex', 'regex': '.*/excluded_folder_name/.*'},
                           {'type': 'decorator_usage', 'decorator_name': 'deprecated_service'}]},
             {'UserService'}),
        ]
        for config, expected in collectors_test_cases:
            with self.subTest(config=config):
                self.test_collector(config, expected)

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
                    {'name': 'models_layer', 'collectors': [{'type': 'directory', 'directories': ['models']}]},
                    {'name': 'controllers_layer', 'collectors': [{'type': 'directory', 'directories': ['controllers']}]},
                ],
                'ruleset': {'controllers_layer': {'disallow': ['models_layer']}}
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
    parser = argparse.ArgumentParser(prog="deply", description='Deply - A dependency analysis tool')
    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')
    parser_analyse = subparsers.add_parser('analyze', help='Analyze the project dependencies')
    parser_analyse.add_argument("--config", type=str, default="deply.yaml", help="Path to the configuration YAML file")
    parser_analyse.add_argument("--report-format", type=str, choices=["text", "json", "html"], default="text", help="Format of the output report")
    parser_analyse.add_argument("--output", type=str, help="Output file for the report")
    unittest.main()