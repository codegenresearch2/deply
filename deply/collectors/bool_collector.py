import ast
from typing import Any, Dict, List, Set
from pathlib import Path
from deply.models.code_element import CodeElement
from .base_collector import BaseCollector
from .collector_factory import CollectorFactory

class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.paths = paths
        self.exclude_files = exclude_files
        self.must_configs = config.get('must', [])
        self.any_of_configs = config.get('any_of', [])
        self.must_not_configs = config.get('must_not', [])
        self.pre_instantiated_collectors = {}

        # Pre-instantiate collectors based on configurations
        for config in self.must_configs + self.any_of_configs:
            collector = CollectorFactory.create(config, self.paths, self.exclude_files)
            self.pre_instantiated_collectors[config['type']] = collector

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for collector_type, collector in self.pre_instantiated_collectors.items():
            elements.update(collector.match_in_file(file_ast, file_path))
        return elements

    def collect(self) -> Set[CodeElement]:
        must_elements_list = []
        any_of_elements_list = []

        # Collect elements based on must_configs
        for collector_config in self.must_configs:
            collector = self.pre_instantiated_collectors[collector_config['type']]
            must_elements_list.append(set(collector.collect()))

        # Collect elements based on any_of_configs
        for collector_config in self.any_of_configs:
            collector = self.pre_instantiated_collectors[collector_config['type']]
            any_of_elements_list.append(set(collector.collect()))

        # Combine must_elements and any_of_elements
        must_elements = set.intersection(*must_elements_list) if must_elements_list else set()
        any_of_elements = set.union(*any_of_elements_list) if any_of_elements_list else set()

        # Final elements after removing must_not_elements
        final_elements = must_elements & any_of_elements

        return final_elements