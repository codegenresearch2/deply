import argparse
import sys
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
    # Parse command-line arguments
    parser = argparse.ArgumentParser(prog="deply", description='A dependency analysis tool for Python projects')
    subparsers = parser.add_subparsers(dest='command', title='Sub-commands', help='Available commands')

    parser_analyze = subparsers.add_parser('analyze', help='Analyze code for dependencies')
    parser_analyze.add_argument("--config", type=str, default='deply.yaml', help="Path to the configuration YAML file")
    parser_analyze.add_argument("--report-format", type=str, choices=["text", "json", "html"], default="text",
                                help="Format of the output report")
    parser_analyze.add_argument("--output", type=str, help="Output file for the report")

    if len(sys.argv) == 1:
        sys.argv.append('analyze')

    args = parser.parse_args()

    config_path = Path(args.config)

    # Parse configuration
    config = ConfigParser(config_path).parse()

    # Set default paths if they are empty
    if not config.get('paths'):
        config['paths'] = ['./']

    # Collect code elements and organize them by layers
    layers = {}
    code_element_to_layer = {}

    for layer_config in config.get('layers', []):
        layer_name = layer_config['name']
        collectors = [CollectorFactory.create(collector_config, config['paths'], config.get('exclude_files', []))
                      for collector_config in layer_config.get('collectors', [])]
        collected_elements = {element for collector in collectors for element in collector.collect()}

        layer = Layer(name=layer_name, code_elements=collected_elements, dependencies=set())
        layers[layer_name] = layer

        for element in collected_elements:
            code_element_to_layer[element] = layer_name

    # Analyze code to find dependencies
    analyzer = CodeAnalyzer(set(code_element_to_layer.keys()))
    dependencies = analyzer.analyze()

    # Assign dependencies to respective layers
    for dependency in dependencies:
        source_layer_name = code_element_to_layer.get(dependency.code_element)
        if source_layer_name in layers:
            layers[source_layer_name].dependencies.add(dependency)

    # Apply rules
    rule = DependencyRule(config.get('ruleset', {}))
    violations = rule.check(layers)

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
    sys.exit(1 if violations else 0)

if __name__ == "__main__":
    main()