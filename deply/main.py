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

class ASTVisitor(ast.NodeVisitor):
    def __init__(self, code_element):
        self.code_element = code_element
        self.dependencies = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.dependencies.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.dependencies.add(node.module)
        self.generic_visit(node)

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
        collectors = layer_config.get('collectors', [])
        collected_elements: set[CodeElement] = set()

        for collector_config in collectors:
            collector_type = collector_config.get('type', 'unknown')
            logging.debug(f"Using collector: {collector_type} for layer: {layer_name}")
            collector = CollectorFactory.create(collector_config, config['paths'], config['exclude_files'])
            collected = collector.collect()
            collected_elements.update(collected)
            logging.debug(f"Collected {len(collected)} elements for collector {collector_type}")

        layer = Layer(name=layer_name, code_elements=collected_elements, dependencies=set())
        layers[layer_name] = layer
        logging.info(f"Layer '{layer_name}' collected {len(collected_elements)} code elements.")

        for element in collected_elements:
            code_element_to_layer[element] = layer_name

    logging.info("Preparing dependency rules...")
    rules = RuleFactory.create_rules(config['ruleset'])

    violations: set[Violation] = set()
    metrics = {'total_dependencies': 0}

    def dependency_handler(source_element, target_element):
        source_layer = code_element_to_layer.get(source_element)
        target_layer = code_element_to_layer.get(target_element)

        metrics['total_dependencies'] += 1

        if not target_layer:
            return

        for rule in rules:
            violation = rule.check(source_layer, target_layer, source_element, target_element)
            if violation:
                violations.add(violation)

    logging.info("Analyzing code and checking dependencies ...")
    for element in code_element_to_layer.keys():
        with open(element.file, 'r') as file:
            tree = ast.parse(file.read())
        visitor = ASTVisitor(element)
        visitor.visit(tree)
        for dependency in visitor.dependencies:
            if dependency in code_element_to_layer:
                dependency_handler(element, code_element_to_layer[dependency])

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