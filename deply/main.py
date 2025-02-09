import argparse\"nimport logging\"nimport sys\"nfrom pathlib import Path\"nfrom deply import __version__\"nfrom deply.rules import RuleFactory\"nfrom deply.code_analyzer import CodeAnalyzer\"nfrom deply.collectors.collector_factory import CollectorFactory\"nfrom deply.config_parser import ConfigParser\"nfrom deply.models.code_element import CodeElement\"nfrom deply.models.layer import Layer\"nfrom deply.models.violation import Violation\"nfrom deply.reports.report_generator import ReportGenerator\"n\"n\"ndef main():\"n    parser = argparse.ArgumentParser(prog='deply', description='Deply - A dependency analysis tool')\"n    parser.add_argument('-V', '--version', action='store_true', help='Show the version number and exit')\"n    parser.add_argument('-v', '--verbose', action='count', default=1, help='Increase output verbosity')\"n\"n    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')\"n    analyze_parser = subparsers.add_parser('analyze', help='Analyze the project dependencies')\"n    analyze_parser.add_argument('--config', type=str, default='deply.yaml', help='Path to the configuration YAML file')\"n    analyze_parser.add_argument('--report-format', type=str, choices=['text', 'json', 'html'], default='text', help='Format of the output report')\"n    analyze_parser.add_argument('--output', type=str, help='Output file for the report')\"n\"n    args = parser.parse_args()\"n\"n    if args.version:\"n        print(f'deply {__version__}')\"n        sys.exit(0)\"n\"n    # Set up logging\"n    log_level = logging.WARNING  # Default log level\"n    if args.verbose == 1:\"n        log_level = logging.INFO\"n    elif args.verbose >= 2:\"n        log_level = logging.DEBUG\"n\"n    logging.basicConfig(\"n        level=log_level,\"n        format='[%(asctime)s] [%(levelname)s] %(message)s',\"n        datefmt='%Y-%m-%d %H:%M:%S'\"n    )\"n\"n    logging.info('Starting Deply analysis...')\"n\"n    # Parse configuration\"n    config_path = Path(args.config)\"n    logging.info(f'Using configuration file: {config_path}')\"n    config = ConfigParser(config_path).parse()\"n\"n    # Collect code elements and organize them by layers\"n    layers = {}\"n    code_element_to_layer = {}\"n\"n    logging.info('Collecting code elements for each layer...')\"n    for layer_config in config['layers']:\"n        layer_name = layer_config['name']\"n        logging.debug(f'Processing layer: {layer_name}')\"n        collectors = layer_config.get('collectors', [])\"n        collected_elements = set()\"n\"n        for collector_config in collectors:\"n            collector_type = collector_config.get('type', 'unknown')\"n            logging.debug(f'Using collector: {collector_type} for layer: {layer_name}')\"n            collector = CollectorFactory.create(collector_config, config['paths'], config['exclude_files'])\"n            collected_elements.update(collector.collect())\"n            logging.debug(f'Collected {len(collected_elements)} elements for collector {collector_type}')\"n\"n        layer = Layer(\"n            name=layer_name,\"n            code_elements=collected_elements,\"n            dependencies=set()\"n        )\"n        layers[layer_name] = layer\"n        logging.info(f'Layer \'{layer_name}\' collected {len(collected_elements)} code elements.')\"n\"n        for element in collected_elements:\"n            code_element_to_layer[element] = layer_name\"n\"n    logging.info('Preparing dependency rules...')\"n    rules = RuleFactory.create_rules(config['ruleset'])\"n\"n    violations = set()\"n    metrics = {'total_dependencies': 0}\"n\"n    def dependency_handler(dependency):\"n        source_element = dependency.code_element\"n        target_element = dependency.depends_on_code_element\"n\"n        source_layer = code_element_to_layer.get(source_element)\"n        target_layer = code_element_to_layer.get(target_element)\"n\"n        if not target_layer:\"n            return\"n\"n        metrics['total_dependencies'] += 1\"n\"n        for rule in rules:\"n            violation = rule.check(source_layer, target_layer, dependency)\"n            if violation:\"n                violations.add(violation)\"n\"n    logging.info('Analyzing code and checking dependencies...')\"n    analyzer = CodeAnalyzer(\"n        code_elements=set(code_element_to_layer.keys()),\"n        dependency_handler=dependency_handler\"n    )\"n    analyzer.analyze()\"n\"n    logging.info(f'Analysis complete. Found {metrics['total_dependencies']} dependencies(s).')\"n\"n    report_generator = ReportGenerator(list(violations))\"n    report = report_generator.generate(format=args.report_format)\"n\"n    if args.output:\"n        output_path = Path(args.output)\"n        output_path.write_text(report)\"n        logging.info(f'Report written to {output_path}')\"n    else:\"n        print(report)\"n\"n    if violations:\"n        print(f'\nTotal violation(s): {len(violations)}')\"n        sys.exit(1)\"n    else:\"n        print('\nNo violations detected.')\"n        sys.exit(0)\"n\"nif __name__ == '__main__':\"n    main()\