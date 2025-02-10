import argparse
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager
from io import StringIO
from pathlib import Path

import yaml

from deply.collectors import FileRegexCollector, ClassInheritsCollector, ClassNameRegexCollector, DirectoryCollector, DecoratorUsageCollector
from deply.collectors.bool_collector import BoolCollector
from deply.main import main

class TestCollectors(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.test_dir) / 'test_project'
        self.test_project_dir.mkdir()
        self.setup_test_project()
        self.paths = [str(self.test_project_dir)]
        self.exclude_files = []

    def tearDown(self):
        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    def setup_test_project(self):
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

    def test_class_inherits_collector(self):
        collector_config = {'base_class': 'BaseModel'}
        collector = ClassInheritsCollector(collector_config, self.paths, self.exclude_files)
        collected_elements = collector.collect()
        expected_classes = {'UserModel'}
        self.assert_collected_classes(collected_elements, expected_classes)

    def test_file_regex_collector(self):
        collector_config = {'regex': r'.*controller.py$'}
        collector = FileRegexCollector(collector_config, self.paths, self.exclude_files)
        collected_elements = collector.collect()
        expected_classes = {'BaseController', 'UserController'}
        self.assert_collected_classes(collected_elements, expected_classes)

    def test_class_name_regex_collector(self):
        collector_config = {'class_name_regex': '^User.*'}
        collector = ClassNameRegexCollector(collector_config, self.paths, self.exclude_files)
        collected_elements = collector.collect()
        expected_classes = {'UserController', 'UserModel', 'UserService'}
        self.assert_collected_classes(collected_elements, expected_classes)

    def test_directory_collector(self):
        collector_config = {'directories': ['services']}
        collector = DirectoryCollector(collector_config, self.paths, self.exclude_files)
        collected_elements = collector.collect()
        expected_classes = {'BaseService', 'UserService'}
        self.assert_collected_classes(collected_elements, expected_classes)

    def test_decorator_usage_collector(self):
        collector_config = {'decorator_name': 'login_required'}
        collector = DecoratorUsageCollector(collector_config, self.paths, self.exclude_files)
        collected_elements = collector.collect()
        expected_names = {'UserController'}
        self.assert_collected_names(collected_elements, expected_names)

        collector_config = {'decorator_regex': '^.*decorator$'}
        collector = DecoratorUsageCollector(collector_config, self.paths, self.exclude_files)
        collected_elements = collector.collect()
        expected_names = {'UserService', 'helper_function'}
        self.assert_collected_names(collected_elements, expected_names)

    def test_bool_collector(self):
        collector_config = {
            'type': 'bool',
            'must': [{'type': 'class_name_regex', 'class_name_regex': '.*Service$'}],
            'must_not': [
                {'type': 'file_regex', 'regex': '.*/base_service.py'},
                {'type': 'file_regex', 'regex': '.*/excluded_folder_name/.*'},
                {'type': 'decorator_usage', 'decorator_name': 'deprecated_service'}
            ]
        }
        collector = BoolCollector(collector_config, self.paths, self.exclude_files)
        collected_elements = collector.collect()
        expected_classes = {'UserService'}
        self.assert_collected_classes(collected_elements, expected_classes)

    def assert_collected_classes(self, collected_elements, expected_classes):
        collected_class_names = {element.name for element in collected_elements}
        self.assertEqual(collected_class_names, expected_classes)

    def assert_collected_names(self, collected_elements, expected_names):
        collected_names = {element.name for element in collected_elements}
        self.assertEqual(collected_names, expected_names)

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
    unittest.main()