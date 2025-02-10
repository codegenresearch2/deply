import argparse
import sys
from pathlib import Path
from typing import Any, Dict
import yaml

class ConfigParser:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def parse(self) -> Dict[str, Any]:
        with self.config_path.open("r") as f:
            config = yaml.safe_load(f)

        deply_config = config.get('deply', {})
        deply_config = deply_config if deply_config else config
        deply_config.setdefault('paths', [str(self.config_path.parent)])
        deply_config.setdefault('exclude_files', [])
        deply_config.setdefault('layers', [])
        deply_config.setdefault('ruleset', {})

        return deply_config

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
    config_path = Path(args.config)

    # Parse configuration
    config = ConfigParser(config_path).parse()

    # Rest of the main function...

if __name__ == "__main__":
    main()