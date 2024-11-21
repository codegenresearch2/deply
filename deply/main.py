import argparse
import sys
import logging
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

    # Set up logging
    log_level = logging.WARNING  # Default log level
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if args.command is None:
        args = parser.parse_args(['analyze'] + sys.argv[1:])

    logging.info("Starting Deply analysis...")

    # Parse configuration
    config_path = Path(args.config)
    logging.info(f"Using configuration file: {config_path}")
    config = ConfigParser(config_path).parse()

    # Collect code elements and organize them by layers
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

        # Initialize Layer with collected code elements
        layer = Layer(
            name=layer_name,
            code_elements=collected_elements,
            dependencies=set()
        )
        layers[layer_name] = layer
        logging.info(f"Layer '{layer_name}' collected {len(collected_elements)} code elements.")

        # Map each code element to its layer
        for element in collected_elements:
            code_element_to_layer[element] = layer_name

    # Analyze code to find dependencies
    logging.info("Analyzing code to find dependencies...")
    analyzer = CodeAnalyzer(set(code_element_to_layer.keys()))
    dependencies: set[Dependency] = analyzer.analyze()
    logging.info(f"Found {len(dependencies)} dependencies.")

    # Assign dependencies to respective layers
    logging.info("Assigning dependencies to layers...")
    for dependency in dependencies:
        source_layer_name = code_element_to_layer.get(dependency.code_element)
        if source_layer_name and source_layer_name in layers:
            layers[source_layer_name].dependencies.add(dependency)
            logging.debug(f"Assigned dependency from {dependency.code_element.name} to layer '{source_layer_name}'")

    # Apply rules
    logging.info("Applying dependency rules...")
    rule = DependencyRule(config['ruleset'])
    violations = rule.check(layers=layers)
    logging.info(f"Analysis complete. Found {len(violations)} violation(s).")

    # Generate report
    logging.info("Generating report...")
    report_generator = ReportGenerator(violations)
    report = report_generator.generate(format=args.report_format)

    # Output the report
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        logging.info(f"Report written to {output_path}")
    else:
        print(report)

    # Exit with appropriate status
    if violations:
        exit(1)
    else:
        logging.info("No violations detected.")
        exit(0)


if __name__ == "__main__":
    main()
