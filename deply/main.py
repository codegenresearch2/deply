import argparse
import sys
from pathlib import Path

from deply import __version__
from .code_analyzer import CodeAnalyzer
from .collectors.collector_factory import CollectorFactory
from .config_parser import ConfigParser
from .models.code_element import CodeElement
from .models.dependency import Dependency
from .models.layer import Layer
from .reports.report_generator import ReportGenerator
from .rules.dependency_rule import DependencyRule


def main():
    parser = argparse.ArgumentParser(prog="deply", description='Deply - A dependency analysis tool')
    parser.add_argument('-V', '--version', action='store_true', help='Show the version number and exit')

    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')
    parser_analyse = subparsers.add_parser('analyze', help='Analyze the project dependencies')
    parser_analyse.add_argument('--config', type=str, default="deply.yaml", help="Path to the configuration YAML file")
    parser_analyse.add_argument('--report-format', type=str, choices=["text", "json", "html"], default="text",
                                help="Format of the output report")
    parser_analyse.add_argument('--output', type=str, help="Output file for the report")
    args = parser.parse_args()

    if args.version:
        version = __version__
        print(f"deply {version}")
        sys.exit(0)

    # Parse configuration
    config_path = Path(args.config)
    config = ConfigParser(config_path).parse()

    # Collect code elements and organize them by layers
    layers: dict[str, Layer] = {}
    code_element_to_layer: dict[CodeElement, str] = {}

    for layer_config in config['layers']:
        layer_name = layer_config['name']
        collectors = layer_config.get('collectors', [])
        collected_elements: set[CodeElement] = set()

        for collector_config in collectors:
            collector = CollectorFactory.create(collector_config, config['paths'], config['exclude_files'])
            collected = collector.collect()
            collected_elements.update(collected)

        # Initialize Layer with collected code elements
        layer = Layer(
            name=layer_name,
            code_elements=collected_elements,
            dependencies=set()
        )
        layers[layer_name] = layer

        # Map each code element to its layer
        for element in collected_elements:
            code_element_to_layer[element] = layer_name

    # Analyze code to find dependencies
    analyzer = CodeAnalyzer(set(code_element_to_layer.keys()))
    dependencies: set[Dependency] = analyzer.analyze()

    # Assign dependencies to respective layers
    for dependency in dependencies:
        source_layer_name = code_element_to_layer.get(dependency.code_element)
        if source_layer_name and source_layer_name in layers:
            layers[source_layer_name].dependencies.add(dependency)

    # Apply rules
    rule = DependencyRule(config['ruleset'])
    violations = rule.check(layers=layers)

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
