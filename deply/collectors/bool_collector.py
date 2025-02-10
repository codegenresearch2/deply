import ast
from typing import Any, Dict, List, Set
from pathlib import Path
from deply.models.code_element import CodeElement
from .base_collector import BaseCollector

class BoolCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any], paths: List[str], exclude_files: List[str]):
        self.paths = paths
        self.exclude_files = exclude_files
        self.must_configs = config.get('must', [])
        self.any_of_configs = config.get('any_of', [])
        self.must_not_configs = config.get('must_not', [])
        self.must_collectors = []
        self.any_of_collectors = []
        self.must_not_collectors = []

        # Pre-instantiate collectors based on configurations
        for config in self.must_configs:
            collector = CollectorFactory.create(config, self.paths, self.exclude_files)
            self.must_collectors.append(collector)
        for config in self.any_of_configs:
            collector = CollectorFactory.create(config, self.paths, self.exclude_files)
            self.any_of_collectors.append(collector)
        for config in self.must_not_configs:
            collector = CollectorFactory.create(config, self.paths, self.exclude_files)
            self.must_not_collectors.append(collector)

    def match_in_file(self, file_ast: ast.AST, file_path: Path) -> Set[CodeElement]:
        elements = set()
        for collector in self.must_collectors:
            elements.update(collector.match_in_file(file_ast, file_path))
        return elements

    def collect(self) -> Set[CodeElement]:
        must_elements = set()
        any_of_elements = set()
        must_not_elements = set()

        # Collect elements based on must_configs
        for collector in self.must_collectors:
            must_elements.update(collector.collect())

        # Collect elements based on any_of_configs
        for collector in self.any_of_collectors:
            any_of_elements.update(collector.collect())

        # Collect elements based on must_not_configs
        for collector in self.must_not_collectors:
            must_not_elements.update(collector.collect())

        # Combine must_elements and any_of_elements
        combined_elements = must_elements & any_of_elements

        # Final elements after removing must_not_elements
        final_elements = combined_elements - must_not_elements

        return final_elements