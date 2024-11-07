import argparse
from pathlib import Path
from .config_parser import ConfigParser
from .collectors.collector_factory import CollectorFactory
from .code_analyzer import CodeAnalyzer
from .rules.dependency_rule import DependencyRule
from .reports.report_generator import ReportGenerator


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(prog="deply", description='Deply')
    parser.add_argument("--config", required=True, type=str, help="Path to the configuration YAML file")
    parser.add_argument("--project_root", required=True, type=str, help="Root directory of the project to analyze")
    parser.add_argument("--report-format", type=str, choices=["text", "json", "html"], default="text",
                        help="Format of the output report")
    parser.add_argument("--output", type=str, help="Output file for the report")
    args = parser.parse_args()

    config_path = Path(args.config)
    project_root = Path(args.project_root)

    # Parse configuration
    config = ConfigParser(config_path).parse()

    # Collect code elements
    code_elements = set()
    code_element_to_layer = {}
    for layer in config['layers']:
        layer_name = layer['name']
        for collector_config in layer['collectors']:
            collector = CollectorFactory.create(collector_config, project_root)
            collected = collector.collect()
            code_elements.update(collected)
            for element in collected:
                code_element_to_layer[element] = layer_name

    # Analyze code to find dependencies
    analyzer = CodeAnalyzer(code_elements)
    code_element_dependencies = analyzer.analyze()

    # Apply rules
    rule = DependencyRule(config['ruleset'])
    violations = rule.check(
        code_element_to_layer=code_element_to_layer,
        code_element_dependencies=code_element_dependencies
    )

    # Generate report
    report_generator = ReportGenerator(violations)
    report = report_generator.generate(format=args.report_format)

    # Output the report
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
    else:
        print(report)

    # Exit with appropriate status
    if violations:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
