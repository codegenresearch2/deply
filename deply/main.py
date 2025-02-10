import argparse
from pathlib import Path
import sys
import yaml

from .code_analyzer import CodeAnalyzer
from .collectors.collector_factory import CollectorFactory
from .config_parser import ConfigParser
from .models.code_element import CodeElement
from .models.dependency import Dependency
from .models.layer import Layer
from .reports.report_generator import ReportGenerator
from .rules.dependency_rule import DependencyRule

def main():
    parser = argparse.ArgumentParser(prog="deply", description='Deply - A tool for analyzing code dependencies.')
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands to run specific tasks.")

    # Sub-command for analyzing code
    analyze_parser = subparsers.add_parser('analyze', help='Analyze code dependencies based on the provided configuration.')
    analyze_parser.add_argument('--config', type=str, default="deply.yaml", help='Path to the configuration YAML file.')
    analyze_parser.add_argument('--report-format', type=str, choices=["text", "json", "html"], default="text", help='Format of the output report.')
    analyze_parser.add_argument('--output', type=str, help='Output file for the report.')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    config_path = Path(args.config)

    # Parse configuration
    try:
        config = ConfigParser(config_path).parse()
    except Exception as e:
        print(f"Error parsing configuration: {e}")
        sys.exit(2)

    # Collect code elements and organize them by layers
    layers: dict[str, Layer] = {}
    code_element_to_layer: dict[CodeElement, str] = {}

    for layer_config in config.get('layers', []):
        layer_name = layer_config.get('name')
        if not layer_name:
            print("Error: Layer name is missing in the configuration.")
            sys.exit(2)
        collectors = layer_config.get('collectors', [])
        collected_elements: set[CodeElement] = set()

        for collector_config in collectors:
            collector = CollectorFactory.create(collector_config, config.get('paths', []), config.get('exclude_files', []))
            collected = collector.collect()
            collected_elements.update(collected)

        layer = Layer(
            name=layer_name,
            code_elements=collected_elements,
            dependencies=set()
        )
        layers[layer_name] = layer

        for element in collected_elements:
            code_element_to_layer[element] = layer_name

    # Analyze code to find dependencies
    try:
        analyzer = CodeAnalyzer(set(code_element_to_layer.keys()))
        dependencies: set[Dependency] = analyzer.analyze()
    except Exception as e:
        print(f"Error during code analysis: {e}")
        sys.exit(2)

    # Assign dependencies to respective layers
    for dependency in dependencies:
        source_layer_name = code_element_to_layer.get(dependency.code_element)
        if source_layer_name and source_layer_name in layers:
            layers[source_layer_name].dependencies.add(dependency)

    # Apply rules
    try:
        rule = DependencyRule(config.get('ruleset', {}))
        violations = rule.check(layers)
    except Exception as e:
        print(f"Error applying rules: {e}")
        sys.exit(2)

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
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()