import argparse
import os
import sys

import yaml

from .reporter import Reporter
from .rule_loader import load_rules


def main():
    parser = argparse.ArgumentParser(description='Architecture Checker')
    parser.add_argument('--config', type=str, help='Path to the configuration file', default='config.yaml')
    parser.add_argument('--project_root', type=str, help='Path to project root', default=os.getcwd())
    args = parser.parse_args()

    project_root = args.project_root
    config_path = args.config

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Configuration file not found at {config_path}")
        sys.exit(1)

    rules = load_rules(config, project_root)

    reporter = Reporter()
    for rule in rules:
        rule.run()
        violations = rule.report()
        reporter.collect(violations)

    exit_code = reporter.generate_report()
    sys.exit(exit_code)
