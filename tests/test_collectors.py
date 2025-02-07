import unittest\"import tempfile\"import shutil\"import os\"from pathlib import Path\"import sys\"import yaml\"from contextlib import contextmanager\"from io import StringIO\n\nfrom deply.main import main\nfrom deply.collectors import FileRegexCollector, ClassInheritsCollector, ClassNameRegexCollector, DirectoryCollector, DecoratorUsageCollector\n\n@contextmanager\ndef captured_output():\n    new_out, new_err = StringIO(), StringIO()\n    old_out, old_err = sys.stdout, sys.stderr\n    try:\n        sys.stdout, sys.stderr = new_out, new_err\n        yield sys.stdout, sys.stderr\n    finally:\n        sys.stdout, sys.stderr = old_out, old_err\n\nclass TestCollectors(unittest.TestCase):\n    def setUp(self):\n        self.test_dir = tempfile.mkdtemp()\n        self.test_project_dir = Path(self.test_dir) / 'test_project'\n        self.test_project_dir.mkdir()\n\n        # Create directories\n        (self.test_project_dir / 'controllers').mkdir()\n        (self.test_project_dir / 'models').mkdir()\n        (self.test_project_dir / 'services').mkdir()\n        (self.test_project_dir / 'utilities').mkdir()\n\n        # Create files in controllers\n        base_controller_py = self.test_project_dir / 'controllers' / 'base_controller.py'\n        base_controller_py.write_text('class BaseController:\n    pass\n')\n\n        user_controller_py = self.test_project_dir / 'controllers' / 'user_controller.py'\n        user_controller_py.write_text('@login_required\nclass UserController(BaseController):\n    pass\n')\n\n        # Create files in models\n        base_model_py = self.test_project_dir / 'models' / 'base_model.py'\n        base_model_py.write_text('class BaseModel:\n    pass\n')\n\n        user_model_py = self.test_project_dir / 'models' / 'user_model.py'\n        user_model_py.write_text('class UserModel(BaseModel):\n    pass\n')\n\n        # Create files in services\n        base_service_py = self.test_project_dir / 'services' / 'base_service.py'\n        base_service_py.write_text('class BaseService:\n    pass\n')\n\n        user_service_py = self.test_project_dir / 'services' / 'user_service.py'\n        user_service_py.write_text('@service_decorator\nclass UserService(BaseService):\n    pass\n')\n\n        # Create utility functions\n        utils_py = self.test_project_dir / 'utilities' / 'utils.py'\n        utils_py.write_text('@utility_decorator\ndef helper_function():\n    pass\n')\n\n    def tearDown(self):\n        shutil.rmtree(self.test_dir)\n\n    def test_class_inherits_collector(self):\n        collector_config = {\n            'base_class': 'BaseModel',\n        }\n        paths = [str(self.test_project_dir)]\n        exclude_files = []\n        collector = ClassInheritsCollector(collector_config, paths, exclude_files)\n        collected_elements = collector.collect()\n        collected_class_names = {element.name for element in collected_elements}\n        expected_classes = {'UserModel'}\n        self.assertEqual(collected_class_names, expected_classes)\n\n    def test_file_regex_collector(self):\n        collector_config = {\n            'regex': r'.*controller.py$',\n        }\n        paths = [str(self.test_project_dir)]\n        exclude_files = []\n        collector = FileRegexCollector(collector_config, paths, exclude_files)\n        collected_elements = collector.collect()\n        collected_class_names = {element.name for element in collected_elements}\n        expected_classes = {'BaseController', 'UserController'}\n        self.assertEqual(collected_class_names, expected_classes)\n\n    def test_class_name_regex_collector(self):\n        collector_config = {\n            'class_name_regex': '^User.*',\n        }\n        paths = [str(self.test_project_dir)]\n        exclude_files = []\n        collector = ClassNameRegexCollector(collector_config, paths, exclude_files)\n        collected_elements = collector.collect()\n        collected_class_names = {element.name for element in collected_elements}\n        expected_classes = {'UserController', 'UserModel', 'UserService'}\n        self.assertEqual(collected_class_names, expected_classes)\n\n    def test_directory_collector(self):\n        collector_config = {\n            'directories': ['services'],\n        }\n        paths = [str(self.test_project_dir)]\n        exclude_files = []\n        collector = DirectoryCollector(collector_config, paths, exclude_files)\n        collected_elements = collector.collect()\n        collected_class_names = {element.name for element in collected_elements}\n        expected_classes = {'BaseService', 'UserService'}\n        self.assertEqual(collected_class_names, expected_classes)\n\n    def test_decorator_usage_collector(self):\n        collector_config = {\n            'decorator_name': 'login_required',\n        }\n        paths = [str(self.test_project_dir)]\n        exclude_files = []\n        collector = DecoratorUsageCollector(collector_config, paths, exclude_files)\n        collected_elements = collector.collect()\n        collected_names = {element.name for element in collected_elements}\n        expected_names = {'UserController'}\n        self.assertEqual(collected_names, expected_names)\n\n    def test_decorator_usage_collector_regex(self):\n        collector_config = {\n            'decorator_regex': '^.*decorator$',\n        }\n        paths = [str(self.test_project_dir)]\n        exclude_files = []\n        collector = DecoratorUsageCollector(collector_config, paths, exclude_files)\n        collected_elements = collector.collect()\n        collected_names = {element.name for element in collected_elements}\n        expected_names = {'UserService', 'helper_function'}\n        self.assertEqual(collected_names, expected_names)\n\n    def test_class_name_regex_collector_no_matches(self):\n        collector_config = {\n            'class_name_regex': '^NonExistentClass.*',\n        }\n        paths = [str(self.test_project_dir)]\n        exclude_files = []\n        collector = ClassNameRegexCollector(collector_config, paths, exclude_files)\n        collected_elements = collector.collect()\n        self.assertEqual(len(collected_elements), 0)\n\n    def test_bool_collector(self):\n        collector_config = {\n            'type': 'bool',\n            'must': [\n                {'type': 'class_name_regex', 'class_name_regex': '.*Service$'}\n            ],\n            'must_not': [\n                {'type': 'file_regex', 'regex': '.*/base_service.py'}, \n                {'type': 'file_regex', 'regex': '.*/excluded_folder_name/.*'}, \n                {'type': 'decorator_usage', 'decorator_name': 'deprecated_service'}\n            ]\n        }\n        paths = [str(self.test_project_dir)]\n        exclude_files = []\n        collector = BoolCollector(collector_config, paths, exclude_files)\n        collected_elements = collector.collect()\n        collected_class_names = {element.name for element in collected_elements}\n        expected_classes = {'UserService'}\n        self.assertEqual(collected_class_names, expected_classes)\n\n    def test_directory_collector_with_rules(self):\n        user_controller_py = self.test_project_dir / 'controllers' / 'user_controller.py'\n        user_controller_py.write_text(\n            'from ..models.user_model import UserModel\nclass UserController:\n    def __init__(self):\n        self.model = UserModel()')\n        config_yaml = Path(self.test_dir) / 'config_directory_collector_rules.yaml'\n        config_data = {\n            'deply': {\n                'paths': [str(self.test_project_dir)], \n                'layers': [\n                    {\n                        'name': 'models_layer',\n                        'collectors': [\n                            {\n                                'type': 'directory',\n                                'directories': ['models'],\n                            }\n                        ]\n                    },\n                    {\n                        'name': 'controllers_layer',\n                        'collectors': [\n                            {\n                                'type': 'directory',\n                                'directories': ['controllers'],\n                            }\n                        ]\n                    }\n                ],\n                'ruleset': {\n                    'controllers_layer': {\n                        'disallow': ['models_layer']\n                    }\n                }\n            }\n        }\n        with config_yaml.open('w') as f:\n            yaml.dump(config_data, f)\n\n        with self.capture_output() as (out, err):\n            try:\n                sys.argv = ['main.py', 'analyze', '--config', str(config_yaml)]\n                main()\n            except SystemExit as e:\n                exit_code = e.code\n        output = out.getvalue()\n        self.assertEqual(exit_code, 1)\n        self.assertIn('Layer 'controllers_layer' is not allowed to depend on layer 'models_layer'', output)\n\n    @staticmethod\n    def capture_output():\n        from contextlib import contextmanager\n        from io import StringIO\n        import sys\n\n        @contextmanager\n        def _capture_output():\n            new_out, new_err = StringIO(), StringIO()\n            old_out, old_err = sys.stdout, sys.stderr\n            try:\n                sys.stdout, sys.stderr = new_out, new_err\n                yield sys.stdout, sys.stderr\n            finally:\n                sys.stdout, sys.stderr = old_out, old_err\n\n        return _capture_output()\n\nif __name__ == '__main__':\n    unittest.main()