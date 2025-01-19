import os
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager
from io import StringIO
from pathlib import Path

import yaml

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


class TestFalseDependencyPath(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.test_dir) / 'test_project'
        self.test_project_dir.mkdir()

        file_with_linkparams = self.test_project_dir / 'service.py'
        file_with_linkparams.write_text(
            'from dataclasses import dataclass, field\n'
            'class LinkParams:\n'
            '    path: str = field(default="")\n'
            '    query: dict[str, str] = field(default_factory=dict)\n'
        )

        file_with_django_import = self.test_project_dir / 'urls.py'
        file_with_django_import.write_text(
            'from django.urls import path\n'
            '\n'
            'def create_path():\n'
            '    return path("some/url", None)\n'
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def run_deply(self, config_data):
        config_path = Path(self.test_dir) / 'deply.yaml'
        with config_path.open('w') as f:
            yaml.dump(config_data, f)

        old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        try:
            with captured_output() as (out, err):
                exit_code = 0
                try:
                    sys.argv = ['main.py', 'analyze', '--config', str(config_path)]
                    main()
                except SystemExit as e:
                    exit_code = e.code
            output = out.getvalue()
        finally:
            os.chdir(old_cwd)

        return exit_code, output

    def test_path_not_flagged_as_false_dependency(self):
        config_data = {
            'deply': {
                'paths': ['./test_project'],
                'layers': [
                    {
                        'name': 'service',
                        'collectors': [
                            {
                                'type': 'file_regex',
                                'regex': '.*/service.py'
                            }
                        ]
                    },
                    {
                        'name': 'urls',
                        'collectors': [
                            {
                                'type': 'file_regex',
                                'regex': '.*/urls.py'
                            }
                        ]
                    }
                ],
                'ruleset': {
                    'urls': {
                        'disallow_layer_dependencies': ['service']
                    }
                }
            }
        }

        exit_code, output = self.run_deply(config_data)
        self.assertEqual(exit_code, 0, f"Expected no violations. Output:\n{output}")


if __name__ == '__main__':
    unittest.main()
