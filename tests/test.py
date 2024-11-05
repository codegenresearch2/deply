# tests/test_archcheck.py

import unittest
import os
import shutil
from architecture_checker.main import main
from unittest.mock import patch
from io import StringIO
import sys


class TestArchCheck(unittest.TestCase):

    def setUp(self):
        # Set up a simulated project structure
        self.test_project_root = os.path.abspath('tests/test_project')
        self.app_path = os.path.join(self.test_project_root, 'app')
        os.makedirs(self.app_path, exist_ok=True)

        # Create config.yaml for the test
        self.config_path = os.path.join(self.test_project_root, 'config.yaml')
        with open(self.config_path, 'w') as f:
            f.write("""
layers:
  - name: models
    collectors:
      - type: file_regex
        regex: ".*/models.py"

  - name: views
    collectors:
      - type: file_regex
        regex: ".*/views.py"

ruleset:
  views:
    disallow:
      - models
""")

        # Create models.py with a class
        with open(os.path.join(self.app_path, 'models.py'), 'w') as f:
            f.write("""
class MyModel:
    pass
""")

    def tearDown(self):
        # Clean up the test project directory after each test
        shutil.rmtree(self.test_project_root)

    def test_class_dependency_violation(self):
        # Create views.py that imports MyModel from models
        with open(os.path.join(self.app_path, 'views.py'), 'w') as f:
            f.write("""
from .models import MyModel

def view_function():
    instance = MyModel()
""")
        # Capture the output
        with patch.object(sys, 'argv', [
            'archcheck',
            '--project_root', self.test_project_root,
            '--config', self.config_path
        ]):
            with patch('sys.stdout', new=StringIO()) as fake_out, patch('sys.stderr', new=StringIO()):
                try:
                    main()
                except SystemExit:
                    pass
                output = fake_out.getvalue()

                self.assertIn('views.py:2', output)

    def test_no_violation(self):
        # Create views.py that does not import from models
        with open(os.path.join(self.app_path, 'views.py'), 'w') as f:
            f.write("""
def view_function():
    pass
""")
        # Capture the output
        with patch.object(sys, 'argv', [
            'archcheck',
            '--project_root', self.test_project_root,
            '--config', self.config_path
        ]):
            with patch('sys.stdout', new=StringIO()) as fake_out, patch('sys.stderr', new=StringIO()):
                try:
                    main()
                except SystemExit:
                    pass
                output = fake_out.getvalue()

                self.assertNotIn('views', output)


if __name__ == '__main__':
    unittest.main()
