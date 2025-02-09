import unittest
import tempfile
import shutil
import os
from pathlib import Path
import sys
import yaml
from contextlib import contextmanager
from io import StringIO

from deply.main import main


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestCodeAnalyzer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.test_dir) / 'test_project'
        self.test_project_dir.mkdir()

        models_dir = self.test_project_dir / 'models'
        models_dir.mkdir()
        base_model_py = models_dir / 'base_model.py'
        base_model_py.write_text('class BaseModel:\n    pass\n')        

        my_model_py = models_dir / 'my_model.py'
        my_model_py.write_text('from .base_model import BaseModel\n\nclass MyModel(BaseModel):\n    pass\n')        

        views_dir = self.test_project_dir / 'views'
        views_dir.mkdir()
        views_py = views_dir / 'views.py'
        views_py.write_text('from ..models.my_model import MyModel\n\ndef my_view():\n    model = MyModel()\n')        

        self.config_yaml = Path(self.test_dir) / 'config.yaml'
        config_data = {
            'deply': {
                'paths': ['./test_project'],
                'layers': [
                    {
                        'name': 'models',
                        'collectors': [
                            {
                                'type': 'class_inherits',
                                'base_class': 'BaseModel'
                            }
                        ]
                    },
                    {
                        'name': 'views',
                        'collectors': [
                            {
                                'type': 'file_regex',
                                'regex': '.*/views.py'
                            }
                        ]
                    }
                ],
                'ruleset': {
                    'views': {
                        'disallow': ['models']
                    }
                }
            }
        }
        with self.config_yaml.open('w') as f:
            yaml.dump(config_data, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_code_analyzer(self):
        old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        try:
            with captured_output() as (out, err):
                try:
                    sys.argv = ['main.py', '--config', str(self.config_yaml)]
                    if 'analyze' in sys.argv:
                        main()
                    else:
                        raise ValueError('Command not recognized.')
                except SystemExit as e:
                    exit_code = e.code
            output = out.getvalue().strip()
            self.assertEqual(exit_code, 1)
            self.assertIn('Layer \'views\' is not allowed to depend on layer \'models\'', output)
        finally:
            os.chdir(old_cwd)


if __name__ == '__main__':
    unittest.main()