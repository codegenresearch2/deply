import argparse\\\nimport sys\\nimport tempfile\\nimport shutil\\nimport os\\nfrom pathlib import Path\\nimport yaml\\nfrom contextlib import contextmanager\\nfrom io import StringIO\\n\\nfrom deply.main import main\\\\\n\\n@contextmanager\\ndef captured_output() -> tuple[StringIO, StringIO]:\\n    new_out, new_err = StringIO(), StringIO()\\n    old_out, old_err = sys.stdout, sys.stderr\\n    try:\\n        sys.stdout, sys.stderr = new_out, new_err\\n        yield sys.stdout, sys.stderr\\n    finally:\\n        sys.stdout, sys.stderr = old_out, old_err\\\\\n\\nclass TestCodeAnalyzer(unittest.TestCase):\\n    def setUp(self) -> None:\\n        self.test_dir = tempfile.mkdtemp()\\n        self.test_project_dir = Path(self.test_dir) / 'test_project'\\n        self.test_project_dir.mkdir()\\\\\n\\n        models_dir = self.test_project_dir / 'models'\\n        models_dir.mkdir()\\n        base_model_py = models_dir / 'base_model.py'\\n        base_model_py.write_text('class BaseModel:\\\n    pass')\\\\\n\\n        my_model_py = models_dir / 'my_model.py'\\n        my_model_py.write_text('from .base_model import BaseModel\\\n\\\nclass MyModel(BaseModel):\\\n    pass')\\\\\n\\n        views_dir = self.test_project_dir / 'views'\\n        views_dir.mkdir()\\n        views_py = views_dir / 'views.py'\\n        views_py.write_text('from ..models.my_model import MyModel\\\n\\\ndef my_view():\\n    model = MyModel()')\\\\\n\\n        self.config_yaml = Path(self.test_dir) / 'config.yaml'\\n        config_data = {\\\\\n            'deply': {\\\\\n                'paths': ['./test_project'],\\\n                'layers': [\\\n                    {\\\\\n                        'name': 'models',\\\n                        'collectors': [\\\n                            {\\\\\n                                'type': 'class_inherits',\\\n                                'base_class': 'BaseModel'\\\n                            }\\\n                        ]\\\n                    },\\\n                    {\\\\\n                        'name': 'views',\\\n                        'collectors': [\\\n                            {\\\\\n                                'type': 'file_regex',\\\n                                'regex': '.*/views.py'\\\n                            }\\\n                        ]\\\n                    }\\\n                ],\\\n                'ruleset': {\\\\\n                    'views': {\\\\\n                        'disallow': ['models']\\\n                    }\\\n                }\\\n            }\\\n        }\\\\\n        with self.config_yaml.open('w') as f:\\n            yaml.dump(config_data, f)\\\\\n\\n    def tearDown(self) -> None:\\n        shutil.rmtree(self.test_dir)\\\\\n\\n    def test_code_analyzer(self) -> None:\\n        old_cwd = os.getcwd()\\n        os.chdir(self.test_dir)\\\\\n\\n        with captured_output() as (out, err):\\n            try:\\n                sys.argv = ['main.py', 'analyze', '--config', str(self.config_yaml)]\\n                main()\\n            except SystemExit as e:\\n                exit_code = e.code\\n        output = out.getvalue()\\n        self.assertEqual(exit_code, 1)\\n        self.assertIn('Layer 'test_project' is not allowed to depend on layer 'models'', output)\\\\\n\\nif __name__ == '__main__':\\n    unittest.main()