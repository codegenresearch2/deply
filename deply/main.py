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
from contextlib import redirect_stdout, redirect_stderr
import io

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(prog="deply", description='Deply')
    parser.add_argument("--config", required=True, type=str, help="Path to the configuration YAML file")
    parser.add_argument("--report-format", type=str, choices=["text", "json", "html"], default="text",
                        help="Format of the output report")
    parser.add_argument("--output", type=str, help="Output file for the report")
    args = parser.parse_args()

    config_path = Path(args.config)

    # Parse configuration
    config = ConfigParser(config_path).parse()

    # Collect code elements and organize them by layers
    layers: dict[str, Layer] = {}
    code_element_to_layer: dict[CodeElement, str] = {}

    for layer_config in config['layers']:
        layer_name = layer_config['name']
        collectors = layer_config.get('collectors', [])
        collected_elements: set[CodeElement] = set()

        for collector_config in collectors:
            collector = CollectorFactory.create(collector_config, config['paths'], config['exclude_files'])
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
    dependencies: set[Dependency] = analyzer.analyze()

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

def run_main_with_captured_output(config_path: str, report_format: str, output: str = None) -> (str, str, int):
    # Capture the output
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            # Run main with the test config
            sys.argv = ['main.py', 'analyze', '--config', str(config_path), '--report-format', report_format]
            if output:
                sys.argv.extend(['--output', str(output)])
            main()
        except SystemExit as e:
            exit_code = e.code
    return out.getvalue(), err.getvalue(), exit_code