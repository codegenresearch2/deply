import argparse
from pathlib import Path

from .code_analyzer import CodeAnalyzer
from .collectors.collector_factory import CollectorFactory
from .config_parser import ConfigParser
from .models.code_element import CodeElement
from .models.dependency import Dependency
from .models.layer import Layer
from .reports.report_generator import ReportGenerator
from .rules.dependency_rule import DependencyRule


def main():
    parser = argparse.ArgumentParser(prog='deply', description='Deply - A tool for analyzing code dependencies')
    subparsers = parser.add_subparsers(dest='command', help='Sub-command help')

    # Add sub-command for 'analyze'
    analyze_parser = subparsers.add_parser('analyze', help='Analyze command help')
    analyze_parser.add_argument('--config', required=True, type=str, help='Path to the configuration YAML file')
    analyze_parser.add_argument('--report-format', type=str, choices=['text', 'json', 'html'], default='text', help='Format of the output report')
    analyze_parser.add_argument('--output', type=str, help='Output file for the report')

    args = parser.parse_args()

    if args.command != 'analyze':
        parser.error('Unsupported command')

    config_path = Path(args.config)

    # Parse configuration
    config = ConfigParser(config_path).parse()

    # Collect code elements and organize them by layers
    layers = {}
    code_element_to_layer = {}

    for layer_config in get(config, 'layers', []):
        layer_name = layer_config['name']
        collectors = get(layer_config, 'collectors', [])
        collected = set()

        for collector_config in collectors:
            collector = CollectorFactory.create(collector_config, get(config, 'paths', []), get(config, 'exclude_files', []))
            collected.update(collector.collect())

        layer = Layer(
            name=layer_name,
            code_elements=collected,
            dependencies=set()
        )
        layers[layer_name] = layer

        for element in collected:
            code_element_to_layer[element] = layer_name

    # Analyze code to find dependencies
    dependencies = CodeAnalyzer(set(code_element_to_layer.keys())).analyze()

    for dependency in dependencies:
        source_layer_name = code_element_to_layer.get(dependency.code_element)
        if source_layer_name and source_layer_name in layers:
            layers[source_layer_name].dependencies.add(dependency)

    violations = DependencyRule(get(config, 'ruleset', {})).check(layers)

    report = ReportGenerator(violations).generate(format=args.report_format)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
    else:
        print(report)

    if violations:
        exit(1)
    else:
        exit(0)


if __name__ == '__main__':
    main()