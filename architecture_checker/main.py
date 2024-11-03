import argparse
from pathlib import Path
from .config_parser import ConfigParser
from .code_analyzer import CodeAnalyzer
from .reports.report_generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(prog="architecture_checker")
    parser.add_argument("--config", type=str, help="Path to the configuration YAML file")
    parser.add_argument("--project_root", type=str, help="Root directory of the project to analyze")
    parser.add_argument("--report-format", type=str, choices=["text", "json", "html"], default="text")
    parser.add_argument("--output", type=str, help="Output file for the report")
    args = parser.parse_args()

    config_path = Path(args.config)
    project_root = Path(args.project_root)

    config = ConfigParser(config_path).parse()
    analyzer = CodeAnalyzer(config, project_root)
    violations = analyzer.analyze()

    report_generator = ReportGenerator(violations)
    report = report_generator.generate(format=args.report_format)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
    else:
        print(report)


if __name__ == "__main__":
    main()
