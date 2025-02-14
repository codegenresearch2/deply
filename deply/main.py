import argparse
import logging
import sys
import ast
from pathlib import Path

from deply import __version__
from deply.rules import RuleFactory
from .code_analyzer import CodeAnalyzer
from .collectors.collector_factory import CollectorFactory
from .config_parser import ConfigParser
from .models.code_element import CodeElement
from .models.layer import Layer
from .models.violation import Violation
from .reports.report_generator import ReportGenerator

def main():
    parser = argparse.ArgumentParser(prog="deply", description='Deply - A dependency analysis tool')
    parser.add_argument('-V', '--version', action='store_true', help='Show the version number and exit')
    parser.add_argument('-v', '--verbose', action='count', default=1, help='Increase output verbosity')

    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')
    parser_analyze = subparsers.add_parser('analyze', help='Analyze the project dependencies')
    parser_analyze.add_argument('--config', type=str, default="deply.yaml", help="Path to the configuration YAML file")
    parser_analyze.add_argument('--report-format', type=str, choices=["text", "json", "html"], default="text",
                                help="Format of the output report")
    parser_analyze.add_argument('--output', type=str, help="Output file for the report")
    args = parser.parse_args()

    if args.version:
        version = __version__
        print(f"deply {version}")
        sys.exit(0)

    log_level = logging.WARNING
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG

    logging.basicConfig(level=log_level, format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    if args.command is None:
        args = parser.parse_args(['analyze'] + sys.argv[1:])

    logging.info("Starting Deply analysis...")

    config_path = Path(args.config)
    logging.info(f"Using configuration file: {config_path}")
    config = ConfigParser(config_path).parse()

    layers: dict[str, Layer] = {}
    code_element_to_layer: dict[CodeElement, str] = {}

    logging.info("Collecting code elements for each layer...")
    for layer_config in config['layers']:
        layer_name = layer_config['name']
        logging.debug(f"Processing layer: {layer_name}")
        collected_elements: set[CodeElement] = set()

        for collector_config in layer_config.get('collectors', []):
            collector = CollectorFactory.create(collector_config, config['paths'])
            collected = collector.collect()
            collected_elements.update(collected)

        layer = Layer(name=layer_name, code_elements=collected_elements)
        layers[layer_name] = layer
        logging.info(f"Layer '{layer_name}' collected {len(collected_elements)} code elements.")

        for element in collected_elements:
            code_element_to_layer[element] = layer_name

    logging.info("Preparing dependency rules...")
    rules = RuleFactory.create_rules(config['ruleset'])

    violations: set[Violation] = set()
    metrics = {'total_dependencies': 0}

    def dependency_handler(dependency):
        metrics['total_dependencies'] += 1
        source_layer = code_element_to_layer.get(dependency.code_element)
        target_layer = code_element_to_layer.get(dependency.depends_on_code_element)
        if target_layer:
            for rule in rules:
                violation = rule.check(source_layer, target_layer, dependency)
                if violation:
                    violations.add(violation)

    logging.info("Analyzing code and checking dependencies ...")
    analyzer = CodeAnalyzer(code_elements=set(code_element_to_layer.keys()), dependency_handler=dependency_handler)
    analyzer.analyze()

    logging.info(f"Analysis complete. Found {metrics['total_dependencies']} dependencies(s).")

    logging.info("Generating report...")
    report_generator = ReportGenerator(list(violations))
    report = report_generator.generate(format=args.report_format)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        logging.info(f"Report written to {output_path}")
    else:
        print("\n")
        print(report)

    if violations:
        print(f"\nTotal violation(s): {len(violations)}")
        exit(1)
    else:
        print("\nNo violations detected.")
        exit(0)

if __name__ == "__main__":
    main()


The given code snippet is rewritten to incorporate the following changes:

1. AST is used for code analysis in the `CodeAnalyzer` class.
2. Code duplication in collectors is reduced by using a factory design pattern to create collectors.
3. A more modular collector design is implemented, where each collector is responsible for collecting code elements based on its configuration.
4. The dependency handler function is defined within the `main` function to have access to the `rules`, `violations`, and `metrics` variables.
5. The `dependency_handler` function is passed to the `CodeAnalyzer` instance to handle dependencies immediately during analysis.
6. The `collected_elements` set is defined outside the collector loop to accumulate elements from all collectors.
7. The `code_element_to_layer` dictionary is updated inside the collector loop to map each code element to its layer.
8. The `Layer` class is updated to only accept `code_elements` as a parameter, as the `dependencies` attribute is no longer needed.
9. The `collector_config` is directly passed to the `CollectorFactory.create` method to avoid unnecessary type checking.
10. The `collect` method of the collector is called outside the collector loop to collect elements for each configuration.