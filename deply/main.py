import argparse
import logging
import sys
import re
from pathlib import Path
from typing import List

from deply import __version__
from deply.rules import RuleFactory
from deply.code_analyzer import CodeAnalyzer
from deply.collectors import CollectorFactory
from deply.config_parser import ConfigParser
from deply.models.code_element import CodeElement
from deply.models.layer import Layer
from deply.models.violation import Violation
from deply.reports.report_generator import ReportGenerator

class Deply:
    def __init__(self, config_path: Path):
        self.config = ConfigParser(config_path).parse()
        self.layers = {}
        self.code_element_to_layer = {}
        self.collectors = self.initialize_collectors()
        self.rules = RuleFactory.create_rules(self.config['ruleset'])
        self.violations = set()
        self.metrics = {'total_dependencies': 0}

    def initialize_collectors(self) -> List[CollectorFactory]:
        collectors = []
        for layer_config in self.config['layers']:
            for collector_config in layer_config.get('collectors', []):
                collectors.append(CollectorFactory.create(collector_config, self.config['paths'], self.config['exclude_files']))
        return collectors

    def collect_code_elements(self):
        for layer_config in self.config['layers']:
            layer_name = layer_config['name']
            collected_elements = set()
            for collector in self.collectors:
                if re.match(collector.file_regex, layer_config['name']):
                    collected = collector.collect()
                    collected_elements.update(collected)
            layer = Layer(name=layer_name, code_elements=collected_elements, dependencies=set())
            self.layers[layer_name] = layer
            for element in collected_elements:
                self.code_element_to_layer[element] = layer_name

    def dependency_handler(self, dependency):
        source_element = dependency.code_element
        target_element = dependency.depends_on_code_element
        source_layer = self.code_element_to_layer.get(source_element)
        target_layer = self.code_element_to_layer.get(target_element)
        self.metrics['total_dependencies'] += 1
        if not target_layer:
            return
        for rule in self.rules:
            violation = rule.check(source_layer, target_layer, dependency)
            if violation:
                self.violations.add(violation)

    def analyze(self):
        analyzer = CodeAnalyzer(code_elements=set(self.code_element_to_layer.keys()), dependency_handler=self.dependency_handler)
        analyzer.analyze()

    def generate_report(self, format: str) -> str:
        report_generator = ReportGenerator(list(self.violations))
        return report_generator.generate(format=format)

def main():
    parser = argparse.ArgumentParser(prog="deply", description='Deply - A dependency analysis tool')
    parser.add_argument('-V', '--version', action='store_true', help='Show the version number and exit')
    parser.add_argument('-v', '--verbose', action='count', default=1, help='Increase output verbosity')

    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')
    parser_analyze = subparsers.add_parser('analyze', help='Analyze the project dependencies')
    parser_analyze.add_argument('--config', type=str, default="deply.yaml", help="Path to the configuration YAML file")
    parser_analyze.add_argument('--report-format', type=str, choices=["text", "json", "html"], default="text", help="Format of the output report")
    parser_analyze.add_argument('--output', type=str, help="Output file for the report")
    args = parser.parse_args()

    if args.version:
        print(f"deply {__version__}")
        sys.exit(0)

    log_level = logging.WARNING
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    deply = Deply(Path(args.config))
    deply.collect_code_elements()
    deply.analyze()
    report = deply.generate_report(args.report_format)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        logging.info(f"Report written to {output_path}")
    else:
        print(report)

    if deply.violations:
        print(f"\nTotal violation(s): {len(deply.violations)}")
        sys.exit(1)
    else:
        print("\nNo violations detected.")
        sys.exit(0)

if __name__ == "__main__":
    main()