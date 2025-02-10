import argparse
import sys
from pathlib import Path
import yaml
from typing import Any, Dict

class ConfigParser:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def parse(self) -> Dict[str, Any]:
        with self.config_path.open("r") as f:
            config = yaml.safe_load(f)

        config = config.get('deply', config)
        config.setdefault('exclude_files', [])
        config.setdefault('layers', [])
        config.setdefault('ruleset', {})
        config.setdefault('paths', [str(self.config_path.parent)])

        return config

def main():
    parser = argparse.ArgumentParser(prog="deply", description='Deply - A dependency analysis tool')
    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')

    parser_analyze = subparsers.add_parser('analyze', help='Analyze the project dependencies')
    parser_analyze.add_argument("--config", type=str, default="deply.yaml", help="Path to the configuration YAML file")
    parser_analyze.add_argument("--report-format", type=str, choices=["text", "json", "html"], default="text", help="Format of the output report")
    parser_analyze.add_argument("--output", type=str, help="Output file for the report")

    args = parser.parse_args()

    if not args.command:
        args = parser.parse_args(['analyze'] + sys.argv[1:])

    config_path = Path(args.config)
    config = ConfigParser(config_path).parse()

if __name__ == "__main__":
    main()