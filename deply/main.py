import argparse\nfrom pathlib import Path\n\nfrom .code_analyzer import CodeAnalyzer\nfrom .collectors.collector_factory import CollectorFactory\nfrom .config_parser import ConfigParser\nfrom .models.code_element import CodeElement\nfrom .models.dependency import Dependency\nfrom .models.layer import Layer\nfrom .reports.report_generator import ReportGenerator\nfrom .rules.dependency_rule import DependencyRule\n\n\ndef main():\n    parser = argparse.ArgumentParser(prog='deply', description='Deply')\n    parser.add_argument('--config', required=True, type=str, help='Path to the configuration YAML file')\n    parser.add_argument('--report-format', type=str, choices=['text', 'json', 'html'], default='text', help='Format of the output report')\n    parser.add_argument('--output', type=str, help='Output file for the report')\n    args = parser.parse_args()\n\n    config_path = Path(args.config)\n\n    # Parse configuration\n    config = ConfigParser(config_path).parse()\n\n    # Collect code elements and organize them by layers\n    layers = {}\n    code_element_to_layer = {}\n\n    for layer_config in config['layers']:\n        layer_name = layer_config['name']\n        collectors = layer_config.get('collectors', [])\n        collected_elements = set()\n\n        for collector_config in collectors:\n            collector = CollectorFactory.create(collector_config, config['paths'], config['exclude_files'])\n            collected = collector.collect()\n            collected_elements.update(collected)\n\n        # Initialize Layer with collected code elements\n        layer = Layer(\n            name=layer_name,\n            code_elements=collected_elements,\n            dependencies=set()\n        )\n        layers[layer_name] = layer\n\n        # Map each code element to its layer\n        for element in collected_elements:\n            code_element_to_layer[element] = layer_name\n\n    # Analyze code to find dependencies\n    analyzer = CodeAnalyzer(set(code_element_to_layer.keys()))\n    dependencies = analyzer.analyze()\n\n    # Assign dependencies to respective layers\n    for dependency in dependencies:\n        source_layer_name = code_element_to_layer.get(dependency.code_element)\n        if source_layer_name and source_layer_name in layers:\n            layers[source_layer_name].dependencies.add(dependency)\n\n    # Apply rules\n    rule = DependencyRule(config['ruleset'])\n    violations = rule.check(layers)\n\n    # Generate report\n    report_generator = ReportGenerator(violations)\n    report = report_generator.generate(format=args.report_format)\n\n    # Output the report\n    if args.output:\n        output_path = Path(args.output)\n        output_path.write_text(report)\n    else:\n        print(report)\n\n    # Exit with appropriate status\n    if violations:\n        exit(1)\n    else:\n        exit(0)\n\nif __name__ == '__main__':\n    main()