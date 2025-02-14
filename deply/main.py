import argparse\nimport logging\nimport sys\nfrom pathlib import Path\n\nfrom deply import __version__\nfrom deply.rules import RuleFactory\nfrom .code_analyzer import CodeAnalyzer\nfrom .collectors.collector_factory import CollectorFactory\nfrom .config_parser import ConfigParser\nfrom .models.code_element import CodeElement\nfrom .models.layer import Layer\nfrom .models.violation import Violation\nfrom .reports.report_generator import ReportGenerator\n\n\ndef main():\n    parser = argparse.ArgumentParser(prog=\"deply\", description='Deply - A dependency analysis tool')\n    parser.add_argument('-V', '--version', action='store_true', help='Show the version number and exit')\n    parser.add_argument('-v', '--verbose', action='count', default=1, help='Increase output verbosity')\n\n    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')\n    parser_analyze = subparsers.add_parser('analyze', help='Analyze the project dependencies')\n    parser_analyze.add_argument('--config', type=str, default="deply.yaml", help=\"Path to the configuration YAML file\")\n    parser_analyze.add_argument('--report-format', type=str, choices=['text', 'json', 'html'], default='text',\n                                help=\"Format of the output report\")\n    parser_analyze.add_argument('--output', type=str, help=\"Output file for the report\")\n    args = parser.parse_args()\n\n    if args.version:\n        version = __version__\n        print(f\\"deply {version}\")\n        sys.exit(0)\n\n    # Set up logging\n    log_level = logging.WARNING  # Default log level\n    if args.verbose == 1:\n        log_level = logging.INFO\n    elif args.verbose >= 2:\n        log_level = logging.DEBUG\n\n    logging.basicConfig(\n        level=log_level,\n        format='[%(asctime)s] [%(levelname)s] %(message)s',\n        datefmt='%Y-%m-%d %H:%M:%S'\n    )\n\n    if args.command is None:\n        args = parser.parse_args(['analyze'] + sys.argv[1:])\n\n    logging.info(\"Starting Deply analysis...\")\n\n    # Parse configuration\n    config_path = Path(args.config)\n    logging.info(f\\"Using configuration file: {config_path}\")\n    config = ConfigParser(config_path).parse()\n\n    # Collect code elements and organize them by layers\n    layers = {}\n    code_element_to_layer = {}\n\n    logging.info(\"Collecting code elements for each layer...\")\n    for layer_config in config['layers']:\n        layer_name = layer_config['name']\n        logging.debug(f\\"Processing layer: {layer_name}\")\n        collectors = layer_config.get('collectors', [])\n        collected_elements = set()\n\n        for collector_config in collectors:\n            collector_type = collector_config.get('type', 'unknown')\n            logging.debug(f\\"Using collector: {collector_type} for layer: {layer_name}\")\n            collector = CollectorFactory.create(collector_config, config['paths'], config['exclude_files'])\n            collected_elements.update(collector.collect())\n            logging.debug(f\\"Collected {len(collected_elements)} elements for collector {collector_type}\")\n\n        # Initialize Layer with collected code elements\n        layer = Layer(\n            name=layer_name,\n            code_elements=collected_elements,\n            dependencies=set()  # No longer needed but kept for potential future use\n        )\n        layers[layer_name] = layer\n        logging.info(f\\"Layer '{layer_name}' collected {len(collected_elements)} code elements.\")\n\n        # Map each code element to its layer\n        for element in collected_elements:\n            code_element_to_layer[element] = layer_name\n\n    # Prepare the dependency rule\n    logging.info(\"Preparing dependency rules...\")\n    rules = RuleFactory.create_rules(config['ruleset'])\n\n    # Initialize a list to collect violations and metrics\n    violations = set()\n    metrics = {\n        'total_dependencies': 0,\n    }\n\n    # Define the dependency handler function\n    def dependency_handler(dependency):\n        source_element = dependency.code_element\n        target_element = dependency.depends_on_code_element\n\n        # Determine the layers of the source and target elements\n        source_layer = code_element_to_layer.get(source_element)\n        target_layer = code_element_to_layer.get(target_element)\n\n        # Increment total dependencies metric\n        metrics['total_dependencies'] += 1\n\n        # Skip if target element is not mapped to a layer\n        if not target_layer:\n            return\n\n        # Check the dependency against the rules immediately\n        for rule in rules:\n            violation = rule.check(source_layer, target_layer, dependency)\n            if violation:\n                violations.add(violation)\n\n    # Analyze code to find dependencies and check them immediately\n    logging.info(\"Analyzing code and checking dependencies...\")\n    analyzer = CodeAnalyzer(\n        code_elements=set(code_element_to_layer.keys()),\n        dependency_handler=dependency_handler  # Pass the handler to the analyzer\n    )\n    analyzer.analyze()\n\n    logging.info(f\\"Analysis complete. Found {metrics['total_dependencies']} dependencies(s).\")\n\n    # Generate report\n    logging.info(\"Generating report...\")\n    report_generator = ReportGenerator(list(violations))\n    report = report_generator.generate(format=args.report_format)\n\n    # Output the report\n    if args.output:\n        output_path = Path(args.output)\n        output_path.write_text(report)\n        logging.info(f\\"Report written to {output_path}\")\n    else:\n        print(\"\\n\\")\n        print(report)\n\n    # Exit with appropriate status\n    if violations:\n        print(f\\"\\nTotal violation(s): {len(violations)}\")\n        exit(1)\n    else:\n        print(\"\\nNo violations detected.\")\n        exit(0)\n\n\nif __name__ == '\\"__main__\\"':\n    main()\n