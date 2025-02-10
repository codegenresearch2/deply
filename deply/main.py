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
    # Parse command-line arguments
    parser = argparse.ArgumentParser(prog="deply", description='A tool for analyzing and enforcing rules on code layers')
    parser.add_argument("command", nargs='?', default='analyze', help="Command to run (default: analyze)")
    parser.add_argument("--config", type=str, default="deply.yaml", help="Path to the configuration YAML file")
    parser.add_argument("--report-format", type=str, choices=["text", "json", "html"], default="text",
                        help="Format of the output report")
    parser.add_argument("--output", type=str, help="Output file for the report")
    args = parser.parse_args()

    config_path = Path(args.config)

    # Parse configuration
    config = ConfigParser(config_path).parse()

    # Collect code elements and organize them by layers
    layers = {}
    code_element_to_layer = {}

    for layer_config in config['layers']:
        layer_name = layer_config['name']
        collectors = layer_config.get('collectors', [])
        collected_elements = set()

        for collector_config in collectors:
            collector = CollectorFactory.create(collector_config, config['paths'], config.get('exclude_files', []))
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
    dependencies = analyzer.analyze()

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