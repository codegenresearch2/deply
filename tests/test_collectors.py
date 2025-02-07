import shutil\"import sys\"import tempfile\"import unittest\"from pathlib import Path\"import yaml\"from deply.collectors import FileRegexCollector, ClassInheritsCollector\"from deply.collectors.bool_collector import BoolCollector\"from deply.collectors.class_name_regex_collector import ClassNameRegexCollector\"from deply.collectors.decorator_usage_collector import DecoratorUsageCollector\"from deply.collectors.directory_collector import DirectoryCollector\"from deply.main import main\n\nclass TestCollectors(unittest.TestCase):\n    def setUp(self):\n        # Create a temporary directory\n        self.test_dir = tempfile.mkdtemp()\n        self.test_project_dir = Path(self.test_dir) / 'test_project'\n        self.test_project_dir.mkdir()\n\n        # Create directories\n        (self.test_project_dir / 'controllers').mkdir()\n        (self.test_project_dir / 'models').mkdir()\n        (self.test_project_dir / 'services').mkdir()\n        (self.test_project_dir / 'excluded_folder_name').mkdir()\n        (self.test_project_dir / 'utilities').mkdir()\n\n        # Create files in controllers\n        base_controller_py = self.test_project_dir / 'controllers' / 'base_controller.py'\n        base_controller_py.write_text('class BaseController:\n    pass\n')\n\n        user_controller_py = self.test_project_dir / 'controllers' / 'user_controller.py'\n        user_controller_py.write_text('@login_required\nclass UserController(BaseController):\n    pass\n')\n\n        # Create files in models\n        base_model_py = self.test_project_dir / 'models' / 'base_model.py'\n        base_model_py.write_text('class BaseModel:\n    pass\n')\n\n        user_model_py = self.test_project_dir / 'models' / 'user_model.py'\n        user_model_py.write_text('class UserModel(BaseModel):\n    pass\n')\n\n        # Create files in services\n        base_service_py = self.test_project_dir / 'services' / 'base_service.py'\n        base_service_py.write_text('class BaseService:\n    pass\n')\n\n        user_service_py = self.test_project_dir / 'services' / 'user_service.py'\n        user_service_py.write_text('@service_decorator\nclass UserService(BaseService):\n    pass\n')