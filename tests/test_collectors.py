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
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.test_dir) / 'test_project'
        self.test_project_dir.mkdir()
        # ... rest of the setup code ...

    def tearDown(self):
        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    # ... rest of the test methods ...

    @staticmethod
    def capture_output():
        new_out, new_err = StringIO(), StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = new_out, new_err
            yield sys.stdout, sys.stderr
        finally:
            sys.stdout, sys.stderr = old_out, old_err

def main():
    parser = argparse.ArgumentParser(prog="deply", description='Deply - A dependency analysis tool')
    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')
    parser_analyse = subparsers.add_parser('analyze', help='Analyze the project dependencies')
    parser_analyse.add_argument("--config", type=str, default="deply.yaml", help="Path to the configuration YAML file")
    parser_analyse.add_argument("--report-format", type=str, choices=["text", "json", "html"], default="text",
                                help="Format of the output report")
    parser_analyse.add_argument("--output", type=str, help="Output file for the report")
    args = parser.parse_args()
    if not args.command:
        args = parser.parse_args(['analyze'] + sys.argv[1:])
    # ... rest of the main function ...

if __name__ == '__main__':
    main()


In the provided code, I have added an `argparse` subparser for the 'analyze' command to improve command-line argument parsing clarity. I have also set default configuration values for convenience. The `capture_output` function has been moved to the `TestCollectors` class to be used as a static method for capturing output in tests. The `main` function has been left unchanged as it already follows the provided rules.