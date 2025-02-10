import argparse
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager
from io import StringIO
from pathlib import Path

import yaml

from deply.collectors import FileRegexCollector, ClassInheritsCollector
from deply.collectors.bool_collector import BoolCollector
from deply.collectors.class_name_regex_collector import ClassNameRegexCollector
from deply.collectors.decorator_usage_collector import DecoratorUsageCollector
from deply.collectors.directory_collector import DirectoryCollector
from deply.main import main

class TestCollectors(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.test_dir) / 'test_project'
        self.test_project_dir.mkdir()
        self.setup_test_project()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def setup_test_project(self):
        # Create directories and files directly within the setUp method
        directories = ['controllers', 'models', 'services', 'excluded_folder_name', 'utilities']
        for directory in directories:
            (self.test_project_dir / directory).mkdir()

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

    # ... rest of the code ...

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="test_collectors", description='Test collectors for deply')
    parser.add_argument("--config", type=str, default="deply.yaml", help="Path to the configuration YAML file")
    args = parser.parse_args()
    unittest.main(argv=[sys.argv[0], '-v', '-k', 'test_collectors'])