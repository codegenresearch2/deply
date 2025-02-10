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

        config = config['deply']
        config.setdefault('paths', [])
        config.setdefault('exclude_files', [])
        config.setdefault('layers', [])
        config.setdefault('ruleset', {})

        return config

def main(args=None):
    parser = argparse.ArgumentParser(prog="deply", description='Deply - A dependency analysis tool')
    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')

    parser_analyze = subparsers.add_parser('analyze', help='Analyze the project dependencies')
    parser_analyze.add_argument("--config", type=str, default="deply.yaml", help="Path to the configuration YAML file")
    parser_analyze.add_argument("--report-format", type=str, choices=["text", "json", "html"], default="text",
                                help="Format of the output report")
    parser_analyze.add_argument("--output", type=str, help="Output file for the report")

    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    if not args.command:
        args = parser.parse_args(['analyze'] + sys.argv[1:])

    config_path = Path(args.config)

    # Parse configuration
    config = ConfigParser(config_path).parse()

    # Rest of the main function...

if __name__ == "__main__":
    main()


In the rewritten code, I have added an `argparse` subparser for the `analyze` command. This command has arguments for the configuration file path, report format, and output file. I have also modified the `main` function to accept arguments, which allows for better testing and organization. The `ConfigParser` class remains unchanged.