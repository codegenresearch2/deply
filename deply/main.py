import argparse
import ast
import logging
import re
import sys
from pathlib import Path

from deply import __version__
from deply.rules.rule_factory import RuleFactory
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

    # Collect paths and excluded files
    paths = [Path(p) for p in config["paths"]]
    exclude_files = [re.compile(pattern) for pattern in config["exclude_files"]]

    # Prepare layer configuration
    layers_config = config["layers"]
    ruleset = config["ruleset"]

    # Map layer collectors
    logging.info("Mapping layer collectors...")
    layer_collectors = []
    for layer_config in layers_config:
        layer_name = layer_config["name"]
        collector_configs = layer_config.get("collectors", [])
        for collector_config in collector_configs:
            collector = CollectorFactory.create(
                config=collector_config,
                paths=[str(p) for p in paths],
                exclude_files=[p.pattern for p in exclude_files])
            layer_collectors.append((layer_name, collector))

    # Collect all files
    logging.info("Collecting all files...")
    all_files = []
    for base_path in paths:
        if not base_path.exists():
            continue
        files = [f for f in base_path.rglob("*.py") if f.is_file()]

        def is_excluded(file_path: Path) -> bool:
            relative_path = str(file_path.relative_to(base_path))
            return any(pattern.search(relative_path) for pattern in exclude_files)

        files = [f for f in files if not is_excluded(f)]
        all_files.extend(files)

    # Initialize layers
    layers: dict[str, Layer] = {}
    for layer_config in layers_config:
        layers[layer_config["name"]] = Layer(name=layer_config["name"], code_elements=set(), dependencies=set())

    code_element_to_layer: dict[CodeElement, str] = {}
    logging.info("Collecting code elements for each layer...")
    for file_path in all_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            file_ast = ast.parse(file_content, filename=str(file_path))
        except:
            continue

        # Match collectors
        for layer_name, collector in layer_collectors:
            matched = collector.match_in_file(file_ast, file_path)
            for m in matched:
                layers[layer_name].code_elements.add(m)
                code_element_to_layer[m] = layer_name

    for ln, l in layers.items():
        logging.info(f"Layer '{ln}' collected {len(l.code_elements)} code elements.")

    # Prepare the rules
    logging.info("Preparing rules...")
    rules = RuleFactory.create_rules(ruleset)

    # Initialize a list to collect violations and metrics
    violations: set[Violation] = set()
    metrics = {
        'total_dependencies': 0,
    }

    # Define the dependency handler function
    def dependency_handler(dependency):
        source_element = dependency.code_element
        target_element = dependency.depends_on_code_element

        # Determine the layers of the source and target elements
        source_layer = code_element_to_layer.get(source_element)
        target_layer = code_element_to_layer.get(target_element)

        # Increment total dependencies metric
        metrics['total_dependencies'] += 1

        # Skip if target element is not mapped to a layer
        if not target_layer:
            return

        # Check the dependency against the rules immediately
        for rule in rules:
            violation = rule.check(source_layer, target_layer, dependency)
            if violation:
                violations.add(violation)

    # Analyze code to find dependencies and check them immediately
    logging.info("Analyzing code and checking dependencies ...")
    analyzer = CodeAnalyzer(
        code_elements=set(code_element_to_layer.keys()),
        dependency_handler=dependency_handler  # Pass the handler to the analyzer
    )
    analyzer.analyze()

    logging.info(f"Analysis complete. Found {metrics['total_dependencies']} dependencies(s).")

    # Now also run element-based checks
    # We iterate over each layer and its code elements
    # and run rule.check_element for each rule that supports it.
    logging.info("Running element-based checks ...")
    for layer_name, layer in layers.items():
        for element in layer.code_elements:
            for rule in rules:
                v = rule.check_element(layer_name, element)
                if v:
                    violations.add(v)

    # Generate report
    logging.info("Generating report...")
    report_generator = ReportGenerator(list(violations))
    report = report_generator.generate(format=args.report_format)

    # Output the report
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        logging.info(f"Report written to {output_path}")
    else:
        print("\n")
        print(report)

    # Exit with appropriate status
    if violations:
        print(f"\nTotal violation(s): {len(violations)}")
        exit(1)
    else:
        print("\nNo violations detected.")
        exit(0)


if __name__ == "__main__":
    main()